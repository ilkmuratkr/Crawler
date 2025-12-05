# Proxy Rotation Sistemi

Bu proje artık otomatik proxy rotation desteğine sahiptir. Her worker farklı bir proxy kullanır ve retry işlemlerinde proxy otomatik olarak değiştirilir.

## Özellikler

- **Worker Bazlı Proxy Atama**: Her worker thread'i farklı bir proxy kullanır
- **Round-Robin Rotation**: Proxy'ler sırayla worker'lara atanır
- **Retry'da Otomatik Proxy Değiştirme**: Bir indirme başarısız olduğunda, retry işlemi farklı bir IP ile yapılır
- **Thread-Safe**: Çoklu thread ortamında güvenli çalışır

## Kurulum

### 1. Proxy'leri Yapılandırma

`config.py` dosyasını düzenleyin:

```python
ENABLE_PROXY = True
PROXY_HOST = "localhost"  # Proxy sunucunuzun host'u

PROXY_CONFIGS = [
    {"name": "alpine-vpn-3973", "port": 8956, "vpn_ip": "223.165.69.73"},
    {"name": "alpine-vpn-2547", "port": 8955, "vpn_ip": "68.235.38.19"},
    # Daha fazla proxy ekleyin...
]
```

### 2. Kullanım

#### Proxy ile çalıştırma:

```bash
python process_warcs.py --enable-proxy --workers 5 --limit 10
```

#### Proxy olmadan çalıştırma:

```bash
python process_warcs.py --workers 5 --limit 10
```

#### Özel proxy host:

```bash
python process_warcs.py --enable-proxy --proxy-host "192.168.1.100" --workers 5
```

## Nasıl Çalışır?

### 1. Worker Proxy Ataması

Her worker thread başlatıldığında, ProxyManager otomatik olarak bir proxy atar:

```
Worker 1 -> Proxy 1 (223.165.69.73:8956)
Worker 2 -> Proxy 2 (68.235.38.19:8955)
Worker 3 -> Proxy 3 (134.19.179.50:8954)
...
```

### 2. Retry'da Proxy Değişimi

Bir indirme başarısız olursa, retry işleminde farklı bir proxy kullanılır:

```
Attempt 1: Proxy 1 (223.165.69.73) -> FAILED
Attempt 2: Proxy 2 (68.235.38.19) -> FAILED
Attempt 3: Proxy 3 (134.19.179.50) -> SUCCESS
```

### 3. Round-Robin Rotasyon

Proxy'ler sırayla kullanılır. Listedeki son proxy'ye ulaşıldığında, tekrar başa dönülür.

## Örnek Log Çıktıları

```
INFO - Proxy manager initialized with 15 proxies
INFO - Worker 140735212345600 using proxy: alpine-vpn-3973 (223.165.69.73)
DEBUG - Using proxy: 223.165.69.73:8956
WARNING - Error on attempt 1/5: Connection timeout
INFO - Switching proxy for retry 2: 223.165.69.73 -> 68.235.38.19
INFO - Success on attempt 2
```

## Proxy Sunucu Gereksinimleri

Proxy sunucularınız HTTP/HTTPS proxy protokolünü desteklemelidir:

- **HTTP Proxy**: Basit HTTP proxy
- **HTTPS Proxy**: SSL/TLS destekli proxy
- **SOCKS Proxy**: SOCKS4/5 (requests kütüphanesi SOCKS için ek paket gerektirir)

## Performans İpuçları

1. **Worker Sayısı = Proxy Sayısı**: En iyi performans için worker sayısını proxy sayısına eşit veya daha az tutun
2. **Retry Delay**: Proxy rotation kullanıyorsanız retry delay'i azaltabilirsiniz
3. **Rate Limiting**: Proxy kullanırken rate limit'i artırabilirsiniz (her IP farklı olduğu için)

## Sorun Giderme

### Proxy bağlantı hatası:

```
ConnectionError: Failed to establish connection through proxy
```

**Çözüm**: Proxy sunucularınızın çalıştığını ve erişilebilir olduğunu kontrol edin.

### Tüm proxy'ler aynı:

```
WARNING - Only one proxy available, reusing same proxy
```

**Çözüm**: `config.py` dosyasına daha fazla proxy ekleyin.

### Proxy kullanılmıyor:

**Çözüm**: `--enable-proxy` bayrağını eklemeyi unutmayın.

## Güvenlik Notları

- Proxy sunucularınızı güvenli tutun
- VPN/Proxy credentials'larını config dosyasına eklemeyin
- Proxy loglarını düzenli olarak kontrol edin
- Rate limit'lere dikkat edin (IP ban'dan kaçınmak için)
