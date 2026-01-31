# Cloudflare Tunnel RDP Bağlantı Aracı

Windows/Linux/macOS için Cloudflare Tunnel üzerinden güvenli RDP bağlantısı sağlayan Python aracı.

## 🌐 Desteklenen Platformlar

| Platform | Terminal | RDP Client |
|----------|----------|------------|
| Windows | PowerShell | mstsc (built-in) |
| Linux | gnome-terminal, konsole, xterm | xfreerdp, rdesktop |
| macOS | Terminal.app | Microsoft Remote Desktop |

## 🚀 Hızlı Başlangıç

```bash
# Tek komutla bağlan
python cloudflare_rdp.py client -b -c
```

Bu komut:
1. Harici PowerShell penceresinde cloudflared proxy başlatır
2. mstsc ile RDP bağlantısını otomatik açar

## 📋 Kurulum

### Gereksinimler
- Python 3.x
- Cloudflared (`winget install cloudflare.cloudflared`)

### Cloudflared Kurulumu (Windows)
```powershell
winget install cloudflare.cloudflared
```

### Cloudflared Kurulumu (Linux)
```bash
# Debian/Ubuntu
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb -o cloudflared.deb
sudo dpkg -i cloudflared.deb

# Diğer dağıtımlar
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o cloudflared
chmod +x cloudflared
sudo mv cloudflared /usr/local/bin/
```

## 💻 Kullanım

### Client Modu (Uzak Masaüstüne Bağlan)

```bash
# Varsayılan ayarlarla bağlan (win01-rdp.spacenets.org:11389)
python cloudflare_rdp.py client -b -c

# Özel hostname ve port ile
python cloudflare_rdp.py client -H myhost.example.com -p 13389 -b -c

# Sadece proxy başlat (RDP bağlantısını manuel aç)
python cloudflare_rdp.py client -b
```

### Parametreler

| Parametre | Kısa | Açıklama |
|-----------|------|----------|
| `--hostname` | `-H` | Cloudflare Tunnel hostname (varsayılan: win01-rdp.spacenets.org) |
| `--port` | `-p` | Yerel port (varsayılan: 11389) |
| `--background` | `-b` | Harici terminal penceresinde başlat |
| `--connect` | `-c` | Otomatik RDP bağlantısı başlat |
| `--username` | `-u` | RDP kullanıcı adı |
| `--wait` | `-w` | Proxy'yi ön planda tut |

### Hızlı Bağlantı

```bash
python cloudflare_rdp.py quick
```

### Server Modu (Tunnel Başlat)

```bash
# Tunnel başlat
python cloudflare_rdp.py server -t win01-rdp -b

# Config dosyası ile
python cloudflare_rdp.py server -C ~/.cloudflared/config.yml -b

# Tunnel durumunu kontrol et
python cloudflare_rdp.py server -s
```

## 🔧 Manuel Bağlantı

Eğer script kullanmak istemezseniz:

```powershell
# 1. Ayrı bir terminalde cloudflared başlat
cloudflared access tcp --hostname win01-rdp.spacenets.org --url localhost:11389

# 2. Başka bir terminalde RDP bağlan
mstsc /v:localhost:11389
```

## 📁 Dosya Yapısı

```
gcp-gemini-demo/
├── cloudflare_rdp.py              # Ana Python scripti
├── README.md                       # Bu dosya
├── CLOUDFLARE_RDP_CLIENT_SETUP.md # Detaylı kurulum rehberi
└── CLOUDFLARE_TUNNEL_TROUBLESHOOTING.md # Sorun giderme
```

## ❓ Sorun Giderme

### "Bad handshake" hatası
- Sunucu tarafında tunnel çalışmıyor olabilir
- Cloudflare Dashboard'dan tunnel durumunu kontrol edin

### Port zaten kullanımda
- Farklı bir port deneyin: `python cloudflare_rdp.py client -p 13389 -b -c`

### Bağlantı zaman aşımı
- DNS çözünürlüğünü kontrol edin: `nslookup win01-rdp.spacenets.org`
- İnternet bağlantınızı kontrol edin

## ⚙️ Ortam Değişkenleri

Script'in varsayılan değerlerini değiştirmek için ortam değişkenleri kullanabilirsiniz:

```bash
# Linux/macOS
export CLOUDFLARE_HOSTNAME="myhost.example.com"
export CLOUDFLARE_PORT="13389"

# Windows PowerShell
$env:CLOUDFLARE_HOSTNAME = "myhost.example.com"
$env:CLOUDFLARE_PORT = "13389"
```

Veya doğrudan script içindeki varsayılan değerleri düzenleyin:
```python
DEFAULT_HOSTNAME = "win01-rdp.spacenets.org"
DEFAULT_LOCAL_PORT = 11389
```

## 🔐 Güvenlik

### Cloudflare Access Kimlik Doğrulama

Cloudflare Access ile kimlik doğrulama etkinleştirilmişse, ilk bağlantıda tarayıcıda kimlik doğrulama yapmanız gerekebilir:

1. `cloudflared access tcp` komutu çalıştırıldığında tarayıcı açılır
2. E-posta veya SSO ile giriş yapın
3. Kimlik doğrulama token'ı otomatik olarak kaydedilir
4. Sonraki bağlantılarda tekrar giriş gerekmez

### Güvenli Bağlantı Avantajları

- 🔒 Tüm trafik TLS ile şifrelenir
- 🌍 VPN'e gerek kalmadan güvenli uzak erişim
- 🚫 Açık port yok - sunucuda firewall açmanıza gerek yok
- 🔑 Zero Trust güvenlik modeli

## 📊 Kullanım Örnekleri

### Senaryo 1: Evden Ofise Bağlanma
```bash
# Ofisteki Windows bilgisayara evden bağlan
python cloudflare_rdp.py client -H office-pc.company.com -b -c
```

### Senaryo 2: Farklı Port Kullanma
```bash
# 11389 portu meşgulse farklı port kullan
python cloudflare_rdp.py client -p 23389 -b -c
```

### Senaryo 3: Belirli Kullanıcı ile Bağlanma
```bash
# RDP kullanıcı adını belirt
python cloudflare_rdp.py client -u administrator -b -c
```

### Senaryo 4: Proxy'yi Arka Planda Tutma
```bash
# Bağlantıyı açık tut, RDP kapatılsa bile
python cloudflare_rdp.py client -b -w
```

### Senaryo 5: Sunucu Tarafında Tunnel Başlatma
```bash
# Windows sunucuda tunnel çalıştır
python cloudflare_rdp.py server -t win01-rdp -b
```

## 🤝 Katkıda Bulunma

Katkılarınızı bekliyoruz! 

1. Fork edin
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Değişikliklerinizi commit edin (`git commit -m 'Add amazing feature'`)
4. Branch'i push edin (`git push origin feature/amazing-feature`)
5. Pull Request açın

### Geliştirme Ortamı

```bash
git clone https://github.com/muratkarahan/gcp-gemini-demo.git
cd gcp-gemini-demo
python cloudflare_rdp.py --help
```

## 📄 Lisans

MIT License

## 👤 Yazar

Murat Karahan - [@muratkarahan](https://github.com/muratkarahan)
