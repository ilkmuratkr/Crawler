# Sunucuya Kurulum Talimatları

Bu rehber, projeyi GitHub'dan sunucunuza kurma adımlarını içerir.

## Gereksinimler

- Python 3.8+
- Git
- Çalışan VPN proxy'ler (Docker container'lar)
- Minimum 2GB RAM
- Minimum 10GB disk alanı

## 1. Sunucuya Bağlanma

```bash
ssh kullanici@sunucu-ip
```

## 2. Gerekli Paketleri Yükleme

### Ubuntu/Debian:
```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv git

# Eğer python3-venv yüklü değilse veya hata alırsanız:
sudo apt install -y python3.10-venv  # veya python3.11-venv, python sürümünüze göre
```

### CentOS/RHEL:
```bash
sudo yum install -y python3 python3-pip git

# RHEL/CentOS 8+:
sudo dnf install -y python3 python3-pip git
```

**Not:** Ubuntu'da `python3 -m venv` komutu çalışmazsa `python3-venv` paketini yüklemeniz gerekir.

## 3. Projeyi İndirme

```bash
# Ana dizine git
cd ~

# Projeyi klonla
git clone https://github.com/ilkmuratkr/Crawler.git

# Proje dizinine gir
cd Crawler
```

## 4. Python Virtual Environment Oluşturma

```bash
# Virtual environment oluştur
python3 -m venv venv

# Eğer "No module named venv" hatası alırsanız:
# Ubuntu/Debian:
sudo apt install -y python3-venv
# veya Python sürümünüze özel:
sudo apt install -y python3.10-venv

# Virtual environment'ı aktif et
source venv/bin/activate

# pip'i güncelle
pip install --upgrade pip
```

**Alternatif:** virtualenv kullanmak isterseniz:
```bash
sudo apt install -y python3-virtualenv
virtualenv venv
source venv/bin/activate
```

## 5. Bağımlılıkları Yükleme

```bash
pip install -r requirements.txt
```

## 6. Yapılandırma

### 6.1. Config Dosyası Oluşturma

```bash
# Örnek config'i kopyala
cp config.example.py config.py

# Config'i düzenle
nano config.py
```

### 6.2. Proxy Ayarları

`config.py` dosyasında proxy ayarlarını yapın:

```python
ENABLE_PROXY = True
PROXY_HOST = "localhost"  # veya Docker host IP'si

PROXY_CONFIGS = [
    {"name": "alpine-vpn-3973", "port": 8956, "vpn_ip": "223.165.69.73"},
    {"name": "alpine-vpn-2547", "port": 8955, "vpn_ip": "68.235.38.19"},
    # Proxy'lerinizi buraya ekleyin...
]
```

### 6.3. Worker ve Rate Limit Ayarları

```python
# Paralel işlem sayısı
MAX_WORKERS = 10  # Proxy sayınıza göre ayarlayın

# Rate limiting (proxy kullanıyorsanız artırabilirsiniz)
REQUESTS_PER_SECOND = 5.0

# Retry ayarları
MAX_RETRIES = 5
RETRY_DELAY = 300  # 5 dakika
```

## 7. Dizin Yapısını Oluşturma

```bash
# Gerekli dizinleri oluştur
mkdir -p data/output
mkdir -p data/failures
mkdir -p logs
```

## 8. WARC Paths Dosyası

### Seçenek 1: Mevcut warc.paths.gz kullanma
```bash
# Eğer warc.paths.gz varsa
gunzip -k warc.paths.gz
```

### Seçenek 2: Yeni WARC listesi oluşturma
```bash
# CDX API'den WARC listesi çek (örnek)
curl "https://index.commoncrawl.org/CC-MAIN-2025-47-index?url=*.com&output=json" | \
  jq -r '.filename' | sort -u > warc.paths
```

## 9. Test Çalıştırması

### Küçük bir test:
```bash
# 5 WARC ile test (proxy ile)
python process_warcs.py --enable-proxy --workers 3 --limit 5 --log-level DEBUG
```

### Proxy olmadan test:
```bash
python process_warcs.py --workers 3 --limit 5
```

## 10. Production Çalıştırması

### Screen veya tmux ile arka planda çalıştırma:

```bash
# Screen oturumu başlat
screen -S crawler

# Virtual environment'ı aktif et
cd ~/Crawler
source venv/bin/activate

# Büyük scale'de çalıştır
python process_warcs.py \
  --enable-proxy \
  --workers 15 \
  --limit 10000 \
  --sample-size 10 \
  --rate-limit 5.0 \
  --max-retries 5 \
  --retry-delay 300 \
  --log-level INFO

# Screen'den çık (CTRL+A, sonra D)
```

### Screen oturumuna tekrar bağlanma:
```bash
screen -r crawler
```

## 11. Systemd Service Oluşturma (Opsiyonel)

Otomatik başlatma için systemd service:

```bash
sudo nano /etc/systemd/system/crawler.service
```

İçeriği:
```ini
[Unit]
Description=Common Crawl WARC Crawler
After=network.target

[Service]
Type=simple
User=kullanici_adiniz
WorkingDirectory=/home/kullanici_adiniz/Crawler
Environment="PATH=/home/kullanici_adiniz/Crawler/venv/bin"
ExecStart=/home/kullanici_adiniz/Crawler/venv/bin/python process_warcs.py --enable-proxy --workers 15 --limit 10000
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Service'i etkinleştirme:
```bash
sudo systemctl daemon-reload
sudo systemctl enable crawler
sudo systemctl start crawler
sudo systemctl status crawler
```

## 12. Monitoring ve Loglar

### Logları izleme:
```bash
# Real-time log izleme
tail -f logs/crawler.log

# Son 100 satır
tail -n 100 logs/crawler.log

# Error logları
grep ERROR logs/crawler.log
```

### Process izleme:
```bash
# CPU/Memory kullanımı
htop

# Specific process
ps aux | grep process_warcs
```

## 13. Sonuçları İndirme

### SCP ile:
```bash
# Yerel makinenizden
scp kullanici@sunucu-ip:~/Crawler/data/output/*.json ./
scp kullanici@sunucu-ip:~/Crawler/data/output/*.csv ./
```

### rsync ile:
```bash
# Yerel makinenizden (tüm output klasörü)
rsync -avz kullanici@sunucu-ip:~/Crawler/data/output/ ./output/
```

## 14. Güncelleme ve Maintenance

### Projeyi güncelleme:
```bash
cd ~/Crawler
git pull origin main

# Virtual environment'ı aktif et
source venv/bin/activate

# Bağımlılıkları güncelle
pip install -r requirements.txt --upgrade
```

### Eski logları temizleme:
```bash
# 7 günden eski logları sil
find logs/ -name "*.log" -mtime +7 -delete

# Eski output dosyalarını arşivle
tar -czf output_backup_$(date +%Y%m%d).tar.gz data/output/
mv output_backup_*.tar.gz ~/backups/
```

## 15. Sorun Giderme

### Proxy bağlantı problemi:
```bash
# Proxy'leri test et
curl --proxy http://localhost:8956 https://data.commoncrawl.org/

# Docker container'ları kontrol et
docker ps | grep alpine-vpn
```

### Memory problemi:
```bash
# Worker sayısını azalt
python process_warcs.py --workers 5 ...

# Sample size'ı küçült
python process_warcs.py --sample-size 5 ...
```

### Disk doldu:
```bash
# Disk kullanımını kontrol et
df -h

# Büyük dosyaları bul
du -sh data/* logs/*

# Cache temizle
rm -rf data/cache/*
```

## 16. Performans Optimizasyonu

### Optimal ayarlar:
```bash
# Proxy sayınız kadar worker
# 15 proxy varsa -> 15 worker

python process_warcs.py \
  --enable-proxy \
  --workers 15 \
  --rate-limit 10.0 \
  --sample-size 10 \
  --max-retries 3 \
  --retry-delay 60
```

### Resource limits (opsiyonel):
```bash
# ulimit ile limit koyma
ulimit -n 65535  # Açık dosya sayısı
ulimit -u 4096   # Process sayısı
```

## 17. Güvenlik

```bash
# Config dosyasını koruma (proxy bilgileri için)
chmod 600 config.py

# Log dosyalarına erişim kontrolü
chmod 600 logs/*.log

# Firewall ayarları (sadece gerekli portlar)
sudo ufw allow 22/tcp  # SSH
sudo ufw enable
```

## 18. Backup Stratejisi

```bash
# Günlük backup scripti
#!/bin/bash
BACKUP_DIR=~/backups/$(date +%Y%m%d)
mkdir -p $BACKUP_DIR

# Sonuçları yedekle
cp -r ~/Crawler/data/output $BACKUP_DIR/
cp -r ~/Crawler/data/failures $BACKUP_DIR/
cp ~/Crawler/config.py $BACKUP_DIR/

# Eski backupları sil (30 günden eski)
find ~/backups/ -mtime +30 -delete
```

## Özet Komutlar

```bash
# Hızlı kurulum
git clone https://github.com/ilkmuratkr/Crawler.git
cd Crawler
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp config.example.py config.py
# config.py'yi düzenle
mkdir -p data/output data/failures logs

# Çalıştırma
screen -S crawler
source venv/bin/activate
python process_warcs.py --enable-proxy --workers 15 --limit 10000

# Monitoring
tail -f logs/crawler.log
screen -r crawler
```

## Destek ve Sorunlar

Sorun yaşarsanız:
1. Logları kontrol edin: `tail -f logs/crawler.log`
2. Debug mode ile çalıştırın: `--log-level DEBUG`
3. GitHub Issues: https://github.com/ilkmuratkr/Crawler/issues
