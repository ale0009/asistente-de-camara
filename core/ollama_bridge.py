import requests
import json
import logging
import os
import time
import yaml
from typing import Tuple, List, Dict, Any, Optional

logger = logging.getLogger(__name__)

HEAVY_MODELS = {
    "qwen3:8b", "qwen2.5-coder:7b", "hermes3:8b", "llama3:8b",
    "deepseek-coder:6.7b", "qwen2.5:7b", "codellama:7b"
}


class OllamaBridge:
    """
    Puente de comunicación híbrido con Ollama (Local + Remoto por Tailscale).
    - Enrutador inteligente: envía modelos ligeros (1.5B/tiny-h) a la GPU local (GTX 1050 3GB).
    - Detecta la presencia de 'pc-principal' (Windows por Tailscale) y delega modelos pesados (8B/visión)
      sin riesgo de colgar el sistema local ni saturar la VRAM.
    - Soporte completo para streaming, visión y fallbacks automáticos.
    """
    def __init__(self, host: str = "http://127.0.0.1:11434", default_model: str = None, config_path: str = "config.yaml"):
        self.local_host = (host or "http://127.0.0.1:11434").rstrip("/")
        self._config = self._load_config(config_path)
        llm_cfg = self._config.get("llm", {})

        # Configuración remota por variable de entorno o config.yaml
        env_remote = os.environ.get("OLLAMA_REMOTE_HOST") or os.environ.get("OLLAMA_HOST_REMOTE")
        self.remote_host = (env_remote or llm_cfg.get("remote_host", "http://pc-principal:11434")).rstrip("/")

        self.default_model = default_model or llm_cfg.get("model", "granite4:tiny-h")
        self.fallback_models = llm_cfg.get("fallback_models", ["qwen2.5-coder:1.5b", "qwen3:1.7b", "qwen3:4b"])
        self.vision_model = llm_cfg.get("vision_model", "qwen3-vl:2b")
        self.temperature = float(llm_cfg.get("temperature", 0.2))

        # Estado y caché del enrutador
        self._cached_local_models: List[str] = []
        self._last_local_fetch = 0.0
        self._remote_online = False
        self._last_remote_check = 0.0

    @property
    def host(self) -> str:
        """Compatibilidad regresiva: devuelve el host local por defecto."""
        return self.local_host

    def _load_config(self, path: str) -> dict:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                logger.warning(f"No se pudo cargar {path} en OllamaBridge: {e}")
        return {}

    def is_remote_available(self, force: bool = False) -> bool:
        """Verifica si el PC principal por Tailscale está respondiendo (sonda de 350ms, caché de 15s)."""
        now = time.time()
        if not force and (now - self._last_remote_check < 15.0):
            return self._remote_online

        try:
            resp = requests.get(f"{self.remote_host}/api/version", timeout=0.35)
            self._remote_online = (resp.status_code == 200)
        except Exception:
            self._remote_online = False

        self._last_remote_check = now
        return self._remote_online

    def check_connection(self) -> bool:
        """Verifica si al menos un servidor de Ollama (local o remoto) está operativo."""
        try:
            resp = requests.get(f"{self.local_host}/api/tags", timeout=1.5)
            if resp.status_code == 200:
                return True
        except requests.exceptions.RequestException:
            pass

        return self.is_remote_available()

    def get_models(self, force_refresh: bool = False) -> list:
        """Devuelve la lista de modelos descargados localmente (caché de 30s)."""
        now = time.time()
        if not force_refresh and self._cached_local_models and (now - self._last_local_fetch < 30.0):
            return self._cached_local_models

        try:
            response = requests.get(f"{self.local_host}/api/tags", timeout=2.5)
            if response.status_code == 200:
                data = response.json()
                self._cached_local_models = [m["name"] for m in data.get("models", [])]
                self._last_local_fetch = now
                return self._cached_local_models
            return self._cached_local_models
        except requests.exceptions.RequestException:
            return self._cached_local_models

    def resolve_endpoint_and_model(self, requested_model: str = None) -> Tuple[str, str]:
        """
        Enrutador Inteligente:
        - Si el modelo solicitado es pesado (8B+, coder:7b) y el PC remoto está online -> (remote_host, requested_model).
        - Si el PC remoto está apagado y se pidió un modelo pesado -> degrada a local_host con modelo ligero.
        - Para modelos rápidos locales -> (local_host, resolved_local_model).
        """
        target = requested_model or self.default_model
        is_heavy = any(target.startswith(h) or h in target for h in HEAVY_MODELS)

        if is_heavy:
            if self.is_remote_available():
                logger.info(f"[Enrutador Híbrido] Despachando modelo pesado '{target}' al PC remoto ({self.remote_host})")
                return self.remote_host, target
            else:
                fallback_local = self.fallback_models[0] if self.fallback_models else "granite4:tiny-h"
                logger.info(f"[Enrutador Híbrido] PC remoto offline; degradando modelo '{target}' a local '{fallback_local}'")
                return self.local_host, self.resolve_model(fallback_local)

        return self.local_host, self.resolve_model(target)

    def resolve_model(self, requested_model: str = None) -> str:
        """Resuelve el mejor modelo disponible localmente con coincidencia y fallback."""
        target = requested_model or self.default_model
        available = self.get_models()

        if not available:
            return target

        for m in available:
            if m == target or m.split(":")[0] == target.split(":")[0]:
                return m

        for fb in self.fallback_models:
            for m in available:
                if m == fb or m.split(":")[0] == fb.split(":")[0]:
                    return m

        return available[0]

    def query(self, prompt: str, model: str = None, json_mode: bool = False, max_tokens: int = 250, system: str = None) -> str:
        """Envía un prompt al host óptimo (local o remoto) y retorna la respuesta."""
        endpoint_host, resolved_model = self.resolve_endpoint_and_model(model)
        url = f"{endpoint_host}/api/generate"
        payload = {
            "model": resolved_model,
            "prompt": prompt,
            "stream": False,
            "keep_alive": "10m",
            "think": False,
            "options": {"num_predict": max_tokens},
        }
        if system:
            payload["system"] = system
        if json_mode:
            payload["format"] = "json"

        try:
            logger.info(f"Consultando Ollama [{endpoint_host}] con {resolved_model}...")
            response = requests.post(url, json=payload, timeout=50)

            if response.status_code == 200:
                data = response.json()
                return data.get("response", "").strip()
            elif response.status_code == 404:
                return f"Modelo '{resolved_model}' no disponible en {endpoint_host}."
            else:
                return f"Error HTTP {response.status_code} desde Ollama."
        except requests.exceptions.RequestException as e:
            logger.error(f"Error de red consultando a Ollama ({endpoint_host}): {e}")
            return "No se pudo conectar con el servidor de inteligencia artificial."

    def query_stream(self, prompt: str, model: str = None, max_tokens: int = 500, system: str = None):
        """Generador asíncrono de tokens para la interfaz HUD o terminal."""
        endpoint_host, resolved_model = self.resolve_endpoint_and_model(model)
        url = f"{endpoint_host}/api/generate"
        payload = {
            "model": resolved_model,
            "prompt": prompt,
            "stream": True,
            "keep_alive": "10m",
            "think": False,
            "options": {"num_predict": max_tokens},
        }
        if system:
            payload["system"] = system

        try:
            logger.info(f"Iniciando streaming con Ollama [{endpoint_host}] ({resolved_model})...")
            response = requests.post(url, json=payload, stream=True, timeout=50)

            if response.status_code == 200:
                for line in response.iter_lines():
                    if line:
                        data = json.loads(line.decode('utf-8'))
                        token = data.get("response", "")
                        if token:
                            yield token
            else:
                yield f"[Error HTTP {response.status_code} al conectar con {endpoint_host}]"
        except requests.exceptions.RequestException as e:
            logger.error(f"Error en streaming de Ollama ({endpoint_host}): {e}")
            yield f"[Error de conexión con {endpoint_host}: {e}]"

    def query_chat(self, messages: list, model: str = None, json_mode: bool = False, max_tokens: int = 350) -> str:
        """Envía historial de conversación al endpoint /api/chat del host óptimo."""
        endpoint_host, resolved_model = self.resolve_endpoint_and_model(model)
        url = f"{endpoint_host}/api/chat"
        payload = {
            "model": resolved_model,
            "messages": messages,
            "stream": False,
            "keep_alive": "10m",
            "think": False,
            "options": {"num_predict": max_tokens},
        }
        if json_mode:
            payload["format"] = "json"

        try:
            response = requests.post(url, json=payload, timeout=50)
            if response.status_code == 200:
                data = response.json()
                return data.get("message", {}).get("content", "").strip()
            return f"Error de chat ({response.status_code}) en {endpoint_host}."
        except requests.exceptions.RequestException as e:
            return f"Error de red en chat: {e}"

    def query_vision(self, prompt: str, image_input, model: str = None, max_tokens: int = 350) -> str:
        """Envía imagen (BGR, bytes o Base64) al modelo de visión."""
        import base64

        # Si el PC remoto está activo, preferir visión remota si está configurada
        endpoint_host = self.remote_host if self.is_remote_available() else self.local_host
        target_model = model or self.vision_model

        url = f"{endpoint_host}/api/generate"
        b64_str = ""
        try:
            if isinstance(image_input, str):
                b64_str = image_input
            elif isinstance(image_input, bytes):
                b64_str = base64.b64encode(image_input).decode('utf-8')
            else:
                # Frame OpenCV
                import cv2
                _, buffer = cv2.imencode('.jpg', image_input, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
                b64_str = base64.b64encode(buffer).decode('utf-8')

            payload = {
                "model": target_model,
                "prompt": prompt,
                "images": [b64_str],
                "stream": False,
                "keep_alive": "5m",
                "options": {"num_predict": max_tokens}
            }
            res = requests.post(url, json=payload, timeout=40)
            if res.status_code == 200:
                return res.json().get("response", "").strip()
            return f"Error en inferencia visual ({res.status_code})."
        except Exception as e:
            logger.error(f"Error en visión multimodal: {e}")
            return f"No se pudo procesar la imagen: {e}"
