import os
import json
import logging
from duckduckgo_search import DDGS

from core.persona import NOVA_IDENTITY

logger = logging.getLogger(__name__)

INTENT_PROMPT = """{identity}

Eres además el clasificador de intención de NOVA. Dado el comando del usuario,
responde ÚNICAMENTE con un JSON válido, sin texto adicional antes o después,
con esta forma:

{{"action": "search_files", "query": "..."}}
{{"action": "read_document", "target": "...", "question": "..."}}
{{"action": "run_command", "command": "..."}}
{{"action": "open_app", "app_name": "..."}}
{{"action": "research", "topic": "..."}}
{{"action": "answer"}}

Reglas:
- "search_files": el usuario pide buscar/encontrar la ubicación de un archivo en el equipo.
- "read_document": el usuario pide leer, consultar, resumir o preguntar qué dice un documento, nota de Obsidian o reporte específico (ej. "qué dice el reporte de addons", "lee la nota X").
- "write_note": el usuario pide anotar/apuntar/tomar nota de algo.
- "run_command": el usuario pide algo que coincide en significado con uno de
  estos comandos ya disponibles (aunque lo diga con otras palabras). Copia el
  texto EXACTO de la lista en "command", nunca inventes uno nuevo:
  {known_commands}
- "open_app": el usuario pide abrir/lanzar un programa o aplicación. Pon en
  "app_name" solo el nombre del programa mencionado.
- "research": el usuario pide explícitamente investigar, buscar en internet, buscar en la web, o realizar una investigación o reporte sobre un tema (ej. "investiga sobre X", "busca en internet qué es Y"). Pon el tema de investigación en "topic".
- "answer": cualquier otra pregunta o conversación general, saludo o charla. No agregues campos adicionales de texto en este JSON.
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
        if action == "read_document":
            return self._handle_read_document(data.get("target", ""), data.get("question", text))
        if action == "write_note":
            return self._handle_note(data.get("title", "Nota de voz"), data.get("content", ""))
        if action == "run_command":
            return self._handle_run_command(data.get("command", ""))
        if action == "open_app":
            return self._handle_open_app(data.get("app_name", ""))
        if action == "research":
            return self._handle_research(data.get("topic", ""))
        if action == "answer":
            ans_prompt = (
                f"{NOVA_IDENTITY}\n"
                f"Responde a esta pregunta o conversación del usuario, de forma concisa "
                f"(máximo 3 oraciones) y en español: {text}"
            )
            if self.dispatcher:
                tokens = self.ollama.query_stream(ans_prompt)
                return self.dispatcher._stream_sentences(tokens)
            else:
                return self.ollama.query(ans_prompt)

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

    def _handle_read_document(self, target: str, question: str = ""):
        target = (target or "").strip()
        if not target:
            return "¿Qué documento quieres que lea?"
        doc_text = self.files.read_document(target)
        if not doc_text:
            return f"No encontré el documento '{target}' en tus carpetas autorizadas o vault de Obsidian."
        
        rag_prompt = (
            f"{NOVA_IDENTITY}\n"
            f"Con base en la siguiente información del documento:\n{doc_text}\n\n"
            f"Responde a esta pregunta o solicitud del usuario en voz alta, de forma concisa y en español: {question or 'Resume qué dice este documento.'}"
        )
        
        if self.dispatcher:
            tokens = self.ollama.query_stream(rag_prompt)
            return self.dispatcher._stream_sentences(tokens)
        else:
            return self.ollama.query(rag_prompt)

    def _handle_research(self, topic: str):
        topic = (topic or "").strip()
        if not topic:
            return "No especificaste qué tema investigar."

        def _research_stream():
            yield f"Entendido, estoy iniciando una investigación en internet sobre {topic}. Por favor espera un momento..."
            
            try:
                # 1. Generar sub-búsquedas para Ollama
                sub_queries_prompt = (
                    f"Necesito investigar sobre: {topic}.\n"
                    f"Genera exactamente 2 términos de búsqueda concisos para buscar en Google/DuckDuckGo en español.\n"
                    f"Responde ÚNICAMENTE con los 2 términos separados por salto de línea, sin números ni texto adicional."
                )
                raw_queries = self.ollama.query(sub_queries_prompt)
                queries = [q.strip() for q in raw_queries.split("\n") if q.strip()]
                if not queries:
                    queries = [topic]
                else:
                    queries = queries[:3]
                
                logger.info(f"Sub-búsquedas generadas para investigación: {queries}")
                
                # 2. Buscar en DuckDuckGo
                search_results = []
                with DDGS() as ddgs:
                    for query in queries:
                        try:
                            results = ddgs.text(query, max_results=4)
                            for r in results:
                                search_results.append({
                                    "title": r.get("title", ""),
                                    "link": r.get("href", ""),
                                    "snippet": r.get("body", "")
                                })
                        except Exception as e:
                            logger.error(f"Error buscando en DDG para '{query}': {e}")
                
                if not search_results:
                    yield "No logré obtener resultados de internet para esta investigación."
                    return
                
                # 3. Compilar los snippets recopilados
                compiled_context = ""
                for idx, res in enumerate(search_results[:8]):
                    compiled_context += f"--- Fuente [{idx+1}]: {res['title']} ({res['link']}) ---\n{res['snippet']}\n\n"
                
                # 4. Generar el reporte Markdown vía Ollama
                report_prompt = (
                    f"{NOVA_IDENTITY}\n"
                    f"Eres un agente de investigación experto. Has recopilado la siguiente información de internet "
                    f"sobre el tema: '{topic}':\n\n"
                    f"{compiled_context}\n"
                    f"Escribe un reporte de investigación detallado en Markdown. "
                    f"Debe ser claro, profesional y estructurado con secciones (Introducción, Avances Clave, Conclusiones y Fuentes). "
                    f"Utiliza español de manera impecable."
                )
                report_markdown = self.ollama.query(report_prompt)
                
                # 5. Escribir reporte en Obsidian
                safe_title = "".join(c for c in topic if c.isalnum() or c in " -_").strip() or "Investigacion"
                filename = f"Investigacion - {safe_title}"
                obsidian_folder = "NOVA/Investigaciones"
                
                notes_dir = os.path.join(self.files.vault_path, obsidian_folder)
                os.makedirs(notes_dir, exist_ok=True)
                file_path = os.path.join(notes_dir, f"{filename}.md")
                
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(report_markdown)
                
                logger.info(f"Reporte de investigación guardado en {file_path}")
                
                # 6. Generar una breve lectura final en streaming
                summary_prompt = (
                    f"{NOVA_IDENTITY}\n"
                    f"Con base en el reporte que acabas de escribir:\n{report_markdown[:2000]}\n\n"
                    f"Resume en 2 o 3 oraciones concisas y fáciles de entender en voz alta los hallazgos principales, "
                    f"mencionando que has guardado el reporte en tu Obsidian."
                )
                tokens = self.ollama.query_stream(summary_prompt)
                for sentence in self.dispatcher._stream_sentences(tokens):
                    yield sentence
                    
            except Exception as e:
                logger.exception("Error durante la investigación agentica")
                yield "Hubo un error al realizar la investigación en internet."

        if self.dispatcher:
            return _research_stream()
        else:
            # Síncrono fallback
            return f"No tengo configurado el dispatcher para streaming de investigación."
