# Cloudflare Tunnel ile RDP Client Bağlantısı

Bu döküman, Cloudflare Tunnel üzerinden uzak bir Windows makinesine RDP ile bağlanmak için gerekli client tarafı kurulum ve yapılandırma adımlarını içerir.

## Gereksinimler

- Windows 10/11
- Cloudflared CLI (`C:\Program Files (x86)\cloudflared\cloudflared.exe`)
- Uzak makinede çalışan Cloudflare Tunnel (RDP servisine yönlendirilmiş)

## Hızlı Başlangıç

### 1. Cloudflared Access TCP Proxy Başlatma

Harici PowerShell penceresinde sürekli çalışan proxy başlatın:

```powershell
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cloudflared access tcp --hostname win01-rdp.spacenets.org --url localhost:13389"
```

### 2. RDP Bağlantısı

```powershell
mstsc /v:localhost:13389
```

## Detaylı Kurulum

### Adım 1: RDP Dosyası Oluşturma

Kolay bağlantı için RDP dosyası oluşturun:

```powershell
$rdpContent = @"
full address:s:localhost:13389
username:s:murat
"@
$rdpContent | Set-Content C:\Users\murat\rdp-win01.rdp -Encoding ASCII
```

### Adım 2: Cloudflared Access TCP Başlatma

#### Tek Seferlik Çalıştırma:
```powershell
cloudflared access tcp --hostname win01-rdp.spacenets.org --url localhost:13389
```

#### Harici PowerShell Penceresinde:
```powershell
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cloudflared access tcp --hostname win01-rdp.spacenets.org --url localhost:13389"
```

#### Sürekli Çalışan (Otomatik Yeniden Başlatma):
```powershell
Start-Process powershell -ArgumentList "-NoExit", "-Command", "while(`$true) { cloudflared access tcp --hostname win01-rdp.spacenets.org --url localhost:13389; Start-Sleep -Seconds 2 }"
```

### Adım 3: RDP Bağlantısı

```powershell
mstsc C:\Users\murat\rdp-win01.rdp
```

veya

```powershell
mstsc /v:localhost:13389
```

## Kullanıcı Kimlik Bilgileri

RDP kimlik bilgilerini kaydetmek için:

```powershell
cmdkey /generic:TERMSRV/localhost:13389 /user:murat /pass:YOUR_PASSWORD
```

Kayıtlı kimlik bilgilerini silmek için:

```powershell
cmdkey /delete:localhost:13389
cmdkey /delete:TERMSRV/localhost:13389
```

## Yapılandırma Parametreleri

| Parametre | Değer | Açıklama |
|-----------|-------|----------|
| Hostname | `win01-rdp.spacenets.org` | Cloudflare Tunnel DNS adresi |
| Local Port | `13389` | Yerel proxy portu |
| Username | `murat` | Uzak makine kullanıcı adı |

## Sorun Giderme

### Port Kontrolü
```powershell
netstat -ano | findstr "13389"
```

### Cloudflared Process Kontrolü
```powershell
Get-Process cloudflared -ErrorAction SilentlyContinue | Format-Table Id, StartTime
```

### Tunnel Durumu Kontrolü
```powershell
cloudflared tunnel list
```

### DNS Çözümleme Testi
```powershell
nslookup win01-rdp.spacenets.org
```

### Bağlantı Hata Logları
```powershell
cloudflared access tcp --hostname win01-rdp.spacenets.org --url localhost:13389 --loglevel debug
```

## Yaygın Hatalar

### "websocket: bad handshake"
- Tunnel tarafında hostname için TCP routing yapılandırılmamış
- Cloudflare Zero Trust Dashboard'da Public Hostname ekleyin

### "Port already in use"
- Başka bir cloudflared process çalışıyor
- Farklı port kullanın veya mevcut process'i durdurun:
```powershell
Stop-Process -Name cloudflared -Force
```

### Bağlantı Reddedildi
- Uzak makinede RDP servisi çalışmıyor
- Uzak makinede tunnel aktif değil
- Firewall RDP portunu engelliyor

## Komut Referansı

| Komut | Açıklama |
|-------|----------|
| `cloudflared access tcp` | TCP proxy başlatır |
| `cloudflared access rdp` | RDP-specific proxy (tcp ile aynı) |
| `mstsc /v:HOST:PORT` | RDP istemcisi başlatır |
| `cmdkey` | Windows kimlik bilgisi yönetimi |

## Notlar

- Bu makine (MURAT-PC) Windows 11 Home olduğu için RDP Server çalıştıramaz
- Bu döküman sadece **client** tarafı kurulumunu içerir
- Server tarafı için tunnel'ın uzak makinede yapılandırılması gerekir

---

# RDP Bağlantı Rehberi - win01-rdp.spacenets.org (Sunucu Tarafı)

## Gereksinimler

Client tarafında `cloudflared` kurulu olmalı:
- https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/

---

## Bağlantı Adımları

### 1. Cloudflared Access Başlat

PowerShell veya CMD'de:

```powershell
cloudflared access rdp --hostname win01-rdp.spacenets.org --url localhost:11389
```

Bu komut arka planda çalışmaya devam edecek.

### 2. RDP ile Bağlan

Yeni bir terminal veya RDP uygulamasında:

```powershell
mstsc /v:localhost:11389
```

Veya **Remote Desktop Connection** uygulamasını açıp `localhost:11389` yazın.

---

## Giriş Bilgileri

### Seçenek 1: Microsoft Hesabı (murat oturumu)

| Alan | Değer |
|------|-------|
| **Kullanıcı** | `muratkarahan@gmail.com` |
| **Şifre** | Microsoft hesabı şifresi |

### Seçenek 2: Yerel Kullanıcı (rdpuser)

| Alan | Değer |
|------|-------|
| **Kullanıcı** | `rdpuser` |
| **Şifre** | `Rdp@2026!` |

---

## Tek Satırda (PowerShell)

```powershell
# Terminal 1: Access başlat
Start-Process cloudflared -ArgumentList "access","rdp","--hostname","win01-rdp.spacenets.org","--url","localhost:11389"

# Terminal 2: Birkaç saniye bekle, sonra bağlan
Start-Sleep 3; mstsc /v:localhost:11389
```

---

## Diğer Servisler

| Servis | Adres |
|--------|-------|
| Web | https://win01-web.spacenets.org |
| Ollama | https://win01-ollama.spacenets.org |
| SSH | win01-ssh.spacenets.org |

---

## Sorun Giderme

- **Şifre kabul edilmiyor:** Microsoft hesabı için email adresi + Microsoft şifresi kullanın (PIN değil)
- **Bağlantı zaman aşımı:** cloudflared access komutunun çalıştığından emin olun
- **Port kullanımda:** 11389 yerine farklı port deneyin (örn: 13389)

---

*Oluşturulma: 31 Ocak 2026*
