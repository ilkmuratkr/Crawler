# Retry & Failure Tracking System

Gelişmiş retry mekanizması ve başarısızlık takip sistemi dokümantasyonu.

## Özellikler

✅ **5 Deneme Hakkı**: Her WARC için maksimum 5 deneme
✅ **5 Dakika Bekleme**: Her başarısız denemeden sonra 5 dakika bekle
✅ **Failure Tracking**: Başarısız WARC'ları JSON ve TXT formatında kaydet
✅ **Resume Desteği**: Önceki başarısızlıkları yeniden dene
✅ **Detaylı Raporlama**: Başarısızlık sebeplerini kategorize et
✅ **Paralel İşlem**: Birden fazla WARC aynı anda işle

## Nasıl Çalışır?

### 1. Retry Mekanizması

```python
# Her WARC için:
for attempt in range(1, 6):  # 1-5 arası 5 deneme
    try:
        fetch_warc()
        # Başarılı!
        break
    except Exception as e:
        if attempt == 5:
            # Son deneme, başarısız
            save_to_failures(warc_path, reason, error)
        else:
            # Tekrar dene
            wait(300)  # 5 dakika bekle
```

### 2. Failure Tracking

Başarısız her WARC için şunlar kaydedilir:

```json
{
  "url": "https://data.commoncrawl.org/crawl-data/...",
  "warc_path": "crawl-data/CC-MAIN-2025-47/...",
  "failure_reason": "timeout",
  "failure_count": 5,
  "last_attempt": "2024-01-15T10:30:00Z",
  "error_message": "Timeout after 120s",
  "first_failed": "2024-01-15T10:00:00Z"
}
```

### 3. Failure Kategorileri

- **timeout**: Bağlantı zaman aşımı
- **connection_error**: Ağ bağlantı hatası
- **http_error**: HTTP status hatası (404, 500, vb.)
- **parse_error**: WARC parse hatası
- **unknown**: Bilinmeyen hata

## Kullanım

### Temel Kullanım

```bash
# 100 WARC işle, başarısızları kaydet
python process_warcs.py --limit 100

# Output:
# ✓ data/output/nextjs_sites_20240115_103000.json
# ✓ data/failures/failed_warcs_20240115_103000.json
```

### Başarısızları Yeniden Dene (Resume)

```bash
# Manuel
python process_warcs.py --resume-from data/failures/failed_warcs_20240115_103000.json

# Veya Makefile ile (otomatik en son failure'ı bulur)
make resume
```

### Özel Parametreler

```bash
# Daha az bekleme (test için)
python process_warcs.py --limit 10 --retry-delay 60

# Daha fazla deneme
python process_warcs.py --limit 100 --max-retries 10

# Daha fazla paralel işlem
python process_warcs.py --limit 100 --workers 20
```

## Dosya Formatları

### Failure JSON

```json
{
  "session_id": "20240115_103000",
  "total_failures": 15,
  "generated_at": "2024-01-15T12:00:00Z",
  "failures": [
    {
      "url": "https://data.commoncrawl.org/...",
      "warc_path": "crawl-data/...",
      "failure_reason": "timeout",
      "failure_count": 5,
      "last_attempt": "2024-01-15T11:50:00Z",
      "error_message": "ReadTimeout: HTTPSConnectionPool...",
      "first_failed": "2024-01-15T10:30:00Z"
    }
  ]
}
```

### Failure TXT (Kolay Resume İçin)

```
crawl-data/CC-MAIN-2025-47/segments/1762439342185.16/warc/CC-MAIN-20251106200718-00001.warc.gz
crawl-data/CC-MAIN-2025-47/segments/1762439342185.16/warc/CC-MAIN-20251106200718-00005.warc.gz
crawl-data/CC-MAIN-2025-47/segments/1762439342185.16/warc/CC-MAIN-20251106200718-00012.warc.gz
```

## İstatistikler

İşlem sonunda detaylı istatistikler gösterilir:

```
============================================================
FINAL STATISTICS
============================================================
Total processed: 100
Successful: 85
Failed: 15
Next.js sites found: 42
Unique domains: 38

Failure breakdown:
  timeout: 8
  connection_error: 5
  http_error: 2
============================================================
Failed WARCs saved to: data/failures/failed_warcs_20240115_103000.json
You can retry with: --resume-from data/failures/failed_warcs_20240115_103000.json
```

## Workflow Örnekleri

### Senaryo 1: İlk Çalıştırma

```bash
# 1. İlk 1000 WARC'ı işle
make process-large

# Output:
# ✓ 950 başarılı, 50 başarısız
# ✓ Sonuçlar: data/output/nextjs_sites_20240115_103000.json
# ✓ Başarısızlar: data/failures/failed_warcs_20240115_103000.json
```

### Senaryo 2: Başarısızları Yeniden Dene

```bash
# 2. Başarısızları tekrar dene (örneğin ertesi gün)
make resume

# Bu sefer belki 40 başarılı, 10 hala başarısız
# ✓ Yeni sonuçlar eklendi
# ✓ Hala başarısız olanlar yeni failure dosyasında
```

### Senaryo 3: Manuel Retry

```bash
# 3. Belirli bir failure file'ı retry et
python process_warcs.py \
  --resume-from data/failures/failed_warcs_20240115_103000.json \
  --retry-delay 600 \
  --workers 3

# Daha uzun bekleme, daha az paralel işlem
```

### Senaryo 4: Full Pipeline

```bash
# Day 1: İlk 10,000 WARC
python process_warcs.py --limit 10000 --workers 10

# Output:
# - 9,500 successful
# - 500 failed → saved to failed_warcs_DAY1.json

# Day 2: Kalan 90,000 WARC
python process_warcs.py --limit 90000 --workers 10

# Output:
# - 85,500 successful
# - 4,500 failed → saved to failed_warcs_DAY2.json

# Day 3: Tüm başarısızları retry
python process_warcs.py --resume-from data/failures/failed_warcs_DAY1.json
python process_warcs.py --resume-from data/failures/failed_warcs_DAY2.json

# Day 4: Hala başarısız olanlar için son deneme
make resume
```

## Performans Optimizasyonu

### Hız vs Güvenilirlik

**Hızlı ama riskli:**
```bash
python process_warcs.py \
  --workers 20 \
  --retry-delay 60 \
  --max-retries 2
```

**Yavaş ama güvenli:**
```bash
python process_warcs.py \
  --workers 3 \
  --retry-delay 600 \
  --max-retries 10
```

**Dengeli (önerilen):**
```bash
python process_warcs.py \
  --workers 5-10 \
  --retry-delay 300 \
  --max-retries 5
```

## Sorun Giderme

### Çok Fazla Timeout

```bash
# Daha uzun timeout
# config.py veya src/warc_processor.py içinde:
timeout=180  # 3 dakika

# Daha az paralel işlem
--workers 3
```

### Çok Fazla Connection Error

```bash
# Rate limit düşür
--rate-limit 1.0

# Daha uzun retry delay
--retry-delay 600  # 10 dakika
```

### Memory Problemi

```bash
# Daha küçük sample size
--sample-size 5  # 5 MB instead of 10

# Daha az worker
--workers 3
```

### Disk Doldu

```bash
# Eski sonuçları temizle
make clean

# Veya manuel
rm -rf data/output/*.json
rm -rf data/failures/*.json
```

## API Referansı

### RetryHandler

```python
from src.utils import RetryHandler

handler = RetryHandler(
    max_retries=5,
    retry_delay=300,
    failure_tracker=FailureTracker()
)

result = handler.execute_with_retry(
    fetch_function,
    warc_path="crawl-data/...",
    arg1=value1
)
```

### FailureTracker

```python
from src.utils import FailureTracker

tracker = FailureTracker(output_dir="data/failures")

# Başarısızlık ekle
tracker.add_failure(
    warc_path="crawl-data/...",
    reason=FailureReason.TIMEOUT,
    error=exception,
    attempt=5
)

# Kaydet
filepath = tracker.save_failures()

# Yükle
paths = tracker.load_failures("data/failures/failed_warcs_*.json")

# İstatistikler
stats = tracker.get_statistics()
```

### WARCProcessor

```python
from src.warc_processor import WARCProcessor

processor = WARCProcessor(
    warc_paths_file="warc.paths",
    workers=5,
    max_retries=5,
    retry_delay=300
)

# İşle
results = processor.process_all(limit=100)

# Kaydet
processor.save_results(results)

# Finalize (failures'ları kaydet)
processor.finalize()
```

## Best Practices

1. **Küçük başla:** İlk çalıştırmada `--limit 10` ile test et
2. **İlerle:** Sonra 100, 1000, 10000 şeklinde artır
3. **Resume kullan:** Her batch'ten sonra başarısızları retry et
4. **İstatistikleri takip et:** Failure rate %10'dan fazlaysa parametreleri ayarla
5. **Sabırlı ol:** 5 dakika bekleme uzun görünebilir ama ban yememek için gerekli
6. **Log'ları izle:** `tail -f logs/crawler_*.log`
7. **Disk izle:** Sonuç dosyaları büyüyebilir
8. **Backup al:** Önemli sonuçları yedekle

## Örnek Timeline

```
00:00 - Start processing 1000 WARCs
00:10 - 100 processed (90 success, 10 retrying)
00:20 - 200 processed (180 success, 20 retrying)
...
02:00 - 1000 processed (950 success, 50 failed)
02:01 - Saving results...
02:01 - Saving failures...
02:01 - Done!

Next day:
00:00 - Resume from failures
00:30 - 50 processed (40 success, 10 still failing)
00:31 - Done!
```

## Sıkça Sorulan Sorular

**S: 5 dakika çok uzun, daha kısa yapabilir miyim?**
A: Evet, `--retry-delay 60` ile 1 dakika yapabilirsin ama ban riski artar.

**S: Tüm 100,000 WARC'ı işlemek ne kadar sürer?**
A: 5 worker ile ~7-10 gün. 10 worker ile ~3-5 gün.

**S: Başarısızlıkları nasıl azaltabilirim?**
A: Daha az worker, daha uzun timeout, daha düşük rate limit.

**S: Resume sonsuz döngüye girer mi?**
A: Hayır, her resume yeni bir failure file oluşturur.

**S: Sonuçlar duplicate içerir mi?**
A: Hayır, domain-level deduplication var.
