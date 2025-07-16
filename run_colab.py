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
    os.system("pip install -q pyngrok") # Adicionar pyngrok
    
    # 3. Baixar arquivos do GitHub
    print("📥 Baixando arquivos...")
    result1 = os.system("wget -q https://raw.githubusercontent.com/ssousa455/opendubcolab/main/app.py")
    result2 = os.system("wget -q https://raw.githubusercontent.com/ssousa455/opendubcolab/main/utils.py")

    if result1 != 0 or result2 != 0:
        print("❌ Erro ao baixar arquivos do GitHub")
        sys.exit(1)
    else:
        print("✅ Arquivos baixados com sucesso")
    
    
    # 4. Configurar GPU
    print("🎮 Configurando GPU...")
    try:
        import torch
        if torch.cuda.is_available():
            os.environ["CUDA_VISIBLE_DEVICES"] = "0"
            os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "max_split_size_mb:128"
            print(f"✅ GPU detectada: {torch.cuda.get_device_name(0)}")
            # Forçar o uso da GPU no ambiente, se disponível
            os.environ["SONITR_DEVICE"] = "cuda"
        else:
            print("⚠️ GPU não disponível, usando CPU")
            os.environ["SONITR_DEVICE"] = "cpu"
    except Exception as e:
        print(f"⚠️ Erro ao configurar GPU: {e}")
        os.environ["SONITR_DEVICE"] = "cpu"
    
    # 5. Executar aplicação e expor com ngrok
    print("🎬 Iniciando aplicação e expondo com ngrok...")
    from pyngrok import ngrok
    
    # Autenticar ngrok usando variável de ambiente
    ngrok_auth_token = os.environ.get("NGROK_AUTH_TOKEN")
    if ngrok_auth_token:
        ngrok.set_auth_token(ngrok_auth_token)
    else:
        print("⚠️ NGROK_AUTH_TOKEN não definida. O túnel ngrok pode não funcionar.")

    # Iniciar túnel ngrok para a porta 7860
    public_url = ngrok.connect(7860)
    print(f"🔗 Gradio URL: {public_url}")
    
    # Executar a aplicação Gradio
    os.system("python app.py")

if __name__ == "__main__":
    setup_colab()


