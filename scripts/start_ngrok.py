import os
import sys

try:
    from pyngrok import ngrok
except ImportError:
    print("Mendownload pyngrok...")
    os.system(f"{sys.executable} -m pip install pyngrok")
    from pyngrok import ngrok

def main():
    print("=== Menyiapkan Ngrok Tunnel ===")
    token = input("Masukkan Authtoken Ngrok Anda (kosongkan jika sudah pernah login): ").strip()
    
    if token:
        ngrok.set_auth_token(token)
        print("Token berhasil disimpan.")
        
    print("\nMembuka tunnel ke port 8004...")
    try:
        public_url = ngrok.connect(8004).public_url
        print("\n" + "="*50)
        print("✅ BERHASIL! URL API Anda adalah:")
        print(f"👉  {public_url}")
        print("="*50)
        print("\nMasukkan URL di atas ke dalam file App.jsx di PC Lokal Anda.")
        print("(Tekan Ctrl+C untuk menutup tunnel)\n")
        
        ngrok_process = ngrok.get_ngrok_process()
        ngrok_process.proc.wait()
    except Exception as e:
        print(f"\n❌ Gagal membuka tunnel: {e}")
        print("Pastikan Anda sudah memasukkan Authtoken yang benar dari dashboard ngrok (https://dashboard.ngrok.com).")

if __name__ == "__main__":
    main()
