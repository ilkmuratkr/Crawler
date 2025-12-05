# Proje Özeti

Common Crawl'dan Next.js kullanan web sitelerini tespit eden profesyonel crawler sistemi.

## 🎯 Proje Hedefi

**100,000 WARC dosyasını tara → Next.js kullanan tüm siteleri bul (subdomain dahil tüm TLD'ler)**

## 🚀 Temel Özellikler

### 1. Verimli Veri Çekme
- ✅ HTTP Range requests (sadece gerekli kısmı indir)
- ✅ ~%99.9 bant genişliği tasarrufu
- ✅ 1GB WARC yerine 10MB sample

### 2. Akıllı Next.js Tespiti
- ✅ `__NEXT_DATA__` script tag
- ✅ `/_next/static/` path'leri
- ✅ Build ID extraction
- ✅ Meta tag analizi
- ✅ 3 seviye güven skoru (high/medium/low)

### 3. Gelişmiş Retry Sistemi ⭐ YENİ
- ✅ 5 deneme hakkı
- ✅ Her başarısızlıkta 5 dakika bekleme
- ✅ Başarısız WARC'ları kaydetme
- ✅ Resume desteği (kaldığı yerden devam)
- ✅ Detaylı failure raporlama

### 4. Rate Limiting & Ban Prevention
- ✅ Token bucket algorithm
- ✅ Adaptive rate limiter
- ✅ Common Crawl friendly

### 5. Paralel İşleme
- ✅ ThreadPoolExecutor ile paralel WARC işleme
- ✅ Configurable worker count
- ✅ Progress tracking

### 6. Tam Coverage
- ✅ Tüm TLD'ler (.com, .org, .io, .dev, .xyz, vb.)
- ✅ Subdomain'ler (blog.example.com, api.test.io)
- ✅ Country TLD'ler (.co.uk, .com.tr, .de)

## 📁 Proje Yapısı

```
CrawData/
├── src/
│   ├── cdx/                    # CDX API client
│   │   ├── __init__.py
│   │   └── client.py
│   ├── warc/                   # WARC fetcher & parser
│   │   ├── __init__.py
│   │   ├── fetcher.py         # HTTP Range ile segment çekme
│   │   └── parser.py          # WARC parse & HTML extraction
│   ├── detectors/              # Next.js detection
│   │   ├── __init__.py
│   │   └── nextjs.py          # Pattern matching & confidence scoring
│   ├── utils/                  # Utilities
│   │   ├── __init__.py
│   │   ├── rate_limiter.py    # Rate limiting
│   │   ├── logger.py          # Logging
│   │   └── retry_handler.py   # ⭐ Retry & failure tracking
│   ├── crawler.py              # Main crawler orchestrator
│   └── warc_processor.py       # ⭐ Advanced WARC processor
│
├── examples/
│   ├── simple_search.py        # Basit CDX arama
│   ├── specific_domains.py     # Belirli domainleri kontrol
│   ├── bulk_warc_search.py     # Toplu WARC tarama
│   ├── find_all_nextjs.py      # Tüm TLD'leri tara
│   └── test_components.py      # Component testleri
│
├── main.py                     # CDX-based ana script
├── process_warcs.py            # ⭐ WARC processor ana script (ADVANCED)
├── warc.paths                  # 100,000 WARC dosya listesi
│
├── data/
│   ├── output/                 # Sonuçlar (JSON + CSV)
│   └── failures/               # ⭐ Başarısız WARC'lar
│
├── logs/                       # Log dosyaları
│
├── README.md                   # Ana dokümantasyon
├── QUICKSTART.md              # Hızlı başlangıç
├── COMPARISON.md              # Yöntem karşılaştırması
├── ARCHITECTURE.md            # Mimari detayları
├── RETRY_SYSTEM.md            # ⭐ Retry sistemi dokümantasyonu
├── requirements.txt           # Python bağımlılıkları
├── Makefile                   # Kolay komutlar
└── .gitignore
```

## 🎮 Kullanım

### Hızlı Başlangıç

```bash
# 1. Kurulum
make install

# 2. Test (10 WARC)
make process-test

# 3. Küçük ölçek (100 WARC)
make process-small

# 4. Büyük ölçek (1000 WARC)
make process-large

# 5. Başarısızları retry
make resume
```

### Detaylı Kullanım

```bash
# Özel parametrelerle
python process_warcs.py \
  --limit 500 \
  --workers 10 \
  --retry-delay 300 \
  --max-retries 5 \
  --sample-size 10

# Önceki başarısızlıkları retry
python process_warcs.py \
  --resume-from data/failures/failed_warcs_20240115.json
```

## 📊 Çıktı Formatı

### JSON
```json
[
  {
    "domain": "blog.example.com",
    "url": "https://blog.example.com/page",
    "confidence": "high",
    "indicators": ["__NEXT_DATA__", "/_next/static/"],
    "build_id": "abc123xyz",
    "warc_source": "crawl-data/CC-MAIN-2025-47/..."
  }
]
```

### CSV
```csv
domain,url,confidence,build_id,warc_source
blog.example.com,https://blog.example.com,high,abc123xyz,crawl-data/...
api.test.io,https://api.test.io,medium,,crawl-data/...
```

### Failure JSON
```json
{
  "session_id": "20240115_103000",
  "total_failures": 15,
  "failures": [
    {
      "warc_path": "crawl-data/...",
      "failure_reason": "timeout",
      "failure_count": 5,
      "error_message": "ReadTimeout..."
    }
  ]
}
```

## 🔄 Workflow

### Tam Pipeline

```
1. İlk çalıştırma (1000 WARC)
   ├─> 950 başarılı
   ├─> 50 başarısız (saved)
   └─> ~300 Next.js sitesi bulundu

2. Resume (50 başarısız WARC)
   ├─> 40 başarılı
   ├─> 10 hala başarısız
   └─> ~12 Next.js sitesi daha bulundu

3. Son retry (10 WARC)
   ├─> 8 başarılı
   ├─> 2 kalıcı başarısız
   └─> ~2 Next.js sitesi daha bulundu

Toplam: ~314 Next.js sitesi ✅
```

## 🎯 Performans

### Hız
- **10 WARC:** ~5-10 dakika
- **100 WARC:** ~1-2 saat
- **1,000 WARC:** ~10-20 saat
- **10,000 WARC:** ~4-8 gün
- **100,000 WARC:** ~40-80 gün (1-3 ay)

### Beklenen Sonuçlar
- **1,000 WARC:** ~200-500 Next.js sitesi
- **10,000 WARC:** ~2,000-5,000 Next.js sitesi
- **100,000 WARC:** ~20,000-50,000 Next.js sitesi

### Kaynak Kullanımı
- **Memory:** ~500MB-1GB (5-10 worker)
- **Disk:** ~100MB-1GB (sonuçlar)
- **Network:** ~10-50 Mbps sustained
- **CPU:** Moderate (parsing)

## 🛡️ Güvenlik & Best Practices

### Rate Limiting
```python
# Default: 2 req/s (güvenli)
rate_limit = 2.0

# Aggressive: 5-10 req/s (riskli)
# Conservative: 0.5-1 req/s (çok yavaş)
```

### Retry Strategy
```python
# Default: 5 deneme, 5 dakika bekleme
max_retries = 5
retry_delay = 300  # seconds

# Hızlı test: 3 deneme, 1 dakika
# Güvenli: 10 deneme, 10 dakika
```

### Worker Count
```python
# Başlangıç: 3-5 workers
# Normal: 5-10 workers
# Aggressive: 10-20 workers (riskli)
```

## 📈 İzleme & Raporlama

### Real-time Output
```bash
Processing WARCs: 45%|████████████████     | 450/1000 [02:15<02:45,  3.32it/s]

✓ Found: blog.example.com (high)
✓ Found: api.test.io (medium)
✓ Found: shop.demo.org (high)
```

### Final Report
```
============================================================
FINAL STATISTICS
============================================================
Total processed: 1000
Successful: 950
Failed: 50
Next.js sites found: 314
Unique domains: 298

Failure breakdown:
  timeout: 30
  connection_error: 15
  http_error: 5
============================================================
```

## 🔧 Troubleshooting

### Çok Fazla Timeout
```bash
# Daha uzun timeout, daha az worker
--retry-delay 600 --workers 3
```

### Memory Hatası
```bash
# Daha küçük sample, daha az worker
--sample-size 5 --workers 2
```

### Ban/Rate Limit
```bash
# Daha yavaş rate limit
--rate-limit 1.0 --retry-delay 600
```

## 📚 Dokümantasyon

- **README.md**: Genel bakış
- **QUICKSTART.md**: Hızlı başlangıç rehberi
- **COMPARISON.md**: Yöntem karşılaştırması
- **ARCHITECTURE.md**: Teknik mimari
- **RETRY_SYSTEM.md**: Retry sistemi detayları

## 🎓 Örnekler

### 1. Test Çalıştırması
```bash
make process-test
# 10 WARC, ~5 dakika, ~5-10 site
```

### 2. Küçük Araştırma
```bash
make process-small
# 100 WARC, ~2 saat, ~50-100 site
```

### 3. Ciddi Tarama
```bash
make process-large
# 1000 WARC, ~20 saat, ~300-500 site
```

### 4. Full Tarama (Uzun Vadeli)
```bash
# Split into batches
for i in {1..10}; do
  python process_warcs.py --limit 10000 --workers 10
  make resume
  sleep 3600  # 1 saat ara
done
```

## 🌟 Gelişmiş Özellikler

### 1. Adaptive Rate Limiting
```python
from src.utils import AdaptiveRateLimiter

# Otomatik rate ayarlama
# Success → rate artır
# Error → rate azalt
```

### 2. Failure Analysis
```python
from src.utils import FailureTracker

tracker = FailureTracker()
stats = tracker.get_statistics()
# {'timeout': 30, 'connection_error': 15, ...}
```

### 3. Resume System
```bash
# Otomatik en son failure'ı bul ve retry et
make resume

# Manuel belirli failure file
python process_warcs.py --resume-from data/failures/failed_warcs_X.json
```

## 🎯 Sonuç

Bu proje, Common Crawl'ın 100,000 WARC dosyasından Next.js kullanan siteleri verimli, güvenli ve ölçeklenebilir bir şekilde bulur.

**Temel Avantajlar:**
- ✅ HTTP Range ile %99.9 veri tasarrufu
- ✅ 5 deneme + 5 dakika bekleme ile yüksek başarı oranı
- ✅ Failure tracking ile hiçbir veri kaybı yok
- ✅ Resume desteği ile kesintisiz işlem
- ✅ Tüm TLD ve subdomain'leri kapsar
- ✅ Paralel işlem ile hızlı tarama

**Kullanım Senaryoları:**
1. Next.js market araştırması
2. Akademik çalışmalar
3. SEO analizi
4. Framework adoption trends
5. Web teknoloji analizi

**İletişim & Katkı:**
- Issues: GitHub issues
- Katkıda bulunmak için pull request gönderin
- Dokümantasyon iyileştirmeleri hoş karşılanır

---

Made with ❤️ for the Next.js community
