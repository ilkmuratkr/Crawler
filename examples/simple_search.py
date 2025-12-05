#!/usr/bin/env python3
"""
Simple example: Search for Next.js sites
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

    # Create crawler
    crawler = NextJsCrawler(
        output_dir="data/output",
        rate_limit=2.0,
        max_workers=3,
        min_confidence="medium"
    )

    try:
        # Search for .com domains
        # This will search the latest Common Crawl index
        results = crawler.search_and_detect(
            url_pattern="*.com/",
            limit=100,  # Process first 100 URLs
            match_type="prefix"
        )

        # Save results
        if results:
            crawler.save_results(results, filename="simple_search_results.json")
            print(f"\nFound {len(results)} Next.js sites!")

            # Print results
            for i, site in enumerate(results, 1):
                print(f"{i}. {site['domain']} (confidence: {site['confidence']})")
        else:
            print("No Next.js sites found")

    finally:
        crawler.close()


if __name__ == '__main__':
    main()
