#!/usr/bin/env python3
"""
Common Crawl Next.js Site Detector
Main entry point for the crawler
"""

import argparse
import logging
from pathlib import Path

from src.crawler import NextJsCrawler
from src.utils import setup_logger, get_default_log_file


def main():
    parser = argparse.ArgumentParser(
        description="Detect Next.js sites from Common Crawl data"
    )

    parser.add_argument(
        '--pattern',
        type=str,
        default='*/',
        help='URL pattern to search - all TLDs and subdomains (default: */)'
    )

    parser.add_argument(
        '--domains-file',
        type=str,
        help='File with domain list (one per line)'
    )

    parser.add_argument(
        '--index',
        type=str,
        help='Common Crawl index (e.g., 2024-10). Uses latest if not specified.'
    )

    parser.add_argument(
        '--match-type',
        type=str,
        choices=['exact', 'prefix', 'host', 'domain'],
        default='prefix',
        help='CDX match type (default: prefix)'
    )

    parser.add_argument(
        '--limit',
        type=int,
        default=1000,
        help='Maximum URLs to process (default: 1000)'
    )

    parser.add_argument(
        '--workers',
        type=int,
        default=5,
        help='Number of parallel workers (default: 5)'
    )

    parser.add_argument(
        '--rate-limit',
        type=float,
        default=2.0,
        help='Requests per second (default: 2.0)'
    )

    parser.add_argument(
        '--min-confidence',
        type=str,
        choices=['low', 'medium', 'high'],
        default='medium',
        help='Minimum confidence level (default: medium)'
    )

    parser.add_argument(
        '--output-dir',
        type=str,
        default='data/output',
        help='Output directory (default: data/output)'
    )

    parser.add_argument(
        '--log-level',
        type=str,
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level (default: INFO)'
    )

    parser.add_argument(
        '--log-file',
        type=str,
        help='Log file path (auto-generated if not specified)'
    )

    args = parser.parse_args()

    # Setup logging
    log_file = args.log_file or get_default_log_file()
    log_level = getattr(logging, args.log_level)
    logger = setup_logger(level=log_level, log_file=log_file)

    logger.info("=" * 60)
    logger.info("Common Crawl Next.js Site Detector")
    logger.info("=" * 60)
    logger.info(f"Pattern: {args.pattern}")
    logger.info(f"Index: {args.index or 'latest'}")
    logger.info(f"Match type: {args.match_type}")
    logger.info(f"Limit: {args.limit}")
    logger.info(f"Workers: {args.workers}")
    logger.info(f"Rate limit: {args.rate_limit} req/s")
    logger.info(f"Min confidence: {args.min_confidence}")
    logger.info(f"Output dir: {args.output_dir}")
    logger.info(f"Log file: {log_file}")
    logger.info("=" * 60)

    # Initialize crawler
    crawler = NextJsCrawler(
        output_dir=args.output_dir,
        rate_limit=args.rate_limit,
        max_workers=args.workers,
        min_confidence=args.min_confidence
    )

    try:
        # Run crawler
        if args.domains_file:
            logger.info(f"Processing domains from file: {args.domains_file}")
            results = crawler.search_domains_from_file(
                domains_file=args.domains_file,
                index=args.index,
                limit_per_domain=args.limit
            )
        else:
            logger.info(f"Searching for pattern: {args.pattern}")
            results = crawler.search_and_detect(
                url_pattern=args.pattern,
                index=args.index,
                limit=args.limit,
                match_type=args.match_type
            )

        # Save results
        if results:
            crawler.save_results(results)
            logger.info(f"Found {len(results)} Next.js sites!")

            # Print summary
            print("\n" + "=" * 60)
            print("SUMMARY")
            print("=" * 60)
            print(f"Total Next.js sites found: {len(results)}")

            # Group by confidence
            by_confidence = {}
            for r in results:
                conf = r['confidence']
                by_confidence[conf] = by_confidence.get(conf, 0) + 1

            for conf in ['high', 'medium', 'low']:
                if conf in by_confidence:
                    print(f"  {conf.capitalize()} confidence: {by_confidence[conf]}")

            # Show some examples
            print("\nExample domains:")
            for i, result in enumerate(results[:10], 1):
                print(f"  {i}. {result['domain']} (confidence: {result['confidence']})")

            print("=" * 60)
        else:
            logger.warning("No Next.js sites found")

        # Print statistics
        stats = crawler.get_statistics()
        print(f"\nStatistics:")
        print(f"  Total processed: {stats['total_processed']}")
        print(f"  Next.js found: {stats['nextjs_found']}")
        print(f"  Errors: {stats['errors']}")
        print(f"  Elapsed time: {stats['elapsed_seconds']:.2f}s")
        print(f"  Rate: {stats['rate_per_second']:.2f} URLs/sec")

    except KeyboardInterrupt:
        logger.warning("Interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
    finally:
        crawler.close()
        logger.info("Crawler closed")


if __name__ == '__main__':
    main()
