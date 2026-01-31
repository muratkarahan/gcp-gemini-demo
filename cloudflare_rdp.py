#!/usr/bin/env python3
"""
Cloudflare Tunnel RDP Bağlantı Aracı
====================================
Hem client hem de server tarafında çalışan RDP bağlantı yönetimi.

Kullanım:
    Client tarafı (RDP'ye bağlanan):
        python cloudflare_rdp.py client --hostname win01-rdp.spacenets.org --port 11389
    
    Server tarafı (RDP sunan - tunnel başlatma):
        python cloudflare_rdp.py server --config C:\\Users\\murat\\.cloudflared\\config.yml
"""

import subprocess
import sys
import argparse
import time
import os
import platform
import signal
from pathlib import Path

# Varsayılan ayarlar
DEFAULT_HOSTNAME = "win01-rdp.spacenets.org"
DEFAULT_LOCAL_PORT = 11389
DEFAULT_RDP_PORT = 3389


class CloudflareRDP:
    """Cloudflare Tunnel üzerinden RDP bağlantı yönetimi."""
    
    def __init__(self):
        self.cloudflared_path = self._find_cloudflared()
        self.process = None
        
    def _find_cloudflared(self) -> str:
        """Cloudflared executable'ı bul."""
        if platform.system() == "Windows":
            paths = [
                r"C:\Program Files (x86)\cloudflared\cloudflared.exe",
                r"C:\Program Files\cloudflared\cloudflared.exe",
                "cloudflared.exe",
                "cloudflared"
            ]
        else:
            paths = [
                "/usr/local/bin/cloudflared",
                "/usr/bin/cloudflared",
                "cloudflared"
            ]
        
        for path in paths:
            if os.path.exists(path):
                return path
            # PATH'te ara
            try:
                result = subprocess.run(
                    ["where" if platform.system() == "Windows" else "which", path.split(os.sep)[-1]],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    return result.stdout.strip().split('\n')[0]
            except:
                pass
        
        return "cloudflared"  # PATH'te olduğunu varsay
    
    def _get_terminal_command(self, cmd: list) -> list:
        """
        Sisteme göre harici terminal komutu oluştur.
        
        Args:
            cmd: Çalıştırılacak komut listesi
        
        Returns:
            Terminal ile sarılmış komut listesi
        """
        # Yolları tırnak içine al (boşluk ve parantez için)
        quoted_cmd = []
        for c in cmd:
            if ' ' in c or '(' in c or ')' in c:
                quoted_cmd.append(f'"{c}"')
            else:
                quoted_cmd.append(c)
        cmd_str = " ".join(quoted_cmd)
        
        if platform.system() == "Windows":
            # Windows - PowerShell veya CMD
            # & operatörü ile çalıştır
            return ["powershell", "-NoExit", "-Command", f"& {cmd_str}"]
        
        elif platform.system() == "Darwin":
            # macOS - Terminal.app veya iTerm
            script = f'tell application "Terminal" to do script "{cmd_str}"'
            return ["osascript", "-e", script]
        
        else:
            # Linux - Çeşitli terminal emülatörleri dene
            terminals = [
                # GNOME Terminal
                ["gnome-terminal", "--", "bash", "-c", f"{cmd_str}; exec bash"],
                # Konsole (KDE)
                ["konsole", "-e", "bash", "-c", f"{cmd_str}; exec bash"],
                # XFCE Terminal
                ["xfce4-terminal", "-e", f"bash -c '{cmd_str}; exec bash'"],
                # LXTerminal
                ["lxterminal", "-e", f"bash -c '{cmd_str}; exec bash'"],
                # xterm (fallback)
                ["xterm", "-hold", "-e", cmd_str],
                # Alacritty
                ["alacritty", "-e", "bash", "-c", f"{cmd_str}; exec bash"],
                # Kitty
                ["kitty", "bash", "-c", f"{cmd_str}; exec bash"],
            ]
            
            # Hangi terminal mevcut kontrol et
            for term_cmd in terminals:
                try:
                    result = subprocess.run(
                        ["which", term_cmd[0]],
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        return term_cmd
                except:
                    continue
            
            # Hiçbiri bulunamazsa, arka planda çalıştır
            print("⚠️  Harici terminal bulunamadı, arka planda çalıştırılıyor...")
            return cmd
    
    def start_client(self, hostname: str, local_port: int, background: bool = False) -> subprocess.Popen:
        """
        Client tarafında cloudflared access tcp başlat.
        
        Args:
            hostname: Cloudflare Tunnel hostname (örn: win01-rdp.spacenets.org)
            local_port: Yerel port (örn: 11389)
            background: Arka planda çalıştır
        
        Returns:
            subprocess.Popen nesnesi
        """
        cmd = [
            self.cloudflared_path,
            "access", "tcp",
            "--hostname", hostname,
            "--url", f"localhost:{local_port}"
        ]
        
        print(f"🔗 Cloudflared Access TCP başlatılıyor...")
        print(f"   Hostname: {hostname}")
        print(f"   Yerel Port: {local_port}")
        
        if background:
            # Harici terminal penceresinde başlat
            terminal_cmd = self._get_terminal_command(cmd)
            
            if platform.system() == "Windows":
                self.process = subprocess.Popen(
                    terminal_cmd,
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
            elif platform.system() == "Darwin":
                # macOS osascript için özel işlem
                self.process = subprocess.Popen(terminal_cmd)
            else:
                # Linux
                if terminal_cmd == cmd:
                    # Terminal bulunamadı, arka planda çalıştır
                    self.process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                else:
                    self.process = subprocess.Popen(terminal_cmd)
        else:
            self.process = subprocess.Popen(cmd)
        
        time.sleep(2)  # Bağlantının kurulmasını bekle
        print(f"✅ Proxy başlatıldı: localhost:{local_port}")
        return self.process
    
    def connect_rdp(self, port: int, username: str = None):
        """
        RDP bağlantısı başlat.
        
        Args:
            port: Bağlanılacak port
            username: Kullanıcı adı (opsiyonel)
        """
        if platform.system() == "Windows":
            # Windows - mstsc kullan
            rdp_file = Path.home() / "cloudflare_rdp_temp.rdp"
            rdp_content = f"full address:s:localhost:{port}\n"
            if username:
                rdp_content += f"username:s:{username}\n"
            
            rdp_file.write_text(rdp_content, encoding="ascii")
            
            print(f"🖥️  RDP bağlantısı başlatılıyor: localhost:{port}")
            subprocess.Popen(["mstsc", str(rdp_file)])
        
        elif platform.system() == "Darwin":
            # macOS - Microsoft Remote Desktop veya rdesktop
            print(f"🖥️  RDP bağlantısı başlatılıyor: localhost:{port}")
            
            # Microsoft Remote Desktop varsa kullan
            rdp_file = Path.home() / "cloudflare_rdp_temp.rdp"
            rdp_content = f"full address:s:localhost:{port}\n"
            if username:
                rdp_content += f"username:s:{username}\n"
            rdp_file.write_text(rdp_content, encoding="ascii")
            
            try:
                subprocess.Popen(["open", str(rdp_file)])
            except:
                print(f"⚠️  Manuel bağlantı için: open rdp://localhost:{port}")
        
        else:
            # Linux - rdesktop, xfreerdp veya remmina
            print(f"🖥️  RDP bağlantısı başlatılıyor: localhost:{port}")
            
            rdp_clients = [
                # xfreerdp (en yaygın)
                ["xfreerdp", f"/v:localhost:{port}", f"/u:{username}" if username else ""],
                # rdesktop
                ["rdesktop", f"localhost:{port}", "-u", username if username else ""],
                # remmina
                ["remmina", "-c", f"rdp://localhost:{port}"],
            ]
            
            for client_cmd in rdp_clients:
                try:
                    # Boş parametreleri temizle
                    client_cmd = [c for c in client_cmd if c]
                    result = subprocess.run(
                        ["which", client_cmd[0]],
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        subprocess.Popen(client_cmd)
                        return
                except:
                    continue
            
            print(f"⚠️  RDP client bulunamadı.")
            print(f"   Kurulum: sudo apt install freerdp2-x11")
            print(f"   Manuel bağlantı: xfreerdp /v:localhost:{port}")
    
    def start_server(self, config_path: str = None, tunnel_name: str = None, background: bool = False):
        """
        Server tarafında tunnel başlat.
        
        Args:
            config_path: Tunnel config dosyası yolu
            tunnel_name: Tunnel adı
            background: Harici terminal penceresinde başlat
        """
        if config_path:
            cmd = [
                self.cloudflared_path,
                "tunnel",
                "--config", config_path,
                "run"
            ]
            if tunnel_name:
                cmd.append(tunnel_name)
        elif tunnel_name:
            cmd = [
                self.cloudflared_path,
                "tunnel", "run",
                tunnel_name
            ]
        else:
            print("❌ Config dosyası veya tunnel adı belirtilmeli.")
            return None
        
        print(f"🚀 Tunnel başlatılıyor...")
        print(f"   Komut: {' '.join(cmd)}")
        
        if background:
            # Harici terminal penceresinde başlat
            terminal_cmd = self._get_terminal_command(cmd)
            
            if platform.system() == "Windows":
                self.process = subprocess.Popen(
                    terminal_cmd,
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
            elif platform.system() == "Darwin":
                self.process = subprocess.Popen(terminal_cmd)
            else:
                if terminal_cmd == cmd:
                    self.process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                else:
                    self.process = subprocess.Popen(terminal_cmd)
            
            time.sleep(2)
            print(f"✅ Tunnel harici terminalde başlatıldı.")
        else:
            self.process = subprocess.Popen(cmd)
        
        return self.process
    
    def check_tunnel_status(self):
        """Tunnel durumunu kontrol et."""
        cmd = [self.cloudflared_path, "tunnel", "list"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
    
    def stop(self):
        """Çalışan process'i durdur."""
        if self.process:
            self.process.terminate()
            self.process.wait()
            print("🛑 Process durduruldu.")


def client_mode(args):
    """Client modu - RDP'ye bağlan."""
    rdp = CloudflareRDP()
    
    try:
        # Access TCP başlat
        rdp.start_client(args.hostname, args.port, background=True)
        
        time.sleep(2)  # Proxy'nin başlamasını bekle
        
        if args.connect:
            # RDP bağlantısı başlat
            rdp.connect_rdp(args.port, args.username)
            print("\n✅ RDP bağlantısı başlatıldı.")
            print("ℹ️  Cloudflared arka planda çalışıyor.")
        else:
            print(f"\n📌 RDP bağlantısı için:")
            print(f"   mstsc /v:localhost:{args.port}")
        
        if args.wait:
            print("\n⏳ Çıkmak için Ctrl+C basın...")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n👋 Çıkılıyor...")
                rdp.stop()
    
    except Exception as e:
        print(f"❌ Hata: {e}")
        rdp.stop()


def server_mode(args):
    """Server modu - Tunnel başlat."""
    rdp = CloudflareRDP()
    
    try:
        if args.status:
            rdp.check_tunnel_status()
            return
        
        rdp.start_server(args.config, args.tunnel, background=args.background)
        
        print("\n✅ Tunnel başlatıldı.")
        
        if not args.background:
            print("⏳ Çıkmak için Ctrl+C basın...")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n👋 Çıkılıyor...")
            rdp.stop()
    
    except Exception as e:
        print(f"❌ Hata: {e}")
        rdp.stop()


def quick_connect(args):
    """Hızlı bağlantı - tek komutla client başlat ve bağlan."""
    rdp = CloudflareRDP()
    
    print("🚀 Hızlı bağlantı başlatılıyor...")
    
    # Access TCP başlat (arka planda)
    rdp.start_client(args.hostname, args.port, background=True)
    
    time.sleep(3)  # Bağlantının kurulmasını bekle
    
    # RDP bağlan
    rdp.connect_rdp(args.port, args.username)
    
    print("\n✅ Bağlantı hazır!")
    print("ℹ️  Cloudflared arka planda çalışıyor.")


def main():
    parser = argparse.ArgumentParser(
        description="Cloudflare Tunnel RDP Bağlantı Aracı",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Örnekler:
  # Hızlı bağlantı (varsayılan ayarlarla)
  python cloudflare_rdp.py quick

  # Client modu - sadece proxy başlat
  python cloudflare_rdp.py client --hostname win01-rdp.spacenets.org --port 11389

  # Client modu - proxy + RDP bağlantısı
  python cloudflare_rdp.py client --hostname win01-rdp.spacenets.org --port 11389 --connect

  # Server modu - tunnel başlat
  python cloudflare_rdp.py server --config C:\\Users\\murat\\.cloudflared\\config.yml

  # Tunnel durumunu kontrol et
  python cloudflare_rdp.py server --status
        """
    )
    
    subparsers = parser.add_subparsers(dest="mode", help="Çalışma modu")
    
    # Client modu
    client_parser = subparsers.add_parser("client", help="Client modu - RDP'ye bağlan")
    client_parser.add_argument(
        "--hostname", "-H",
        default=DEFAULT_HOSTNAME,
        help=f"Cloudflare Tunnel hostname (varsayılan: {DEFAULT_HOSTNAME})"
    )
    client_parser.add_argument(
        "--port", "-p",
        type=int,
        default=DEFAULT_LOCAL_PORT,
        help=f"Yerel port (varsayılan: {DEFAULT_LOCAL_PORT})"
    )
    client_parser.add_argument(
        "--username", "-u",
        help="RDP kullanıcı adı"
    )
    client_parser.add_argument(
        "--connect", "-c",
        action="store_true",
        help="Otomatik RDP bağlantısı başlat"
    )
    client_parser.add_argument(
        "--wait", "-w",
        action="store_true",
        help="Proxy'yi ön planda tut"
    )
    
    # Server modu
    server_parser = subparsers.add_parser("server", help="Server modu - Tunnel başlat")
    server_parser.add_argument(
        "--config", "-C",
        help="Tunnel config dosyası yolu"
    )
    server_parser.add_argument(
        "--tunnel", "-t",
        help="Tunnel adı"
    )
    server_parser.add_argument(
        "--status", "-s",
        action="store_true",
        help="Tunnel durumunu göster"
    )
    server_parser.add_argument(
        "--background", "-b",
        action="store_true",
        help="Harici terminal penceresinde başlat"
    )
    
    # Hızlı bağlantı
    quick_parser = subparsers.add_parser("quick", help="Hızlı bağlantı")
    quick_parser.add_argument(
        "--hostname", "-H",
        default=DEFAULT_HOSTNAME,
        help=f"Cloudflare Tunnel hostname (varsayılan: {DEFAULT_HOSTNAME})"
    )
    quick_parser.add_argument(
        "--port", "-p",
        type=int,
        default=DEFAULT_LOCAL_PORT,
        help=f"Yerel port (varsayılan: {DEFAULT_LOCAL_PORT})"
    )
    quick_parser.add_argument(
        "--username", "-u",
        help="RDP kullanıcı adı"
    )
    
    args = parser.parse_args()
    
    if args.mode == "client":
        client_mode(args)
    elif args.mode == "server":
        server_mode(args)
    elif args.mode == "quick":
        quick_connect(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
