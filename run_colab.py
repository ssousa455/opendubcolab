# Arquivo para executar no Google Colab
import os
import subprocess
import sys

def setup_colab():
    """Configurar ambiente no Google Colab"""
    
    print("🚀 Configurando Open-Dubbing no Google Colab...")
    
    # 1. Instalar dependências do sistema
    print("📦 Instalando dependências do sistema...")
    os.system("apt-get update -qq")
    os.system("apt-get install -y ffmpeg espeak-ng")
    
    # 2. Instalar Python packages
    print("🐍 Instalando packages Python...")
    os.system("pip install -q gradio>=4.0.0 torch torchvision torchaudio")
    os.system("pip install -q open-dubbing")
    
    # 3. Baixar arquivos do GitHub
    print("📥 Baixando arquivos...")
    os.system("wget -q https://raw.githubusercontent.com/SEU_USUARIO/open-dubbing-ui/main/app.py")
    os.system("wget -q https://raw.githubusercontent.com/SEU_USUARIO/open-dubbing-ui/main/utils.py")
    
    # 4. Configurar GPU
    print("🎮 Configurando GPU...")
    try:
        import torch
        if torch.cuda.is_available():
            os.environ["CUDA_VISIBLE_DEVICES"] = "0"
            os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "max_split_size_mb:128"
            print(f"✅ GPU detectada: {torch.cuda.get_device_name(0)}")
        else:
            print("⚠️ GPU não disponível")
    except:
        print("⚠️ Erro ao configurar GPU")
    
    # 5. Executar aplicação
    print("🎬 Iniciando aplicação...")
    os.system("python app.py")

if __name__ == "__main__":
    setup_colab()
