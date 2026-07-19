import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.file_tools import FileTools

def test_read_document_found(tmp_path):
    doc_path = tmp_path / "reporte_addons.md"
    doc_path.write_text("# Reporte Addons Blender\n- Addon 1: Auto-Rig\n- Addon 2: HardOps", encoding="utf-8")

    files = FileTools(allowed_folders=[str(tmp_path)])
    res = files.read_document("reporte_addons")

    assert res is not None
    assert "reporte_addons.md" in res
    assert "Auto-Rig" in res

def test_read_document_not_found(tmp_path):
    files = FileTools(allowed_folders=[str(tmp_path)])
    res = files.read_document("documento_inexistente")
    assert res is None
