import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config_validator import validate_config


def _valid_config():
    return {
        "camera": {
            "camera_index": 0,
            "resolution": "640x360",
            "osc_host": "127.0.0.1",
            "osc_port": 16284,
        },
        "voice": {"mic_index": 1},
        "gestures": {"enabled": True},
        "obsidian": {
            "vault_path": "D:\\Vault",
            "nova_folder": "NOVA",
            "log_voice_commands": True,
            "log_gestures": False,
        },
    }


def test_valid_config_has_no_errors():
    assert validate_config(_valid_config()) == []


def test_empty_config_reports_all_missing_sections():
    errors = validate_config({})
    assert any("camera:" in e for e in errors)
    assert any("voice:" in e for e in errors)
    assert any("gestures:" in e for e in errors)
    assert any("obsidian:" in e for e in errors)


def test_missing_vault_path_reported():
    cfg = _valid_config()
    del cfg["obsidian"]["vault_path"]

    errors = validate_config(cfg)

    assert any("vault_path" in e for e in errors)


def test_missing_camera_osc_port_reported():
    cfg = _valid_config()
    del cfg["camera"]["osc_port"]

    errors = validate_config(cfg)

    assert any("osc_port" in e for e in errors)


def test_malformed_resolution_reported():
    cfg = _valid_config()
    cfg["camera"]["resolution"] = "640"

    errors = validate_config(cfg)

    assert any("resolution" in e for e in errors)


def test_null_section_reported_as_missing():
    cfg = _valid_config()
    cfg["voice"] = None

    errors = validate_config(cfg)

    assert any("voice:" in e for e in errors)


def test_non_dict_input_returns_error_not_exception():
    assert validate_config(None) != []
    assert validate_config([1, 2, 3]) != []
    assert validate_config("no es un mapa") != []


def test_missing_log_flags_reported():
    cfg = _valid_config()
    del cfg["obsidian"]["log_voice_commands"]
    del cfg["obsidian"]["log_gestures"]

    errors = validate_config(cfg)

    assert any("log_voice_commands" in e for e in errors)
    assert any("log_gestures" in e for e in errors)
