# Ubuntu Sunucuya Kurulum Talimatları

Ubuntu sistemler için optimize edilmiş kurulum rehberi. Virtual environment kullanmadan direkt sistem Python'u ile çalışır.

## Gereksinimler

- Ubuntu 20.04 veya üzeri
- Python 3.8+
- Root veya sudo yetkisi
- Çalışan VPN proxy'ler (Docker container'lar)
- Minimum 2GB RAM
- Minimum 10GB disk alanı

## 1. Sunucuya Bağlanma

```bash
ssh kullanici@sunucu-ip
```

## 2. Sistem Güncellemesi ve Paketlerin Yüklenmesi

```bash
# Sistem paketlerini güncelle
sudo apt update
sudo apt upgrade -y

# Python ve gerekli paketleri yükle
sudo apt install -y python3 python3-pip git curl wget

# Ek Python kütüphaneleri
sudo apt install -y python3-requests python3-urllib3
```

## 3. Projeyi İndirme

```bash
# Ana dizine git
cd ~

# Projeyi klonla
git clone https://github.com/ilkmuratkr/Crawler.git

# Proje dizinine gir
cd Crawler
```

## 4. Bağımlılıkları Yükleme

**ÖNEMLİ:** Ubuntu 23.04+ ve Python 3.11+ sürümlerinde sistem Python'u korumalıdır (PEP 668).

### Çözüm 1: APT ile Yükleme (Önerilen)
```bash
# Ubuntu paket depolarından mevcut paketleri yükle
sudo apt install -y python3-requests python3-urllib3 python3-tqdm

# Pip gerekiyorsa --break-system-packages ile
sudo pip3 install --break-system-packages warcio tenacity
```

### Çözüm 2: Break System Packages (Hızlı)
```bash
# Tüm bağımlılıkları zorla yükle
sudo pip3 install --break-system-packages -r requirements.txt
```

### Çözüm 3: Virtual Environment (En Güvenli)
```bash
# Python venv paketini yükle
sudo apt install -y python3-venv

# Virtual environment oluştur
python3 -m venv venv

# Aktif et
source venv/bin/activate

# Bağımlılıkları yükle (sudo YOK!)
pip install -r requirements.txt
```

**Not:** Çözüm 2 veya 3'ü kullanmanızı öneriyorum. Çözüm 3 en güvenli yöntemdir.

## 5. Yapılandırma

### 5.1. Config Dosyası Oluşturma

```bash
# Örnek config'i kopyala
cp config.example.py config.py

# Config'i düzenle
nano config.py
```

### 5.2. Proxy Ayarları

`config.py` dosyasında proxy ayarlarını yapın:

```python
ENABLE_PROXY = True
PROXY_HOST = "localhost"  # veya Docker host IP'si

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

### 5.3. Worker ve Rate Limit Ayarları

```python
# Paralel işlem sayısı (proxy sayınıza göre ayarlayın)
MAX_WORKERS = 15

# Rate limiting (proxy kullanıyorsanız artırabilirsiniz)
REQUESTS_PER_SECOND = 5.0

# Retry ayarları
MAX_RETRIES = 5
RETRY_DELAY = 300  # 5 dakika (saniye cinsinden)
```

### 5.4. Config dosyasını kaydetme
```bash
# Ctrl+O ile kaydet, Enter, Ctrl+X ile çık
```

## 6. Dizin Yapısını Oluşturma

```bash
# Gerekli dizinleri oluştur
mkdir -p data/output
mkdir -p data/failures
mkdir -p logs

# İzinleri ayarla
chmod 755 data
chmod 755 logs
```

## 7. WARC Paths Dosyası Hazırlama

### Mevcut warc.paths.gz'yi açma:
```bash
# warc.paths.gz dosyasını aç
gunzip -k warc.paths.gz

# Dosyayı kontrol et
head -5 warc.paths
wc -l warc.paths
```

### Veya yeni WARC listesi oluşturma:
```bash
# Kendi WARC listenizi oluşturabilirsiniz
# Örnek: warc.paths dosyasını elle oluşturun
nano warc.paths
```

## 8. Test Çalıştırması

### Küçük bir test (3 WARC, proxy ile):
```bash
python3 process_warcs.py --enable-proxy --workers 3 --limit 3 --log-level DEBUG
```

### Proxy olmadan test:
```bash
python3 process_warcs.py --workers 3 --limit 3
```

### Test sonuçlarını kontrol etme:
```bash
# Output klasörünü kontrol et
ls -lh data/output/

# JSON sonuçlarına bak
cat data/output/*.json | head -20
```

## 9. Production Çalıştırması

### Screen ile arka planda çalıştırma:

```bash
# Screen yükle (yoksa)
sudo apt install -y screen

# Screen oturumu başlat
screen -S crawler

# Projeye git
cd ~/Crawler

# EĞER VENV KULLANIYORSANIZ:
source venv/bin/activate

# Büyük scale'de çalıştır
python3 process_warcs.py \
  --enable-proxy \
  --workers 15 \
  --limit 10000 \
  --sample-size 10 \
  --rate-limit 5.0 \
  --max-retries 5 \
  --retry-delay 300 \
  --log-level INFO

# Screen'den çık (CTRL+A, sonra D)
# Programın çalışmaya devam etmesi için Ctrl+A D ile detach edin
```

### Screen oturumuna tekrar bağlanma:
```bash
# Aktif screen oturumlarını listele
screen -ls

# crawler oturumuna bağlan
screen -r crawler

# Birden fazla varsa:
screen -r [screen-id]
```

### Screen oturumunu sonlandırma:
```bash
# Screen içindeyken
exit
# veya
Ctrl+D
```

## 10. Systemd Service ile Otomatik Başlatma

### Service dosyası oluşturma:

```bash
# Service dosyası oluştur
sudo nano /etc/systemd/system/crawler.service
```

**VENV KULLANMIYORSANIZ:**
```ini
[Unit]
Description=Common Crawl WARC Crawler with Proxy Rotation
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/Crawler
ExecStart=/usr/bin/python3 /home/ubuntu/Crawler/process_warcs.py --enable-proxy --workers 15 --limit 10000 --log-level INFO
Restart=on-failure
RestartSec=60
StandardOutput=append:/home/ubuntu/Crawler/logs/service.log
StandardError=append:/home/ubuntu/Crawler/logs/service_error.log

[Install]
WantedBy=multi-user.target
```

**VENV KULLANIYORSANIZ:**
```ini
[Unit]
Description=Common Crawl WARC Crawler with Proxy Rotation
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/Crawler
ExecStart=/home/ubuntu/Crawler/venv/bin/python /home/ubuntu/Crawler/process_warcs.py --enable-proxy --workers 15 --limit 10000 --log-level INFO
Restart=on-failure
RestartSec=60
StandardOutput=append:/home/ubuntu/Crawler/logs/service.log
StandardError=append:/home/ubuntu/Crawler/logs/service_error.log

[Install]
WantedBy=multi-user.target
```

**Not:** `User=ubuntu` ve `/home/ubuntu/` kısımlarını kendi kullanıcı adınızla değiştirin.

### Service'i etkinleştirme:
```bash
# systemd'yi yeniden yükle
sudo systemctl daemon-reload

# Service'i başlat
sudo systemctl start crawler

# Durumu kontrol et
sudo systemctl status crawler

# Otomatik başlatmayı etkinleştir (sunucu açılışında)
sudo systemctl enable crawler
```

### Service komutları:
```bash
# Durdurmak için
sudo systemctl stop crawler

# Yeniden başlatmak için
sudo systemctl restart crawler

# Logları görmek için
sudo journalctl -u crawler -f

# Son 100 satır
sudo journalctl -u crawler -n 100
```

## 11. Monitoring ve Loglar

### Log dosyalarını izleme:
```bash
# Real-time log izleme
tail -f logs/crawler.log

# Son 100 satır
tail -n 100 logs/crawler.log

# Error logları
grep ERROR logs/crawler.log

# Belirli bir kelimeyi arama
grep "Next.js" logs/crawler.log
```

### System resource monitoring:
```bash
# htop yükle (yoksa)
sudo apt install -y htop

# Resource kullanımı
htop

# Specific process
ps aux | grep process_warcs

# Memory kullanımı
free -h

# Disk kullanımı
df -h

# Network kullanımı (opsiyonel)
sudo apt install -y iftop
sudo iftop
```

## 12. Sonuçları İndirme

### SCP ile (yerel makinenizden):
```bash
# JSON dosyalarını indir
scp ubuntu@sunucu-ip:~/Crawler/data/output/*.json ./

# CSV dosyalarını indir
scp ubuntu@sunucu-ip:~/Crawler/data/output/*.csv ./

# Tüm output klasörünü indir
scp -r ubuntu@sunucu-ip:~/Crawler/data/output/ ./crawler-output/
```

### rsync ile (daha hızlı, devam ettirebilir):
```bash
# Tüm output klasörünü senkronize et
rsync -avz --progress ubuntu@sunucu-ip:~/Crawler/data/output/ ./crawler-output/

# Sadece yeni dosyaları al
rsync -avz --update ubuntu@sunucu-ip:~/Crawler/data/output/ ./crawler-output/
```

## 13. Güncelleme

### Projeyi güncelleme:
```bash
cd ~/Crawler

# Değişiklikleri çek
git pull origin main

# Bağımlılıkları güncelle
sudo pip3 install -r requirements.txt --upgrade

# Service'i yeniden başlat (eğer kullanıyorsanız)
sudo systemctl restart crawler
```

## 14. Temizlik ve Maintenance

### Eski logları temizleme:
```bash
# 7 günden eski logları sil
find logs/ -name "*.log" -mtime +7 -delete

# Log dosyalarını sıkıştır
gzip logs/*.log
```

### Output dosyalarını arşivleme:
```bash
# Backup dizini oluştur
mkdir -p ~/backups

# Output'ları arşivle
tar -czf ~/backups/crawler_output_$(date +%Y%m%d).tar.gz data/output/

# Eski output'ları temizle
rm -rf data/output/*
```

### Disk temizliği:
```bash
# Cache temizle (eğer varsa)
rm -rf data/cache/*

# APT cache temizle
sudo apt clean
sudo apt autoclean
```

## 15. Sorun Giderme

### Proxy bağlantı problemi:
```bash
# Proxy'leri test et
curl --proxy http://localhost:8956 https://data.commoncrawl.org/

# Proxy yanıt veriyor mu?
nc -zv localhost 8956

# Docker container'ları kontrol et
docker ps | grep alpine-vpn

# Tüm container'ları kontrol et
docker ps -a
```

### "Module not found" hatası:
```bash
# Eksik modülü yükle
sudo pip3 install [module-name]

# Tüm bağımlılıkları yeniden yükle
sudo pip3 install -r requirements.txt --force-reinstall
```

### Permission denied hatası:
```bash
# Dizin izinlerini düzelt
chmod -R 755 ~/Crawler
chown -R $USER:$USER ~/Crawler
```

### Memory problemi:
```bash
# Worker sayısını azalt
python3 process_warcs.py --workers 5 --limit 1000

# Sample size'ı küçült
python3 process_warcs.py --sample-size 5 --limit 1000

# Swap alanı ekle (eğer yoksa)
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### Disk doldu:
```bash
# Disk kullanımını kontrol et
df -h

# Büyük dosyaları bul
du -sh ~/Crawler/* | sort -h

# ncdu ile interaktif analiz (opsiyonel)
sudo apt install -y ncdu
ncdu ~/Crawler
```

## 16. Performans Optimizasyonu

### Optimal ayarlar (15 proxy için):
```bash
python3 process_warcs.py \
  --enable-proxy \
  --workers 15 \
  --rate-limit 10.0 \
  --sample-size 10 \
  --max-retries 3 \
  --retry-delay 60 \
  --limit 50000
```

### System limits artırma:
```bash
# Açık dosya limiti
sudo nano /etc/security/limits.conf

# Dosyanın sonuna ekle:
* soft nofile 65535
* hard nofile 65535

# Yeniden giriş yap veya:
ulimit -n 65535
```

### Network optimizasyonu:
```bash
# TCP ayarları (opsiyonel)
sudo nano /etc/sysctl.conf

# Ekle:
net.core.rmem_max = 134217728
net.core.wmem_max = 134217728
net.ipv4.tcp_rmem = 4096 87380 67108864
net.ipv4.tcp_wmem = 4096 65536 67108864

# Uygula
sudo sysctl -p
```

## 17. Güvenlik

### Config dosyasını koruma:
```bash
# Config dosyasına sadece owner erişebilir
chmod 600 config.py

# Root'un bile okumasını engelle (opsiyonel)
sudo chattr +i config.py  # immutable yap
# Geri almak için: sudo chattr -i config.py
```

### Firewall ayarları:
```bash
# UFW yükle ve aktif et
sudo apt install -y ufw

# SSH portunu aç (kendinizi kilitlemeden önce!)
sudo ufw allow 22/tcp

# Firewall'u aktif et
sudo ufw enable

# Durumu kontrol et
sudo ufw status
```

### Fail2ban kurulumu (SSH koruması):
```bash
sudo apt install -y fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

## 18. Hızlı Komut Özeti

### Yöntem 1: Break System Packages (En Hızlı)
```bash
# ===== KURULUM =====
sudo apt update && sudo apt install -y python3 python3-pip git
git clone https://github.com/ilkmuratkr/Crawler.git
cd Crawler
sudo pip3 install --break-system-packages -r requirements.txt
cp config.example.py config.py
nano config.py  # Proxy'leri düzenle
mkdir -p data/output data/failures logs

# ===== TEST =====
python3 process_warcs.py --enable-proxy --workers 3 --limit 5

# ===== PRODUCTION (Screen ile) =====
screen -S crawler
python3 process_warcs.py --enable-proxy --workers 15 --limit 10000
# Ctrl+A, sonra D (detach)
```

### Yöntem 2: Virtual Environment (Önerilen)
```bash
# ===== KURULUM =====
sudo apt update && sudo apt install -y python3 python3-pip python3-venv git
git clone https://github.com/ilkmuratkr/Crawler.git
cd Crawler
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp config.example.py config.py
nano config.py  # Proxy'leri düzenle
mkdir -p data/output data/failures logs

# ===== TEST =====
python3 process_warcs.py --enable-proxy --workers 3 --limit 5

# ===== PRODUCTION (Screen ile) =====
screen -S crawler
source venv/bin/activate
python3 process_warcs.py --enable-proxy --workers 15 --limit 10000
# Ctrl+A, sonra D (detach)
```

### Ortak Komutlar
```bash
# ===== MONİTORİNG =====
screen -r crawler  # Screen'e dön
tail -f logs/crawler.log  # Logları izle
htop  # Resource kullanımı

# ===== SONUÇLARI İNDİR (yerel makineden) =====
scp -r ubuntu@sunucu-ip:~/Crawler/data/output/ ./

# ===== GÜNCELLEME =====
cd ~/Crawler && git pull
# Venv ile: source venv/bin/activate && pip install -r requirements.txt --upgrade
# Venv olmadan: sudo pip3 install --break-system-packages -r requirements.txt --upgrade
```

## Faydalı Alias'lar

`~/.bashrc` dosyasına ekleyin:

```bash
# Crawler alias'ları
alias crawler-start='cd ~/Crawler && screen -S crawler'
alias crawler-attach='screen -r crawler'
alias crawler-log='tail -f ~/Crawler/logs/crawler.log'
alias crawler-status='ps aux | grep process_warcs'
alias crawler-update='cd ~/Crawler && git pull && sudo pip3 install -r requirements.txt --upgrade'

# Sonra:
source ~/.bashrc
```

## Destek ve Yardım

- **GitHub:** https://github.com/ilkmuratkr/Crawler
- **Issues:** https://github.com/ilkmuratkr/Crawler/issues
- **Dokümantasyon:** README.md, PROXY_SETUP.md

## Notlar

- Virtual environment kullanmıyoruz, sistem Python'unu kullanıyoruz
- `sudo pip3` ile global olarak yüklüyoruz
- Screen veya systemd ile arka planda çalıştırıyoruz
- 15 proxy ile optimal performans için 15 worker kullanın
- Logları düzenli kontrol edin
- Disk alanını düzenli temizleyin
