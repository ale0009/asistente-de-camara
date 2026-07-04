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

    def query(self, prompt: str, model: str = None) -> str:
        """
        Envía un prompt a Ollama y retorna la respuesta.
        Esta llamada es sincrónica y puede bloquear, se recomienda ejecutar en un hilo.
        """
        if not model:
            model = self.default_model
            
        url = f"{self.host}/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False
        }
        
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

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    ollama = OllamaBridge()
    if ollama.check_connection():
        models = ollama.get_models()
        print("Modelos disponibles:", models)
        # print(ollama.query("Hola, ¿puedes escucharme? Responde en una oración."))
