"""
Advanced WARC Processor with Retry & Failure Tracking
warc.paths dosyasından WARC'ları işler, başarısızları kaydeder
"""

import logging
import requests
import gzip
import signal
import sys
from typing import List, Dict, Optional
from pathlib import Path
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from warcio.archiveiterator import ArchiveIterator

from .detectors import NextJsDetector
from .utils.retry_handler import RetryHandler, FailureTracker
from .utils.rate_limiter import RateLimiter
from .utils.proxy_manager import ProxyManager

logger = logging.getLogger(__name__)


class WARCProcessor:
    """
    Gelişmiş WARC işleyici
    - warc.paths'ten okuma
    - Retry logic (5 deneme, 5 dakika bekleme)
    - Başarısız WARC'ları kaydetme
    - Paralel işleme
    """

    BASE_URL = "https://data.commoncrawl.org/"

    def __init__(
        self,
        warc_paths_file: str = "warc.paths",
        output_dir: str = "data/output",
        failure_dir: str = "data/failures",
        workers: int = 5,
        sample_size_mb: int = 10,
        rate_limit: float = 2.0,
        max_retries: int = 5,
        retry_delay: int = 300,  # 5 dakika
        proxy_configs: Optional[List[Dict]] = None,
        proxy_host: str = "localhost"
    ):
        """
        Initialize WARC processor

        Args:
            warc_paths_file: warc.paths dosya yolu
            output_dir: Çıktı dizini
            failure_dir: Başarısız WARC'ların kaydedileceği dizin
            workers: Paralel worker sayısı
            sample_size_mb: Her WARC'tan alınacak sample boyutu (MB)
            rate_limit: Rate limit (req/sec)
            max_retries: Maksimum deneme sayısı
            retry_delay: Deneme arası bekleme (saniye)
            proxy_configs: Proxy konfigürasyonları [{name, port, vpn_ip}, ...]
            proxy_host: Proxy host (default: localhost)
        """
        self.warc_paths_file = Path(warc_paths_file)
        self.output_dir = Path(output_dir)
        self.failure_dir = Path(failure_dir)
        self.workers = workers
        self.sample_size = sample_size_mb * 1024 * 1024  # MB to bytes
        self.rate_limit = rate_limit

        # Shutdown flag for graceful termination
        self.shutdown_requested = False
        self._setup_signal_handlers()

        # Create directories
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.failure_dir.mkdir(parents=True, exist_ok=True)

        # Initialize proxy manager (opsiyonel)
        self.proxy_manager = None
        if proxy_configs:
            self.proxy_manager = ProxyManager(
                proxy_configs=proxy_configs,
                host=proxy_host
            )
            logger.info(f"Proxy manager initialized with {len(proxy_configs)} proxies")

        # Initialize components
        self.detector = NextJsDetector()
        self.rate_limiter = RateLimiter(requests_per_second=rate_limit)
        self.failure_tracker = FailureTracker(output_dir=str(self.failure_dir))
        self.retry_handler = RetryHandler(
            max_retries=max_retries,
            retry_delay=retry_delay,
            failure_tracker=self.failure_tracker,
            proxy_manager=self.proxy_manager
        )

        # Statistics
        self.stats = {
            'processed': 0,
            'successful': 0,
            'failed': 0,
            'nextjs_found': 0,
            'total_domains': set(),
            'total_urls': set()  # Track unique URLs instead of just domains
        }

        # Session
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'NextJS-Detector/1.0 (Research Project)'
        })

    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            sig_name = signal.Signals(signum).name
            logger.warning(f"\n\nReceived {sig_name}. Initiating graceful shutdown...")
            logger.warning("Please wait for current tasks to complete...")
            self.shutdown_requested = True

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def load_warc_paths(self, limit: Optional[int] = None) -> List[str]:
        """
        warc.paths dosyasından WARC yollarını yükle

        Args:
            limit: Max kaç WARC yüklenecek (None = hepsi)

        Returns:
            WARC path'lerinin listesi
        """
        if not self.warc_paths_file.exists():
            raise FileNotFoundError(f"WARC paths file not found: {self.warc_paths_file}")

        logger.info(f"Loading WARC paths from {self.warc_paths_file}")

        paths = []
        with open(self.warc_paths_file, 'r') as f:
            for line in f:
                path = line.strip()
                if path:
                    paths.append(path)

                if limit and len(paths) >= limit:
                    break

        logger.info(f"Loaded {len(paths)} WARC paths")
        return paths

    def fetch_warc_sample(
        self,
        warc_path: str,
        current_proxy=None
    ) -> Optional[BytesIO]:
        """
        WARC dosyasından sample al (HTTP Range ile)

        Args:
            warc_path: WARC dosya yolu
            current_proxy: Kullanılacak proxy (ProxyConfig)

        Returns:
            BytesIO veya None (başarısızlık)
        """
        # Check for shutdown request
        if self.shutdown_requested:
            logger.info("Shutdown requested, skipping fetch")
            raise KeyboardInterrupt("Shutdown requested")

        url = f"{self.BASE_URL}{warc_path}"

        # HTTP Range request - download sample or full file
        headers = {}
        if self.sample_size > 0:
            # Sample mode: only first N MB
            headers = {'Range': f'bytes=0-{self.sample_size - 1}'}
            logger.debug(f"Fetching sample ({self.sample_size / 1024 / 1024}MB) from {warc_path}")
        else:
            # Full mode: download entire WARC
            logger.debug(f"Fetching FULL WARC: {warc_path}")

        # Proxy ayarları
        proxies = None
        proxy_info = "direct"
        if current_proxy:
            proxies = current_proxy.proxies
            proxy_info = f"{current_proxy.name} ({current_proxy.vpn_ip}:{current_proxy.port})"
            logger.debug(f"Using proxy: {proxy_info}")

        try:
            response = self.session.get(
                url,
                headers=headers,
                timeout=120,
                proxies=proxies,
                stream=False
            )

            # 206 (Partial Content) veya 200 (OK) bekliyoruz
            if response.status_code in [200, 206]:
                data = response.content
                logger.debug(f"Fetched {len(data)} bytes from {warc_path} via {proxy_info}")
                return BytesIO(data)
            else:
                error_msg = f"HTTP {response.status_code}"
                if current_proxy:
                    error_msg += f" (proxy: {proxy_info})"
                raise Exception(error_msg)

        except requests.exceptions.ProxyError as e:
            logger.error(f"Proxy error with {proxy_info}: {e}")
            raise
        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout with {proxy_info}: {e}")
            raise
        except Exception as e:
            if current_proxy:
                logger.error(f"Error with proxy {proxy_info}: {e}")
            raise

    def parse_warc_sample(self, warc_data: BytesIO) -> List[Dict]:
        """
        WARC sample'ı parse et ve HTML kayıtları çıkar

        Args:
            warc_data: WARC data

        Returns:
            [{url, html}, ...] listesi
        """
        results = []

        try:
            # Decompress
            warc_data.seek(0)
            try:
                decompressed = gzip.GzipFile(fileobj=warc_data)
                # Test if gzipped
                decompressed.read(1)
                decompressed.seek(0)
                stream = decompressed
            except (gzip.BadGzipFile, OSError):
                warc_data.seek(0)
                stream = warc_data

            # Parse WARC records
            for record in ArchiveIterator(stream):
                if record.rec_type != 'response':
                    continue

                url = record.rec_headers.get_header('WARC-Target-URI')
                content = record.content_stream().read()

                # Decode
                if isinstance(content, bytes):
                    try:
                        content = content.decode('utf-8', errors='ignore')
                    except:
                        continue

                # Only HTML
                if 'html' in content[:1000].lower():
                    results.append({
                        'url': url,
                        'html': content
                    })

        except Exception as e:
            # Partial WARC hatası normal (10MB sample alıyoruz)
            if "Compressed file ended" in str(e) or "end-of-stream" in str(e):
                logger.debug(f"Partial WARC (expected): {e}")
            else:
                logger.warning(f"Parse error: {e}")
            pass

        return results

    def process_warc(self, warc_path: str) -> List[Dict]:
        """
        Bir WARC dosyasını işle (fetch + parse + detect)

        Args:
            warc_path: WARC dosya yolu

        Returns:
            Bulunan Next.js siteleri
        """
        # Check for shutdown request
        if self.shutdown_requested:
            logger.info(f"Shutdown requested, skipping WARC: {warc_path}")
            return []

        results = []

        # Rate limiting
        self.rate_limiter.acquire()

        # Worker için proxy ata
        import threading
        worker_id = threading.get_ident()
        current_proxy = None

        if self.proxy_manager:
            current_proxy = self.proxy_manager.get_proxy_for_worker(worker_id)
            logger.debug(
                f"Worker {worker_id} using proxy: "
                f"{current_proxy.name} ({current_proxy.vpn_ip})"
            )

        # Fetch ile retry logic (execute_with_retry'e warc_path ver, içinde func'a parametre olarak geçer)
        def fetch_func(current_proxy=None):
            return self.fetch_warc_sample(warc_path, current_proxy=current_proxy)

        try:
            warc_data = self.retry_handler.execute_with_retry(
                func=fetch_func,
                warc_path=warc_path,
                current_proxy=current_proxy
            )
        except KeyboardInterrupt:
            logger.info(f"Interrupted while processing: {warc_path}")
            return []

        if warc_data is None:
            # Retry handler başarısız oldu, skip
            self.stats['failed'] += 1
            return []

        # Parse
        try:
            samples = self.parse_warc_sample(warc_data)
        except Exception as e:
            # Partial WARC hatası görmezden gel
            if "Compressed file ended" not in str(e) and "end-of-stream" not in str(e):
                logger.error(f"Failed to parse {warc_path}: {e}")
            self.stats['failed'] += 1
            return []

        # Detect Next.js
        found_in_this_warc = set()  # Per-WARC deduplication

        for sample in samples:
            if self.shutdown_requested:
                break

            detection = self.detector.detect(sample['html'], sample['url'])

            if detection['is_nextjs'] and detection['confidence'] in ['high', 'medium']:
                from urllib.parse import urlparse
                parsed = urlparse(sample['url'])
                domain = parsed.netloc
                full_url = sample['url']
                schema = parsed.scheme  # http or https

                # Duplicate check - only within this WARC file
                if full_url not in found_in_this_warc:
                    found_in_this_warc.add(full_url)

                    # Global stats tracking (for reporting only)
                    self.stats['total_urls'].add(full_url)
                    self.stats['total_domains'].add(domain)
                    self.stats['nextjs_found'] += 1

                    results.append({
                        'domain': domain,
                        'url': full_url,
                        'schema': schema,  # Add http/https
                        'confidence': detection['confidence'],
                        'indicators': detection['indicators'],
                        'build_id': detection['build_id'],
                        'warc_source': warc_path
                    })

        self.stats['successful'] += 1
        return results

    def process_all(
        self,
        limit: Optional[int] = None,
        resume_from: Optional[str] = None
    ) -> List[Dict]:
        """
        Tüm WARC'ları işle

        Args:
            limit: Max kaç WARC işlenecek
            resume_from: Önceki başarısızlıkları retry et (failure file path)

        Returns:
            Bulunan tüm Next.js siteleri
        """
        # WARC paths yükle
        if resume_from:
            logger.info(f"Resuming from failures: {resume_from}")
            warc_paths = self.failure_tracker.load_failures(resume_from)
        else:
            warc_paths = self.load_warc_paths(limit=limit)

        logger.info(f"Processing {len(warc_paths)} WARC files with {self.workers} workers")

        all_results = []

        # Parallel processing
        try:
            with ThreadPoolExecutor(max_workers=self.workers) as executor:
                future_to_path = {
                    executor.submit(self.process_warc, path): path
                    for path in warc_paths
                }

                with tqdm(total=len(warc_paths), desc="Processing WARCs") as pbar:
                    for future in as_completed(future_to_path):
                        # Check for shutdown
                        if self.shutdown_requested:
                            logger.warning("Shutdown requested, cancelling remaining tasks...")
                            executor.shutdown(wait=False, cancel_futures=True)
                            break

                        path = future_to_path[future]

                        try:
                            results = future.result(timeout=600)  # 10 min timeout per WARC
                            all_results.extend(results)

                            # Real-time feedback
                            if results:
                                for r in results:
                                    schema_icon = "🔒" if r.get('schema') == 'https' else "🔓"
                                    print(f"\n✓ Found: {schema_icon} {r['url']} ({r['confidence']})")

                        except KeyboardInterrupt:
                            logger.warning("Interrupted, stopping gracefully...")
                            self.shutdown_requested = True
                            break
                        except Exception as e:
                            logger.error(f"Unexpected error processing {path}: {e}")
                            self.stats['failed'] += 1

                        self.stats['processed'] += 1
                        pbar.update(1)

                        # Progress report every 100 WARCs
                        if self.stats['processed'] % 100 == 0:
                            self._log_progress()

        except KeyboardInterrupt:
            logger.warning("Processing interrupted by user")
            self.shutdown_requested = True

        return all_results

    def _log_progress(self):
        """Log current progress"""
        logger.info(
            f"Progress: {self.stats['processed']} processed, "
            f"{self.stats['successful']} successful, "
            f"{self.stats['failed']} failed, "
            f"{self.stats['nextjs_found']} Next.js URLs found "
            f"({len(self.stats['total_domains'])} unique domains)"
        )

    def save_results(self, results: List[Dict], filename: Optional[str] = None):
        """Sonuçları kaydet"""
        import json
        from datetime import datetime

        if not results:
            logger.warning("No results to save")
            return

        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"nextjs_sites_{timestamp}.json"

        filepath = self.output_dir / filename

        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2)

        logger.info(f"Saved {len(results)} results to {filepath}")

        # CSV
        import csv
        csv_path = filepath.with_suffix('.csv')
        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'domain', 'url', 'schema', 'confidence', 'build_id', 'warc_source'
            ])
            writer.writeheader()
            for r in results:
                writer.writerow({
                    'domain': r['domain'],
                    'url': r['url'],
                    'schema': r.get('schema', 'unknown'),
                    'confidence': r['confidence'],
                    'build_id': r['build_id'],
                    'warc_source': r.get('warc_source', '')
                })

        logger.info(f"Saved CSV to {csv_path}")

    def finalize(self):
        """İşlemi sonlandır ve raporları kaydet"""
        # Başarısızlıkları kaydet
        failure_file = self.retry_handler.save_failures()

        # İstatistikleri logla
        stats = self.retry_handler.get_statistics()
        logger.info("=" * 60)
        logger.info("FINAL STATISTICS")
        logger.info("=" * 60)
        logger.info(f"Total WARC files processed: {self.stats['processed']}")
        logger.info(f"Successful: {self.stats['successful']}")
        logger.info(f"Failed: {self.stats['failed']}")
        logger.info(f"Next.js URLs found: {self.stats['nextjs_found']}")
        logger.info(f"Unique domains: {len(self.stats['total_domains'])}")
        logger.info(f"Unique full URLs: {len(self.stats['total_urls'])}")
        logger.info("")
        logger.info("Failure breakdown:")
        for reason, count in stats.get('by_reason', {}).items():
            logger.info(f"  {reason}: {count}")
        logger.info("=" * 60)

        if failure_file:
            logger.info(f"Failed WARCs saved to: {failure_file}")
            logger.info("You can retry with: --resume-from " + failure_file)

    def close(self):
        """Cleanup"""
        self.session.close()
