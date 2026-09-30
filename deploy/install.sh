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

# 5. Servicios de usuario en systemd (Daemon y Tray Companion)
mkdir -p "$HOME/.config/systemd/user"
cp "$PROJ_DIR/deploy/nova.service" "$HOME/.config/systemd/user/nova.service"
cp "$PROJ_DIR/deploy/nova-tray.service" "$HOME/.config/systemd/user/nova-tray.service"
systemctl --user daemon-reload
systemctl --user enable --now nova.service
systemctl --user enable --now nova-tray.service
echo "  ✓ Servicios systemd activos: nova.service y nova-tray.service"

# 6. Iconos de aplicación en tema hicolor
mkdir -p "$HOME/.local/share/icons/hicolor/scalable/apps"
cp "$PROJ_DIR/assets/nova.svg" "$HOME/.local/share/icons/hicolor/scalable/apps/nova.svg"
kbuildsycoca6 2>/dev/null || true

echo "==> ¡Despliegue de NOVA 2.0 completado con éxito!"
