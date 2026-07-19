' Lanzador en segundo plano para NOVA (evita consolas de comandos negras en Windows)
Set WshShell = CreateObject("WScript.Shell")
WshShell.Run ".\venv\Scripts\pythonw.exe main.py", 0, False
Set WshShell = Nothing
