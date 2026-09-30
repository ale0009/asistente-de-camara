#!/usr/bin/env bash
# ==============================================================================
# Script de Instalación y Despliegue de NOVA 2.0 (Copiloto de Estación de Trabajo)
# ==============================================================================
set -e

PROJ_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "==> Desplegando NOVA 2.0 en el entorno de usuario..."

# 1. Enlace global a CLI
mkdir -p "$HOME/.local/bin"
cat << 'EOF' > "$HOME/.local/bin/nova"
#!/usr/bin/env bash
cd /home/alejandro/Datos/Projects/asistente-de-camara
exec .venv/bin/python -m core.cli_handler "$@"
EOF
chmod +x "$HOME/.local/bin/nova"
echo "  ✓ CLI instalado en ~/.local/bin/nova"

# 2. Hook de Bash para interceptar errores de terminal
mkdir -p "$HOME/.bashrc.d"
cp "$PROJ_DIR/core/terminal_hook.bash" "$HOME/.bashrc.d/nova-hook.bash"
chmod +x "$HOME/.bashrc.d/nova-hook.bash"
echo "  ✓ Hook de terminal instalado en ~/.bashrc.d/nova-hook.bash"

# 3. Lanzador .desktop para KDE Plasma
mkdir -p "$HOME/.local/share/applications"
cp "$PROJ_DIR/deploy/nova.desktop" "$HOME/.local/share/applications/nova.desktop"
chmod +x "$HOME/.local/share/applications/nova.desktop"
echo "  ✓ Lanzador instalado en ~/.local/share/applications/nova.desktop"

# 4. Atajo Global en KDE Plasma (Meta+Space)
if command -v kwriteconfig6 >/dev/null 2>&1; then
    kwriteconfig6 --file kglobalshortcutsrc --group "services" --group "nova.desktop" --key "_launch" "Meta+Space"
    if command -v qdbus-qt6 >/dev/null 2>&1; then
        qdbus-qt6 org.kde.KWin /KWin reconfigure 2>/dev/null || true
    fi
    echo "  ✓ Atajo global configurado en KDE Plasma: Meta+Space"
fi

# 5. Servicio de usuario en systemd
mkdir -p "$HOME/.config/systemd/user"
cp "$PROJ_DIR/deploy/nova.service" "$HOME/.config/systemd/user/nova.service"
systemctl --user daemon-reload
systemctl --user enable --now nova.service
echo "  ✓ Servicio systemd activo: nova.service"

# 6. Icono residente en la bandeja del sistema (autostart)
mkdir -p "$HOME/.config/autostart"
cp "$PROJ_DIR/deploy/nova-tray.desktop" "$HOME/.config/autostart/nova-tray.desktop"
chmod +x "$HOME/.config/autostart/nova-tray.desktop"
echo "  ✓ Autostart de la bandeja instalado en ~/.config/autostart/nova-tray.desktop"

echo "==> ¡Despliegue de NOVA 2.0 completado con éxito!"
