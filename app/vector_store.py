from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import SentenceTransformerEmbeddings
import os
import config
import logging
import time
from typing import List, Optional, Dict, Any
from langchain.schema import Document
import torch
import json

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
VECTOR_STORE_DIR = os.path.join(os.path.dirname(__file__), "..", "vector_store")
CHROMA_DIR = os.path.join(os.path.dirname(__file__), "..", "chroma")
MAPPING_FILE = os.path.join(CHROMA_DIR, "vector_store_map.json")

# Ensure directories exist
os.makedirs(VECTOR_STORE_DIR, exist_ok=True)
os.makedirs(CHROMA_DIR, exist_ok=True)

class VectorStoreManager:
    """Class to manage vector store operations"""

    @staticmethod
    def get_embeddings():
        """
        Get embedding model with improved parameters for better semantic understanding
        """
        try:
            # Use more advanced sentence transformer model for better semantic understanding
            return SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
        except Exception as e:
            logger.error(f"Error loading embeddings model: {str(e)}")
            # Fallback to a simpler model
            return SentenceTransformerEmbeddings(model_name="all-mpnet-base-v2")

    def create_vector_store(self, documents: List[Document], source_type: str, collection_name: Optional[str] = None) -> Optional[Chroma]:
        """
        Create a new vector store with the provided documents.

        Args:
            documents: List of documents to add to the vector store
            source_type: Type of the source (Website, PDF Document, etc.)
            collection_name: Optional name for the collection

        Returns:
            Chroma vector store object or None if creation failed
        """
        try:
            if not documents:
                logger.warning("No documents provided to create vector store")
                return None

            # Generate a collection name if not provided
            if not collection_name:
                timestamp = int(time.time())
                collection_name = f"{source_type.lower().replace(' ', '_')}_{timestamp}"

            logger.info(f"Creating vector store with {len(documents)} documents in collection '{collection_name}'")

            # Get embedding function
            embeddings = self.get_embeddings()

            # Add metadata to documents for better retrieval
            for i, doc in enumerate(documents):
                if not hasattr(doc, 'metadata') or doc.metadata is None:
                    doc.metadata = {}
                doc.metadata["source"] = source_type
                doc.metadata["chunk_id"] = i
                doc.metadata["collection"] = collection_name

            # Create vector store with optimized parameters
            vector_store = Chroma.from_documents(
                documents=documents,
                embedding=embeddings,
                persist_directory=VECTOR_STORE_DIR,
                collection_name=collection_name,
                collection_metadata={"source": source_type, "created_at": time.time()}
            )

            # Persist the vector store
            vector_store.persist()
            logger.info(f"Vector store created and persisted: {collection_name}")

            return vector_store
        except Exception as e:
            logger.error(f"Error creating vector store: {str(e)}")
            return None

    def load_vector_store(self, collection_name: str) -> Optional[Chroma]:
        """
        Load an existing vector store by collection name

        Args:
            collection_name: Name of the collection to load

        Returns:
            Chroma vector store object or None if loading failed
        """
        try:
            logger.info(f"Loading vector store collection: {collection_name}")
            embeddings = self.get_embeddings()

            vector_store = Chroma(
                persist_directory=VECTOR_STORE_DIR,
                embedding_function=embeddings,
                collection_name=collection_name
            )

            # Verify the collection has documents
            if vector_store._collection.count() == 0:
                logger.warning(f"Vector store collection '{collection_name}' is empty")
                return None

            logger.info(f"Vector store loaded: {collection_name} with {vector_store._collection.count()} documents")
            return vector_store
        except Exception as e:
            logger.error(f"Error loading vector store: {str(e)}")
            return None

    def get_vector_store_for_url(self, url: str) -> Optional[Chroma]:
        """
        Get vector store for a specific URL from the mapping file

        Args:
            url: URL to get the vector store for

        Returns:
            Chroma vector store object or None if not found
        """
        try:
            if not os.path.exists(MAPPING_FILE):
                logger.warning(f"Vector store mapping file not found: {MAPPING_FILE}")
                return None

            with open(MAPPING_FILE, 'r') as f:
                mapping = json.load(f)

            if url not in mapping:
                logger.warning(f"No vector store mapping found for URL: {url}")
                return None

            collection_name = mapping[url]
            return self.load_vector_store(collection_name)
        except Exception as e:
            logger.error(f"Error getting vector store for URL: {str(e)}")
            return None

    def get_latest_collection(self) -> Optional[str]:
        """
        Get the name of the latest collection in the vector store

        Returns:
            Name of the latest collection or None if no collections found
        """
        try:
            # Initialize Chroma client
            embeddings = self.get_embeddings()
            client = Chroma(persist_directory=VECTOR_STORE_DIR, embedding_function=embeddings)

            # Get all collections
            collections = client._client.list_collections()

            if not collections:
                logger.warning("No collections found in vector store")
                return None

            # Get the latest collection (assuming collection names include timestamps)
            latest_collection = collections[-1].name
            logger.info(f"Latest collection: {latest_collection}")
            return latest_collection
        except Exception as e:
            logger.error(f"Error getting latest collection: {str(e)}")
            return None

    def hybrid_search(self, vector_store: Chroma, query: str, k: int = 5) -> List[Document]:
        """
        Perform hybrid search (combining vector similarity and keyword matching) for better retrieval

        Args:
            vector_store: Chroma vector store to search in
            query: Query string
            k: Number of documents to retrieve

        Returns:
            List of retrieved documents
        """
        try:
            # Get documents by vector similarity
            vector_docs = vector_store.similarity_search(query, k=k)

            # Get document IDs to avoid duplicates
            doc_ids = set(doc.metadata.get("chunk_id", i) for i, doc in enumerate(vector_docs))

            # Get additional documents by keyword matching if available
            try:
                # Use max_marginal_relevance_search with only required parameters
                # Without fetch_k parameter that's causing the error
                keyword_docs = vector_store.max_marginal_relevance_search(
                    query, k=k
                )

                # Add non-duplicate keyword docs
                for doc in keyword_docs:
                    doc_id = doc.metadata.get("chunk_id")
                    if doc_id not in doc_ids:
                        vector_docs.append(doc)
                        doc_ids.add(doc_id)
                        if len(vector_docs) >= k*2:
                            break
            except Exception as mmr_error:
                # Log the specific error with max_marginal_relevance_search
                logger.warning(f"MMR search not supported: {str(mmr_error)}. Using vector similarity only.")
                pass

            return vector_docs
        except Exception as e:
            logger.error(f"Error in hybrid search: {str(e)}")
            return []

# Create a global instance of the vector store manager
vector_store_manager = VectorStoreManager()

# Global functions that use the manager
def get_embeddings():
    """Global function to get embeddings"""
    return vector_store_manager.get_embeddings()

def create_vector_store(documents: List[Document], content_type: str, collection_name: str = None) -> Optional[Chroma]:
    """Global function to create a vector store"""
    return vector_store_manager.create_vector_store(documents, content_type, collection_name=collection_name)

def load_vector_store(collection_name: str) -> Optional[Chroma]:
    """Global function to load a vector store"""
    return vector_store_manager.load_vector_store(collection_name)

def get_latest_collection() -> Optional[str]:
    """Global function to get the latest collection"""
    return vector_store_manager.get_latest_collection()

def hybrid_search(vector_store: Chroma, query: str, k: int = 5) -> List[Document]:
    """Global function to perform hybrid search"""
    return vector_store_manager.hybrid_search(vector_store, query, k=k)

def save_vector_store_mapping(website_url, collection_name):
    """Save mapping between website URL and vector store collection name"""
    # Ensure the directory exists
    os.makedirs(CHROMA_DIR, exist_ok=True)
    # Load or create the mapping file
    if os.path.exists(MAPPING_FILE):
        with open(MAPPING_FILE, 'r') as f:
            mapping = json.load(f)
    else:
        mapping = {}
    mapping[website_url] = collection_name
    with open(MAPPING_FILE, 'w') as f:
        json.dump(mapping, f)
