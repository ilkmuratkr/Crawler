#!/usr/bin/env python3
"""
Test individual components
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.cdx import CDXClient
from src.warc import WARCFetcher, WARCParser
from src.detectors import NextJsDetector


def test_cdx_client():
    """Test CDX API client"""
    print("=" * 60)
    print("Testing CDX Client")
    print("=" * 60)

    with CDXClient() as client:
        # Get latest index
        latest = client.get_latest_index()
        print(f"Latest index: {latest}")

        # Search for a known Next.js site
        print("\nSearching for vercel.com...")
        records = list(client.search(
            url="vercel.com",
            match_type="domain",
            limit=5
        ))

        print(f"Found {len(records)} records")

        if records:
            print("\nFirst record:")
            warc_info = client.extract_warc_info(records[0])
            for key, value in warc_info.items():
                print(f"  {key}: {value}")

    print("✓ CDX Client test passed\n")


def test_warc_fetcher():
    """Test WARC fetcher"""
    print("=" * 60)
    print("Testing WARC Fetcher")
    print("=" * 60)

    # First get a WARC location from CDX
    with CDXClient() as client:
        records = list(client.search(
            url="vercel.com",
            match_type="domain",
            limit=1
        ))

        if not records:
            print("No CDX records found to test")
            return

        warc_info = client.extract_warc_info(records[0])

    # Fetch WARC segment
    print(f"\nFetching WARC segment...")
    print(f"  File: {warc_info['filename']}")
    print(f"  Offset: {warc_info['offset']}")
    print(f"  Length: {warc_info['length']}")

    with WARCFetcher() as fetcher:
        data = fetcher.fetch_warc_record(warc_info)
        print(f"  Fetched: {len(data.getvalue())} bytes")

    print("✓ WARC Fetcher test passed\n")


def test_warc_parser():
    """Test WARC parser"""
    print("=" * 60)
    print("Testing WARC Parser")
    print("=" * 60)

    # Get WARC data
    with CDXClient() as client:
        records = list(client.search(
            url="vercel.com",
            match_type="domain",
            limit=1
        ))

        if not records:
            print("No CDX records found to test")
            return

        warc_info = client.extract_warc_info(records[0])

    with WARCFetcher() as fetcher:
        warc_data = fetcher.fetch_warc_record(warc_info)

    # Parse WARC
    parser = WARCParser()
    parsed = parser.parse_warc_record(warc_data)

    if parsed:
        print(f"URL: {parsed['url']}")
        print(f"Status: {parsed['status']}")
        print(f"Content length: {len(parsed['content'])} chars")
        print(f"Content preview: {parsed['content'][:200]}...")
    else:
        print("Failed to parse WARC")

    print("✓ WARC Parser test passed\n")


def test_nextjs_detector():
    """Test Next.js detector"""
    print("=" * 60)
    print("Testing Next.js Detector")
    print("=" * 60)

    detector = NextJsDetector()

    # Test with sample HTML containing Next.js indicators
    test_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="next-head-count" content="5">
    </head>
    <body>
        <div id="__next">
            <h1>Test Page</h1>
        </div>
        <script id="__NEXT_DATA__" type="application/json">
            {"props":{"pageProps":{}},"page":"/","query":{},"buildId":"test123"}
        </script>
        <script src="/_next/static/chunks/webpack.js"></script>
    </body>
    </html>
    """

    result = detector.detect(test_html, url="test.com")

    print(f"Is Next.js: {result['is_nextjs']}")
    print(f"Confidence: {result['confidence']}")
    print(f"Indicators: {result['indicators']}")
    print(f"Build ID: {result['build_id']}")

    if result['is_nextjs']:
        print("✓ Next.js Detector test passed\n")
    else:
        print("✗ Next.js Detector test failed\n")


def main():
    print("\n" + "=" * 60)
    print("Component Tests")
    print("=" * 60 + "\n")

    try:
        test_cdx_client()
        test_warc_fetcher()
        test_warc_parser()
        test_nextjs_detector()

        print("=" * 60)
        print("All tests passed!")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
