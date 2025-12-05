#!/usr/bin/env python3
"""
WARC Processor - Advanced
warc.paths dosyasından WARC'ları işler
- 5 deneme, 5 dakika bekleme
- Başarısızları kaydeder
- Resume desteği
"""

import argparse
import logging
import sys
from pathlib import Path

from src.warc_processor import WARCProcessor
from src.utils import setup_logger


def main():
    parser = argparse.ArgumentParser(
        description="Process WARC files with retry logic and failure tracking"
    )

    parser.add_argument(
        '--warc-paths',
        type=str,
        default='warc.paths',
        help='WARC paths file (default: warc.paths)'
    )

    parser.add_argument(
        '--limit',
        type=int,
        help='Max WARC files to process (default: all)'
    )

    parser.add_argument(
        '--workers',
        type=int,
        default=5,
        help='Number of parallel workers (default: 5)'
    )

    parser.add_argument(
        '--sample-size',
        type=int,
        default=10,
        help='Sample size per WARC in MB (default: 10, use 0 for full WARC)'
    )

    parser.add_argument(
        '--rate-limit',
        type=float,
        default=2.0,
        help='Requests per second (default: 2.0)'
    )

    parser.add_argument(
        '--max-retries',
        type=int,
        default=5,
        help='Maximum retry attempts (default: 5)'
    )

    parser.add_argument(
        '--retry-delay',
        type=int,
        default=300,
        help='Delay between retries in seconds (default: 300 = 5 minutes)'
    )

    parser.add_argument(
        '--resume-from',
        type=str,
        help='Resume from previous failure file (JSON or TXT)'
    )

    parser.add_argument(
        '--output-dir',
        type=str,
        default='data/output',
        help='Output directory (default: data/output)'
    )

    parser.add_argument(
        '--failure-dir',
        type=str,
        default='data/failures',
        help='Failure tracking directory (default: data/failures)'
    )

    parser.add_argument(
        '--log-level',
        type=str,
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level (default: INFO)'
    )

    parser.add_argument(
        '--enable-proxy',
        action='store_true',
        help='Enable proxy rotation (requires config.py with PROXY_CONFIGS)'
    )

    parser.add_argument(
        '--proxy-host',
        type=str,
        default='localhost',
        help='Proxy host (default: localhost)'
    )

    args = parser.parse_args()

    # Setup logging
    log_level = getattr(logging, args.log_level)
    logger = setup_logger(level=log_level)

    # Load proxy configs from config.py (opsiyonel)
    proxy_configs = None
    if args.enable_proxy:
        try:
            import config
            if hasattr(config, 'PROXY_CONFIGS') and config.PROXY_CONFIGS:
                proxy_configs = config.PROXY_CONFIGS
                logger.info(f"Loaded {len(proxy_configs)} proxy configs from config.py")
            else:
                logger.warning("--enable-proxy specified but no PROXY_CONFIGS found in config.py")
        except ImportError:
            logger.warning("--enable-proxy specified but config.py not found")

    # Print configuration
    print("=" * 70)
    print("WARC PROCESSOR - ADVANCED")
    print("=" * 70)
    print(f"WARC paths file: {args.warc_paths}")
    print(f"Limit: {args.limit or 'ALL'}")
    print(f"Workers: {args.workers}")
    print(f"Sample size: {args.sample_size} MB")
    print(f"Rate limit: {args.rate_limit} req/s")
    print(f"Max retries: {args.max_retries}")
    print(f"Retry delay: {args.retry_delay}s ({args.retry_delay // 60} minutes)")
    print(f"Output dir: {args.output_dir}")
    print(f"Failure dir: {args.failure_dir}")

    if args.enable_proxy and proxy_configs:
        print(f"Proxy: ENABLED ({len(proxy_configs)} proxies)")
    else:
        print("Proxy: DISABLED")

    if args.resume_from:
        print(f"Resume from: {args.resume_from}")

    print("=" * 70)
    print()

    # Confirm if processing many WARCs
    if not args.resume_from and (not args.limit or args.limit > 1000):
        total_warcs = args.limit or "ALL (100,000)"
        print(f"⚠️  You are about to process {total_warcs} WARC files.")
        print(f"⚠️  With {args.workers} workers, this may take a long time.")
        print()
        response = input("Continue? (yes/no): ").strip().lower()
        if response not in ['yes', 'y']:
            print("Cancelled.")
            return

    # Initialize processor
    processor = WARCProcessor(
        warc_paths_file=args.warc_paths,
        output_dir=args.output_dir,
        failure_dir=args.failure_dir,
        workers=args.workers,
        sample_size_mb=args.sample_size,
        rate_limit=args.rate_limit,
        max_retries=args.max_retries,
        retry_delay=args.retry_delay,
        proxy_configs=proxy_configs,
        proxy_host=args.proxy_host
    )

    try:
        # Process
        print("\n🚀 Starting processing...\n")

        results = processor.process_all(
            limit=args.limit,
            resume_from=args.resume_from
        )

        # Save results
        if results:
            print(f"\n\n✅ Found {len(results)} Next.js sites!")
            processor.save_results(results)

            # Show examples
            print("\n" + "=" * 70)
            print("EXAMPLE RESULTS (First 10)")
            print("=" * 70)
            for i, site in enumerate(results[:10], 1):
                print(f"{i:2d}. {site['domain']:40s} [{site['confidence']}]")
            print("=" * 70)
        else:
            print("\n\n❌ No Next.js sites found")

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        logger.warning("Processing interrupted")

    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        logger.error(f"Fatal error: {e}", exc_info=True)

    finally:
        # Finalize (save failures, statistics)
        print("\n\n📊 Finalizing...")
        processor.finalize()
        processor.close()

        print("\n✅ Done!")


if __name__ == '__main__':
    main()
