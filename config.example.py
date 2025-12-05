"""
Configuration file for the crawler
Copy this to config.py and modify as needed
"""

# Common Crawl Settings
DEFAULT_INDEX = "2025-47"  # Latest index
CDX_API_TIMEOUT = 30
WARC_FETCH_TIMEOUT = 60

# Rate Limiting
REQUESTS_PER_SECOND = 2.0
MAX_BURST = 5

# Parallel Processing
MAX_WORKERS = 5
THREAD_POOL_SIZE = 10

# Detection Settings
MIN_CONFIDENCE = "medium"  # 'low', 'medium', 'high'
ENABLE_HIGH_CONFIDENCE_ONLY = False

# Output Settings
OUTPUT_DIR = "data/output"
LOG_DIR = "logs"
SAVE_CSV = True
SAVE_JSON = True

# Search Settings
DEFAULT_LIMIT = 1000
DEFAULT_MATCH_TYPE = "prefix"

# Performance Tuning
WARC_SAMPLE_SIZE = 10 * 1024 * 1024  # 10 MB per WARC sample
ENABLE_CACHING = False
CACHE_DIR = "data/cache"

# Logging
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# User Agent
USER_AGENT = "NextJS-Detector/1.0 (Research Project; +https://github.com/yourusername/project)"

# Advanced: Retry Settings
MAX_RETRIES = 3
RETRY_BACKOFF_MULTIPLIER = 1
RETRY_BACKOFF_MIN = 4
RETRY_BACKOFF_MAX = 10

# Proxy Settings (Optional)
# Her worker farklı proxy kullanır, retry'larda da proxy rotation yapılır
ENABLE_PROXY = False
PROXY_HOST = "localhost"  # Docker container host
PROXY_CONFIGS = [
    # {"name": "alpine-vpn-3973", "port": 8956, "vpn_ip": "223.165.69.73"},
    # {"name": "alpine-vpn-2547", "port": 8955, "vpn_ip": "68.235.38.19"},
    # {"name": "alpine-vpn-5853", "port": 8954, "vpn_ip": "134.19.179.50"},
    # Daha fazla proxy ekleyin...
]
