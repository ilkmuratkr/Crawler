# Mimari Dokümantasyonu

## Sistem Mimarisi

```
┌─────────────────────────────────────────────────────────────┐
│                         USER INPUT                           │
│  (main.py or examples/*.py)                                  │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    NextJsCrawler                             │
│  • Orchestrates the entire pipeline                          │
│  • Manages parallel workers                                  │
│  • Handles results aggregation                               │
└──────┬──────────────────┬──────────────────┬────────────────┘
       │                  │                  │
       ▼                  ▼                  ▼
┌────────────┐   ┌──────────────┐   ┌────────────────┐
│ CDX Client │   │ WARC Fetcher │   │ NextJsDetector │
│            │   │              │   │                │
│ • Search   │   │ • HTTP Range │   │ • Patterns     │
│ • Filter   │   │ • Decompress │   │ • Confidence   │
└────┬───────┘   └──────┬───────┘   └────────┬───────┘
     │                  │                     │
     ▼                  ▼                     ▼
┌─────────────────────────────────────────────────────┐
│              Common Crawl Infrastructure             │
│  • CDX API (index.commoncrawl.org)                  │
│  • S3 Storage (data.commoncrawl.org)                │
└─────────────────────────────────────────────────────┘
```

## Veri Akışı

### Flow 1: CDX-based Search

```
1. User → NextJsCrawler.search_and_detect()
2. CDXClient.search() → CDX API
3. CDX API returns: [{url, filename, offset, length}, ...]
4. For each CDX record:
   a. WARCFetcher.fetch_warc_segment() → S3 with Range header
   b. WARCParser.extract_html() → Parse WARC record
   c. NextJsDetector.detect() → Analyze HTML
   d. If Next.js found → Add to results
5. Save results (JSON + CSV)
```

### Flow 2: Bulk WARC Search

```
1. User → bulk_warc_search.py
2. Download warc.paths.gz
3. For each WARC path (parallel):
   a. Fetch first N MB using Range header
   b. Parse WARC records from sample
   c. Detect Next.js in each record
   d. Collect results
4. Deduplicate by domain
5. Save results
```

## Modül Detayları

### 1. CDX Client (`src/cdx/client.py`)

**Sorumluluk:** Common Crawl CDX API ile iletişim

**Ana Metodlar:**
- `search()`: URL pattern'e göre CDX'te ara
- `get_available_indexes()`: Mevcut crawl index'lerini listele
- `extract_warc_info()`: CDX kaydından WARC bilgisi çıkar

**Özellikleri:**
- Retry logic (exponential backoff)
- Session pooling
- Rate limiting aware
- Streaming response parsing

**Örnek CDX Response:**
```
urlkey timestamp original mimetype statuscode digest length offset filename
com,example)/ 20240115120000 https://example.com/ text/html 200 ABC123 12345 987654321 crawl-data/.../warc/...
```

---

### 2. WARC Fetcher (`src/warc/fetcher.py`)

**Sorumluluk:** WARC dosyalarından verimli segment getirme

**Ana Metodlar:**
- `fetch_warc_segment()`: HTTP Range ile segment indir
- `verify_range_support()`: Server range desteği kontrolü
- `get_file_size()`: WARC dosya boyutu

**Kritik Optimizasyon:**
```python
# ❌ Kötü: Tüm WARC'ı indir (1GB+)
response = requests.get(warc_url)

# ✅ İyi: Sadece gerekli segment (10KB)
headers = {'Range': f'bytes={offset}-{offset+length-1}'}
response = requests.get(warc_url, headers=headers)
# Status: 206 Partial Content
```

**HTTP Range Request:**
```
GET /crawl-data/CC-MAIN-2025-47/segments/.../warc/... HTTP/1.1
Host: data.commoncrawl.org
Range: bytes=123456-133456

HTTP/1.1 206 Partial Content
Content-Range: bytes 123456-133456/1234567890
Content-Length: 10000
```

---

### 3. WARC Parser (`src/warc/parser.py`)

**Sorumluluk:** WARC formatını parse etme ve HTML çıkarma

**Ana Metodlar:**
- `parse_warc_record()`: WARC kaydını full parse et
- `extract_html()`: Sadece HTML içeriği al
- `is_html_response()`: HTML kontrolü

**WARC Format:**
```
WARC/1.0
WARC-Type: response
WARC-Target-URI: https://example.com
WARC-Date: 2024-01-15T12:00:00Z
Content-Length: 12345

HTTP/1.1 200 OK
Content-Type: text/html; charset=utf-8

<!DOCTYPE html>
<html>...
```

**Decompression:**
- Auto-detect gzip compression
- Fallback to raw if not compressed
- Encoding detection (UTF-8, ISO-8859-1, etc.)

---

### 4. Next.js Detector (`src/detectors/nextjs.py`)

**Sorumluluk:** HTML'de Next.js işaretlerini tespit etme

**Detection Strategy:**
```python
# High Confidence (3 points)
- /__NEXT_DATA__
- window.__NEXT_DATA__
- Build ID pattern

# Medium Confidence (2 points)
- /_next/static/
- next-route-announcer
- Next.js meta tags

# Low Confidence (1 point)
- /_next/
- "nextjs" mention
```

**Scoring:**
```python
if max_score >= 3 or total_score >= 5:
    confidence = "high"
elif max_score >= 2 or total_score >= 3:
    confidence = "medium"
else:
    confidence = "low"
```

**Örnek Detection:**
```html
<!-- High confidence indicators -->
<script id="__NEXT_DATA__">{"props":...}</script>
<script src="/_next/static/abc123/..."></script>

<!-- Build ID extraction -->
/_next/static/abc123xyz/_buildManifest.js
                ↓
        Build ID: abc123xyz
```

---

### 5. Rate Limiter (`src/utils/rate_limiter.py`)

**Sorumluluk:** API rate limiting

**3 Tip Limiter:**

#### Token Bucket (Default)
```python
RateLimiter(requests_per_second=2.0, burst=5)
# Burst: 5 istek hemen
# Sürdürülebilir: 2 req/s
```

#### Sliding Window
```python
SlidingWindowRateLimiter(requests_per_second=2.0)
# Daha kesin ama daha fazla memory
```

#### Adaptive
```python
AdaptiveRateLimiter(initial_rate=2.0, max_rate=10.0)
# Otomatik rate ayarlama
# Success → rate artır
# Error → rate azalt
```

**Kullanım:**
```python
limiter = RateLimiter(2.0)
limiter.acquire()  # Blocks until token available
make_request()
```

---

### 6. Main Crawler (`src/crawler.py`)

**Sorumluluk:** Tüm bileşenleri orkestra etme

**Pipeline:**
```python
def search_and_detect():
    # 1. CDX Search
    records = cdx_client.search(pattern)

    # 2. Parallel Processing
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [
            executor.submit(_process_record, record)
            for record in records
        ]

        # 3. Collect Results
        for future in as_completed(futures):
            result = future.result()
            if result and result['is_nextjs']:
                results.append(result)

    # 4. Save
    save_results(results)
```

**Duplicate Prevention:**
```python
found_domains = set()

if domain in found_domains:
    return None  # Skip

found_domains.add(domain)
```

---

## Performans Optimizasyonları

### 1. HTTP Range Requests

**Problem:** WARC dosyaları çok büyük (1-2GB)
**Çözüm:** Sadece gerekli kısmı indir

```python
# 1GB WARC yerine 10KB indir
# Tasarruf: %99.999
```

### 2. Parallel Processing

```python
ThreadPoolExecutor(max_workers=5)
# 5 URL aynı anda işle
# Hız artışı: ~5x
```

### 3. Streaming Parsing

```python
# ❌ Tüm response'u memory'ye al
data = response.content

# ✅ Stream et
for line in response.iter_lines():
    process(line)
```

### 4. Early Exit

```python
# HTML değilse hemen dön
if 'html' not in content_type:
    return None

# Next.js yoksa devam etme
if not detector.detect(html):
    return None
```

### 5. Deduplication

```python
# Domain set ile O(1) duplicate check
if domain in found_domains:
    return None
```

---

## Error Handling

### Retry Strategy

```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
def fetch_warc_segment():
    # 3 deneme
    # Bekleme: 4s, 8s, 10s
```

### Graceful Degradation

```python
try:
    warc_data = fetcher.fetch()
except RequestException:
    logger.error("Fetch failed")
    return None  # Skip, crash etme
```

### Timeout Protection

```python
requests.get(url, timeout=60)
# 60 saniye timeout
# Donmayı engelle
```

---

## Logging & Monitoring

### Log Levels

```python
DEBUG:   İç detaylar (parse, regex match, vb)
INFO:    Progress updates (X URLs processed)
WARNING: Recoverable errors (timeout, retry)
ERROR:   Unrecoverable errors (fatal)
```

### Progress Tracking

```python
ProgressLogger:
- total_processed
- nextjs_found
- errors
- rate_per_second
```

### Output

```python
# Console: Real-time progress
# File: Full logs
# JSON: Results
# CSV: Easy viewing
```

---

## Scalability

### Horizontal Scaling

```bash
# Machine 1
python main.py --pattern "a*.com/" --limit 10000

# Machine 2
python main.py --pattern "b*.com/" --limit 10000

# Combine results
cat results_*.json | jq -s 'add' > final.json
```

### Vertical Scaling

```bash
# Daha fazla worker
--workers 20

# Daha fazla rate
--rate-limit 5.0
```

### Resource Limits

```python
# Memory: ~100MB per worker
# Workers: 5 → ~500MB total
# Network: ~10Mbps sustained
# Disk: Minimal (streaming)
```

---

## Testing Strategy

### Unit Tests

```python
test_cdx_client()       # CDX API interaction
test_warc_fetcher()     # HTTP Range requests
test_warc_parser()      # WARC format parsing
test_nextjs_detector()  # Pattern matching
```

### Integration Tests

```python
test_full_pipeline()    # End-to-end
test_error_handling()   # Failure cases
test_rate_limiting()    # Rate limiter
```

### Manual Testing

```bash
make quick-test  # Quick smoke test
make test       # Component tests
```

---

## Security Considerations

### Input Validation

```python
# URL pattern sanitization
pattern = sanitize(user_input)

# No code execution
# No SQL injection risk (no DB)
```

### Rate Limiting

```python
# Respectful crawling
# No DDoS risk
# Common Crawl friendly
```

### Data Privacy

```python
# Public data only (Common Crawl)
# No personal info collected
# No authentication needed
```

---

## Future Improvements

### 1. Distributed Processing

```python
# Use Celery/RabbitMQ for task queue
# Multiple workers across machines
```

### 2. Caching Layer

```python
# Cache CDX results
# Cache WARC segments
# Redis/Memcached
```

### 3. Database Storage

```python
# PostgreSQL for results
# Time-series analysis
# Historical tracking
```

### 4. Advanced Detection

```python
# Version detection
# Framework detection (React, Vue, etc.)
# Tech stack analysis
```

### 5. API Service

```python
# REST API for queries
# Real-time detection
# Webhook notifications
```
