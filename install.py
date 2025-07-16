import subprocess
import sys
import os

def install_requirements():
    """Instalar dependências automaticamente"""
    print("🔧 Instalando dependências...")
    
    # Atualizar sistema
    os.system("apt-get update -qq")
    os.system("apt-get install -y ffmpeg espeak-ng")
    
    # Instalar Python packages
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    subprocess.check_call([sys.executable, "-m", "pip", "install", "open-dubbing"])
    
    print("✅ Instalação concluída!")

if __name__ == "__main__":
    install_requirements()
