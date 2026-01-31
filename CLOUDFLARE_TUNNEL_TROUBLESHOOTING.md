# Cloudflare Tunnel Sorun Giderme Raporu

**Tarih:** 31 Ocak 2026  
**Durum:** ✅ Çözüldü

## Özet

AI-01 ve AI-02 sunucuları için Cloudflare Tunnel yapılandırması sırasında yaşanan problemler ve çözümleri.

---

## Başlangıç Durumu

### Mevcut Tunnel'lar
- **ai01-tunnel** (e0a805dd-eb9b-4fe3-9723-24865bfbebaa): ✅ Çalışıyor
- **test_linux_01**: AI-02 erişimi sağlıyordu
- **labtunnel1**: ✅ Aktif
- **nyc_311**: ✅ Aktif
- 6 adet kullanılmayan tunnel

### Hedef
Kullanılmayan tunnel'ları temizleyerek sadece ai01, ai02, labtunnel1 ve nyc_311 tunnel'larını aktif tutmak.

---

## Yaşanan Problemler

### 1. Problem: AI-02 Tunnel'ının Yanlışlıkla Silinmesi

**Durum:**
- Kullanılmayan tunnel'ları silerken `test_linux_01` tunnel'ı da silindi
- AI-02'ye erişim kesildi
- `test_linux_01` tunnel'ının AI-02 erişimini sağladığı sonradan fark edildi

**Silinen Tunnel'lar:**
```
- my-server-tunnel
- server-tunnel  
- test-ai-01-tunnel
- test_linux_01  ❌ (AI-02 için kullanılıyordu)
- test_vs
- test_win_01
- win-local-tunnel
```

**Etki:** AI-02 sunucusuna Cloudflare üzerinden erişim tamamen kesildi.

---

### 2. Problem: Yeni ai02-tunnel Oluşturuldu Ama Erişim Sağlanamadı

**Yapılan:**
```bash
cloudflared tunnel create ai02-tunnel
# Tunnel ID: 1dd07d57-42b1-4ada-8d72-1584cbcfa5a3
```

**Sorun:**
- AI-02 fiziksel sunucusu 192.168.1.179 IP adresinde
- AI-01'den AI-02'ye SSH erişimi yok
- AI-02'de tunnel çalıştırmak için erişim gerekli

---

### 3. Problem: AI-01'den AI-02'ye SSH Bağlantısı Başarısız

**Denenen Yöntemler:**

#### Şifre ile Bağlantı Denemeleri:
```bash
ssh test@192.168.1.179
# Permission denied (publickey,password)
```

**Sorun:** AI-02'de PasswordAuthentication devre dışı veya şifre farklı

#### SSH Key ile Bağlantı Denemeleri:
```bash
# AI-01'de key oluşturuldu
ssh-keygen -t rsa
# Ancak AI-02'ye kopyalanamadı (SSH erişimi yok)
```

**Sorun:** AI-02'ye key kopyalamak için zaten SSH erişimi gerekiyordu (chicken-egg problem)

---

### 4. Problem: AI-01'den Relay ile AI-02'ye Tunnel Denemesi

**Yaklaşım:** AI-01'de tunnel çalıştırıp AI-02'ye forward etme

#### Deneme 1: SSH Port Forward
```bash
ssh -N -L 2222:192.168.1.179:22 test@192.168.1.179
# Başarısız: SSH erişimi yok
```

#### Deneme 2: Socat TCP Relay
```bash
# AI-01'de:
socat TCP-LISTEN:2222,fork,reuseaddr TCP:192.168.1.179:22

# Config:
ingress:
  - hostname: ssh-ai02.spacenets.org
    service: ssh://localhost:2222  # veya tcp://localhost:2222
```

**Sonuç:**
- ✅ Socat başarıyla çalıştı
- ✅ Port 2222 açık ve AI-02:22'ye forward ediyor
- ✅ Telnet ile bağlantı OK: `SSH-2.0-OpenSSH_9.6p1`
- ❌ SSH authentication başarısız: `Permission denied (publickey,password)`
- ❌ Cloudflare tunnel SSH proxy: `FATAL ERROR: Remote side unexpectedly closed network connection`

**Kök Neden:** Relay çalışıyor ancak AI-02'nin SSH authentication konfigürasyonu şifre/key kabul etmiyor.

---

### 5. Problem: Cloudflare Tunnel Protocol Uyumsuzluğu

**Denenen Protokoller:**

```yaml
# Deneme 1: ssh://
service: ssh://192.168.1.179:22
# Sonuç: Tunnel başladı ama SSH handshake başarısız

# Deneme 2: tcp://  
service: tcp://192.168.1.179:22
# Sonuç: Cloudflare Access TCP "websocket: bad handshake"

# Deneme 3: ssh:// + localhost relay
service: ssh://localhost:2222
# Sonuç: Relay OK ama authentication başarısız
```

---

## Çözüm

### Başarılı Yaklaşım: AI-02'de Doğrudan Tunnel Çalıştırma

**Keşif:**
```bash
# Windows'tan AI-02'ye direkt SSH:
plink -batch -pw test test@192.168.1.179 "hostname"
# ✅ Başarılı! test-ai-02
```

**Bulgu:** Windows'tan AI-02'ye direkt SSH erişimi vardı, AI-01'den yoktu.

### Uygulama Adımları

#### 1. AI-02'ye Credential Dosyasını Kopyalama
```bash
# Windows'tan AI-02'ye:
type C:\Users\murat\.cloudflared\1dd07d57-42b1-4ada-8d72-1584cbcfa5a3.json | \
  plink -batch -pw test test@192.168.1.179 \
  "cat > ~/.cloudflared/1dd07d57-42b1-4ada-8d72-1584cbcfa5a3.json"
```

#### 2. AI-02'de Config Dosyası Oluşturma
```yaml
# ~/.cloudflared/config-ai02.yml
tunnel: ai02-tunnel
credentials-file: /home/test/.cloudflared/1dd07d57-42b1-4ada-8d72-1584cbcfa5a3.json
ingress:
  - hostname: ssh-ai02.spacenets.org
    service: ssh://localhost:22
  - service: http_status:404
```

#### 3. AI-01'deki Relay ve Tunnel'ı Durdurma
```bash
# AI-01'de çalışan gereksiz process'leri temizleme:
pkill socat
pkill -f 'config-ai02.*ai02-tunnel'
```

#### 4. AI-02'de Tunnel Başlatma
```bash
# İlk deneme (QUIC): Timeout hatası
cloudflared tunnel --config ~/.cloudflared/config-ai02.yml run ai02-tunnel
# Hata: "failed to dial to edge with quic: timeout: no recent network activity"

# İkinci deneme (HTTP2): ✅ Başarılı
cloudflared tunnel --protocol http2 --config ~/.cloudflared/config-ai02.yml run ai02-tunnel
# Çıktı: "Registered tunnel connection ... protocol=http2"
```

#### 5. Doğrulama
```bash
# AI-01'e erişim:
plink -proxycmd "cloudflared.exe access ssh --hostname ssh-ai01.spacenets.org" \
  test@ssh-ai01.spacenets.org "hostname && uptime"
# ✅ test-ai-01, uptime: 3 days, 4:27

# AI-02'ye erişim:
plink -proxycmd "cloudflared.exe access ssh --hostname ssh-ai02.spacenets.org" \
  test@ssh-ai02.spacenets.org "hostname && uptime"
# ✅ test-ai-02, uptime: 21:37
```

---

## Öğrenilen Dersler

### 1. Tunnel Silme Öncesi Kontrol
❌ **Yanlış:**
```bash
cloudflared tunnel delete test_linux_01
# Tunnel hangi sunucuda kullanılıyor kontrol edilmedi
```

✅ **Doğru:**
```bash
# Önce tunnel bilgilerini kontrol et:
cloudflared tunnel info test_linux_01
# Hangi hostname'lere route edilmiş bak:
cloudflared tunnel route dns list
```

### 2. SSH Relay Kullanımı
❌ **Yanlış Yaklaşım:** 
- AI-02'ye erişim olmadan AI-01'den relay yapmaya çalışmak
- Relay teknik olarak çalışsa bile authentication sorunları devam ediyor

✅ **Doğru Yaklaşım:**
- Tunnel'ı her zaman hedef sunucuda çalıştır
- Relay sadece geçici çözüm için (production'da önerilmez)

### 3. Network Protokol Seçimi
**QUIC vs HTTP2:**
- QUIC daha performanslı ancak bazı network'lerde timeout sorunu
- HTTP2 daha kararlı, güvenlik duvarları için uyumlu

```bash
# QUIC (varsayılan):
cloudflared tunnel run ai02-tunnel

# HTTP2 (sorun varsa):
cloudflared tunnel --protocol http2 run ai02-tunnel
```

### 4. SSH Authentication Sorunları
**Sorun:** AI-01'den AI-02'ye SSH yapılamıyor ama Windows'tan yapılabiliyor

**Olası Nedenler:**
- AI-02'de `AllowUsers` veya `AllowGroups` kısıtlaması
- AI-01'in IP'si `/etc/hosts.deny` içinde
- PAM konfigürasyonu farklılıkları
- SSH key formatı uyumsuzluğu (RSA vs ED25519)

**Çözüm:** Alternatif erişim yolu kullan (Windows'tan direkt)

---

## Son Durum

### Aktif Tunnel'lar
```bash
cloudflared tunnel list
```

| ID | İsim | Bağlantılar | Durum |
|----|------|-------------|-------|
| e0a805dd... | ai01-tunnel | 4 (ist04, ist06, ist07) | ✅ Çalışıyor |
| 1dd07d57... | ai02-tunnel | 4 (ist02, ist03, ist04) | ✅ Çalışıyor |
| 5ee9f932... | labtunnel1 | 4 (fra08, fra10, fra17, fra19) | ✅ Çalışıyor |
| af324cda... | nyc_311 | 4 (ist03, ist04, ist06) | ✅ Çalışıyor |

### Tunnel Konumları
- **ai01-tunnel**: AI-01 fiziksel sunucusunda çalışıyor (192.168.1.162)
- **ai02-tunnel**: AI-02 fiziksel sunucusunda çalışıyor (192.168.1.179)
- **labtunnel1**: Frankfurt edge'e bağlı
- **nyc_311**: Istanbul edge'e bağlı

### DNS Route'ları
- `ssh-ai01.spacenets.org` → ai01-tunnel → localhost:22
- `ssh-ai02.spacenets.org` → ai02-tunnel → localhost:22

---

## Tavsiyeler

### 1. Systemd Service Oluşturma
Tunnel'ların otomatik başlaması için:

```bash
# AI-01 için:
sudo cloudflared service install
# Config: /etc/cloudflared/config.yml

# AI-02 için:
sudo cloudflared service install --config /home/test/.cloudflared/config-ai02.yml
```

### 2. Monitoring
```bash
# Tunnel durumunu periyodik kontrol:
*/5 * * * * cloudflared tunnel info ai01-tunnel >> /var/log/tunnel-status.log
*/5 * * * * cloudflared tunnel info ai02-tunnel >> /var/log/tunnel-status.log
```

### 3. Backup
```bash
# Credential dosyalarını yedekle:
tar -czf cloudflared-backup-$(date +%Y%m%d).tar.gz \
  ~/.cloudflared/*.json \
  ~/.cloudflared/*.yml
```

### 4. SSH Key Konfigürasyonu (Gelecek için)
AI-01'den AI-02'ye erişim için:

```bash
# AI-02'de (konsol/fiziksel erişim ile):
echo "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQCiL1vfm82e1xK6n9c6LBMR1wAw6gravli+zJljQYKu2BMFYCwAFSoF0RLAeFSGZ1XgPByEh4BJcdZuffonsAtwruaiLTdw9Gn3LoMmBVpWVeFOed2lJgN/QmOiYpnJqunM4c/YWAh1AzklRfFGO9xlYBbt8PyDUmMaUvyQy1++O7jl5rRlFG8sE9yIny0g6AnnQRCknzz+Q2ZrwljyYnyipi3ai76+sDb2kDp1pnyrW/fzsznG7B3xsw4uZX9a5Pa0yufS4CjwxY7KUfDd8IbVjhWcMUI6R4B+bdwhVJAVBeNthi3NXLYJauve+A3/1TfmRpyKpYFVUhFOU+/xmMCV9WCVA8lqesH1ox9M7bdQY7khvMqNJvD68r2/a59cDEBTI7MS1ipU11VsNWjTWkgH9W6ZdSxXxSvoLjNBlIVHbCZ2sauwKhd0aEBFNhBJRuX9Od23R8LnXTQS0UswIgibFPZVBp2knCUeFKb1P2ZR3G4YpxwVO33gAk2bgiFZTHc= test@test-ai-01" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

---

## Hata Çözüm Referansı

### "Permission denied (publickey,password)"
**Çözüm:** Hedef sunucuda SSH konfigürasyonunu kontrol et veya alternatif erişim yolu kullan

### "FATAL ERROR: Remote side unexpectedly closed network connection"
**Çözüm:** Tunnel'ı hedef sunucunun kendisinde çalıştır, relay kullanma

### "failed to dial to edge with quic: timeout"
**Çözüm:** HTTP2 protokolü kullan: `--protocol http2`

### "websocket: bad handshake"
**Çözüm:** Cloudflare Access TCP yerine SSH servis tipi kullan

---

**Rapor Tarihi:** 31 Ocak 2026  
**Hazırlayan:** GitHub Copilot  
**Durum:** Çözüldü - Tüm tunnel'lar aktif ve çalışıyor
