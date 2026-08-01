import requests
import json
import logging

logger = logging.getLogger(__name__)

class OllamaBridge:
    """
    Puente de comunicación local con Ollama (LLM local).
    Permite hacer preguntas complejas sin necesidad de internet.
    """
    def __init__(self, host="http://127.0.0.1:11434", default_model="qwen3:8b"):
        self.host = host
        self.default_model = default_model
        
    def check_connection(self) -> bool:
        """Verifica si el servidor de Ollama está corriendo."""
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=2)
            if response.status_code == 200:
                logger.info("Conexión con Ollama establecida.")
                return True
            return False
        except requests.exceptions.RequestException:
            logger.warning("Ollama no está disponible localmente.")
            return False

    def get_models(self):
        """Devuelve la lista de modelos descargados en Ollama."""
        try:
            response = requests.get(f"{self.host}/api/tags")
            if response.status_code == 200:
                data = response.json()
                return [model["name"] for model in data.get("models", [])]
            return []
        except requests.exceptions.RequestException:
            return []

    def query(self, prompt: str, model: str = None, json_mode: bool = False, max_tokens: int = 220, system: str = None) -> str:
        """
        Envía un prompt a Ollama y retorna la respuesta.
        Esta llamada es sincrónica y puede bloquear, se recomienda ejecutar en un hilo.
        json_mode=True le pide a Ollama que restrinja la salida a JSON válido
        (usado por IntentRouter para clasificar comandos libres).
        max_tokens limita el largo de la respuesta — NOVA es un asistente de voz,
        las respuestas deben tardar segundos, no minutos, incluso con preguntas abiertas.
        """
        if not model:
            model = self.default_model

        url = f"{self.host}/api/generate"
        payload = {
            "model": model,
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
            logger.info(f"Consultando a Ollama ({model}): {prompt[:50]}...")
            response = requests.post(url, json=payload, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                reply = data.get("response", "").strip()
                logger.info(f"Respuesta de Ollama recibida ({len(reply)} chars)")
                return reply
            elif response.status_code == 404:
                logger.error(f"Error de Ollama HTTP 404: Modelo '{model}' no encontrado.")
                # Intentar fallback a modelos que el usuario podría tener
                return f"No tengo instalado el modelo {model}. Por favor, abre tu consola y ejecuta: ollama run {model}"
            else:
                logger.error(f"Error de Ollama HTTP {response.status_code}")
                return "Hubo un error al consultar la inteligencia artificial local."
                
        except requests.exceptions.Timeout:
            logger.error("Ollama tardó demasiado en responder (Timeout).")
            return "La respuesta de la inteligencia artificial tardó demasiado."
        except requests.exceptions.RequestException as e:
            logger.error(f"Error de red consultando a Ollama: {e}")
            return "No me pude conectar con el servidor local de Ollama."

    def query_chat(self, messages: list, model: str = None, json_mode: bool = False, max_tokens: int = 300) -> str:
        """
        Envía un historial de mensajes (lista de dicts con role y content)
        al endpoint /api/chat de Ollama y retorna el texto de la respuesta.
        """
        if not model:
            model = self.default_model

        url = f"{self.host}/api/chat"
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "keep_alive": "10m",
            "think": False,
            "options": {"num_predict": max_tokens},
        }
        if json_mode:
            payload["format"] = "json"

        try:
            logger.info(f"Enviando chat a Ollama ({model}) con {len(messages)} mensajes...")
            response = requests.post(url, json=payload, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                reply = data.get("message", {}).get("content", "").strip()
                logger.info(f"Respuesta de chat de Ollama recibida ({len(reply)} chars)")
                return reply
            else:
                logger.error(f"Error de Ollama chat HTTP {response.status_code}")
                return "Hubo un error de comunicación con la IA local."
        except requests.exceptions.RequestException as e:
            logger.error(f"Error de red consultando a Ollama chat: {e}")
            return "No me pude conectar con el servidor local de Ollama."

    def query_stream(self, prompt: str, model: str = None, max_tokens: int = 220):
        """
        Envía un prompt a Ollama con stream=True y va cediendo los fragmentos
        de texto (tokens) a medida que llegan.
        Esta llamada es asíncrona mediante generadores (yield) y debe consumirse
        en un hilo adecuado para no bloquear la UI.
        """
        if not model:
            model = self.default_model

        url = f"{self.host}/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": True,
            "keep_alive": "10m",
            "think": False,
            "options": {"num_predict": max_tokens},
        }

        try:
            logger.info(f"Consultando a Ollama en modo stream ({model})...")
            response = requests.post(url, json=payload, stream=True, timeout=60)
            
            if response.status_code == 200:
                for line in response.iter_lines():
                    if line:
                        data = json.loads(line.decode('utf-8'))
                        token = data.get("response", "")
                        if token:
                            yield token
        except requests.exceptions.RequestException as e:
            logger.error(f"Error de red consultando a Ollama en stream: {e}")
            yield "No me pude conectar con el servidor local de Ollama."

    def query_vision(self, prompt: str, image_input, model: str = "moondream", max_tokens: int = 150) -> str:
        """
        Envía una imagen (frame BGR de OpenCV, bytes JPEG o string Base64) junto a un prompt
        al modelo multimodal de Ollama (ej. 'moondream') y devuelve la descripción en texto.
        """
        import base64
        
        url = f"{self.host}/api/generate"
        b64_str = ""

        try:
            if isinstance(image_input, str):
                b64_str = image_input
            elif isinstance(image_input, bytes):
                b64_str = base64.b64encode(image_input).decode('utf-8')
            elif hasattr(image_input, "shape"):  # Numpy array (OpenCV BGR frame)
                import cv2
                success, encoded_img = cv2.imencode('.jpg', image_input)
                if success:
                    b64_str = base64.b64encode(encoded_img.tobytes()).decode('utf-8')
                else:
                    return "No se pudo procesar la imagen de la cámara."
            else:
                return "Formato de imagen no soportado para análisis visual."
        except Exception as e:
            logger.error(f"Error codificando imagen para visión: {e}")
            return "Ocurrió un error al preparar la imagen."

        payload = {
            "model": model,
            "prompt": prompt,
            "images": [b64_str],
            "stream": False,
            "keep_alive": "10m",
            "think": False,
            "options": {"num_predict": max_tokens}
        }

        try:
            logger.info(f"Enviando consulta visual a Ollama ({model}): '{prompt}'...")
            response = requests.post(url, json=payload, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                reply = data.get("response", "").strip()
                logger.info(f"Respuesta de visión recibida ({len(reply)} chars)")
                return reply
            elif response.status_code == 404:
                logger.error(f"Modelo de visión '{model}' no encontrado en Ollama.")
                return f"No encontré el modelo de visión {model}. Ejecuta: ollama pull {model}"
            else:
                logger.error(f"Error HTTP {response.status_code} en Ollama visión.")
                return "Hubo un fallo en la inferencia visual."
        except requests.exceptions.Timeout:
            logger.error("Timeout consultando el modelo de visión.")
            return "El análisis de la imagen tardó demasiado."
        except requests.exceptions.RequestException as e:
            logger.error(f"Error de red en visión: {e}")
            return "No me pude conectar con el servicio local de visión."


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    ollama = OllamaBridge()
    if ollama.check_connection():
        models = ollama.get_models()
        print("Modelos disponibles:", models)
        # print(ollama.query("Hola, ¿puedes escucharme? Responde en una oración."))
