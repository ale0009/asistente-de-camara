# Hook de intercepción de errores de terminal para NOVA 2.0
# Captura comandos fallidos y ofrece solución proactiva mediante notificaciones nativas de KDE.

nova_preexec() {
    export _NOVA_LAST_CMD="$1"
}

nova_precmd() {
    local exit_code=$?
    # Evitar notificaciones en cancelaciones intencionales (Ctrl+C = 130) o comandos vacíos
    if [ $exit_code -ne 0 ] && [ $exit_code -ne 130 ] && [ $exit_code -ne 148 ] && [ -n "$_NOVA_LAST_CMD" ]; then
        local first_word=$(echo "$_NOVA_LAST_CMD" | awk '{print $1}')
        # Ignorar comandos donde exit code 1 es un resultado de búsqueda normal
        if [[ "$first_word" =~ ^(grep|egrep|fgrep|which|test|\[|diff)$ ]] && [ $exit_code -eq 1 ]; then
            return
        fi

        local current_dir="$(pwd)"
        local timestamp="$(date '+%Y-%m-%d %H:%M:%S')"

        # 1. Guardar buffer para 'nova fix'
        python3 -c "
import json, sys
data = {
    'cmd': sys.argv[1],
    'exit_code': int(sys.argv[2]),
    'cwd': sys.argv[3],
    'timestamp': sys.argv[4]
}
try:
    with open('/tmp/nova_last_error.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)
except Exception:
    pass
" "$_NOVA_LAST_CMD" "$exit_code" "$current_dir" "$timestamp" 2>/dev/null &

        # 2. Notificación proactiva interactiva en KDE con botón de solución inmediata
        (
            local icon_path="/home/alejandro/Datos/Projects/asistente-de-camara/assets/nova_icon.png"
            local action=$(notify-send -a "NOVA Copilot" -i "$icon_path" \
                --action=fix="🔧 Solucionar con IA" \
                "Error en terminal (código $exit_code)" \
                "Fallo en: $_NOVA_LAST_CMD" \
                -t 8000 2>/dev/null)

            if [ "$action" = "fix" ]; then
                konsole -e bash -c "nova fix; echo ''; read -p 'Presiona Enter para cerrar...'"
            fi
        ) & disown
    fi
}

if [[ -z "$_NOVA_HOOK_LOADED" ]]; then
    trap 'nova_preexec "$BASH_COMMAND"' DEBUG
    PROMPT_COMMAND="nova_precmd${PROMPT_COMMAND:+; $PROMPT_COMMAND}"
    export _NOVA_HOOK_LOADED=1
fi
