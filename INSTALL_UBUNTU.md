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

# 4. Config oluştur (proxy'ler zaten içinde!)
cp config.example.py config.py
# Eğer proxy portlarınız farklıysa: nano config.py

# 5. Dizinleri oluştur
mkdir -p data/output data/failures logs

# 6. Test et
python3 process_warcs.py --enable-proxy --workers 3 --limit 5

# 7. Production'da çalıştır
screen -S crawler
python3 process_warcs.py --enable-proxy --workers 15 --limit 10000
# Ctrl+A sonra D (detach)
```

## Config.py - Proxy'ler ZATEN HAZIR!

Config dosyasını kopyaladıktan sonra **proxy'ler zaten içinde!** Sadece kontrol et:

```bash
cat config.py | grep -A 20 PROXY_CONFIGS
```

15 proxy otomatik gelir:
- alpine-vpn-3973 → 223.165.69.73:8956
- alpine-vpn-2547 → 68.235.38.19:8955
- alpine-vpn-5853 → 134.19.179.50:8954
- alpine-vpn-6480 → 146.70.67.66:8953
- alpine-vpn-9166 → 68.235.36.19:8946
- alpine-vpn-4505 → 38.88.124.103:8944
- alpine-vpn-8629 → 213.152.161.107:8948
- alpine-vpn-5703 → 184.75.208.170:8943
- alpine-vpn-5374 → 184.75.208.247:8942
- alpine-vpn-110 → 104.254.90.122:8940
- alpine-vpn-864 → 146.70.126.247:8939
- alpine-vpn-8591 → 198.44.134.19:8929
- alpine-vpn-4203 → 213.152.162.116:8949
- alpine-vpn-4180 → 37.120.146.146:8945
- alpine-vpn-9223 → 37.120.233.74:8941

**Eğer proxy portları farklıysa:**
```bash
nano config.py
# PROXY_CONFIGS kısmını düzenle
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
