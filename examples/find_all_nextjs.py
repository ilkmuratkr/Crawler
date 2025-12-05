#!/usr/bin/env python3
"""
TÜM Next.js Sitelerini Bul - Subdomain dahil her şey
Bu script tüm TLD'leri ve subdomain'leri tarar
"""

import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.crawler import NextJsCrawler
from src.utils import setup_logger


def main():
    """
    Tüm TLD'ler ve subdomain'ler dahil Next.js sitelerini bul
    """
    # Setup logging
    logger = setup_logger(level=logging.INFO)

    print("=" * 60)
    print("TÜM NEXT.JS SİTELERİNİ BULMA")
    print("=" * 60)
    print("Bu script şunları kapsar:")
    print("  ✓ Tüm TLD'ler: .com, .org, .io, .dev, .app, vb.")
    print("  ✓ Subdomain'ler: blog.example.com, api.test.org")
    print("  ✓ Country TLD'ler: .co.uk, .com.tr, .de, vb.")
    print("  ✓ Yeni TLD'ler: .xyz, .tech, .blog, vb.")
    print("=" * 60 + "\n")

    # Create crawler
    crawler = NextJsCrawler(
        output_dir="data/output",
        rate_limit=3.0,  # Biraz daha agresif
        max_workers=10,  # Daha fazla paralel işlem
        min_confidence="medium"
    )

    try:
        # Strateji: WARC'ları tara (en kapsamlı yöntem)
        print("Strateji: Bulk WARC tarama (tüm domain'leri bulur)\n")

        # Not: Bu örnek için CDX kullanıyoruz ama gerçek kullanımda
        # bulk_warc_search.py kullanmak daha verimli

        # Pattern: "*/" = Her şey
        # match_type: "prefix" = URL prefix match
        results = crawler.search_and_detect(
            url_pattern="*/",  # Tüm URL'ler
            limit=10000,  # 10k URL kontrol et
            match_type="prefix"
        )

        # Sonuçları analiz et
        if results:
            print("\n" + "=" * 60)
            print("BULUNAN SİTELER")
            print("=" * 60)

            # TLD'lere göre grupla
            by_tld = {}
            for site in results:
                domain = site['domain']
                # TLD çıkar
                parts = domain.split('.')
                tld = parts[-1] if len(parts) > 1 else 'unknown'

                if tld not in by_tld:
                    by_tld[tld] = []
                by_tld[tld].append(site)

            # İstatistikler
            print(f"\nToplam Next.js Sitesi: {len(results)}")
            print(f"\nTLD Dağılımı:")
            for tld, sites in sorted(by_tld.items(), key=lambda x: len(x[1]), reverse=True):
                print(f"  .{tld}: {len(sites)} site")

            # Subdomain olanlar
            subdomains = [s for s in results if s['domain'].count('.') > 1]
            print(f"\nSubdomain'li Siteler: {len(subdomains)}")

            # Örnekler
            print("\n" + "=" * 60)
            print("ÖRNEK SİTELER (İlk 20)")
            print("=" * 60)
            for i, site in enumerate(results[:20], 1):
                domain = site['domain']
                conf = site['confidence']
                print(f"{i:2d}. {domain:40s} [{conf}]")

            # Subdomain örnekleri
            if subdomains:
                print("\n" + "=" * 60)
                print("SUBDOMAIN ÖRNEKLERİ")
                print("=" * 60)
                for i, site in enumerate(subdomains[:10], 1):
                    print(f"{i:2d}. {site['domain']}")

            # Kaydet
            crawler.save_results(results, filename="all_nextjs_sites.json")
            print(f"\n✓ Sonuçlar kaydedildi: data/output/all_nextjs_sites.json")

        else:
            print("❌ Hiç Next.js sitesi bulunamadı")

    except KeyboardInterrupt:
        print("\n\n⚠️  İşlem kullanıcı tarafından durduruldu")
    except Exception as e:
        logger.error(f"Hata: {e}", exc_info=True)
    finally:
        crawler.close()


if __name__ == '__main__':
    main()
