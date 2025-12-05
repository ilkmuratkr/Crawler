# 🚀 BURADAN BAŞLA

## İlk Adımlar

### 1. Kurulum (30 saniye)

```bash
make install
```

Bu komut tüm Python bağımlılıklarını yükler.

### 2. Test Çalıştırması (5 dakika)

```bash
make process-test
```

Bu komut:
- İlk 10 WARC dosyasını işler
- Next.js sitelerini bulur
- Sistemi test eder

**Beklenen sonuç:**
```
✓ Found: vercel.com (high)
✓ Found: nextjs.org (high)
...
Total Next.js sites found: 3-5
```

### 3. Gerçek Tarama (2 saat)

```bash
make process-small
```

Bu komut:
- 100 WARC dosyasını işler
- ~50-100 Next.js sitesi bulur
- Başarısızları kaydeder

---

## ⚡ Hızlı Komutlar

```bash
# Test (10 WARC, ~5 dakika)
make process-test

# Küçük (100 WARC, ~2 saat)
make process-small

# Büyük (1000 WARC, ~20 saat)
make process-large

# Başarısızları tekrar dene
make resume

# Temizlik
make clean

# Yardım
make help
```

---

## 📂 Sonuçlar Nerede?

### Başarılı Sonuçlar
```
data/output/nextjs_sites_YYYYMMDD_HHMMSS.json
data/output/nextjs_sites_YYYYMMDD_HHMMSS.csv
```

### Başarısızlar (Retry için)
```
data/failures/failed_warcs_YYYYMMDD_HHMMSS.json
data/failures/failed_warcs_YYYYMMDD_HHMMSS.txt
```

### Loglar
```
logs/crawler_YYYYMMDD_HHMMSS.log
```

---

## 🎯 En İyi Strateji

### Öneri: Aşama Aşama İlerleme

```bash
# Adım 1: Test (5 dk)
make process-test

# Sonuçları kontrol et:
cat data/output/nextjs_sites_*.json

# Adım 2: Küçük tarama (2 saat)
make process-small

# Başarısızları retry et:
make resume

# Adım 3: Büyük tarama (20 saat)
make process-large

# Tekrar retry:
make resume

# Adım 4: Çok büyük tarama (günler)
python process_warcs.py --limit 10000 --workers 10

# Son retry:
make resume
```

---

## 🔧 Özelleştirme

### Parametreleri Değiştir

```bash
python process_warcs.py \
  --limit 500 \           # Kaç WARC işlenecek
  --workers 10 \          # Paralel worker sayısı
  --retry-delay 300 \     # Retry arası bekleme (saniye)
  --max-retries 5 \       # Max kaç deneme
  --sample-size 10        # Her WARC'tan kaç MB
```

### Hızlı Test İçin

```bash
python process_warcs.py \
  --limit 10 \
  --workers 3 \
  --retry-delay 30 \      # 30 saniye (test için)
  --max-retries 3
```

### Güvenli & Yavaş

```bash
python process_warcs.py \
  --limit 100 \
  --workers 2 \           # Az worker
  --retry-delay 600 \     # 10 dakika bekleme
  --max-retries 10 \      # Çok deneme
  --rate-limit 1.0        # Yavaş rate
```

---

## 📊 Ne Bulacaksın?

### Örnek Sonuç

```json
{
  "domain": "blog.example.com",
  "url": "https://blog.example.com/page",
  "confidence": "high",
  "indicators": [
    "__NEXT_DATA__",
    "/_next/static/",
    "build_id:abc123"
  ],
  "build_id": "abc123xyz"
}
```

### Subdomain Örnekleri

- `blog.example.com` ✅
- `api.test.io` ✅
- `shop.demo.co.uk` ✅
- `docs.app.vercel.com` ✅

### Tüm TLD'ler

- `.com`, `.org`, `.net` ✅
- `.io`, `.dev`, `.app` ✅
- `.co.uk`, `.com.tr`, `.de` ✅
- `.xyz`, `.tech`, `.blog` ✅

---

## 🎓 Öğrenme Kaynakları

1. **README.md** - Genel bakış
2. **QUICKSTART.md** - Detaylı başlangıç
3. **RETRY_SYSTEM.md** - Retry sistemi
4. **COMPARISON.md** - Yöntem karşılaştırması
5. **ARCHITECTURE.md** - Teknik detaylar
6. **PROJECT_SUMMARY.md** - Tam özet

---

## ⚠️ Önemli Notlar

### ✅ Yapılması Gerekenler

- **Küçük test ile başla** (`make process-test`)
- **Sonuçları kontrol et** (data/output/)
- **Başarısızları retry et** (`make resume`)
- **İlerle adım adım** (10 → 100 → 1000)

### ❌ Yapılmaması Gerekenler

- ❌ İlk seferde 100,000 WARC işleme
- ❌ Çok fazla worker (>20) kullanma
- ❌ Retry delay'i çok kısa yapma (<60s)
- ❌ Ban yeme riskini göze alma

---

## 🆘 Sorun Giderme

### "No module named 'src'"

```bash
# Python path hatası
# Çözüm: Script'i root dizinden çalıştır
cd /Users/muratkara/CrawData
python process_warcs.py --limit 10
```

### "warc.paths not found"

```bash
# warc.paths dosyası bulunamadı
# Çözüm: Dosya root dizinde olmalı
ls warc.paths  # Kontrol et
```

### Timeout Hataları

```bash
# Çok fazla timeout
# Çözüm: Daha yavaş parametreler
python process_warcs.py \
  --workers 3 \
  --retry-delay 600 \
  --rate-limit 1.0
```

### Memory Hatası

```bash
# Memory doldu
# Çözüm: Daha küçük sample, az worker
python process_warcs.py \
  --sample-size 5 \
  --workers 2
```

---

## 📱 İletişim

### Yardım

```bash
# Komut yardımı
python process_warcs.py --help

# Makefile komutları
make help

# Component testleri
make test
```

### Log İzleme

```bash
# Real-time log izle
tail -f logs/crawler_*.log

# Son 100 satır
tail -100 logs/crawler_*.log

# Sadece hataları göster
grep ERROR logs/crawler_*.log
```

---

## 🎉 İlk Çalıştırma Checklist

- [ ] `make install` çalıştırdım
- [ ] `make process-test` ile test ettim
- [ ] Sonuçları `data/output/` dizininde gördüm
- [ ] `make process-small` ile 100 WARC işledim
- [ ] `make resume` ile başarısızları retry ettim
- [ ] Logları kontrol ettim
- [ ] Parametreleri anladım
- [ ] Dokümantasyonu okudum
- [ ] Büyük taramaya hazırım! 🚀

---

## 🌟 Başarı!

Artık hazırsın! Küçük bir test ile başla:

```bash
make process-test
```

Sonra yavaş yavaş ölçeği artır. İyi taramalar! 🎯

---

**Not:** Herhangi bir sorun için dokümantasyona bak:
- Teknik: ARCHITECTURE.md
- Retry: RETRY_SYSTEM.md
- Karşılaştırma: COMPARISON.md
- Genel: README.md
