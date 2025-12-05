# Yöntem Karşılaştırması

## Common Crawl'dan Next.js Siteleri Bulmanın 3 Yolu

### 🥇 Yöntem 1: Bulk WARC Search (ÖNERİLEN)

**Dosya:** `examples/bulk_warc_search.py`

#### Nasıl Çalışır?
1. WARC paths listesini indir (`warc.paths.gz`)
2. Her WARC dosyasından küçük sample'lar al (HTTP Range)
3. Sample'larda Next.js ara
4. Paralel işle

#### Avantajlar
✅ **En hızlı yöntem** - CDX query overhead'i yok
✅ **Daha fazla coverage** - Tüm WARC'ları tarayabilirsin
✅ **HTTP Range kullanımı** - Sadece ilk 10MB'ı indir
✅ **Ban riski düşük** - Direct S3 access
✅ **Ölçeklenebilir** - Binlerce WARC'ı paralel işle

#### Dezavantajlar
❌ Random sampling - Bazı siteleri kaçırabilir
❌ Her WARC'tan sadece sample alıyor (tam değil)

#### Performans
- **İşlem hızı:** ~10-20 WARC/dakika (5 worker ile)
- **Bant genişliği:** ~100MB/dakika (sample size'a göre)
- **Sonuç sayısı:** 100 WARC'ta ~50-100 Next.js sitesi bulabilir

#### Kullanım
```bash
python examples/bulk_warc_search.py \
  --index CC-MAIN-2025-47 \
  --max-files 100 \
  --samples 10 \
  --workers 5
```

---

### 🥈 Yöntem 2: CDX API ile Targeted Search

**Dosya:** `main.py`

#### Nasıl Çalışır?
1. CDX API'ye URL pattern sorgusu gönder
2. Dönen her URL için WARC location al
3. WARC'tan sadece o URL'in kaydını indir (HTTP Range)
4. Next.js tespit et

#### Avantajlar
✅ **Targeted search** - Belirli domain veya pattern'leri ara
✅ **HTTP Range kullanımı** - Sadece gerekli kısmı indir
✅ **Kesin sonuçlar** - Her URL kontrol edilir
✅ **Filtering** - Status code, mime type, tarih filtreleme

#### Dezavantajlar
❌ CDX API rate limit'e takılabilir
❌ Her CDX query biraz yavaş
❌ Pattern-based - Önceden ne arayacağını bilmelisin

#### Performans
- **İşlem hızı:** ~2-5 URL/saniye (rate limit'e göre)
- **CDX overhead:** Her URL için 1 CDX query
- **En iyi kullanım:** Belirli domainleri kontrol etmek için

#### Kullanım
```bash
# Genel pattern
python main.py --pattern "*.com/" --limit 1000

# Belirli domain
python main.py --pattern "vercel.com" --match-type domain
```

---

### 🥉 Yöntem 3: Domain List Check

**Dosya:** `examples/specific_domains.py` veya `main.py --domains-file`

#### Nasıl Çalışır?
1. Dosyadan domain listesi oku
2. Her domain için CDX query
3. WARC fetch + detection

#### Avantajlar
✅ **Spesifik kontrol** - Bilinen domainleri kontrol et
✅ **Küçük scope** - Az sayıda domain için ideal
✅ **Doğrulama** - "X sitesi Next.js kullanıyor mu?" sorusuna cevap

#### Dezavantajlar
❌ Önceden domain listesi gerekli
❌ Keşif yapamaz (yeni siteler bulamaz)
❌ Yavaş (her domain için CDX query)

#### Performans
- **İşlem hızı:** ~1-2 domain/saniye
- **En iyi kullanım:** <100 domain kontrolü

#### Kullanım
```bash
# domains.txt dosyası:
# vercel.com
# nextjs.org
# github.com

python main.py --domains-file domains.txt
```

---

## Karşılaştırma Tablosu

| Özellik | Bulk WARC | CDX Targeted | Domain List |
|---------|-----------|--------------|-------------|
| **Hız** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| **Coverage** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐ |
| **Kesinlik** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Ban Riski** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| **Bant Genişliği** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Keşif Yeteneği** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐ |

---

## Senaryolara Göre Öneriler

### Senaryo 1: Geniş Çaplı Keşif
**Amaç:** Mümkün olduğunca çok Next.js sitesi bul

**Önerilen Yöntem:** 🥇 Bulk WARC Search

```bash
python examples/bulk_warc_search.py \
  --index CC-MAIN-2025-47 \
  --max-files 1000 \
  --samples 20 \
  --workers 10
```

**Neden?**
- En fazla coverage
- En hızlı
- Binlerce site bulabilirsin

---

### Senaryo 2: Belirli Niche Arama
**Amaç:** Örneğin sadece `.io` domainlerinde Next.js ara

**Önerilen Yöntem:** 🥈 CDX Targeted Search

```bash
python main.py \
  --pattern "*.io/" \
  --limit 5000 \
  --match-type prefix \
  --workers 10
```

**Neden?**
- Pattern-based filtering
- Targeted ve verimli
- Kesin sonuçlar

---

### Senaryo 3: Doğrulama
**Amaç:** Bilinen 50 domain'in Next.js kullanıp kullanmadığını kontrol et

**Önerilen Yöntem:** 🥉 Domain List Check

```bash
python main.py --domains-file my_domains.txt
```

**Neden?**
- Küçük scope için ideal
- Spesifik ve hızlı
- Her domain garanti kontrol edilir

---

### Senaryo 4: Research Paper
**Amaç:** "Common Crawl'da kaç Next.js sitesi var?" araştırması

**Önerilen Strateji:** Hibrit yaklaşım

```bash
# 1. Geniş sampling ile overview (1 gün)
python examples/bulk_warc_search.py --max-files 5000

# 2. Bulunan domainleri detaylı analiz et
python examples/specific_domains.py

# 3. Belirli pattern'lerde deep dive
python main.py --pattern "*.com/" --limit 50000
```

---

## Teknik Detaylar

### HTTP Range Request Kullanımı

Tüm 3 yöntem de HTTP Range kullanır:

```python
# WARC dosyası 1GB olabilir ama:
# Sadece 10KB'lık bir URL kaydını indir
Range: bytes=123456-133456

# Sonuç: %99.99 daha az veri transferi
```

### Rate Limiting

| Yöntem | API | Rate Limit | Etki |
|--------|-----|------------|------|
| Bulk WARC | S3 Direct | Yok | ✅ Sınırsız |
| CDX Targeted | CDX API | 5-10/s | ⚠️ Dikkat |
| Domain List | CDX API | 5-10/s | ⚠️ Yavaş |

### Paralel İşlem

```bash
# Bulk WARC: Her worker bir WARC alır
--workers 10  # 10 WARC aynı anda

# CDX: Her worker bir URL işler
--workers 5   # 5 URL aynı anda (rate limit nedeniyle az)
```

---

## Best Practices

### 1. Önce Küçük Test Et

```bash
# Bulk WARC mini test
python examples/bulk_warc_search.py --max-files 5 --samples 5

# CDX mini test
python main.py --pattern "vercel.com" --limit 10
```

### 2. Rate Limiting'e Dikkat Et

```bash
# Agresif olma
--rate-limit 2.0

# Adaptive kullan
from src.utils import AdaptiveRateLimiter
```

### 3. İlerlemeyi Takip Et

```bash
# Logları izle
tail -f logs/crawler_*.log

# Çıktıları kontrol et
watch -n 5 "ls -lh data/output/"
```

### 4. Sonuçları Combine Et

```bash
# Birden fazla run'ı birleştir
cat data/output/*.json | jq -s 'add | unique_by(.domain)' > combined.json
```

---

## Sonuç

**Genel Kullanım İçin En İyi:** 🥇 Bulk WARC Search
**Targeted Search İçin:** 🥈 CDX API
**Küçük Kontroller İçin:** 🥉 Domain List

**Profesyonel İpucu:** Bulk WARC ile başla, sonra ilginç pattern'leri CDX ile deep dive et!
