# Common Crawl Next.js Site Detector

Common Crawl'dan Next.js kullanan web sitelerini tespit eden profesyonel bir crawler.

**🚀 YENİ BAŞLIYORSAN → [START_HERE.md](START_HERE.md) dosyasını oku!**

## Özellikler

- **Verimli CDX Index Arama**: URL'leri WARC dosyalarında bulmak için CDX API kullanır
- **HTTP Range İstekleri**: Sadece gerekli WARC segmentlerini indirir (tüm dosya yerine)
- **Akıllı Next.js Tespiti**: Birden fazla yöntemle Next.js kullanımını tespit eder:
  - `_next/` path'leri
  - `__NEXT_DATA__` script tag'leri
  - Next.js meta tag'leri
  - Build ID'leri
- **Rate Limiting**: Common Crawl API'sine aşırı yük bindirmeden çalışır
- **Async İşlemler**: Hızlı ve verimli paralel işleme
- **Hata Yönetimi**: Retry logic ve graceful error handling
- **Progress Tracking**: İlerleme çubuğu ile detaylı bilgilendirme

## Kurulum

```bash
pip install -r requirements.txt
```

## Hızlı Başlangıç

```bash
# 1. Bağımlılıkları yükle
make install

# 2. Temel test (10 WARC)
make process-test

# 3. Küçük ölçek (100 WARC) - Önerilen başlangıç
make process-small

# 4. Büyük ölçek (1000 WARC) - Ciddi kullanım
make process-large

# 5. Başarısız olanları yeniden dene
make resume
```

## Detaylı Kullanım

### Yöntem 1: CDX API ile Arama

```bash
# Temel kullanım
python main.py --pattern "*.com/" --limit 1000

# Belirli bir index ile
python main.py --pattern "*.io/" --index "2025-47" --workers 10

# Yüksek güven seviyesi filtresi
python main.py --pattern "*.com/" --min-confidence high
```

### Yöntem 2: Bulk WARC Arama (Önerilen)

Bu yöntem en hızlı ve verimli yöntemdir. WARC dosyalarını doğrudan tarar.

```bash
# Toplu WARC tarama
python examples/bulk_warc_search.py --index CC-MAIN-2025-47 --max-files 100

# Daha fazla paralel işlem
python examples/bulk_warc_search.py --workers 10 --samples 20

# Küçük test
python examples/bulk_warc_search.py --max-files 10 --samples 5
```

### Yöntem 3: Belirli Domainleri Kontrol

```bash
# Kod içinde domain listesi tanımla
python examples/specific_domains.py

# Veya dosyadan oku
python main.py --domains-file domains.txt
```

## Mimari

```
src/
├── cdx/
│   └── client.py          # CDX API client
├── warc/
│   ├── fetcher.py         # WARC segmentleri için HTTP Range fetcher
│   └── parser.py          # WARC dosyalarını parse etme
├── detectors/
│   └── nextjs.py          # Next.js tespit algoritmaları
└── utils/
    ├── rate_limiter.py    # Rate limiting
    └── logger.py          # Logging utilities
```

## Nasıl Çalışır?

1. **CDX Index Query**: Common Crawl'ın CDX API'sine sorgu gönderilir
2. **WARC Location**: Her URL için WARC dosya konumu, offset ve length bilgisi alınır
3. **Range Request**: HTTP Range header kullanarak sadece ilgili segment indirilir
4. **Parse & Detect**: WARC içeriği parse edilir, HTML'de Next.js işaretleri aranır
5. **Save Results**: Tespit edilen domainler kaydedilir

## Performans

- Tüm WARC dosyası indirmek yerine HTTP Range kullanımı: **%95+ daha hızlı**
- Async işlemler: 10x paralel işlem desteği
- Smart caching: Duplicate kontrolleri

## Çıktı Formatı

```json
{
  "domain": "example.com",
  "url": "https://example.com",
  "detected_at": "2024-01-15T10:30:00Z",
  "crawl_date": "2024-01",
  "indicators": ["_next/static", "__NEXT_DATA__"],
  "confidence": "high"
}
```
