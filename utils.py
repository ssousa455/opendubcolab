import os
import subprocess
import logging
from pathlib import Path
import shutil

logger = logging.getLogger(__name__)

def install_system_dependencies():
    """Instalar dependências do sistema"""
    try:
        # FFmpeg
        subprocess.run(["apt-get", "update", "-qq"], check=True)
        subprocess.run(["apt-get", "install", "-y", "ffmpeg", "espeak-ng"], check=True)
        logger.info("✅ FFmpeg instalado")
        
        # Verificar instalação
        result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True)
        if result.returncode == 0:
            logger.info("✅ FFmpeg verificado")
        else:
            logger.error("❌ Erro ao verificar FFmpeg")
            
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Erro ao instalar dependências: {e}")
        raise

def setup_gpu_environment():
    """Configurar ambiente GPU"""
    try:
        import torch
        if torch.cuda.is_available():
            # Configurações de memória CUDA
            os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "max_split_size_mb:128"
            os.environ["CUDA_VISIBLE_DEVICES"] = "0"
            
            # Limpar cache GPU
            torch.cuda.empty_cache()
            
            logger.info(f"✅ GPU configurada: {torch.cuda.get_device_name(0)}")
            return True
        else:
            logger.warning("⚠️ GPU não disponível")
            return False
    except Exception as e:
        logger.error(f"❌ Erro ao configurar GPU: {e}")
        return False

def cleanup_temp_files():
    """Limpar arquivos temporários"""
    try:
        temp_dirs = ["/tmp", "/var/tmp", "./__pycache__"]
        for temp_dir in temp_dirs:
            if os.path.exists(temp_dir):
                for file in os.listdir(temp_dir):
                    file_path = os.path.join(temp_dir, file)
                    try:
                        if os.path.isfile(file_path):
                            os.remove(file_path)
                        elif os.path.isdir(file_path):
                            shutil.rmtree(file_path)
                    except:
                        pass
        logger.info("✅ Arquivos temporários limpos")
    except Exception as e:
        logger.error(f"❌ Erro ao limpar arquivos: {e}")

def get_video_info(video_path):
    """Obter informações do vídeo"""
    try:
        cmd = [
            "ffprobe", "-v", "quiet", "-print_format", "json", 
            "-show_format", "-show_streams", video_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            import json
            data = json.loads(result.stdout)
            
            # Extrair informações relevantes
            format_info = data.get("format", {})
            duration = float(format_info.get("duration", 0))
            size = int(format_info.get("size", 0))
            
            return {
                "duration": duration,
                "size": size,
                "duration_str": f"{duration//60:.0f}:{duration%60:02.0f}",
                "size_str": f"{size/1024/1024:.1f}MB"
            }
    except Exception as e:
        logger.error(f"❌ Erro ao obter info do vídeo: {e}")
        return None
