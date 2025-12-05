"""
Main Crawler Module
Orchestrates CDX search, WARC fetching, and Next.js detection
"""

import json
import logging
from typing import Iterator, Dict, Optional, List, Set
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

from .cdx import CDXClient
from .warc import WARCFetcher, WARCParser
from .detectors import NextJsDetector
from .utils import RateLimiter, ProgressLogger

logger = logging.getLogger(__name__)


class NextJsCrawler:
    """Main crawler for finding Next.js sites in Common Crawl"""

    def __init__(
        self,
        output_dir: str = "data/output",
        rate_limit: float = 2.0,
        max_workers: int = 5,
        min_confidence: str = "medium"
    ):
        """
        Initialize crawler

        Args:
            output_dir: Directory to save results
            rate_limit: Maximum requests per second
            max_workers: Number of parallel workers
            min_confidence: Minimum confidence level for results
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.cdx_client = CDXClient()
        self.warc_fetcher = WARCFetcher()
        self.warc_parser = WARCParser()
        self.detector = NextJsDetector()

        self.rate_limiter = RateLimiter(requests_per_second=rate_limit)
        self.max_workers = max_workers
        self.min_confidence = min_confidence

        self.progress_logger = ProgressLogger(logger)
        self.found_domains: Set[str] = set()
        self.results: List[Dict] = []

    def search_and_detect(
        self,
        url_pattern: str,
        index: Optional[str] = None,
        limit: Optional[int] = 1000,
        match_type: str = "prefix"
    ) -> List[Dict]:
        """
        Search CDX for URLs and detect Next.js usage

        Args:
            url_pattern: URL pattern to search
            index: Common Crawl index (e.g., "2024-10")
            limit: Maximum URLs to process
            match_type: CDX match type

        Returns:
            List of detected Next.js sites
        """
        logger.info(f"Starting search for pattern: {url_pattern}")

        if index is None:
            index = self.cdx_client.get_latest_index()
            logger.info(f"Using latest index: {index}")

        # Search CDX
        cdx_records = list(self.cdx_client.search(
            url=url_pattern,
            index=index,
            match_type=match_type,
            limit=limit,
            filter_status="200"
        ))

        logger.info(f"Found {len(cdx_records)} CDX records")

        if not cdx_records:
            logger.warning("No CDX records found")
            return []

        # Process records with progress bar
        results = []
        with tqdm(total=len(cdx_records), desc="Processing URLs") as pbar:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit tasks
                future_to_record = {
                    executor.submit(self._process_record, record): record
                    for record in cdx_records
                }

                # Process completed tasks
                for future in as_completed(future_to_record):
                    record = future_to_record[future]
                    try:
                        result = future.result()
                        if result:
                            results.append(result)
                            self.progress_logger.log_processed(
                                result['url'],
                                is_nextjs=True
                            )
                        else:
                            self.progress_logger.log_processed(
                                record.get('url', 'unknown')
                            )
                    except Exception as e:
                        self.progress_logger.log_error(
                            record.get('url', 'unknown'),
                            e
                        )

                    pbar.update(1)

                    # Log stats periodically
                    if pbar.n % 100 == 0:
                        self.progress_logger.log_stats()

        # Final stats
        self.progress_logger.log_stats()

        return results

    def _process_record(self, cdx_record: Dict) -> Optional[Dict]:
        """
        Process a single CDX record

        Args:
            cdx_record: CDX record dictionary

        Returns:
            Detection result if Next.js found, None otherwise
        """
        # Rate limiting
        self.rate_limiter.acquire()

        try:
            # Extract WARC info
            warc_info = self.cdx_client.extract_warc_info(cdx_record)

            # Fetch WARC segment
            warc_data = self.warc_fetcher.fetch_warc_record(warc_info)

            # Parse HTML
            html = self.warc_parser.extract_html(warc_data)
            if not html:
                return None

            # Detect Next.js
            detection = self.detector.detect(html, warc_info['url'])

            if detection['is_nextjs']:
                # Check confidence level
                confidence_levels = {'low': 1, 'medium': 2, 'high': 3}
                if confidence_levels.get(detection['confidence'], 0) >= \
                   confidence_levels.get(self.min_confidence, 2):

                    # Extract domain
                    from urllib.parse import urlparse
                    domain = urlparse(warc_info['url']).netloc

                    # Avoid duplicates
                    if domain in self.found_domains:
                        return None

                    self.found_domains.add(domain)

                    return {
                        'domain': domain,
                        'url': warc_info['url'],
                        'detected_at': datetime.now().isoformat(),
                        'crawl_date': warc_info['timestamp'],
                        'confidence': detection['confidence'],
                        'indicators': detection['indicators'],
                        'build_id': detection['build_id'],
                        'version': detection['version']
                    }

        except Exception as e:
            logger.debug(f"Error processing record: {e}")

        return None

    def search_domains_from_file(
        self,
        domains_file: str,
        index: Optional[str] = None,
        limit_per_domain: int = 10
    ) -> List[Dict]:
        """
        Search for Next.js usage in domains from a file

        Args:
            domains_file: Path to file with domain list (one per line)
            index: Common Crawl index
            limit_per_domain: Max URLs to check per domain

        Returns:
            List of detected Next.js sites
        """
        domains = Path(domains_file).read_text().strip().split('\n')
        logger.info(f"Loaded {len(domains)} domains from {domains_file}")

        all_results = []
        for domain in tqdm(domains, desc="Processing domains"):
            domain = domain.strip()
            if not domain:
                continue

            try:
                results = self.search_and_detect(
                    url_pattern=domain,
                    index=index,
                    limit=limit_per_domain,
                    match_type="domain"
                )
                all_results.extend(results)
            except Exception as e:
                logger.error(f"Error processing domain {domain}: {e}")

        return all_results

    def save_results(self, results: List[Dict], filename: str = None):
        """
        Save results to JSON file

        Args:
            results: List of detection results
            filename: Output filename (auto-generated if None)
        """
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"nextjs_sites_{timestamp}.json"

        output_path = self.output_dir / filename

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved {len(results)} results to {output_path}")

        # Also save as CSV for easy viewing
        csv_path = output_path.with_suffix('.csv')
        self._save_as_csv(results, csv_path)

    def _save_as_csv(self, results: List[Dict], csv_path: Path):
        """Save results as CSV"""
        import csv

        if not results:
            return

        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'domain', 'url', 'confidence', 'build_id',
                'detected_at', 'crawl_date'
            ])
            writer.writeheader()

            for result in results:
                writer.writerow({
                    'domain': result.get('domain'),
                    'url': result.get('url'),
                    'confidence': result.get('confidence'),
                    'build_id': result.get('build_id'),
                    'detected_at': result.get('detected_at'),
                    'crawl_date': result.get('crawl_date')
                })

        logger.info(f"Saved CSV to {csv_path}")

    def get_statistics(self) -> Dict:
        """Get crawler statistics"""
        return self.progress_logger.get_stats()

    def close(self):
        """Clean up resources"""
        self.cdx_client.close()
        self.warc_fetcher.close()
