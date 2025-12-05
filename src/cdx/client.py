"""
CDX API Client for Common Crawl
Efficiently queries the CDX index to find WARC records
"""

import requests
import logging
from typing import Iterator, Dict, Optional, List
from urllib.parse import quote
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class CDXClient:
    """Client for Common Crawl CDX API"""

    CDX_API_URL = "https://index.commoncrawl.org/CC-MAIN-{index}-index"
    INDEXES_URL = "https://index.commoncrawl.org/collinfo.json"

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'NextJS-Detector/1.0 (Research Project)'
        })

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def get_available_indexes(self) -> List[Dict]:
        """Get list of available Common Crawl indexes"""
        try:
            response = self.session.get(self.INDEXES_URL, timeout=self.timeout)
            response.raise_for_status()
            indexes = response.json()
            logger.info(f"Found {len(indexes)} available indexes")
            return indexes
        except Exception as e:
            logger.error(f"Failed to fetch available indexes: {e}")
            raise

    def get_latest_index(self) -> str:
        """Get the most recent index name"""
        indexes = self.get_available_indexes()
        if not indexes:
            raise ValueError("No indexes available")
        # Returns format like "2024-10"
        latest = indexes[0]['id'].replace('CC-MAIN-', '')
        logger.info(f"Latest index: {latest}")
        return latest

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def search(
        self,
        url: str,
        index: Optional[str] = None,
        match_type: str = "exact",
        limit: Optional[int] = None,
        filter_status: Optional[str] = "200",
        from_ts: Optional[str] = None,
        to_ts: Optional[str] = None
    ) -> Iterator[Dict]:
        """
        Search CDX index for URL

        Args:
            url: URL or URL pattern to search
            index: Index name (e.g., "2024-10"), defaults to latest
            match_type: "exact", "prefix", "host", "domain"
            limit: Maximum number of results
            filter_status: HTTP status code filter (e.g., "200")
            from_ts: Start timestamp (format: YYYYMMDDhhmmss)
            to_ts: End timestamp (format: YYYYMMDDhhmmss)

        Yields:
            CDX records as dictionaries
        """
        if index is None:
            index = self.get_latest_index()

        cdx_url = self.CDX_API_URL.format(index=index)

        params = {
            'url': url,
            'output': 'json',
            'matchType': match_type,
        }

        if limit:
            params['limit'] = limit
        if filter_status:
            params['filter'] = f'status:{filter_status}'
        if from_ts:
            params['from'] = from_ts
        if to_ts:
            params['to'] = to_ts

        logger.info(f"Querying CDX: {url} (matchType={match_type}, index={index})")

        try:
            response = self.session.get(
                cdx_url,
                params=params,
                timeout=self.timeout,
                stream=True
            )
            response.raise_for_status()

            # First line is header, skip it
            lines = response.iter_lines(decode_unicode=True)
            header_line = next(lines, None)

            if not header_line:
                logger.warning(f"No results for {url}")
                return

            # Parse header to get field names
            headers = header_line.strip().split()

            count = 0
            for line in lines:
                if not line.strip():
                    continue

                values = line.strip().split()
                if len(values) != len(headers):
                    logger.warning(f"Skipping malformed line: {line}")
                    continue

                record = dict(zip(headers, values))
                yield record

                count += 1
                if limit and count >= limit:
                    break

            logger.info(f"Retrieved {count} CDX records for {url}")

        except requests.exceptions.RequestException as e:
            logger.error(f"CDX query failed for {url}: {e}")
            raise

    def search_domain(
        self,
        domain: str,
        index: Optional[str] = None,
        limit: Optional[int] = 1000
    ) -> Iterator[Dict]:
        """
        Search all URLs for a domain

        Args:
            domain: Domain name (e.g., "example.com")
            index: Index name
            limit: Maximum results

        Yields:
            CDX records
        """
        return self.search(
            url=domain,
            index=index,
            match_type="domain",
            limit=limit
        )

    def search_url_pattern(
        self,
        pattern: str,
        index: Optional[str] = None,
        limit: Optional[int] = 100
    ) -> Iterator[Dict]:
        """
        Search URLs matching a pattern

        Args:
            pattern: URL pattern (e.g., "*.example.com/*")
            index: Index name
            limit: Maximum results

        Yields:
            CDX records
        """
        return self.search(
            url=pattern,
            index=index,
            match_type="prefix",
            limit=limit
        )

    def extract_warc_info(self, cdx_record: Dict) -> Dict:
        """
        Extract WARC file location info from CDX record

        Args:
            cdx_record: CDX record dictionary

        Returns:
            Dictionary with WARC file info
        """
        return {
            'filename': cdx_record.get('filename'),
            'offset': int(cdx_record.get('offset', 0)),
            'length': int(cdx_record.get('length', 0)),
            'url': cdx_record.get('url'),
            'timestamp': cdx_record.get('timestamp'),
            'status': cdx_record.get('status'),
            'mime': cdx_record.get('mime'),
            'digest': cdx_record.get('digest'),
        }

    def close(self):
        """Close the session"""
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
