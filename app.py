import gradio as gr
import os
import subprocess
import torch
import shutil
import tempfile
import json
import sys
from pathlib import Path
import logging
from typing import Optional, Tuple, List
import time

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configurações globais
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB
SUPPORTED_FORMATS = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm']

class OpenDubbingApp:
    def __init__(self):
        self.setup_environment()
        self.output_dir = Path("./outputs")
        self.output_dir.mkdir(exist_ok=True)
        
    def setup_environment(self):
        """Configurar ambiente para usar GPU se disponível"""
        if torch.cuda.is_available():
            os.environ["CUDA_VISIBLE_DEVICES"] = "0"
            os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "max_split_size_mb:128"
            logger.info(f"GPU detectada: {torch.cuda.get_device_name(0)}")
            logger.info(f"Memória GPU: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
        else:
            logger.warning("GPU não disponível, usando CPU")
            
    def validate_inputs(self, video_file, target_language, hf_token) -> Tuple[bool, str]:
        """Validar entradas do usuário"""
        if not video_file:
            return False, "❌ Por favor, selecione um arquivo de vídeo"
            
        if not hf_token:
            return False, "❌ Token HuggingFace é obrigatório"
            
        if not target_language:
            return False, "❌ Selecione um idioma de destino"
            
        # Verificar tamanho do arquivo
        if os.path.getsize(video_file) > MAX_FILE_SIZE:
            return False, f"❌ Arquivo muito grande (max: {MAX_FILE_SIZE/1024/1024:.0f}MB)"
            
        # Verificar formato
        if not any(video_file.lower().endswith(fmt) for fmt in SUPPORTED_FORMATS):
            return False, f"❌ Formato não suportado. Use: {', '.join(SUPPORTED_FORMATS)}"
            
        return True, "✅ Validação ok"
        
    def process_video(self, video_file, target_language, hf_token, 
                     source_language="auto", tts_engine="edge", 
                     use_gpu=True, progress=gr.Progress()):
        """Processar dublagem do vídeo"""
        
        # Validar entradas
        is_valid, message = self.validate_inputs(video_file, target_language, hf_token)
        if not is_valid:
            return None, message, ""
            
        progress(0.1, "🔍 Validando arquivos...")
        
        try:
            # Preparar diretório de saída
            timestamp = int(time.time())
            output_name = f"dubbed_{timestamp}.mp4"
            output_path = self.output_dir / output_name
            
            progress(0.2, "🚀 Iniciando dublagem...")
            
            # Construir comando
            cmd = [
                "python", "-m", "open_dubbing",
                "--input_file", str(video_file),
                "--target_language", target_language,
                "--hugging_face_token", hf_token,
                "--output_directory", str(self.output_dir),
                "--tts_engine", tts_engine,
                "--output_name", output_name
            ]
            
            # Adicionar opções condicionais
            if source_language != "auto":
                cmd.extend(["--source_language", source_language])
                
            if use_gpu and torch.cuda.is_available():
                cmd.extend(["--device", "cuda"])
            else:
                cmd.extend(["--device", "cpu"])
                
            progress(0.3, "🎬 Processando vídeo...")
            
            # Executar comando
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                universal_newlines=True
            )
            
            # Monitorar progresso
            for i in range(30, 90, 5):
                if process.poll() is not None:
                    break
                progress(i/100, f"🔄 Processando... ({i}%)")
                time.sleep(2)
                
            # Aguardar conclusão
            stdout, stderr = process.communicate()
            
            progress(0.95, "🎉 Finalizando...")
            
            if process.returncode == 0:
                if output_path.exists():
                    file_size = output_path.stat().st_size / 1024 / 1024
                    success_msg = f"✅ Dublagem concluída com sucesso!\n📁 Arquivo: {output_name}\n📊 Tamanho: {file_size:.1f}MB"
                    progress(1.0, "✅ Concluído!")
                    return str(output_path), success_msg, ""
                else:
                    return None, "❌ Arquivo de saída não encontrado", stderr
            else:
                error_msg = f"❌ Erro no processamento:\n{stderr}"
                return None, error_msg, stderr
                
        except Exception as e:
            error_msg = f"❌ Erro inesperado: {str(e)}"
            logger.error(error_msg)
            return None, error_msg, str(e)
            
    def get_system_info(self):
        """Obter informações do sistema"""
        info = []
        
        # GPU Info
        if torch.cuda.is_available():
            info.append(f"🎮 GPU: {torch.cuda.get_device_name(0)}")
            info.append(f"💾 VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
            info.append(f"🔥 CUDA: {torch.version.cuda}")
        else:
            info.append("🎮 GPU: Não disponível")
            
        # Python & PyTorch
        info.append(f"🐍 Python: {sys.version.split()[0]}")
        info.append(f"🔥 PyTorch: {torch.__version__}")
        
        return "\n".join(info)

# Instanciar aplicação
app = OpenDubbingApp()

# Criar interface Gradio
with gr.Blocks(
    theme=gr.themes.Soft(),
    title="🎬 Open-Dubbing",
    css="""
    .gradio-container {
        max-width: 800px !important;
        margin: auto !important;
    }
    .status-success { color: #4CAF50; }
    .status-error { color: #f44336; }
    .status-warning { color: #ff9800; }
    """
) as demo:
    
    gr.HTML("""
    <div style="text-align: center; padding: 20px;">
        <h1>🎬 Open-Dubbing</h1>
        <p>Dublagem automática de vídeos com IA</p>
    </div>
    """)
    
    with gr.Row():
        with gr.Column(scale=2):
            # Upload de vídeo
            video_input = gr.File(
                label="📤 Selecione o vídeo",
                file_types=SUPPORTED_FORMATS,
                file_count="single"
            )
            
            # Configurações principais
            with gr.Row():
                target_lang = gr.Dropdown(
                    label="🌍 Idioma de destino",
                    choices=[
                        ("🇧🇷 Português", "por"),
                        ("🇺🇸 Inglês", "eng"),
                        ("🇪🇸 Espanhol", "spa"),
                        ("🇫🇷 Francês", "fra"),
                        ("🇩🇪 Alemão", "deu"),
                        ("🇮🇹 Italiano", "ita"),
                        ("🇷🇺 Russo", "rus"),
                        ("🇯🇵 Japonês", "jpn"),
                        ("🇰🇷 Coreano", "kor"),
                        ("🇨🇳 Chinês", "zho")
                    ],
                    value="por"
                )
                
                source_lang = gr.Dropdown(
                    label="🎤 Idioma original",
                    choices=[
                        ("🤖 Detectar automaticamente", "auto"),
                        ("🇺🇸 Inglês", "eng"),
                        ("🇧🇷 Português", "por"),
                        ("🇪🇸 Espanhol", "spa"),
                        ("🇫🇷 Francês", "fra"),
                        ("🇩🇪 Alemão", "deu"),
                        ("🇮🇹 Italiano", "ita"),
                        ("🇷🇺 Russo", "rus"),
                        ("🇯🇵 Japonês", "jpn"),
                        ("🇰🇷 Coreano", "kor"),
                        ("🇨🇳 Chinês", "zho")
                    ],
                    value="auto"
                )
            
            # Token HuggingFace
            hf_token = gr.Textbox(
                label="🔑 Token HuggingFace",
                placeholder="hf_...",
                type="password",
                info="Necessário para usar os modelos de IA"
            )
            
            # Configurações avançadas
            with gr.Accordion("⚙️ Configurações Avançadas", open=False):
                tts_engine = gr.Dropdown(
                    label="🎵 Motor TTS",
                    choices=[
                        ("🔊 Edge TTS (Rápido)", "edge"),
                        ("🎤 OpenAI TTS (Melhor)", "openai"),
                        ("🤖 Coqui TTS (Local)", "coqui")
                    ],
                    value="edge"
                )
                
                use_gpu = gr.Checkbox(
                    label="🎮 Usar GPU (se disponível)",
                    value=True
                )
            
            # Botão de processamento
            process_btn = gr.Button(
                "🚀 Iniciar Dublagem",
                variant="primary",
                size="lg"
            )
            
        with gr.Column(scale=1):
            # Informações do sistema
            gr.HTML(f"""
            <div style="background: #f0f0f0; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                <h3>💻 Sistema</h3>
                <pre style="font-size: 12px; margin: 0;">{app.get_system_info()}</pre>
            </div>
            """)
            
            # Status
            status_output = gr.Textbox(
                label="📊 Status",
                lines=5,
                interactive=False
            )
            
            # Download
            download_output = gr.File(
                label="📥 Download",
                visible=False
            )
    
    # Área de logs
    with gr.Accordion("📋 Logs Detalhados", open=False):
        logs_output = gr.Textbox(
            label="Logs",
            lines=10,
            interactive=False
        )
    
    # Guia de uso
    with gr.Accordion("📖 Guia de Uso", open=False):
        gr.HTML("""
        <div style="padding: 10px;">
            <h3>🚀 Como usar:</h3>
            <ol>
                <li><strong>Token HuggingFace:</strong> Crie em <a href="https://huggingface.co/settings/tokens" target="_blank">huggingface.co/settings/tokens</a></li>
                <li><strong>Aceite licenças:</strong> 
                    <ul>
                        <li><a href="https://huggingface.co/pyannote/segmentation-3.0" target="_blank">pyannote/segmentation-3.0</a></li>
                        <li><a href="https://huggingface.co/pyannote/speaker-diarization-3.1" target="_blank">pyannote/speaker-diarization-3.1</a></li>
                    </ul>
                </li>
                <li><strong>Suba seu vídeo</strong> (max 500MB)</li>
                <li><strong>Configure idiomas</strong> e token</li>
                <li><strong>Clique em "Iniciar Dublagem"</strong></li>
            </ol>
            
            <h3>⚡ Dicas:</h3>
            <ul>
                <li>🎮 Use GPU para processar mais rápido</li>
                <li>📏 Vídeos menores processam mais rápido</li>
                <li>🔊 Edge TTS é mais rápido</li>
                <li>⏱️ Processo pode demorar alguns minutos</li>
            </ul>
        </div>
        """)
    
    # Eventos
    def on_process_click(video_file, target_lang, hf_token, source_lang, tts_engine, use_gpu):
        if not video_file:
            return None, "❌ Selecione um arquivo de vídeo", "", gr.update(visible=False)
        
        result_file, status, logs = app.process_video(
            video_file, target_lang, hf_token, 
            source_lang, tts_engine, use_gpu
        )
        
        if result_file:
            return result_file, status, logs, gr.update(visible=True, value=result_file)
        else:
            return None, status, logs, gr.update(visible=False)
    
    process_btn.click(
        fn=on_process_click,
        inputs=[video_input, target_lang, hf_token, source_lang, tts_engine, use_gpu],
        outputs=[download_output, status_output, logs_output, download_output]
    )

# Executar aplicação
if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=True,
        inbrowser=True,
        show_error=True
    )
