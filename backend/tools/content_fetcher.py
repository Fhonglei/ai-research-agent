import ipaddress
import httpx
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from config import config
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

    def __init__(self, timeout: float | None = None, max_chars: int | None = None):
        """
        Initialize the content fetcher.

        Args:
            timeout: Request timeout in seconds.
            max_chars: Maximum number of characters to return.
        """
        self.timeout = timeout or config.CONTENT_FETCH_TIMEOUT_SECONDS
        self.max_chars = max_chars or config.CONTENT_FETCH_MAX_CHARS
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

        url = url.strip()

        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https") or not parsed.hostname:
            logger.warning(f"Rejected non-http URL: {url}")
            return ""
        if _is_private_or_local_host(parsed.hostname):
            logger.warning(f"Rejected private or local URL: {url}")
            return ""

        try:
            logger.info(f"Fetching content from: {url}")
            response = self.client.get(url)
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

            # Prefer semantic content containers, then fall back to <body>
            container: BeautifulSoup | None = None
            for tag_name in ("article", "main", '[role="main"]'):
                container = soup.find(tag_name)
                if container is not None:
                    break
            if container is None:
                container = soup.find("body")
            if container is None:
                logger.warning(f"No content container found in {url}")
                return ""

            # Remove hidden elements and empty tags
            for tag in container.find_all(True):
                style = tag.get("style", "")
                if "display:none" in style or "display: none" in style:
                    tag.decompose()
                    continue
                aria = tag.get("aria-hidden", "")
                if aria and aria.lower() == "true":
                    tag.decompose()
                    continue
                if not tag.get_text(strip=True) and tag.name not in ("br", "hr", "img"):
                    tag.decompose()

            text = container.get_text(separator=" ", strip=True)

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


def _is_private_or_local_host(hostname: str) -> bool:
    host = hostname.strip().lower()
    if host in {"localhost", "0.0.0.0"} or host.endswith(".local"):
        return True
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return False
    return ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved
