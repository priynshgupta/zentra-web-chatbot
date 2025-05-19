from langchain.chains import RetrievalQA
from app.vector_store import load_vector_store, create_vector_store, get_latest_collection
from langchain_community.document_loaders import (
    WebBaseLoader,
    PyPDFLoader,
    TextLoader,
    Docx2txtLoader,
    CSVLoader,
    JSONLoader
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
import config
import re
import os
import json
import requests
from bs4 import BeautifulSoup
import logging
import urllib3
import hashlib
from urllib.parse import urlparse, urljoin
from app.scraper import get_page_content, extract_links, extract_text, get_page_with_selenium, close_selenium_driver
from app.website_categorizer import WebsiteCategorizer

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

VECTOR_STORE_PATH = os.path.join(os.path.dirname(__file__), '..', 'chroma')
MAPPING_FILE = os.path.join(VECTOR_STORE_PATH, 'vector_store_map.json')

def save_vector_store_mapping(website_url, collection_name):
    # Ensure the directory exists
    os.makedirs(VECTOR_STORE_PATH, exist_ok=True)
    # Load or create the mapping file
    if os.path.exists(MAPPING_FILE):
        with open(MAPPING_FILE, 'r') as f:
            mapping = json.load(f)
    else:
        mapping = {}
    mapping[website_url] = collection_name
    with open(MAPPING_FILE, 'w') as f:
        json.dump(mapping, f)

class DynamicChatbot:
    def __init__(self):
        self.llm = None
        self.qa_chain = None
        self.vector_store = None
        self.is_initialized = False
        self.website_url = None
        self.document_path = None
        self.content_type = None
        self.collection_name = None
        self.website_categorizer = WebsiteCategorizer()
        self.website_categories = None

    def process_document(self, filepath):
        """Process a document and create a new vector store"""
        try:
            if not os.path.exists(filepath):
                return False, f"File not found: {filepath}"

            # Determine file type and load document
            file_extension = os.path.splitext(filepath)[1].lower()

            if file_extension == '.pdf':
                loader = PyPDFLoader(filepath)
                self.content_type = 'PDF Document'
            elif file_extension == '.docx':
                loader = Docx2txtLoader(filepath)
                self.content_type = 'Word Document'
            elif file_extension == '.txt':
                loader = TextLoader(filepath)
                self.content_type = 'Text File'
            elif file_extension == '.md':
                loader = TextLoader(filepath)
                self.content_type = 'Markdown File'
            elif file_extension == '.csv':
                loader = CSVLoader(filepath)
                self.content_type = 'CSV File'
            elif file_extension == '.json':
                loader = JSONLoader(filepath)
                self.content_type = 'JSON File'
            else:
                return False, f"Unsupported file type: {file_extension}"

            logger.info(f"Loading document: {filepath}")
            documents = loader.load()

            if not documents:
                return False, "No content could be extracted from the document."

            # Split the content into chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )
            splits = text_splitter.split_documents(documents)

            if not splits:
                return False, "No text content could be extracted from the document."

            logger.info(f"Creating vector store for document: {filepath}")
            # Create a new vector store with the document content
            self.vector_store = create_vector_store(splits, self.content_type)
            if not self.vector_store:
                return False, "Failed to create vector store from document content."

            self.is_initialized = True
            self.document_path = filepath
            return True, f"{self.content_type} processed successfully. You can now start chatting!"

        except Exception as e:
            logger.error(f"Error processing document: {str(e)}")
            return False, f"Error processing document: {str(e)}"

    def process_website(self, url, socketio=None, sid=None, abort_checker=None):
        """Process a website URL and create a new vector store"""
        try:
            # Validate URL
            if not url.startswith(('http://', 'https://')):
                return False, "Invalid URL format. URL must start with http:// or https://"

            # Advanced browser headers to mimic a real browser
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Cache-Control': 'max-age=0'
            }

            # Process main page with Selenium support
            logger.info(f"Processing main page: {url}")
            main_content, main_error, main_type = get_page_content(url, headers, use_selenium=True)

            if not main_content:
                if (main_error):
                    return False, main_error
                return False, "Could not access the main page of the website."

            # Website categorization to understand site structure
            if main_type == 'html':
                self.website_categories = self.website_categorizer.analyze_content(main_content)
                logger.info(f"Website categorized as: {self.website_categories['primary_industry']} - {self.website_categories['website_type']}")

                # Special handling for different website types
                is_banking = self.website_categories['primary_industry'] == 'banking'
                is_educational = self.website_categories['primary_industry'] in ['education', 'academic']
                is_corporate = self.website_categories['website_type'] == 'corporate'
                is_ecommerce = self.website_categories['primary_industry'] == 'ecommerce'
                is_js_heavy = False  # We'll detect this

                # Adjust crawling parameters based on website type
                max_pages = 200  # Default
                max_depth = 3    # Default
                link_priority = []

                # Customize parameters based on website type
                if is_banking:
                    max_pages = 250
                    max_depth = 4
                    link_priority = ['login', 'account', 'security', 'service', 'faq', 'help']
                    is_js_heavy = True  # Banking sites often use heavy JS
                elif is_educational:
                    max_pages = 300
                    max_depth = 4
                    link_priority = ['course', 'program', 'faculty', 'admission', 'research']
                elif is_corporate:
                    max_pages = 200
                    max_depth = 3
                    link_priority = ['about', 'product', 'service', 'contact', 'career']
                elif is_ecommerce:
                    max_pages = 250
                    max_depth = 3
                    link_priority = ['product', 'category', 'cart', 'checkout', 'account']
                    is_js_heavy = True  # E-commerce sites often use heavy JS

            # Initialize storage for extracted text and URLs
            all_texts = []
            processed_urls = set()
            all_links = set()

            # Process the main page
            if (main_type == 'html'):
                main_text = extract_text(main_content)
                if main_text:
                    all_texts.append(main_text)
                    processed_urls.add(url)

                # Extract links from main page
                main_links = extract_links(main_content, url)

                # If it's likely a JS-heavy site, get additional links with Selenium
                if is_js_heavy or len(main_links) < 5:
                    logger.info("Using Selenium to extract additional links from the main page")
                    selenium_content = get_page_with_selenium(url)
                    if selenium_content:
                        selenium_links = extract_links(selenium_content, url)
                        main_links.extend([link for link in selenium_links if link not in main_links])

                # Remove duplicates and prioritize important links
                main_links = list(dict.fromkeys(main_links))
                if link_priority:
                    prioritized = []
                    remaining = []
                    for link in main_links:
                        if any(term in link.lower() for term in link_priority):
                            prioritized.append(link)
                        else:
                            remaining.append(link)
                    main_links = prioritized + remaining

                logger.info(f"Found {len(main_links)} unique links on the main page")
                all_links.update(main_links)

            elif main_type in ['pdf', 'docx']:
                # Handle document files
                try:
                    if main_type == 'pdf':
                        loader = PyPDFLoader(main_content)
                    else:
                        loader = Docx2txtLoader(main_content)
                    docs = loader.load()
                    for doc in docs:
                        all_texts.append(doc.page_content)
                    processed_urls.add(url)

                    # For document files, we're done
                    return self._create_vector_store(url, all_texts)
                except Exception as e:
                    logger.warning(f"Failed to process {main_type.upper()}: {url} ({e})")
                    return False, f"Error processing {main_type.upper()}: {e}"

            # BFS crawling with multiple levels
            to_process = main_links
            next_level = []
            current_depth = 0

            # For progress estimation
            total_estimated = len(to_process) + 50  # Initial estimate

            # Create a list of pages we should process with Selenium (more important pages)
            selenium_priority_urls = set()
            if is_js_heavy:
                # For JS-heavy sites, process more pages with Selenium
                selenium_pages_limit = min(50, max_pages // 2)
                for link in to_process[:selenium_pages_limit]:
                    selenium_priority_urls.add(link)
            else:
                # For other sites, just use Selenium for key pages
                for link in to_process:
                    if any(term in link.lower() for term in link_priority):
                        selenium_priority_urls.add(link)

            while current_depth < max_depth and len(processed_urls) < max_pages:
                if not to_process:
                    # Move to next depth level if available
                    if next_level:
                        to_process = next_level
                        next_level = []
                        current_depth += 1
                        logger.info(f"Moving to depth {current_depth} with {len(to_process)} links")
                    else:
                        break  # No more links to process

                # Get next URL to process
                if not to_process:
                    break

                current_url = to_process.pop(0)

                # ABORT CHECK
                if abort_checker and abort_checker():
                    logger.info(f"Aborting website processing for sid {sid}")
                    # Clean up Selenium resources
                    close_selenium_driver()
                    return False, "Processing aborted by user."

                # Skip if already processed or points to the same page with a different fragment
                if current_url in processed_urls:
                    continue

                parsed_url = urlparse(current_url)
                base_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
                if any(urlparse(p).netloc == parsed_url.netloc and urlparse(p).path == parsed_url.path for p in processed_urls):
                    continue

                # Decide whether to use Selenium for this URL
                use_selenium_for_url = current_url in selenium_priority_urls or is_js_heavy

                # Process the current URL
                try:
                    logger.info(f"Processing page: {current_url} (selenium: {use_selenium_for_url})")
                    page_content, page_error, page_type = get_page_content(
                        current_url,
                        headers,
                        use_selenium=use_selenium_for_url
                    )

                    if page_content and page_type == 'html':
                        page_text = extract_text(page_content)
                        if page_text:
                            all_texts.append(page_text)
                            processed_urls.add(current_url)

                            # Extract links for next depth level
                            if current_depth < max_depth - 1:
                                new_links = extract_links(page_content, current_url)

                                # For important pages, also try to get links with Selenium if we haven't already
                                if not use_selenium_for_url and (
                                    len(new_links) < 3 or
                                    any(term in current_url.lower() for term in ['index', 'home', 'main', 'about'])
                                ):
                                    selenium_content = get_page_with_selenium(current_url)
                                    if selenium_content:
                                        selenium_links = extract_links(selenium_content, current_url)
                                        new_links.extend([link for link in selenium_links if link not in new_links])

                                for new_link in new_links:
                                    parsed_new = urlparse(new_link)
                                    base_new = f"{parsed_new.scheme}://{parsed_new.netloc}{parsed_new.path}"

                                    # Skip already processed URLs
                                    if (new_link not in processed_urls and
                                        new_link not in to_process and
                                        new_link not in next_level and
                                        new_link not in all_links and
                                        not any(urlparse(p).netloc == parsed_new.netloc and
                                                urlparse(p).path == parsed_new.path for p in processed_urls)):
                                        next_level.append(new_link)
                                        all_links.add(new_link)

                                        # Decide whether to mark this new URL for Selenium processing
                                        if is_js_heavy or any(term in new_link.lower() for term in link_priority):
                                            selenium_priority_urls.add(new_link)

                        logger.info(f"Processed page: {current_url}")

                        # Update progress estimate
                        total_estimated = max(total_estimated, len(processed_urls) + len(to_process) + len(next_level))

                        # Emit progress to the frontend
                        if socketio and sid:
                            socketio.emit(
                                'scraping_progress',
                                {
                                    'link': current_url,
                                    'current': len(processed_urls),
                                    'total': min(max_pages, total_estimated),
                                    'depth': current_depth + 1,
                                    'max_depth': max_depth
                                },
                                room=sid
                            )

                    elif page_content and page_type in ['pdf', 'docx']:
                        try:
                            if page_type == 'pdf':
                                loader = PyPDFLoader(page_content)
                            else:
                                loader = Docx2txtLoader(page_content)
                            docs = loader.load()
                            for doc in docs:
                                all_texts.append(doc.page_content)
                            processed_urls.add(current_url)
                        except Exception as e:
                            logger.warning(f"Failed to process {page_type.upper()}: {current_url} ({e})")

                except Exception as e:
                    logger.error(f"Error processing page {current_url}: {str(e)}")

            # Clean up Selenium resources
            close_selenium_driver()

            # If we've processed too many pages, log it
            if len(processed_urls) >= max_pages:
                logger.info(f"Reached maximum page limit of {max_pages}")

            logger.info(f"Finished processing website. Pages processed: {len(processed_urls)}")
            logger.info(f"Total links found: {len(all_links)}")

            # Create vector store from extracted texts
            return self._create_vector_store(url, all_texts)

        except Exception as e:
            logger.error(f"Error processing website: {str(e)}")
            # Clean up Selenium resources
            close_selenium_driver()
            return False, f"Error processing website: {str(e)}"

    def _create_vector_store(self, url, all_texts):
        """Helper method to create a vector store from extracted texts"""
        if not all_texts:
            return False, "No text content could be extracted from the website."

        # Create documents from the extracted text
        documents = []
        for text in all_texts:
            if text.strip():
                documents.append(Document(page_content=text))

        # Split the content into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        splits = text_splitter.split_documents(documents)

        if not splits:
            return False, "No text content could be extracted from the website."

        logger.info(f"Created {len(splits)} chunks from {len(documents)} pages")

        # Create a unique collection name for this website
        url_hash = hashlib.md5(url.encode()).hexdigest()
        collection_name = f"website_{url_hash}"
        self.vector_store = create_vector_store(splits, "Website", collection_name=collection_name)
        self.collection_name = collection_name

        self.is_initialized = True
        self.website_url = url
        self.content_type = 'Website'
        save_vector_store_mapping(url, collection_name)
        return True, {
            "message": f"Website processed successfully. Scraped {len(documents)} pages. You can now start chatting!",
            "categories": self.website_categories
        }

    def get_response(self, user_query):
        """Get response from the chatbot with improved context retrieval and prompt engineering"""
        if not self.is_initialized:
            return "Please provide a website URL or upload a document first."

        try:
            if not self.vector_store:
                return "Error: Vector store not initialized. Please try processing the website or document again."

            # Enhanced retrieval with more relevant documents and hybrid search
            retriever = self.vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={
                    "k": 5,  # Increased from 2 to 5 for more context
                    # Removed fetch_k parameter as it's not supported
                    # Removed score_threshold parameter as it's not supported
                }
            )

            # First attempt with original query
            relevant_docs = retriever.get_relevant_documents(user_query)

            # If we didn't get good results, try with query reformulation
            if len(relevant_docs) < 2:
                # Try with a simpler version of the query
                simplified_query = re.sub(r'[^\w\s]', '', user_query).lower()
                simple_docs = retriever.get_relevant_documents(simplified_query)

                # Combine results, prioritizing original query results
                seen_contents = set(doc.page_content for doc in relevant_docs)
                for doc in simple_docs:
                    if doc.page_content not in seen_contents:
                        relevant_docs.append(doc)
                        seen_contents.add(doc.page_content)

                # If still not enough, try keyword extraction
                if len(relevant_docs) < 3:
                    # Extract keywords from query (simple approach)
                    stop_words = {'a', 'an', 'the', 'and', 'or', 'but', 'is', 'are', 'was', 'were',
                                'in', 'on', 'at', 'to', 'for', 'with', 'by', 'about', 'as', 'of'}
                    keywords = [word.lower() for word in user_query.split()
                               if word.lower() not in stop_words and len(word) > 2]

                    # Search for each keyword
                    for keyword in keywords:
                        if len(keyword) > 3:  # Only use substantial keywords
                            keyword_docs = retriever.get_relevant_documents(keyword)
                            for doc in keyword_docs:
                                if doc.page_content not in seen_contents:
                                    relevant_docs.append(doc)
                                    seen_contents.add(doc.page_content)
                                    if len(relevant_docs) >= 8:  # Cap at 8 docs
                                        break
                            if len(relevant_docs) >= 8:
                                break

            # Limit to top most relevant documents
            relevant_docs = relevant_docs[:8]

            if not relevant_docs:
                return "I couldn't find any relevant information in the provided content."

            # Format the context from relevant documents with better structure
            context_parts = []
            for i, doc in enumerate(relevant_docs, 1):
                content = doc.page_content.strip()
                if content:
                    # Add snippet numbers for better organization in prompt
                    context_parts.append(f"[Snippet {i}]: {content}")

            if not context_parts:
                return "I couldn't find any relevant information in the provided content."

            context = "\n\n".join(context_parts)

            # Enhanced prompt with better instructions for using retrieved context
            prompt = f"""

You are a helpful assistant that answers questions based ONLY on the provided website content. You must NOT make up or add any information that is not explicitly stated in the content.

Website Content:
{context}

User Question: {user_query}

Instructions:
1. Focus on directly answering the user's question using ONLY the information in the website content snippets provided above.
2. Read all snippets carefully before answering. The information may be spread across multiple snippets.
3. If the snippets contain contradictory information, mention this to the user.
4. If the answer is not stated in any of the snippets, respond with "Based on the website content available to me, I cannot find specific information about [topic of question]."
5. Do not invent or assume any information not present in the snippets.
6. Cite the snippet numbers in your answer when referring to specific information.
7. Structure your answer clearly and concisely.
8. If the user is looking for detailed technical information not provided in the snippets, acknowledge this limitation.

Please provide your answer based only on the website content above.
"""

            # Get response from the model
            # Try to use a more descriptive system message that helps the model understand context usage
            model_name = "llama3"  # Default model

            # Get response from the model with appropriate formatting
            response = ollama_generate(prompt, model=model_name)

            # Extract the generated text from the response
            if isinstance(response, list) and len(response) > 0:
                generated_text = response[0].get('generated_text', '')
            elif isinstance(response, dict):
                generated_text = response.get('generated_text', '')
            else:
                generated_text = str(response)

            # Clean up the response
            answer = generated_text.strip()
            if answer.startswith("Answer:"):
                answer = answer[7:].trip()

            # Remove the explicit snippet references if present in final output
            answer = re.sub(r'\[Snippet \d+\]:', '', answer)
            answer = re.sub(r'Snippet \d+:', '', answer)

            # Don't include the raw sources as they're already integrated into the answer
            return answer

        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return f"Error generating response: {str(e)}"

    def handle_input(self, user_input):
        """Handle user input and determine the appropriate response"""
        if not self.is_initialized:
            # Check if the input looks like a URL
            if user_input.startswith(('http://', 'https://')):
                success, message = self.process_website(user_input)
                if success:
                    return f"Great! I've processed {user_input}. You can now ask me questions about this website."
                else:
                    return message
            else:
                return "Please provide a valid website URL (starting with http:// or https://) or upload a document to begin."

        # If already initialized, process as a normal chat query
        return self.get_response(user_input)

    def get_website_categories(self):
        """Get the current website's categories"""
        return self.website_categories

# Create a global instance of the chatbot
chatbot = DynamicChatbot()

def get_response(user_input):
    """Global function to handle user input and get response"""
    return chatbot.handle_input(user_input)

def process_website(url, socketio=None, sid=None, abort_checker=None):
    """Global function to process a website"""
    return chatbot.process_website(url, socketio=socketio, sid=sid, abort_checker=abort_checker)

def process_document(filepath):
    """Global function to process a document"""
    return chatbot.process_document(filepath)

def ollama_generate(prompt, model="llama3"):
    """
    Generate text using the specified model.
    Falls back to OpenAI or Hugging Face API when deployed.
    """
    # Check if we're in a deployed environment (Heroku)
    if os.environ.get("HEROKU_APP_NAME"):
        # Option 1: Use OpenAI API if API key is configured
        if os.environ.get("OPENAI_API_KEY"):
            try:
                import openai
                openai.api_key = os.environ.get("OPENAI_API_KEY")
                logger.info("Using OpenAI API for response generation")
                response = openai.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "system", "content": "You are a helpful assistant."},
                              {"role": "user", "content": prompt}],
                    max_tokens=1024,
                    temperature=0.7
                )
                return response.choices[0].message.content
            except Exception as e:
                logger.error(f"Error using OpenAI API: {e}")
                # Fall through to next option if OpenAI fails

        # Option 2: Use Hugging Face API if API key is configured
        if os.environ.get("HUGGINGFACEHUB_API_TOKEN"):
            try:
                from langchain_huggingface import HuggingFaceEndpoint
                logger.info("Using Hugging Face API for response generation")
                llm = HuggingFaceEndpoint(
                    endpoint_url=f"https://api-inference.huggingface.co/models/meta-llama/Meta-Llama-3-8B-Instruct",
                    huggingfacehub_api_token=os.environ.get("HUGGINGFACEHUB_API_TOKEN"),
                    task="text-generation",
                    max_length=1024
                )
                return llm.invoke(prompt)
            except Exception as e:
                logger.error(f"Error using Hugging Face API: {e}")
                # Fall through to fallback if Hugging Face fails

        # Option 3: Fallback to our dedicated fallback model implementation
        try:
            from app.fallback_model import get_fallback_model
            logger.info("Using local fallback model")

            # Check if we need to use minimal resources mode
            if os.environ.get("MINIMAL_RESOURCES") == "true":
                logger.info("Using minimal resources mode")

            # Get properly configured fallback model
            fallback_model = get_fallback_model()
            return fallback_model(prompt)

        except Exception as e:
            logger.error(f"Error using fallback model: {e}")
            return "I'm sorry, I couldn't process that request. The fallback language model encountered an error."

    # Local development - use Ollama
    else:
        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={"model": model, "prompt": prompt}
            )
            response.raise_for_status()
            result = ""
            for line in response.text.strip().splitlines():
                if line.strip():
                    data = json.loads(line)
                    result += data.get("response", "")
            return result
        except Exception as e:
            print(f"Error using Ollama: {e}")
            # Fallback to a simple response if Ollama is not available
            return "I'm sorry, I couldn't process that request. The language model is currently unavailable."
