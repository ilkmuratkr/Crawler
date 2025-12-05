#!/usr/bin/env python3
"""
Proxy Diagnostic Tool
Verilen proxy config'lerini test eder ve durumlarını raporlar
"""

import sys
import requests
import concurrent.futures
from typing import Dict, List

# Test için kullanılacak URL (küçük dosya)
TEST_URL = "https://data.commoncrawl.org/crawl-data/CC-MAIN-2025-05/cc-index.paths.gz"
TIMEOUT = 10  # saniye


def test_proxy(proxy_config: Dict) -> Dict:
    """
    Tek bir proxy'yi test et

    Args:
        proxy_config: {name, port, vpn_ip, host}

    Returns:
        Test sonucu
    """
    name = proxy_config['name']
    port = proxy_config['port']
    host = proxy_config.get('host', 'localhost')
    vpn_ip = proxy_config['vpn_ip']

    proxy_url = f"http://{host}:{port}"
    proxies = {
        'http': proxy_url,
        'https': proxy_url
    }

    result = {
        'name': name,
        'port': port,
        'vpn_ip': vpn_ip,
        'status': 'unknown',
        'error': None,
        'response_time': None
    }

    try:
        import time
        start = time.time()

        response = requests.head(
            TEST_URL,
            proxies=proxies,
            timeout=TIMEOUT,
            allow_redirects=True
        )

        elapsed = time.time() - start

        if response.status_code in [200, 302, 404]:  # 404 de ok, bağlantı var demek
            result['status'] = 'ok'
            result['response_time'] = round(elapsed, 2)
        else:
            result['status'] = 'http_error'
            result['error'] = f"HTTP {response.status_code}"

    except requests.exceptions.ProxyError as e:
        result['status'] = 'proxy_error'
        result['error'] = str(e)
    except requests.exceptions.Timeout:
        result['status'] = 'timeout'
        result['error'] = f"Timeout after {TIMEOUT}s"
    except requests.exceptions.ConnectionError as e:
        result['status'] = 'connection_error'
        result['error'] = "Cannot connect to proxy"
    except Exception as e:
        result['status'] = 'unknown_error'
        result['error'] = str(e)

    return result


def test_all_proxies(proxy_configs: List[Dict], parallel: bool = True) -> List[Dict]:
    """
    Tüm proxy'leri test et

    Args:
        proxy_configs: Proxy config listesi
        parallel: Paralel test et mi?

    Returns:
        Test sonuçları
    """
    if parallel:
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(test_proxy, proxy_configs))
    else:
        results = [test_proxy(config) for config in proxy_configs]

    return results


def print_results(results: List[Dict]):
    """Test sonuçlarını yazdır"""
    print("\n" + "=" * 90)
    print("PROXY TEST RESULTS")
    print("=" * 90)
    print(f"{'Name':<25} {'Port':<8} {'VPN IP':<18} {'Status':<15} {'Response':<10}")
    print("-" * 90)

    ok_count = 0
    for r in results:
        status = r['status']
        if status == 'ok':
            status_str = f"✓ {status}"
            ok_count += 1
        else:
            status_str = f"✗ {status}"

        response_str = f"{r['response_time']}s" if r['response_time'] else "-"

        print(f"{r['name']:<25} {r['port']:<8} {r['vpn_ip']:<18} {status_str:<15} {response_str:<10}")

        if r['error']:
            print(f"  └─ Error: {r['error']}")

    print("-" * 90)
    print(f"Summary: {ok_count}/{len(results)} proxies working")
    print("=" * 90)

    # Failed proxies
    failed = [r for r in results if r['status'] != 'ok']
    if failed:
        print("\n⚠️  Failed proxies:")
        for r in failed:
            print(f"  - {r['name']} (port {r['port']}): {r['status']}")


def main():
    """Ana fonksiyon"""
    print("Proxy Diagnostic Tool")
    print("Testing proxies from config.py...\n")

    # Load config
    try:
        import config
        if not hasattr(config, 'PROXY_CONFIGS') or not config.PROXY_CONFIGS:
            print("❌ No PROXY_CONFIGS found in config.py")
            sys.exit(1)

        proxy_configs = config.PROXY_CONFIGS
        proxy_host = getattr(config, 'PROXY_HOST', 'localhost')

        # Add host to configs
        for p in proxy_configs:
            p['host'] = proxy_host

        print(f"Found {len(proxy_configs)} proxies in config.py")
        print(f"Proxy host: {proxy_host}")
        print(f"Test URL: {TEST_URL}")
        print(f"Timeout: {TIMEOUT}s")
        print("\nTesting...\n")

        # Test all
        results = test_all_proxies(proxy_configs, parallel=True)

        # Print results
        print_results(results)

        # Exit code
        ok_count = sum(1 for r in results if r['status'] == 'ok')
        if ok_count == 0:
            print("\n❌ No working proxies found!")
            sys.exit(1)
        elif ok_count < len(results):
            print(f"\n⚠️  Some proxies are not working ({ok_count}/{len(results)})")
            sys.exit(0)
        else:
            print("\n✅ All proxies are working!")
            sys.exit(0)

    except ImportError:
        print("❌ Cannot import config.py")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
