#!/usr/bin/env python3
"""
Test script to check how many domains are in WARC samples
"""

import gzip
import requests
from io import BytesIO
from warcio.archiveiterator import ArchiveIterator
from collections import Counter

def test_warc_file(warc_path: str, sample_size_mb: int = 10):
    """Test bir WARC dosyasından kaç farklı domain var"""

    url = f"https://data.commoncrawl.org/{warc_path}"
    sample_size = sample_size_mb * 1024 * 1024

    print(f"\nTesting: {warc_path}")
    print(f"Sample size: {sample_size_mb}MB")
    print("-" * 70)

    # Download sample
    headers = {'Range': f'bytes=0-{sample_size - 1}'}
    response = requests.get(url, headers=headers, timeout=120)

    if response.status_code not in [200, 206]:
        print(f"❌ Failed to download: HTTP {response.status_code}")
        return

    data = BytesIO(response.content)
    print(f"✓ Downloaded {len(response.content):,} bytes")

    # Parse WARC
    try:
        data.seek(0)
        decompressed = gzip.GzipFile(fileobj=data)
        decompressed.read(1)
        decompressed.seek(0)
        stream = decompressed
    except:
        data.seek(0)
        stream = data

    # Count domains and URLs
    domains = []
    urls = []
    html_count = 0

    try:
        for record in ArchiveIterator(stream):
            if record.rec_type != 'response':
                continue

            url_str = record.rec_headers.get_header('WARC-Target-URI')
            if not url_str:
                continue

            urls.append(url_str)

            # Extract domain
            from urllib.parse import urlparse
            domain = urlparse(url_str).netloc
            if domain:
                domains.append(domain)

            # Check if HTML
            try:
                content = record.content_stream().read()
                if isinstance(content, bytes):
                    content = content.decode('utf-8', errors='ignore')
                if 'html' in content[:1000].lower():
                    html_count += 1
            except:
                pass

    except Exception as e:
        if "Compressed file ended" not in str(e):
            print(f"⚠️  Parse error: {e}")

    # Statistics
    print(f"\n📊 STATISTICS:")
    print(f"  Total records: {len(urls)}")
    print(f"  HTML records: {html_count}")
    print(f"  Unique domains: {len(set(domains))}")
    print(f"  Unique URLs: {len(set(urls))}")

    if domains:
        print(f"\n📋 Top 10 domains:")
        domain_counts = Counter(domains)
        for domain, count in domain_counts.most_common(10):
            print(f"    {domain}: {count} URLs")

    return {
        'total_records': len(urls),
        'html_records': html_count,
        'unique_domains': len(set(domains)),
        'unique_urls': len(set(urls))
    }


def main():
    """Test birkaç WARC dosyasını"""

    print("=" * 70)
    print("WARC DOMAIN COUNTER - Test Script")
    print("=" * 70)

    # Read first 3 paths from warc.paths
    try:
        with open('warc.paths', 'r') as f:
            paths = [line.strip() for line in f if line.strip()][:3]
    except FileNotFoundError:
        print("❌ warc.paths not found")
        print("Using example WARC path...")
        paths = ['crawl-data/CC-MAIN-2025-05/segments/20250101000000.0/warc/CC-MAIN-20250101000000-20250101000000-00000.warc.gz']

    print(f"\nTesting {len(paths)} WARC files...")

    results = []
    for path in paths:
        try:
            result = test_warc_file(path, sample_size_mb=10)
            if result:
                results.append(result)
        except Exception as e:
            print(f"❌ Error: {e}")
            continue

    # Summary
    if results:
        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)
        avg_domains = sum(r['unique_domains'] for r in results) / len(results)
        avg_html = sum(r['html_records'] for r in results) / len(results)
        print(f"Average unique domains per WARC: {avg_domains:.0f}")
        print(f"Average HTML records per WARC: {avg_html:.0f}")
        print("\n💡 Each WARC file contains MANY different domains!")
        print("   The processor checks ALL of them for Next.js")


if __name__ == '__main__':
    main()
