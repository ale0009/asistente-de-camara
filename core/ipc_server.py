# -*- coding: utf-8 -*-
"""
Servidor IPC UNIX para NOVA (core/ipc_server.py).
Permite comunicación instantánea de baja latencia (<5ms) entre clientes CLI,
atajos globales de teclado, hooks de shell y el daemon de fondo.
"""
import os
import sys
import json
import asyncio
import logging
from pathlib import Path
from typing import Callable, Dict, Any

logger = logging.getLogger("NOVA.IPC")

DEFAULT_SOCKET_PATH = "/tmp/nova.sock"


class NovaIPCServer:
    def __init__(self, socket_path: str = DEFAULT_SOCKET_PATH):
        self.socket_path = socket_path
        self.server: asyncio.Server = None
        self.handlers: Dict[str, Callable] = {}
        self.is_running = False

    def register_handler(self, action: str, handler: Callable):
        """Registra una función para atender una acción específica enviada por el socket."""
        self.handlers[action] = handler
        logger.debug(f"Manejador IPC registrado para acción: '{action}'")

    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        try:
            raw_data = await asyncio.wait_for(reader.read(65536), timeout=10.0)
            if not raw_data:
                writer.close()
                await writer.wait_closed()
                return

            text = raw_data.decode("utf-8").strip()
            logger.info(f"Mensaje IPC recibido: {text[:120]}...")

            try:
                request = json.loads(text)
            except json.JSONDecodeError:
                request = {"action": "query", "text": text}

            action = request.get("action", "query")
            handler = self.handlers.get(action)

            if handler:
                if asyncio.iscoroutinefunction(handler):
                    result = await handler(request)
                else:
                    loop = asyncio.get_running_loop()
                    result = await loop.run_in_executor(None, handler, request)
                response = {"status": "success", "result": result}
            else:
                response = {"status": "error", "message": f"Acción desconocida: '{action}'"}

            data_out = json.dumps(response, ensure_ascii=False).encode("utf-8")
            writer.write(data_out)
            await writer.drain()

        except asyncio.TimeoutError:
            logger.warning("Timeout atendiendo petición IPC de cliente.")
        except Exception as e:
            logger.error(f"Error procesando cliente IPC: {e}")
            try:
                err_resp = json.dumps({"status": "error", "message": str(e)}).encode("utf-8")
                writer.write(err_resp)
                await writer.drain()
            except Exception:
                pass
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass

    async def start(self):
        """Inicia el servidor de socket UNIX."""
        # Limpiar socket previo si quedó huérfano
        if os.path.exists(self.socket_path):
            try:
                os.remove(self.socket_path)
            except OSError as e:
                logger.error(f"No se pudo limpiar socket previo {self.socket_path}: {e}")

        self.server = await asyncio.start_unix_server(self._handle_client, path=self.socket_path)
        # Permisos exclusivos para el usuario (0600)
        try:
            os.chmod(self.socket_path, 0o600)
        except Exception:
            pass

        self.is_running = True
        logger.info(f"Servidor IPC UNIX de NOVA escuchando en: {self.socket_path}")

    async def stop(self):
        """Detiene el servidor y elimina el archivo de socket."""
        self.is_running = False
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        if os.path.exists(self.socket_path):
            try:
                os.remove(self.socket_path)
            except OSError:
                pass
        logger.info("Servidor IPC UNIX detenido.")


def send_ipc_command(request_data: Dict[str, Any], socket_path: str = DEFAULT_SOCKET_PATH, timeout: float = 8.0) -> Dict[str, Any]:
    """Función cliente síncrona para que CLI o scripts envíen comandos al daemon."""
    import socket
    if not os.path.exists(socket_path):
        return {"status": "error", "message": "El daemon de NOVA no está en ejecución (socket no encontrado)."}

    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client.settimeout(timeout)
    try:
        client.connect(socket_path)
        payload = json.dumps(request_data, ensure_ascii=False).encode("utf-8")
        client.sendall(payload)
        
        chunks = []
        while True:
            data = client.recv(4096)
            if not data:
                break
            chunks.append(data)
        raw_resp = b"".join(chunks).decode("utf-8")
        if raw_resp:
            return json.loads(raw_resp)
        return {"status": "error", "message": "Respuesta vacía del daemon."}
    except socket.timeout:
        return {"status": "error", "message": "Timeout esperando respuesta de NOVA."}
    except Exception as e:
        return {"status": "error", "message": f"Fallo comunicando con NOVA: {e}"}
    finally:
        client.close()
