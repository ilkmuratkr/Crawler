#!/usr/bin/env python3
"""
Bulk WARC search - Efficiently search through Common Crawl WARC files
Bu script WARC paths'lerden toplu arama yapar
"""

import sys
import logging
from pathlib import Path
import requests
import gzip
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.warc import WARCFetcher, WARCParser
from src.detectors import NextJsDetector
from src.utils import setup_logger, RateLimiter
import json


def get_warc_paths(index: str = "CC-MAIN-2025-47") -> list:
    """
    WARC paths listesini indir

    Args:
        index: Common Crawl index (e.g., "CC-MAIN-2025-47")

    Returns:
        WARC dosya yollarının listesi
    """
    url = f"https://data.commoncrawl.org/crawl-data/{index}/warc.paths.gz"

    print(f"Downloading WARC paths from {url}...")
    response = requests.get(url, stream=True)
    response.raise_for_status()

    # Decompress and parse
    paths = []
    with gzip.GzipFile(fileobj=response.raw) as f:
        for line in f:
            path = line.decode('utf-8').strip()
            if path:
                paths.append(path)

    print(f"Found {len(paths)} WARC files")
    return paths


def sample_warc_file(warc_path: str, sample_size: int = 10) -> list:
    """
    Bir WARC dosyasından rastgele örnekler al

    Args:
        warc_path: WARC dosya yolu
        sample_size: Kaç örnek alınacak

    Returns:
        HTML içerikleri listesi
    """
    # WARC dosyasından küçük bir kısım al (baştan sample_size MB)
    # Gerçek uygulamada daha akıllı sampling yapılabilir

    base_url = "https://data.commoncrawl.org/"
    full_url = f"{base_url}{warc_path}"

    # İlk birkaç MB'ı indir (bir WARC dosyası çok büyük olabilir)
    chunk_size = 10 * 1024 * 1024  # 10 MB

    headers = {'Range': f'bytes=0-{chunk_size}'}
    response = requests.get(full_url, headers=headers, timeout=60)

    if response.status_code not in [200, 206]:
        return []

    # Parse WARC records
    from io import BytesIO
    from warcio.archiveiterator import ArchiveIterator

    results = []
    try:
        # Decompress
        data = BytesIO(response.content)

        try:
            decompressed = gzip.GzipFile(fileobj=data)
            stream = decompressed
        except:
            data.seek(0)
            stream = data

        # Parse records
        for record in ArchiveIterator(stream):
            if record.rec_type == 'response':
                url = record.rec_headers.get_header('WARC-Target-URI')

                # Get content
                content = record.content_stream().read()

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

                if len(results) >= sample_size:
                    break

    except Exception as e:
        logging.warning(f"Error parsing WARC {warc_path}: {e}")

    return results


def bulk_search_nextjs(
    index: str = "CC-MAIN-2025-47",
    max_warc_files: int = 100,
    samples_per_warc: int = 10,
    workers: int = 5
):
    """
    Toplu WARC arama - birçok WARC dosyasını paralel tara

    Args:
        index: Common Crawl index
        max_warc_files: Max kaç WARC dosyası taranacak
        samples_per_warc: Her WARC'tan kaç örnek
        workers: Paralel worker sayısı
    """
    logger = setup_logger(level=logging.INFO)

    # Get WARC paths
    warc_paths = get_warc_paths(index)
    warc_paths = warc_paths[:max_warc_files]  # Limit

    print(f"\nProcessing {len(warc_paths)} WARC files...")
    print(f"Samples per file: {samples_per_warc}")
    print(f"Workers: {workers}\n")

    # Initialize detector
    detector = NextJsDetector()
    rate_limiter = RateLimiter(requests_per_second=2.0)

    all_results = []
    found_domains = set()

    # Process WARCs in parallel
    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_to_path = {
            executor.submit(sample_warc_file, path, samples_per_warc): path
            for path in warc_paths
        }

        with tqdm(total=len(warc_paths), desc="Processing WARC files") as pbar:
            for future in as_completed(future_to_path):
                path = future_to_path[future]

                rate_limiter.acquire()

                try:
                    samples = future.result(timeout=120)

                    # Detect Next.js in samples
                    for sample in samples:
                        detection = detector.detect(sample['html'], sample['url'])

                        if detection['is_nextjs'] and detection['confidence'] in ['high', 'medium']:
                            from urllib.parse import urlparse
                            domain = urlparse(sample['url']).netloc

                            if domain not in found_domains:
                                found_domains.add(domain)
                                all_results.append({
                                    'domain': domain,
                                    'url': sample['url'],
                                    'confidence': detection['confidence'],
                                    'indicators': detection['indicators'],
                                    'build_id': detection['build_id']
                                })

                                # Print in real-time
                                print(f"\n✓ Found: {domain} ({detection['confidence']})")

                except Exception as e:
                    logger.debug(f"Error processing {path}: {e}")

                pbar.update(1)

    # Save results
    output_dir = Path("data/output")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / f"bulk_search_{index}.json"
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2)

    print(f"\n\n{'=' * 60}")
    print(f"RESULTS")
    print(f"{'=' * 60}")
    print(f"Total Next.js sites found: {len(all_results)}")
    print(f"Saved to: {output_file}")
    print(f"{'=' * 60}\n")

    return all_results


def main():
    """
    Ana fonksiyon - WARC dosyalarından toplu arama
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Bulk search for Next.js sites in WARC files"
    )

    parser.add_argument(
        '--index',
        type=str,
        default='CC-MAIN-2025-47',
        help='Common Crawl index (default: CC-MAIN-2025-47)'
    )

    parser.add_argument(
        '--max-files',
        type=int,
        default=100,
        help='Max WARC files to process (default: 100)'
    )

    parser.add_argument(
        '--samples',
        type=int,
        default=10,
        help='Samples per WARC file (default: 10)'
    )

    parser.add_argument(
        '--workers',
        type=int,
        default=5,
        help='Parallel workers (default: 5)'
    )

    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("Common Crawl WARC Bulk Search")
    print("=" * 60)
    print(f"Index: {args.index}")
    print(f"Max WARC files: {args.max_files}")
    print(f"Samples per file: {args.samples}")
    print(f"Workers: {args.workers}")
    print("=" * 60 + "\n")

    results = bulk_search_nextjs(
        index=args.index,
        max_warc_files=args.max_files,
        samples_per_warc=args.samples,
        workers=args.workers
    )

    if results:
        print("\nExample results:")
        for i, r in enumerate(results[:10], 1):
            print(f"  {i}. {r['domain']} ({r['confidence']})")


if __name__ == '__main__':
    main()
