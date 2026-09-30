# -*- coding: utf-8 -*-
"""
core/hana_bridge.py — Puente de Integración entre NOVA y Hana
============================================================
Conecta el Asistente NOVA con el orquestador de prompts y dictados de Hana.
Permite consultar dictados disponibles, procesar dictados hacia proyectos
estructurados (estándar cerebro/) y crear notas en Obsidian.
"""

import json
import logging
import os
import subprocess
from pathlib import Path
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

HANA_CLI = Path.home() / ".local" / "bin" / "procesar-hana"
HANA_DICTADOS_DIR = Path.home() / "Documentos" / "Hana" / "dictados"
PROJECTS_DIR = Path.home() / "Datos" / "Projects"
VAULT_DIR = Path.home() / "Datos" / "Vault-Obsidian"

class HanaBridge:
    def __init__(self, dictados_dir: Optional[Path] = None, projects_dir: Optional[Path] = None):
        self.dictados_dir = dictados_dir or HANA_DICTADOS_DIR
        self.projects_dir = projects_dir or PROJECTS_DIR

    def list_dictations(self, limit: int = 5) -> List[Dict]:
        """Obtiene la lista de los últimos dictados disponibles en Hana."""
        if not self.dictados_dir.exists():
            logger.warning(f"Directorio de dictados de Hana no existe: {self.dictados_dir}")
            return []

        archivos = list(self.dictados_dir.glob("*.json"))
        dictados = []
        for a in sorted(archivos, key=lambda x: x.stat().st_mtime, reverse=True)[:limit]:
            try:
                data = json.loads(a.read_text(encoding="utf-8"))
                dictados.append({
                    "number": data.get("number", "?"),
                    "name": data.get("name", a.stem),
                    "date": data.get("date", ""),
                    "text": data.get("text", ""),
                    "file": a.name
                })
            except Exception as e:
                logger.error(f"Error leyendo dictado {a.name}: {e}")
        return dictados

    def get_summary(self) -> str:
        """Genera un resumen natural para que NOVA lo hable y lo muestre."""
        dictados = self.list_dictations(limit=3)
        if not dictados:
            return "No hay dictados pendientes en la bandeja de Hana."

        total = len(list(self.dictados_dir.glob("*.json"))) if self.dictados_dir.exists() else 0
        ultimo = dictados[0]
        num = ultimo.get("number", "1")
        nombre = ultimo.get("name", "Dictado")
        preview = ultimo.get("text", "")[:120].strip()

        resp = f"Hana tiene {total} dictados registrados. El más reciente es el número {num}: '{nombre}'."
        if preview:
            resp += f" Trata sobre: {preview}..."
        return resp

    def process_dictation(self, ident: str) -> str:
        """Ejecuta procesar-hana para convertir un dictado en proyecto bajo el estándar cerebro/."""
        ident_clean = str(ident).strip().replace("#", "")
        logger.info(f"Invocando procesar-hana para dictado: {ident_clean}")
        
        if not HANA_CLI.exists() or not os.access(HANA_CLI, os.X_OK):
            return "El ejecutable de procesar-hana no está disponible en el sistema."

        try:
            cmd = [str(HANA_CLI), "--procesar", ident_clean, "--sin-voz"]
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
            
            if proc.returncode == 0:
                logger.info(f"procesar-hana completado con éxito: {proc.stdout[:200]}")
                return f"Dictado {ident_clean} de Hana procesado exitosamente. Proyecto y nota en Obsidian actualizados."
            else:
                logger.error(f"Error ejecutando procesar-hana: {proc.stderr}")
                return f"Hubo un problema al procesar el dictado {ident_clean} en Hana."
        except subprocess.TimeoutExpired:
            return f"El procesamiento del dictado {ident_clean} tomó demasiado tiempo."
        except Exception as e:
            logger.error(f"Excepción en procesar-hana: {e}")
            return f"Error al procesar dictado de Hana: {e}"

    def create_project(self, name: str, description: str = "") -> str:
        """Crea un proyecto bajo el estándar cerebro/ usando procesar-hana."""
        if not HANA_CLI.exists() or not os.access(HANA_CLI, os.X_OK):
            return "El ejecutable de procesar-hana no está disponible."

        try:
            cmd = [str(HANA_CLI), "--crear-proyecto", name, "--descripcion", description, "--sin-voz"]
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
            if proc.returncode == 0:
                return f"Proyecto {name} creado con éxito bajo el estándar cerebro."
            return f"No se pudo crear el proyecto {name}."
        except Exception as e:
            return f"Error creando proyecto: {e}"

    def open_projects_folder(self) -> str:
        """Abre la carpeta de proyectos en el gestor de archivos."""
        try:
            subprocess.Popen(["xdg-open", str(self.projects_dir)])
            return "Abriendo carpeta de proyectos"
        except Exception as e:
            return f"No se pudo abrir la carpeta de proyectos: {e}"
