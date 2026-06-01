import httpx
from bs4 import BeautifulSoup
from utils.logger import logger


class ContentFetcher:
    """
    Fetches and extracts readable text content from web pages.

    Uses httpx for HTTP requests and BeautifulSoup for HTML parsing.
    Extracts the main text body, stripping scripts, styles, and navigation.
    """

    # Browser-like user agent to avoid being blocked
    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    )

    # Tags to strip entirely before extracting text
    STRIP_TAGS = ["script", "style", "nav", "footer", "header", "noscript", "iframe"]

    def __init__(self, timeout: float = 10.0, max_chars: int = 5000):
        """
        Initialize the content fetcher.

        Args:
            timeout: Request timeout in seconds.
            max_chars: Maximum number of characters to return.
        """
        self.timeout = timeout
        self.max_chars = max_chars
        self.client = httpx.Client(
            headers={"User-Agent": self.USER_AGENT},
            timeout=self.timeout,
            follow_redirects=True,
        )
        logger.info("ContentFetcher initialized")

    def fetch_content(self, url: str) -> str:
        """
        Fetch a URL and extract its main text content.

        Args:
            url: The URL to fetch.

        Returns:
            Extracted text content truncated to max_chars, or empty string on failure.
        """
        if not url or not url.strip():
            logger.warning("fetch_content called with empty URL")
            return ""

        try:
            logger.info(f"Fetching content from: {url}")
            response = self.client.get(url.strip())
            response.raise_for_status()

            content_type = response.headers.get("content-type", "")
            if "text/html" not in content_type and "text/plain" not in content_type:
                logger.warning(f"Skipping non-text content type: {content_type} for {url}")
                return ""

            html = response.text

            soup = BeautifulSoup(html, "lxml")

            # Remove unwanted tags
            for tag_name in self.STRIP_TAGS:
                for tag in soup.find_all(tag_name):
                    tag.decompose()

            # Try to get the main content area first
            body = soup.find("body")
            if body is None:
                logger.warning(f"No <body> tag found in {url}")
                return ""

            # Remove hidden elements and empty tags
            for tag in body.find_all(True):
                style = tag.get("style", "")
                if "display:none" in style or "display: none" in style:
                    tag.decompose()
                    continue
                # Remove tags with no text and no meaningful children
                if not tag.get_text(strip=True) and tag.name not in ("br", "hr", "img"):
                    tag.decompose()

            # Extract text from remaining body
            text = body.get_text(separator=" ", strip=True)

            # Clean up whitespace
            text = " ".join(text.split())

            # Truncate to max_chars
            if len(text) > self.max_chars:
                text = text[:self.max_chars].rsplit(" ", 1)[0] + "..."

            logger.info(f"Fetched {len(text)} chars from {url}")
            return text

        except httpx.TimeoutException:
            logger.warning(f"Timeout fetching {url} (timeout={self.timeout}s)")
            return ""
        except httpx.HTTPStatusError as e:
            logger.warning(f"HTTP {e.response.status_code} fetching {url}")
            return ""
        except httpx.RequestError as e:
            logger.warning(f"Request error fetching {url}: {e}")
            return ""
        except Exception as e:
            logger.error(f"Unexpected error fetching {url}: {e}")
            return ""

    def close(self):
        """Close the underlying HTTP client."""
        self.client.close()
