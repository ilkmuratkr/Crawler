# Ubuntu Kurulum - Basit ve Direkt

Ubuntu için en basit kurulum. Virtual environment yok, direkt sistem Python'u.

## Hızlı Kurulum (5 Dakika)

```bash
# 1. Paketleri yükle
sudo apt update
sudo apt install -y python3 python3-pip git screen

# 2. Projeyi indir
cd ~
git clone https://github.com/ilkmuratkr/Crawler.git
cd Crawler

# 3. Python paketlerini yükle
sudo pip3 install --break-system-packages -r requirements.txt

# 4. Config oluştur
cp config.example.py config.py
nano config.py
# 15 proxy'yi düzenle ve kaydet (Ctrl+O, Enter, Ctrl+X)

# 5. Dizinleri oluştur
mkdir -p data/output data/failures logs

# 6. Test et
python3 process_warcs.py --enable-proxy --workers 3 --limit 5

# 7. Production'da çalıştır
screen -S crawler
python3 process_warcs.py --enable-proxy --workers 15 --limit 10000
# Ctrl+A sonra D (detach)
```

## Config.py Proxy Ayarları

`nano config.py` ile açın ve proxy'leri ekleyin:

```python
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

## Monitoring

```bash
# Screen'e geri dön
screen -r crawler

# Logları izle
tail -f logs/crawler.log

# Process durumu
ps aux | grep process_warcs

# Resource kullanımı
htop
```

## Sonuçları İndirme (Yerel Makineden)

```bash
scp -r root@sunucu-ip:~/Crawler/data/output/ ./
```

## Sorun Giderme

### Proxy test
```bash
curl --proxy http://localhost:8956 https://data.commoncrawl.org/
```

### Docker proxy'leri kontrol
```bash
docker ps | grep alpine-vpn
```

## Systemd Service (Otomatik Başlatma)

```bash
sudo nano /etc/systemd/system/crawler.service
```

İçerik:
```ini
[Unit]
Description=Crawler with Proxy
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/Crawler
ExecStart=/usr/bin/python3 /root/Crawler/process_warcs.py --enable-proxy --workers 15 --limit 10000
Restart=on-failure
RestartSec=60

[Install]
WantedBy=multi-user.target
```

Aktif et:
```bash
sudo systemctl daemon-reload
sudo systemctl enable crawler
sudo systemctl start crawler
sudo systemctl status crawler
```

## Tek Komut Kurulum

```bash
sudo apt update && sudo apt install -y python3 python3-pip git screen && cd ~ && git clone https://github.com/ilkmuratkr/Crawler.git && cd Crawler && sudo pip3 install --break-system-packages -r requirements.txt && cp config.example.py config.py && mkdir -p data/output data/failures logs && echo "✅ Kurulum tamam! Şimdi 'nano config.py' ile proxy'leri ekle"
```

## Özet

- ✅ Venv yok
- ✅ `--break-system-packages` kullan
- ✅ Direkt python3 ile çalıştır
- ✅ Screen ile arka planda tut
- ✅ 15 proxy = 15 worker

Hepsi bu kadar!
