"""
WARC Fetcher - HTTP Range requests for efficient WARC segment retrieval
"""

import requests
import logging
from typing import Optional, BinaryIO, Dict
from io import BytesIO
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class WARCFetcher:
    """Fetches WARC segments using HTTP Range requests"""

    S3_BASE_URL = "https://data.commoncrawl.org/"

    def __init__(self, timeout: int = 60, proxies: Optional[Dict[str, str]] = None):
        self.timeout = timeout
        self.proxies = proxies
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'NextJS-Detector/1.0 (Research Project)'
        })

        if proxies:
            logger.debug(f"WARCFetcher initialized with proxy: {proxies.get('http', 'N/A')}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def fetch_warc_segment(
        self,
        filename: str,
        offset: int,
        length: int,
        verify_length: bool = True
    ) -> BytesIO:
        """
        Fetch a specific segment from a WARC file using HTTP Range request

        Args:
            filename: WARC filename (e.g., "crawl-data/CC-MAIN-2024-10/segments/.../warc/...")
            offset: Byte offset in the WARC file
            length: Number of bytes to fetch
            verify_length: Verify that fetched data matches expected length

        Returns:
            BytesIO object containing the WARC segment

        Raises:
            requests.exceptions.RequestException: If fetch fails
            ValueError: If fetched data doesn't match expected length
        """
        url = f"{self.S3_BASE_URL}{filename}"

        # HTTP Range header: "bytes=start-end" (end is inclusive)
        range_header = f"bytes={offset}-{offset + length - 1}"

        logger.debug(f"Fetching {length} bytes from {filename} at offset {offset}")

        try:
            response = self.session.get(
                url,
                headers={'Range': range_header},
                timeout=self.timeout,
                proxies=self.proxies,
                stream=False  # Load entire segment into memory
            )

            # Status code should be 206 (Partial Content)
            if response.status_code == 206:
                data = response.content

                if verify_length and len(data) != length:
                    raise ValueError(
                        f"Expected {length} bytes, got {len(data)} bytes"
                    )

                logger.debug(f"Successfully fetched {len(data)} bytes")
                return BytesIO(data)

            elif response.status_code == 200:
                # Server doesn't support Range requests, got full file
                logger.warning(
                    f"Server returned full file (200) instead of range (206). "
                    f"Extracting bytes {offset}:{offset+length}"
                )
                data = response.content[offset:offset + length]
                return BytesIO(data)

            else:
                response.raise_for_status()
                raise ValueError(f"Unexpected status code: {response.status_code}")

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch WARC segment from {filename}: {e}")
            raise

    def fetch_warc_record(self, warc_info: dict) -> BytesIO:
        """
        Fetch a WARC record using info from CDX

        Args:
            warc_info: Dictionary with 'filename', 'offset', 'length'

        Returns:
            BytesIO containing WARC record
        """
        return self.fetch_warc_segment(
            filename=warc_info['filename'],
            offset=warc_info['offset'],
            length=warc_info['length']
        )

    def get_file_size(self, filename: str) -> Optional[int]:
        """
        Get size of a WARC file without downloading it

        Args:
            filename: WARC filename

        Returns:
            File size in bytes, or None if unavailable
        """
        url = f"{self.S3_BASE_URL}{filename}"

        try:
            response = self.session.head(url, timeout=self.timeout, proxies=self.proxies)
            response.raise_for_status()

            content_length = response.headers.get('Content-Length')
            if content_length:
                return int(content_length)

        except Exception as e:
            logger.warning(f"Could not get file size for {filename}: {e}")

        return None

    def verify_range_support(self, filename: str) -> bool:
        """
        Check if server supports Range requests for a file

        Args:
            filename: WARC filename

        Returns:
            True if Range requests are supported
        """
        url = f"{self.S3_BASE_URL}{filename}"

        try:
            response = self.session.head(url, timeout=self.timeout, proxies=self.proxies)
            response.raise_for_status()

            accept_ranges = response.headers.get('Accept-Ranges', '')
            return accept_ranges.lower() == 'bytes'

        except Exception as e:
            logger.warning(f"Could not verify range support for {filename}: {e}")
            return False

    def close(self):
        """Close the session"""
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
