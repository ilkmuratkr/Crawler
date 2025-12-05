#!/usr/bin/env python3
"""
Example: Search for Next.js in specific domains
"""

import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.crawler import NextJsCrawler
from src.utils import setup_logger


def main():
    # Setup logging
    logger = setup_logger(level=logging.INFO)

    # List of domains to check
    domains = [
        "vercel.com",
        "nextjs.org",
        "github.com",
        "npm.js.com",
        "medium.com"
    ]

    # Create crawler
    crawler = NextJsCrawler(
        output_dir="data/output",
        rate_limit=2.0,
        max_workers=3,
        min_confidence="medium"
    )

    try:
        all_results = []

        # Check each domain
        for domain in domains:
            print(f"\nChecking {domain}...")

            results = crawler.search_and_detect(
                url_pattern=domain,
                limit=10,  # Check first 10 URLs per domain
                match_type="domain"
            )

            all_results.extend(results)

            if results:
                print(f"  ✓ Next.js detected! ({results[0]['confidence']} confidence)")
            else:
                print(f"  ✗ Next.js not detected")

        # Save all results
        if all_results:
            crawler.save_results(all_results, filename="specific_domains_results.json")
            print(f"\n\nTotal: {len(all_results)} domains using Next.js")

    finally:
        crawler.close()


if __name__ == '__main__':
    main()
