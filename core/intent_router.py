import os
import json
import logging

from core.persona import NOVA_IDENTITY

logger = logging.getLogger(__name__)

INTENT_PROMPT = """{identity}

Eres además el clasificador de intención de NOVA. Dado el comando del usuario,
responde ÚNICAMENTE con un JSON válido, sin texto adicional antes o después,
con esta forma:

{{"action": "search_files", "query": "..."}}
{{"action": "write_note", "title": "...", "content": "..."}}
{{"action": "run_command", "command": "..."}}
{{"action": "open_app", "app_name": "..."}}
{{"action": "answer", "text": "..."}}

Reglas:
- "search_files": el usuario pide buscar/encontrar un archivo en el equipo.
- "write_note": el usuario pide anotar/apuntar/tomar nota de algo.
- "run_command": el usuario pide algo que coincide en significado con uno de
  estos comandos ya disponibles (aunque lo diga con otras palabras). Copia el
  texto EXACTO de la lista en "command", nunca inventes uno nuevo:
  {known_commands}
- "open_app": el usuario pide abrir/lanzar un programa o aplicación. Pon en
  "app_name" solo el nombre del programa mencionado.
- "answer": cualquier otra pregunta o conversación — responde tú mismo, breve
  y en español, como si fueras NOVA hablando en voz alta. Si te preguntan qué
  eres o qué puedes hacer, responde según la descripción de ti mismo de arriba.
Incluye solo los campos de la acción elegida.

Comando del usuario: "{command}"
"""


class IntentRouter:
    """
    Fallback para comandos que no matchean los diccionarios fijos del
    CommandDispatcher. Usa el LLM local para clasificar la intención y
    ejecuta la acción real correspondiente (nunca inventa resultados).

    `dispatcher` se asigna después de construirse (ver main.py) porque
    CommandDispatcher necesita una instancia de IntentRouter en su propio
    constructor — evita duplicar los diccionarios de comandos de cámara/
    sistema y la lógica de abrir apps, que ya viven en CommandDispatcher.
    """
    def __init__(self, ollama_bridge, file_tools, dispatcher=None):
        self.ollama = ollama_bridge
        self.files = file_tools
        self.dispatcher = dispatcher

    def _known_commands_text(self) -> str:
        if not self.dispatcher:
            return "(ninguno disponible)"
        keys = list(self.dispatcher.camera_commands.keys()) + list(self.dispatcher.system_commands.keys())
        return ", ".join(keys) if keys else "(ninguno disponible)"

    def route(self, text: str) -> str:
        prompt = INTENT_PROMPT.format(
            identity=NOVA_IDENTITY,
            known_commands=self._known_commands_text(),
            command=text,
        )
        raw = self.ollama.query(prompt, json_mode=True)

        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            logger.warning(f"Ollama no devolvió JSON válido: {raw[:200] if raw else raw}")
            return raw or "No entendí bien ese comando."

        action = data.get("action")

        if action == "search_files":
            return self._handle_search(data.get("query", ""))
        if action == "write_note":
            return self._handle_note(data.get("title", "Nota de voz"), data.get("content", ""))
        if action == "run_command":
            return self._handle_run_command(data.get("command", ""))
        if action == "open_app":
            return self._handle_open_app(data.get("app_name", ""))
        if action == "answer":
            return data.get("text", "").strip() or "No tengo una respuesta para eso."

        logger.warning(f"Acción desconocida del clasificador: {data}")
        return "No entendí ese comando."

    def _handle_run_command(self, command: str) -> str:
        command = (command or "").strip()
        if not self.dispatcher or not command:
            return "No pude identificar qué comando de cámara o sistema ejecutar."

        action = self.dispatcher.camera_commands.get(command) or self.dispatcher.system_commands.get(command)
        if not action:
            logger.warning(f"El clasificador propuso un comando inexistente: '{command}'")
            return "No pude identificar qué comando de cámara o sistema ejecutar."

        logger.info(f"Ejecutando comando (parafraseado -> '{command}') vía IntentRouter")
        result = action()
        return result if isinstance(result, str) else f"Comando {command} ejecutado"

    def _handle_open_app(self, app_name: str) -> str:
        app_name = (app_name or "").strip()
        if not self.dispatcher or not app_name:
            return "¿Qué programa quieres que abra?"
        return self.dispatcher._open_app(app_name)

    def _handle_search(self, query: str) -> str:
        query = (query or "").strip()
        if not query:
            return "¿Qué archivo busco?"
        results = self.files.search_files(query)
        if not results:
            return f"No encontré archivos que coincidan con '{query}' en las carpetas permitidas."
        preview = "; ".join(os.path.basename(p) for p in results[:5])
        extra = f" y {len(results) - 5} más" if len(results) > 5 else ""
        return f"Encontré {len(results)} resultado(s): {preview}{extra}"

    def _handle_note(self, title: str, content: str) -> str:
        content = (content or "").strip()
        if not content:
            return "No entendí qué debía anotar."
        path = self.files.write_note(title or "Nota de voz", content)
        if not path:
            return "No tengo configurado un vault de Obsidian para anotar."
        return f"Anotado en {os.path.basename(path)}"
