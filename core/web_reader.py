# -*- coding: utf-8 -*-
import logging
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class WebReader:
    """
    Descarga y limpia el contenido de páginas web para extraer texto legible.
    """
    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    def read_url(self, url: str, max_chars: int = 8000) -> str:
        """Descarga la URL, remueve HTML irrelevante y devuelve el texto limpio."""
        url = url.strip()
        if not url.startswith("http://") and not url.startswith("https://"):
            return "URL inválida. Debe comenzar con http:// o https://"

        try:
            logger.info(f"Descargando URL: {url}")
            r = requests.get(url, headers=self.headers, timeout=self.timeout)
            if r.status_code != 200:
                logger.warning(f"Error descargando {url}: HTTP {r.status_code}")
                return f"Error al acceder a la página: HTTP {r.status_code}"

            # Intentar detectar la codificación correcta
            if r.encoding is None or r.encoding == 'ISO-8859-1':
                r.encoding = r.apparent_encoding

            soup = BeautifulSoup(r.text, "html.parser")

            # Eliminar scripts, estilos, menús de navegación, pies de página, cabeceras, formularios, etc.
            for tag in soup(["script", "style", "nav", "footer", "header", "form", "aside", "noscript"]):
                tag.decompose()

            # Extraer texto
            text = soup.get_text(separator="\n")

            # Normalizar espacios y saltos de línea
            lines = [line.strip() for line in text.splitlines()]
            chunks = [phrase.strip() for line in lines for phrase in line.split("  ")]
            clean_text = "\n".join(chunk for chunk in chunks if chunk)

            # Limitar longitud para evitar desbordar el contexto del LLM
            if len(clean_text) > max_chars:
                clean_text = clean_text[:max_chars] + "\n\n[... Contenido truncado por longitud ...]"

            logger.info(f"URL {url} procesada con éxito. Longitud: {len(clean_text)} caracteres.")
            return clean_text or "No se pudo extraer texto legible de esta página."

        except Exception as e:
            logger.exception(f"Error leyendo URL {url}")
            return f"Error al intentar leer la página: {str(e)}"
