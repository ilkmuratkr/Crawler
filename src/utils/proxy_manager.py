"""
Proxy Manager - Manages proxy rotation for downloads
"""

import logging
import random
from typing import Optional, Dict, List
from dataclasses import dataclass
import threading

logger = logging.getLogger(__name__)


@dataclass
class ProxyConfig:
    """Proxy configuration"""
    name: str
    port: int
    vpn_ip: str
    host: str = "localhost"

    @property
    def proxy_url(self) -> str:
        """Get proxy URL for requests"""
        return f"http://{self.host}:{self.port}"

    @property
    def proxies(self) -> Dict[str, str]:
        """Get proxies dict for requests library"""
        return {
            'http': self.proxy_url,
            'https': self.proxy_url
        }


class ProxyManager:
    """
    Manages proxy rotation for workers
    - Round-robin proxy assignment
    - Per-worker proxy tracking
    - Automatic proxy switching on retry
    """

    def __init__(self, proxy_configs: List[Dict], host: str = "localhost"):
        """
        Initialize proxy manager

        Args:
            proxy_configs: List of proxy configs [{name, port, vpn_ip}, ...]
            host: Proxy host (default: localhost)
        """
        self.proxies = [
            ProxyConfig(
                name=p['name'],
                port=p['port'],
                vpn_ip=p['vpn_ip'],
                host=host
            )
            for p in proxy_configs
        ]

        if not self.proxies:
            raise ValueError("No proxies configured")

        self.current_index = 0
        self.lock = threading.Lock()

        # Track worker assignments
        self.worker_proxies: Dict[int, ProxyConfig] = {}

        logger.info(f"Initialized ProxyManager with {len(self.proxies)} proxies")
        for proxy in self.proxies:
            logger.info(f"  - {proxy.name}: {proxy.vpn_ip}:{proxy.port}")

    def get_proxy_for_worker(self, worker_id: int) -> ProxyConfig:
        """
        Get or assign proxy for a specific worker

        Args:
            worker_id: Worker ID (thread ID)

        Returns:
            ProxyConfig for the worker
        """
        with self.lock:
            # If worker already has a proxy, return it
            if worker_id in self.worker_proxies:
                return self.worker_proxies[worker_id]

            # Assign new proxy (round-robin)
            proxy = self.proxies[self.current_index % len(self.proxies)]
            self.current_index += 1

            self.worker_proxies[worker_id] = proxy
            logger.debug(f"Assigned proxy {proxy.name} ({proxy.vpn_ip}) to worker {worker_id}")

            return proxy

    def get_next_proxy(self, current_proxy: Optional[ProxyConfig] = None) -> ProxyConfig:
        """
        Get next proxy in rotation (for retries)

        Args:
            current_proxy: Current proxy being used (to skip it)

        Returns:
            Next proxy in rotation
        """
        with self.lock:
            # If no current proxy, just get next
            if current_proxy is None:
                proxy = self.proxies[self.current_index % len(self.proxies)]
                self.current_index += 1
                return proxy

            # Find next different proxy
            start_index = self.current_index
            attempts = 0
            max_attempts = len(self.proxies) * 2  # Prevent infinite loop

            while attempts < max_attempts:
                proxy = self.proxies[self.current_index % len(self.proxies)]
                self.current_index += 1
                attempts += 1

                # If different from current, use it
                if proxy.port != current_proxy.port:
                    logger.debug(f"Switched from {current_proxy.vpn_ip} to {proxy.vpn_ip}")
                    return proxy

            # If all proxies are the same (single proxy), return it
            logger.warning("Only one proxy available, reusing same proxy")
            return current_proxy

    def get_random_proxy(self) -> ProxyConfig:
        """
        Get a random proxy (for initial assignment)

        Returns:
            Random proxy
        """
        return random.choice(self.proxies)

    def update_worker_proxy(self, worker_id: int, proxy: ProxyConfig):
        """
        Update proxy assignment for a worker

        Args:
            worker_id: Worker ID
            proxy: New proxy config
        """
        with self.lock:
            self.worker_proxies[worker_id] = proxy
            logger.debug(f"Updated worker {worker_id} to proxy {proxy.name} ({proxy.vpn_ip})")

    def get_proxy_stats(self) -> Dict:
        """
        Get proxy usage statistics

        Returns:
            Dict with proxy stats
        """
        with self.lock:
            worker_counts = {}
            for proxy in self.worker_proxies.values():
                key = f"{proxy.name} ({proxy.vpn_ip})"
                worker_counts[key] = worker_counts.get(key, 0) + 1

            return {
                'total_proxies': len(self.proxies),
                'active_workers': len(self.worker_proxies),
                'proxy_distribution': worker_counts
            }

    def __len__(self) -> int:
        """Number of available proxies"""
        return len(self.proxies)
