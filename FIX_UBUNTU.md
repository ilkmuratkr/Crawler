# Ubuntu'da Hızlı Fix

## Sorun 1: config.py bulunamıyor

```bash
# Önce kontrol et
ls -la config.py

# Yoksa oluştur
cp config.example.py config.py

# İçeriğini kontrol et
cat config.py | grep PROXY_CONFIGS

# Eğer boşsa veya hatalıysa, direkt düzenle:
nano config.py
```

`config.py` içine şunu ekle/değiştir:

```python
# Proxy Settings
ENABLE_PROXY = True
PROXY_HOST = "localhost"

PROXY_CONFIGS = [
    {"name": "alpine-vpn-3973", "port": 8956, "vpn_ip": "223.165.69.73"},
    {"name": "alpine-vpn-2547", "port": 8955, "vpn_ip": "68.235.38.19"},
    {"name": "alpine-vpn-5853", "port": 8954, "vpn_ip": "134.19.179.50"},
    {"name": "alpine-vpn-6480", "port": 8953, "vpn_ip": "146.70.67.66"},
    {"name": "alpine-vpn-9166", "port": 8946, "vpn_ip": "68.235.36.19"},
    {"name": "alpine-vpn-4505", "port": 8944, "vpn_ip": "38.88.124.103"},
    {"name": "alpine-vpn-8629", "port": 8948, "vpn_ip": "213.152.161.107"},
    {"name": "alpine-vpn-5703", "port": 8943, "vpn_ip": "184.75.208.170"},
    {"name": "alpine-vpn-5374", "port": 8942, "vpn_ip": "184.75.208.247"},
    {"name": "alpine-vpn-110", "port": 8940, "vpn_ip": "104.254.90.122"},
    {"name": "alpine-vpn-864", "port": 8939, "vpn_ip": "146.70.126.247"},
    {"name": "alpine-vpn-8591", "port": 8929, "vpn_ip": "198.44.134.19"},
    {"name": "alpine-vpn-4203", "port": 8949, "vpn_ip": "213.152.162.116"},
    {"name": "alpine-vpn-4180", "port": 8945, "vpn_ip": "37.120.146.146"},
    {"name": "alpine-vpn-9223", "port": 8941, "vpn_ip": "37.120.233.74"},
]
```

## Sorun 2: warc.paths dosyası yok

```bash
# Kontrol et
ls -la warc.paths*

# warc.paths.gz varsa, aç:
gunzip -k warc.paths.gz

# Yeniden kontrol
ls -la warc.paths
head -5 warc.paths
```

Eğer `warc.paths.gz` de yoksa, test için küçük bir liste oluştur:

```bash
cat > warc.paths << 'EOF'
crawl-data/CC-MAIN-2024-51/segments/1733058656814.95/warc/CC-MAIN-20241205084821-20241205114821-00000.warc.gz
crawl-data/CC-MAIN-2024-51/segments/1733058656814.95/warc/CC-MAIN-20241205084821-20241205114821-00001.warc.gz
crawl-data/CC-MAIN-2024-51/segments/1733058656814.95/warc/CC-MAIN-20241205084821-20241205114821-00002.warc.gz
crawl-data/CC-MAIN-2024-51/segments/1733058656814.95/warc/CC-MAIN-20241205084821-20241205114821-00003.warc.gz
crawl-data/CC-MAIN-2024-51/segments/1733058656814.95/warc/CC-MAIN-20241205084821-20241205114821-00004.warc.gz
EOF
```

## Hızlı Test

```bash
# Küçük test (5 WARC)
python3 process_warcs.py --enable-proxy --workers 3 --limit 5
```

## Tek Komut Fix

```bash
cd ~/craw/Crawler
cp config.example.py config.py
gunzip -k warc.paths.gz 2>/dev/null || echo "warc.paths.gz bulunamadı, manuel oluştur"
ls -la warc.paths config.py
```

## Kontrol Listesi

```bash
# 1. Config var mı?
ls -la config.py
cat config.py | grep -A 3 PROXY_CONFIGS

# 2. warc.paths var mı?
ls -la warc.paths
wc -l warc.paths

# 3. Proxy'ler çalışıyor mu?
docker ps | grep alpine-vpn

# 4. Proxy test
curl --proxy http://localhost:8956 https://data.commoncrawl.org/ -I
```

## Şimdi Çalıştır

```bash
python3 process_warcs.py --enable-proxy --workers 3 --limit 5
```
