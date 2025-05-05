from langchain_community.document_loaders import WebBaseLoader
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import hashlib
import logging
import time
import re
import tempfile
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a global Selenium driver that can be reused
_driver = None

def get_selenium_driver():
    """Get or create a Selenium WebDriver instance with appropriate settings."""
    global _driver

    if _driver is not None:
        try:
            # Check if existing driver is still working
            _driver.current_url
            return _driver
        except:
            # If driver is not responsive, close and create a new one
            try:
                _driver.quit()
            except:
                pass
            _driver = None

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--remote-debugging-port=9222")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")

    # Set user agent to mimic a real browser
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

    try:
        _driver = webdriver.Chrome(options=options)
        _driver.set_page_load_timeout(30)
        return _driver
    except Exception as e:
        logger.error(f"Error creating Selenium driver: {str(e)}")
        return None

def close_selenium_driver():
    """Close the Selenium WebDriver if it exists."""
    global _driver
    if _driver is not None:
        try:
            _driver.quit()
        except:
            pass
        _driver = None

def extract_data(url, max_pages=100, same_domain=True):
    """Extract data from a given URL. For websites, crawl up to max_pages."""
    # Heuristic: if it's a web page, use multi-page; if it's a file, use WebBaseLoader
    if url.lower().endswith(('.pdf', '.docx', '.txt', '.md', '.csv', '.json')):
        try:
            loader = WebBaseLoader(url)
            documents = loader.load()
            return documents
        except Exception as e:
            logger.error(f"Error extracting data: {str(e)}")
            return None
    else:
        return extract_data_multi_page(url, max_pages=max_pages, same_domain=same_domain)

def extract_data_multi_page(start_url, max_pages=100, same_domain=True):
    """Extract data from a start URL and crawl internal links up to max_pages, only following links containing the original path."""
    visited = set()
    to_visit = [start_url]
    all_documents = []

    domain = urlparse(start_url).netloc
    original_path = urlparse(start_url).path

    while to_visit and len(visited) < max_pages:
        url = to_visit.pop(0)
        if url in visited:
            continue
        try:
            resp = requests.get(url)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            # Extract main content (customize as needed)
            main_content = soup.get_text()
            all_documents.append({"url": url, "content": main_content})

            # Find all internal links
            for a in soup.find_all("a", href=True):
                link = urljoin(url, a["href"])
                link_parsed = urlparse(link)
                # Only follow links that are on the same domain and contain the original path
                if same_domain and link_parsed.netloc != domain:
                    continue
                if original_path not in link_parsed.path:
                    continue
                if link not in visited and link not in to_visit and link.startswith("http"):
                    to_visit.append(link)
        except Exception as e:
            logger.error(f"Error extracting {url}: {str(e)}")
        visited.add(url)
    return all_documents

def get_page_content(page_url, headers, retries=3, timeout=30, use_selenium=True):
    """
    Get the content of a web page with advanced handling for JavaScript rendering.

    Args:
        page_url: The URL to fetch
        headers: HTTP headers to use with requests
        retries: Number of retry attempts
        timeout: Request timeout in seconds
        use_selenium: Whether to attempt JavaScript rendering with Selenium

    Returns:
        Tuple of (content, error message, content type)
    """
    # First try with regular requests for better performance
    for attempt in range(retries):
        try:
            # Add random delay between attempts to avoid triggering rate limits
            if attempt > 0:
                delay = 2 + attempt * 2  # Increasing backoff
                time.sleep(delay)

            # Normalize URL
            page_url = normalize_url(page_url)

            # Try standard requests first
            response = requests.get(
                page_url,
                headers=headers,
                timeout=timeout,
                verify=False,
                allow_redirects=True
            )
            response.raise_for_status()

            # Check if the content is actually HTML (some servers report wrong content-type)
            content_type = response.headers.get('content-type', '').lower()
            content = response.content

            # If it's HTML, return the text content
            if 'text/html' in content_type or content.strip().startswith(b'<!DOCTYPE html>') or content.strip().startswith(b'<html'):
                # Try to detect encoding correctly
                encoding = response.encoding or 'utf-8'
                try:
                    html_content = content.decode(encoding)
                except UnicodeDecodeError:
                    html_content = content.decode('utf-8', errors='replace')

                # If the page seems to be very small or might be JavaScript-heavy, try with Selenium
                if len(html_content.strip()) < 5000 and use_selenium:
                    selenium_content = get_page_with_selenium(page_url)
                    if selenium_content and len(selenium_content) > len(html_content):
                        logger.info(f"Using Selenium-rendered content for {page_url} (static: {len(html_content)} bytes, dynamic: {len(selenium_content)} bytes)")
                        return selenium_content, None, 'html'

                return html_content, None, 'html'

            # Handle different file types
            elif 'application/pdf' in content_type or page_url.lower().endswith('.pdf'):
                return handle_binary_file(content, page_url, 'pdf')

            elif ('application/msword' in content_type or
                  'application/vnd.openxmlformats-officedocument.wordprocessingml.document' in content_type or
                  page_url.lower().endswith(('.doc', '.docx'))):
                return handle_binary_file(content, page_url, 'docx')

            elif 'text/plain' in content_type or page_url.lower().endswith(('.txt', '.csv')):
                # For plain text files
                return content.decode('utf-8', errors='replace'), None, 'text'

            else:
                # For unrecognized content types, try with Selenium if it's likely HTML
                if use_selenium:
                    selenium_content = get_page_with_selenium(page_url)
                    if selenium_content:
                        return selenium_content, None, 'html'

                # As a fallback, try to process as HTML anyway
                try:
                    html_content = content.decode('utf-8', errors='replace')
                    if "<html" in html_content or "<body" in html_content:
                        return html_content, None, 'html'
                    else:
                        return None, f"Unsupported content type: {content_type}", None
                except:
                    return None, f"Unsupported content type: {content_type}", None

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching {page_url} with requests (attempt {attempt+1}/{retries}): {str(e)}")

            # Special handling for common errors
            if isinstance(e, requests.exceptions.SSLError):
                logger.warning(f"SSL error for {page_url}, trying with verify=False")
                try:
                    response = requests.get(
                        page_url,
                        headers=headers,
                        timeout=timeout,
                        verify=False,
                        allow_redirects=True
                    )
                    response.raise_for_status()
                    return response.text, None, 'html'
                except:
                    pass

            # If regular request fails and we haven't tried Selenium yet, try with Selenium
            if use_selenium and attempt == retries - 1:
                logger.info(f"Trying {page_url} with Selenium after requests failure")
                selenium_content = get_page_with_selenium(page_url)
                if selenium_content:
                    return selenium_content, None, 'html'

            if attempt >= retries - 1:
                return None, str(e), None

        except Exception as e:
            logger.error(f"Unknown error fetching {page_url}: {str(e)}")

            # Try Selenium as a last resort
            if use_selenium and attempt == retries - 1:
                selenium_content = get_page_with_selenium(page_url)
                if selenium_content:
                    return selenium_content, None, 'html'

            if attempt >= retries - 1:
                return None, str(e), None

def get_page_with_selenium(url, wait_time=10):
    """
    Get page content using Selenium WebDriver with JavaScript execution.

    Args:
        url: The URL to fetch
        wait_time: Time to wait for page to load in seconds

    Returns:
        HTML content as string or None if failed
    """
    try:
        driver = get_selenium_driver()
        if not driver:
            return None

        # Load the page
        logger.info(f"Loading {url} with Selenium WebDriver")
        driver.get(url)

        # Wait for the page to load (body to be present)
        WebDriverWait(driver, wait_time).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        # Additional wait for potential AJAX content
        time.sleep(3)

        # Click on any "Accept Cookies" or similar buttons to get to the content
        try:
            cookie_buttons = driver.find_elements(By.XPATH,
                "//button[contains(text(), 'Accept') or contains(text(), 'accept') or contains(text(), 'Cookie') or contains(text(), 'cookie') or contains(@id, 'cookie') or contains(@class, 'cookie')]"
            )
            for button in cookie_buttons:
                button.click()
                time.sleep(1)
        except:
            pass

        # Extract all links while we have the browser open
        links = extract_selenium_links(driver, url)

        # Get page source after JavaScript execution
        page_source = driver.page_source

        return page_source

    except TimeoutException:
        logger.warning(f"Timeout while loading {url} with Selenium")
        # Even if timeout occurs, try to get whatever content was loaded
        try:
            return driver.page_source
        except:
            return None
    except WebDriverException as e:
        logger.error(f"Selenium WebDriver error for {url}: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error with Selenium for {url}: {str(e)}")
        return None

def extract_selenium_links(driver, base_url):
    """
    Extract all links from a page loaded in Selenium WebDriver.

    Args:
        driver: Selenium WebDriver instance with loaded page
        base_url: The base URL for resolving relative links

    Returns:
        List of normalized URLs
    """
    links = []
    base_domain = urlparse(base_url).netloc

    try:
        # Get all href attributes from a tags
        elements = driver.find_elements(By.TAG_NAME, "a")
        for element in elements:
            try:
                href = element.get_attribute("href")
                if href and not href.startswith(('javascript:', '#')):
                    parsed = urlparse(href)
                    if not parsed.netloc or parsed.netloc == base_domain:
                        links.append(href)
            except:
                continue

        # Also find links in buttons and other clickable elements
        clickable_elements = driver.find_elements(
            By.XPATH,
            "//button | //*[@onclick] | //*[@role='button'] | //*[contains(@class, 'btn')]"
        )

        for element in clickable_elements:
            try:
                # Check for onclick attribute
                onclick = element.get_attribute("onclick")
                if onclick and ('location' in onclick or 'href' in onclick):
                    # Extract URL from onclick using regex
                    urls = re.findall(r"(?:location\.href|window\.location)\s*=\s*['\"]([^'\"]+)['\"]", onclick)
                    for url in urls:
                        if url and not url.startswith('javascript:'):
                            links.append(urljoin(base_url, url))
            except:
                continue

    except Exception as e:
        logger.error(f"Error extracting links with Selenium: {str(e)}")

    # Normalize and deduplicate links
    normalized_links = []
    for link in links:
        try:
            norm_link = normalize_url(link)
            if norm_link not in normalized_links:
                normalized_links.append(norm_link)
        except:
            continue

    return normalized_links

def normalize_url(url):
    """Normalize a URL by removing fragments and trailing slashes."""
    parsed = urlparse(url)
    # Remove fragments
    normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    # Remove trailing slash unless it's the root path
    if normalized.endswith('/') and len(normalized) > len(f"{parsed.scheme}://{parsed.netloc}/"):
        normalized = normalized[:-1]
    # Add query parameters if they exist
    if parsed.query:
        normalized += f"?{parsed.query}"
    return normalized

def handle_binary_file(content, url, file_type):
    """Handle binary file content like PDF or DOCX by saving to temp file."""
    # Create a temporary file with the right extension
    fd, tmp_path = tempfile.mkstemp(suffix=f".{file_type}")
    os.close(fd)

    # Write the content to the temporary file
    with open(tmp_path, 'wb') as f:
        f.write(content)

    return tmp_path, None, file_type

def extract_links(html_content, base_url):
    """
    Extract all links from an HTML page.

    Args:
        html_content: HTML content as string
        base_url: Base URL for resolving relative links

    Returns:
        List of normalized URLs
    """
    if not html_content:
        return []

    soup = BeautifulSoup(html_content, 'html.parser')
    links = []
    parsed_base = urlparse(base_url)
    base_domain = parsed_base.netloc
    base_url_no_fragment = f"{parsed_base.scheme}://{base_domain}{parsed_base.path}"

    # Look for links in href attributes of a tags
    for a in soup.find_all('a', href=True):
        href = a['href']

        # Skip JavaScript pseudo-links and empty links
        if href.startswith('javascript:') or href == "#" or not href:
            continue

        # Skip fragment-only links that point to the same page (e.g., #section1)
        # But keep track of the base URL so we don't miss content
        if href.startswith('#'):
            if base_url_no_fragment not in links:
                links.append(base_url_no_fragment)
            continue

        # Handle relative URLs
        if href.startswith('/'):
            href = f"{parsed_base.scheme}://{base_domain}{href}"
        elif not href.startswith(('http://', 'https://')):
            # Handle URLs without leading slash
            href = urljoin(base_url, href)

        # Only include links from the same domain
        parsed_href = urlparse(href)
        if parsed_href.netloc == base_domain:
            # Remove fragments as they point to the same page content
            clean_href = f"{parsed_href.scheme}://{parsed_href.netloc}{parsed_href.path}"
            if parsed_href.query:
                clean_href += f"?{parsed_href.query}"

            # Don't add duplicate URLs
            if clean_href not in links:
                links.append(clean_href)

    # Also extract links from dropdown menus which are common in banking sites
    # Look for nav, menu, dropdown elements
    for nav_element in soup.find_all(['nav', 'ul', 'div'], class_=lambda c: c and any(x in str(c).lower() for x in ['menu', 'nav', 'dropdown', 'header-links', 'footer-links'])):
        for a in nav_element.find_all('a', href=True):
            href = a['href']
            if href.startswith('javascript:') or href == "#" or not href:
                continue

            if href.startswith('#'):
                if base_url_no_fragment not in links:
                    links.append(base_url_no_fragment)
                continue

            if href.startswith('/'):
                href = f"{parsed_base.scheme}://{base_domain}{href}"
            elif not href.startswith(('http://', 'https://')):
                href = urljoin(base_url, href)

            parsed_href = urlparse(href)
            if parsed_href.netloc == base_domain:
                clean_href = f"{parsed_href.scheme}://{parsed_href.netloc}{parsed_href.path}"
                if parsed_href.query:
                    clean_href += f"?{parsed_href.query}"

                if clean_href not in links:
                    links.append(clean_href)

    # Find links in onclick attributes that might contain URLs
    for element in soup.find_all(attrs={"onclick": True}):
        onclick = element["onclick"]
        # Look for URL patterns in onclick handlers
        urls = re.findall(r'window\.location\s*=\s*[\'"]([^"\']*)[\'"]\s*;|href=[\'"](https?://[^"\']*)[\'"]|openWindow\([\'"]([^"\']*)[\'"]', onclick)
        for url_group in urls:
            for url in url_group:
                if url and not url.startswith('javascript:'):
                    if not url.startswith(('http://', 'https://')):
                        url = urljoin(base_url, url)

                    parsed_url = urlparse(url)
                    if parsed_url.netloc == base_domain:
                        clean_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
                        if parsed_url.query:
                            clean_url += f"?{parsed_url.query}"

                        if clean_url not in links:
                            links.append(clean_url)

    # Look for forms that might lead to important pages
    for form in soup.find_all('form', action=True):
        action = form['action']
        if not action or action == "#":
            continue

        if not action.startswith(('http://', 'https://')):
            action = urljoin(base_url, action)

        parsed_action = urlparse(action)
        if parsed_action.netloc == base_domain:
            clean_action = f"{parsed_action.scheme}://{parsed_action.netloc}{parsed_action.path}"
            if parsed_action.query:
                clean_action += f"?{parsed_action.query}"

            if clean_action not in links:
                links.append(clean_action)

    return list(set(links))

def extract_text(html_content):
    """
    Extract clean text from HTML content with improved formatting and encoding handling.

    Args:
        html_content: HTML content as string or bytes

    Returns:
        Extracted text as string
    """
    if not html_content:
        return ""
    try:
        # If html_content is bytes, decode it properly
        if isinstance(html_content, bytes):
            try:
                html_content = html_content.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    html_content = html_content.decode('latin-1')
                except UnicodeDecodeError:
                    try:
                        html_content = html_content.decode('iso-8859-1')
                    except:
                        html_content = html_content.decode('utf-8', errors='ignore')

        soup = BeautifulSoup(html_content, 'html.parser')

        # Remove unwanted elements that don't contain useful text
        for element in soup(['script', 'style', 'noscript', 'iframe', 'head', 'meta']):
            element.decompose()

        # Handle common text containers better
        for div in soup.find_all(['div', 'section', 'article']):
            # Add spacing after containers for better text separation
            if len(div.get_text(strip=True)) > 0:
                div.append(soup.new_string('\n\n'))

        # Add spacing after headings, paragraphs and list items
        for elem in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'li']):
            elem.append(soup.new_string('\n'))

        # Extract text with proper spacing
        text = soup.get_text(separator=' ', strip=True)

        # Clean up the text: normalize spaces, remove non-printable characters
        import re
        # Replace multiple spaces with a single space
        text = re.sub(r'\s+', ' ', text)
        # Remove non-printable characters that could cause garbled output
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]', '', text)
        # Replace problematic Unicode characters with their ASCII equivalents
        text = text.replace('—', '-').replace('–', '-').replace(''', "'").replace(''', "'")
        text = text.replace('"', '"').replace('"', '"').replace('…', '...').replace('•', '*')

        # Split into lines and remove empty ones
        lines = []
        for line in text.splitlines():
            if line.strip():
                lines.append(line.strip())

        return '\n'.join(lines)
    except Exception as e:
        logger.error(f"Error extracting text: {str(e)}")
        return ""
