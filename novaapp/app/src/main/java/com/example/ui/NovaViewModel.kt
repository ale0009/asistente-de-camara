package com.example.ui

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.example.data.Mission
import com.example.data.NovaDatabase
import com.example.data.NovaRepository
import com.example.data.ObsidianNote
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.flatMapLatest
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

enum class SceneMode(val label: String, val icon: String, val description: String) {
    TRABAJO("Modo Trabajo", "💼", "Tracking humano suave, zoom 1.0x, filtro de ruido alto"),
    PRESENTACION("Modo Presentación", "🎙️", "Tracking rápido, zoom 1.5x, enfoque en rostro"),
    DESCANSO("Modo Descanso", "🌙", "Cámara en reposo, micrófono en espera, bajo consumo")
}

class NovaViewModel(application: Application) : AndroidViewModel(application) {
    private val repository: NovaRepository

    val missions: StateFlow<List<Mission>>
    val recentLogs: StateFlow<List<com.example.data.ActionLogEntry>>
    val allNotes: StateFlow<List<ObsidianNote>>

    private val _searchQuery = MutableStateFlow("")
    val searchQuery = _searchQuery.asStateFlow()

    private val _currentScene = MutableStateFlow(SceneMode.TRABAJO)
    val currentScene = _currentScene.asStateFlow()

    private val _isListening = MutableStateFlow(true)
    val isListening = _isListening.asStateFlow()

    private val _isCameraConnected = MutableStateFlow(true)
    val isCameraConnected = _isCameraConnected.asStateFlow()

    private val _isTrackingActive = MutableStateFlow(true)
    val isTrackingActive = _isTrackingActive.asStateFlow()

    private val _zoomLevel = MutableStateFlow(1.0f)
    val zoomLevel = _zoomLevel.asStateFlow()

    private val _fps = MutableStateFlow(30)
    val fps = _fps.asStateFlow()

    private val _latencyMs = MutableStateFlow(12)
    val latencyMs = _latencyMs.asStateFlow()

    private val _poseAnalysisActive = MutableStateFlow(true)
    val poseAnalysisActive = _poseAnalysisActive.asStateFlow()

    private val _isMicMuted = MutableStateFlow(false)
    val isMicMuted = _isMicMuted.asStateFlow()

    private val _isFloatingHudOpen = MutableStateFlow(false)
    val isFloatingHudOpen = _isFloatingHudOpen.asStateFlow()

    private val _focusTimeLeftSeconds = MutableStateFlow(2700) // 45:00
    val focusTimeLeftSeconds = _focusTimeLeftSeconds.asStateFlow()

    private val _isFocusSprintRunning = MutableStateFlow(false)
    val isFocusSprintRunning = _isFocusSprintRunning.asStateFlow()

    private val _showFocusCompleteModal = MutableStateFlow(false)
    val showFocusCompleteModal = _showFocusCompleteModal.asStateFlow()

    private val _selectedTab = MutableStateFlow(0)
    val selectedTab = _selectedTab.asStateFlow()

    private val _toastMessage = MutableStateFlow<String?>(null)
    val toastMessage = _toastMessage.asStateFlow()

    private val _volumeLevel = MutableStateFlow(80)
    val volumeLevel = _volumeLevel.asStateFlow()

    private val _voiceCommandInput = MutableStateFlow("")
    val voiceCommandInput = _voiceCommandInput.asStateFlow()

    private val _lastAiResponse = MutableStateFlow("")
    val lastAiResponse = _lastAiResponse.asStateFlow()

    private val _panAngle = MutableStateFlow(0.0f)
    val panAngle = _panAngle.asStateFlow()

    private val _tiltAngle = MutableStateFlow(0.0f)
    val tiltAngle = _tiltAngle.asStateFlow()

    private var timerJob: Job? = null

    init {
        val db = NovaDatabase.getDatabase(application, viewModelScope)
        repository = NovaRepository(db)

        missions = repository.allMissions.stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5000),
            initialValue = emptyList()
        )

        recentLogs = repository.recentLogs.stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5000),
            initialValue = emptyList()
        )

        allNotes = _searchQuery.flatMapLatest { query ->
            repository.searchNotes(query)
        }.stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5000),
            initialValue = emptyList()
        )
    }

    fun setTab(tab: Int) {
        _selectedTab.value = tab
    }

    fun setSearchQuery(query: String) {
        _searchQuery.value = query
    }

    fun setVoiceCommandInput(text: String) {
        _voiceCommandInput.value = text
    }

    fun toggleListening() {
        _isListening.value = !_isListening.value
        val state = if (_isListening.value) "ACTIVO" else "EN ESPERA"
        showToast("Reconocimiento de voz: $state")
        logAction("SYSTEM", "OpenWakeWord y Whisper STT: $state")
    }

    fun toggleCameraConnection() {
        _isCameraConnected.value = !_isCameraConnected.value
        val state = if (_isCameraConnected.value) "CONECTADO" else "DESCONECTADO"
        showToast("OBSBOT Tiny 3 Lite: $state")
        logAction("CAMERA_1", "Estado de conexión UVC DirectShow: $state", if (_isCameraConnected.value) "SUCCESS" else "ERROR")
    }

    fun toggleTracking() {
        _isTrackingActive.value = !_isTrackingActive.value
        val status = if (_isTrackingActive.value) "ACTIVADO (ToggleAILock: 1)" else "DESACTIVADO (ToggleAILock: 0)"
        showToast("Seguimiento Humano: ${if (_isTrackingActive.value) "ACTIVO" else "INACTIVO"}")
        logAction("OBSBOT", "OSC /OBSBOT/WebCam/Tiny/ToggleAILock -> $status", "SUCCESS")
    }

    fun wakeCamera() {
        _isCameraConnected.value = true
        _isTrackingActive.value = true
        showToast("Cámara Despertada ☀️")
        logAction("OBSBOT", "OSC /OBSBOT/WebCam/Tiny/Sleep -> 0 (Wake)", "SUCCESS")
    }

    fun sleepCamera() {
        _isTrackingActive.value = false
        showToast("Cámara en Reposo 🌙")
        logAction("OBSBOT", "OSC /OBSBOT/WebCam/Tiny/Sleep -> 1 (Standby)", "INFO")
    }

    fun captureSnapshot() {
        val timeStr = SimpleDateFormat("HH-mm-ss", Locale.getDefault()).format(Date())
        showToast("Captura guardada: snapshot_$timeStr.png")
        logAction("CAMERA_1", "Captura de pantalla tomada en alta resolución (4K)", "SUCCESS")
    }

    fun toggleMicMute() {
        _isMicMuted.value = !_isMicMuted.value
        val status = if (_isMicMuted.value) "SILENCIADO 🔇" else "ACTIVADO 🎙️"
        showToast("Micrófono: $status")
        logAction("SYSTEM", "Estado de entrada de audio cambiado a: $status")
    }

    fun adjustVolume(delta: Int) {
        val newVol = (_volumeLevel.value + delta).coerceIn(0, 100)
        _volumeLevel.value = newVol
        showToast("Volumen: $newVol%")
        logAction("SYSTEM", "desktop_set_volume -> $newVol%")
    }

    fun setZoom(zoom: Float) {
        val rounded = (zoom * 10).toInt() / 10.0f
        _zoomLevel.value = rounded.coerceIn(1.0f, 4.0f)
        logAction("OBSBOT", "OSC /OBSBOT/WebCam/Tiny/SetZoom -> ${rounded}x")
    }

    fun panTilt(deltaPan: Float, deltaTilt: Float) {
        _panAngle.value = (_panAngle.value + deltaPan).coerceIn(-129f, 129f)
        _tiltAngle.value = (_tiltAngle.value + deltaTilt).coerceIn(-59f, 59f)
        logAction("OBSBOT", "OSC /OBSBOT/WebCam/Tiny/SetPanTilt -> Pan: ${_panAngle.value}°, Tilt: ${_tiltAngle.value}°")
    }

    fun resetGimbal() {
        _panAngle.value = 0f
        _tiltAngle.value = 0f
        _zoomLevel.value = 1.0f
        showToast("Gimbal reajustado a posición central")
        logAction("OBSBOT", "OSC Gimbal Reset -> Pan: 0°, Tilt: 0°, Zoom: 1.0x")
    }

    fun togglePoseAnalysis() {
        _poseAnalysisActive.value = !_poseAnalysisActive.value
        showToast("Análisis de Postura: ${if (_poseAnalysisActive.value) "ACTIVO" else "DESACTIVADO"}")
        logAction("AI_CORE", "MediaPipe Pose & HandLandmarker: ${_poseAnalysisActive.value}")
    }

    fun toggleFloatingHud() {
        _isFloatingHudOpen.value = !_isFloatingHudOpen.value
    }

    fun selectScene(scene: SceneMode) {
        _currentScene.value = scene
        showToast("Escena cambiada: ${scene.label}")
        logAction("SYSTEM", "Escena aplicada: ${scene.label} - ${scene.description}", "SUCCESS")
        when (scene) {
            SceneMode.TRABAJO -> {
                _zoomLevel.value = 1.0f
                _isTrackingActive.value = true
            }
            SceneMode.PRESENTACION -> {
                _zoomLevel.value = 1.5f
                _isTrackingActive.value = true
            }
            SceneMode.DESCANSO -> {
                _zoomLevel.value = 1.0f
                _isTrackingActive.value = false
            }
        }
    }

    fun executeVoiceCommand(input: String? = null) {
        val cmd = (input ?: _voiceCommandInput.value).trim()
        if (cmd.isBlank()) return
        _voiceCommandInput.value = ""

        viewModelScope.launch {
            logAction("CMD", cmd)
            val lower = cmd.lowercase()
            when {
                lower.contains("despierta") || lower.contains("encender") -> wakeCamera()
                lower.contains("parar") || lower.contains("deten") || lower.contains("apaga") -> sleepCamera()
                lower.contains("acerc") || lower.contains("zoom in") -> setZoom(_zoomLevel.value + 0.5f)
                lower.contains("alej") || lower.contains("zoom out") -> setZoom(_zoomLevel.value - 0.5f)
                lower.contains("sígueme") || lower.contains("trackear") -> {
                    _isTrackingActive.value = true
                    logAction("OBSBOT", "OSC ToggleAILock -> 1", "SUCCESS")
                    showToast("Seguimiento iniciado")
                }
                lower.contains("busca") || lower.contains("obsidian") -> {
                    val term = cmd.replace("busca", "", ignoreCase = true).replace("en obsidian", "", ignoreCase = true).trim()
                    _searchQuery.value = term
                    _selectedTab.value = 3
                    _lastAiResponse.value = "Buscando '$term' en notas de Obsidian Vault..."
                    logAction("MCP", "vault_search('$term')", "SUCCESS")
                }
                lower.contains("abre") -> {
                    val app = cmd.replace("abre", "", ignoreCase = true).trim()
                    showToast("Lanzando aplicación: $app")
                    logAction("MCP", "desktop_launch_app('$app')", "SUCCESS")
                    _lastAiResponse.value = "Iniciando $app en segundo plano."
                }
                lower.contains("modo trabajo") -> selectScene(SceneMode.TRABAJO)
                lower.contains("modo presentación") || lower.contains("modo presentacion") -> selectScene(SceneMode.PRESENTACION)
                lower.contains("modo descanso") -> selectScene(SceneMode.DESCANSO)
                lower.contains("silencio") || lower.contains("mutear") -> toggleMicMute()
                else -> {
                    _lastAiResponse.value = "NOVA Agent: Entendido '$cmd'. Invocando modelo local qwen3:8b vía Ollama HTTP..."
                    delay(400)
                    logAction("AI_CORE", "Respuesta Ollama: Procesado comando agéntico correctamente", "SUCCESS")
                }
            }
        }
    }

    fun toggleMission(mission: Mission) {
        viewModelScope.launch {
            val updated = mission.copy(isCompleted = !mission.isCompleted)
            repository.updateMission(updated)
            val state = if (updated.isCompleted) "Completada ✅" else "Pendiente"
            showToast("Misión '${mission.title}': $state")
            logAction("COMMAND", "task_update --id=${mission.id} --status=${if (updated.isCompleted) "complete" else "pending"}", "SUCCESS")
        }
    }

    fun addMission(title: String, time: String = "12:00 PM") {
        if (title.isBlank()) return
        viewModelScope.launch {
            val newMission = Mission(title = title, time = time, isCompleted = false)
            repository.insertMission(newMission)
            showToast("Misión agregada: $title")
            logAction("SYSTEM", "Misión creada: $title ($time)")
        }
    }

    fun resetMissions() {
        viewModelScope.launch {
            repository.resetAllMissions()
            showToast("Progreso de misiones reiniciado")
            logAction("SYSTEM", "Progreso diario reiniciado")
        }
    }

    fun startFocusSprint() {
        _isFocusSprintRunning.value = true
        _showFocusCompleteModal.value = false
        timerJob?.cancel()
        timerJob = viewModelScope.launch {
            logAction("SYSTEM", "Focus Sprint de 45:00 iniciado. Distraction-Free: ON")
            while (_focusTimeLeftSeconds.value > 0 && _isFocusSprintRunning.value) {
                delay(1000)
                _focusTimeLeftSeconds.value--
            }
            if (_focusTimeLeftSeconds.value <= 0) {
                _isFocusSprintRunning.value = false
                _showFocusCompleteModal.value = true
                logAction("AI_CORE", "Deep Work Session Complete! 0 Distractions. Status: Optimized", "SUCCESS")
            }
        }
    }

    fun pauseFocusSprint() {
        _isFocusSprintRunning.value = false
        timerJob?.cancel()
        logAction("SYSTEM", "Focus Sprint pausado en ${formatTime(_focusTimeLeftSeconds.value)}")
    }

    fun resetFocusSprint() {
        _isFocusSprintRunning.value = false
        timerJob?.cancel()
        _focusTimeLeftSeconds.value = 2700
        _showFocusCompleteModal.value = false
    }

    fun dismissFocusModal() {
        _showFocusCompleteModal.value = false
    }

    fun updateObsidianNote(note: ObsidianNote, newContent: String) {
        viewModelScope.launch {
            try {
                repository.updateNote(note.copy(content = newContent, updatedAt = System.currentTimeMillis()))
                showToast("Nota '${note.title}' actualizada")
                logAction("MCP", "vault_write_note('${note.title}')", "SUCCESS")
            } catch (e: Exception) {
                showToast("⚠️ ${e.message}")
                logAction("MCP", "OverwriteError: ${e.message}", "ERROR")
            }
        }
    }

    fun clearLogs() {
        viewModelScope.launch {
            repository.clearLogs()
        }
    }

    private fun logAction(source: String, message: String, type: String = "INFO") {
        viewModelScope.launch {
            repository.addLog(source, message, type)
        }
    }

    fun showToast(msg: String) {
        _toastMessage.value = msg
    }

    fun dismissToast() {
        _toastMessage.value = null
    }

    private fun formatTime(seconds: Int): String {
        val m = seconds / 60
        val s = seconds % 60
        return String.format(Locale.getDefault(), "%02d:%02d", m, s)
    }
}
