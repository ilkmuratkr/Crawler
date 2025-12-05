# Quick Start Guide

Common Crawl'dan Next.js siteleri bulmak için hızlı başlangıç rehberi.

## 1. Kurulum

```bash
# Bağımlılıkları yükle
pip install -r requirements.txt
```

## 2. Temel Kullanım

### Örnek 1: Basit Arama

En son Common Crawl'dan Next.js siteleri ara:

```bash
python main.py --pattern "*.com/" --limit 100
```

### Örnek 2: Belirli Domainleri Kontrol Et

```bash
python examples/specific_domains.py
```

### Örnek 3: Toplu WARC Arama (Önerilen - En Hızlı)

```bash
python examples/bulk_warc_search.py --index CC-MAIN-2025-47 --max-files 50 --workers 10
```

Bu yöntem:
- ✅ En hızlı yöntem (HTTP Range ile sadece gerekli parçaları indirir)
- ✅ Birçok WARC dosyasını paralel işler
- ✅ Ban yeme riski düşük

## 3. Parametreler

### Ana Script (main.py)

```bash
python main.py \
  --pattern "*.com/" \           # Aranacak URL pattern'i
  --index "2025-47" \             # Common Crawl index'i
  --limit 1000 \                  # Max işlenecek URL sayısı
  --workers 5 \                   # Paralel worker sayısı
  --rate-limit 2.0 \              # İstek/saniye
  --min-confidence medium \       # Minimum güven seviyesi
  --output-dir data/output        # Çıktı dizini
```

### Bulk WARC Search (Önerilen)

```bash
python examples/bulk_warc_search.py \
  --index CC-MAIN-2025-47 \       # Hangi crawl index'i
  --max-files 100 \               # Kaç WARC dosyası işlenecek
  --samples 10 \                  # Her WARC'tan kaç örnek
  --workers 5                     # Paralel worker
```

## 4. Çıktı Formatı

Sonuçlar `data/output/` dizininde JSON ve CSV olarak kaydedilir:

**JSON:**
```json
[
  {
    "domain": "example.com",
    "url": "https://example.com",
    "confidence": "high",
    "indicators": ["__NEXT_DATA__", "/_next/static/"],
    "build_id": "abc123xyz",
    "detected_at": "2024-01-15T10:30:00Z",
    "crawl_date": "20240110120000"
  }
]
```

**CSV:**
```csv
domain,url,confidence,build_id,detected_at,crawl_date
example.com,https://example.com,high,abc123xyz,2024-01-15T10:30:00Z,20240110120000
```

## 5. Strateji Önerileri

### Küçük Test (İlk Deneme)

```bash
# Az sayıda URL ile test et
python main.py --pattern "vercel.com" --limit 10
```

### Orta Ölçekli Arama

```bash
# CDX API ile belirli pattern ara
python main.py --pattern "*.io/" --limit 5000 --workers 10
```

### Büyük Ölçekli Arama (Önerilen)

```bash
# WARC dosyalarını toplu tara
python examples/bulk_warc_search.py \
  --index CC-MAIN-2025-47 \
  --max-files 1000 \
  --samples 20 \
  --workers 10
```

## 6. Rate Limiting

Common Crawl'a karşı nazik olun:

- **Önerilen:** 2-5 request/second
- **Maksimum:** 10 request/second
- **Ban yapmama için:** Adaptive rate limiter kullan

```python
from src.utils import AdaptiveRateLimiter

limiter = AdaptiveRateLimiter(
    initial_rate=2.0,
    min_rate=0.5,
    max_rate=10.0
)
```

## 7. Performans İpuçları

### Hızlandırma

1. **HTTP Range kullan** (zaten implement edildi ✅)
   - Tüm WARC yerine sadece gerekli parçayı indir

2. **Paralel işlem**
   ```bash
   --workers 10  # Daha fazla paralel işlem
   ```

3. **Bulk WARC search kullan**
   ```bash
   python examples/bulk_warc_search.py --max-files 500
   ```

4. **Confidence seviyesini düşür**
   ```bash
   --min-confidence low  # Daha az filtreleme = daha hızlı
   ```

### Memory Optimizasyonu

```bash
# Daha az örnek = daha az memory
python examples/bulk_warc_search.py --samples 5
```

## 8. Sorun Giderme

### HTTP 429 (Too Many Requests)

Rate limiting çok agresif:

```bash
--rate-limit 1.0  # Daha yavaş yap
```

### Timeout Hataları

```bash
# CDX_API_TIMEOUT ve WARC_FETCH_TIMEOUT'u artır
# config.py dosyasında:
WARC_FETCH_TIMEOUT = 120
```

### Memory Problemi

```bash
# Worker sayısını azalt
--workers 2

# Veya sample size'ı küçült
--samples 5
```

## 9. Sonuçları Analiz Et

```bash
# JSON sonuçları görüntüle
cat data/output/nextjs_sites_*.json | jq '.[].domain'

# CSV'yi aç
open data/output/nextjs_sites_*.csv
```

## 10. İleri Seviye

### Belirli Tarih Aralığı

```python
from src.cdx import CDXClient

client = CDXClient()
records = client.search(
    url="*.com/",
    from_ts="20240101000000",
    to_ts="20240131235959"
)
```

### Custom Detection Patterns

```python
from src.detectors import NextJsDetector

detector = NextJsDetector()

# Custom pattern ekle
detector.HIGH_CONFIDENCE_PATTERNS.append(r'your-custom-pattern')
```

## Yardım

Sorun mu var? Loglara bak:

```bash
# Log dosyası
tail -f logs/crawler_*.log
```

Veya debug mode:

```bash
python main.py --log-level DEBUG --pattern "test.com" --limit 5
```
