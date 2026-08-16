package com.example

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.viewModels
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Checklist
import androidx.compose.material.icons.filled.Dashboard
import androidx.compose.material.icons.filled.FolderSpecial
import androidx.compose.material.icons.filled.Insights
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.Icon
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.NavigationBarItemDefaults
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.example.ui.NovaViewModel
import com.example.ui.components.FloatingHudOverlayModal
import com.example.ui.components.NovaHeader
import com.example.ui.components.NovaToast
import com.example.ui.screens.CommandCenterScreen
import com.example.ui.screens.DailyMissionsScreen
import com.example.ui.screens.ObsidianVaultScreen
import com.example.ui.screens.SettingsScreen
import com.example.ui.screens.WarriorStatsScreen
import com.example.ui.theme.MyApplicationTheme
import com.example.ui.theme.NovaBgCanvas
import com.example.ui.theme.NovaBgDarkNavy
import com.example.ui.theme.NovaCyan
import com.example.ui.theme.NovaCyanBorder
import com.example.ui.theme.NovaCyanGlow
import com.example.ui.theme.NovaSurfaceCard
import com.example.ui.theme.NovaTextDim
import com.example.ui.theme.NovaTextWhite

class MainActivity : ComponentActivity() {
    private val viewModel: NovaViewModel by viewModels()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            MyApplicationTheme {
                NovaAppContent(viewModel = viewModel)
            }
        }
    }
}

@Composable
fun NovaAppContent(viewModel: NovaViewModel) {
    val selectedTab by viewModel.selectedTab.collectAsStateWithLifecycle()
    val currentScene by viewModel.currentScene.collectAsStateWithLifecycle()
    val isListening by viewModel.isListening.collectAsStateWithLifecycle()
    val isCameraConnected by viewModel.isCameraConnected.collectAsStateWithLifecycle()
    val isTrackingActive by viewModel.isTrackingActive.collectAsStateWithLifecycle()
    val zoomLevel by viewModel.zoomLevel.collectAsStateWithLifecycle()
    val fps by viewModel.fps.collectAsStateWithLifecycle()
    val latencyMs by viewModel.latencyMs.collectAsStateWithLifecycle()
    val poseAnalysisActive by viewModel.poseAnalysisActive.collectAsStateWithLifecycle()
    val isMicMuted by viewModel.isMicMuted.collectAsStateWithLifecycle()
    val isFloatingHudOpen by viewModel.isFloatingHudOpen.collectAsStateWithLifecycle()
    val focusTimeLeftSeconds by viewModel.focusTimeLeftSeconds.collectAsStateWithLifecycle()
    val isFocusSprintRunning by viewModel.isFocusSprintRunning.collectAsStateWithLifecycle()
    val showFocusCompleteModal by viewModel.showFocusCompleteModal.collectAsStateWithLifecycle()
    val toastMessage by viewModel.toastMessage.collectAsStateWithLifecycle()
    val voiceCommandInput by viewModel.voiceCommandInput.collectAsStateWithLifecycle()
    val searchQuery by viewModel.searchQuery.collectAsStateWithLifecycle()
    val panAngle by viewModel.panAngle.collectAsStateWithLifecycle()
    val tiltAngle by viewModel.tiltAngle.collectAsStateWithLifecycle()

    val missions by viewModel.missions.collectAsStateWithLifecycle()
    val recentLogs by viewModel.recentLogs.collectAsStateWithLifecycle()
    val allNotes by viewModel.allNotes.collectAsStateWithLifecycle()

    Scaffold(
        topBar = {
            NovaHeader(
                currentScene = currentScene,
                isListening = isListening,
                onSceneSelect = { viewModel.selectScene(it) },
                onOpenFloatingHud = { viewModel.toggleFloatingHud() }
            )
        },
        bottomBar = {
            NavigationBar(
                containerColor = NovaBgDarkNavy,
                tonalElevation = 8.dp,
                modifier = Modifier
                    .fillMaxWidth()
                    .border(width = 1.dp, color = NovaCyanBorder.copy(alpha = 0.2f))
            ) {
                val navItems = listOf(
                    NavItem("HUD", Icons.Default.Dashboard, 0, "nav_item_hud"),
                    NavItem("Misiones", Icons.Default.Checklist, 1, "nav_item_missions"),
                    NavItem("Stats", Icons.Default.Insights, 2, "nav_item_stats"),
                    NavItem("Obsidian", Icons.Default.FolderSpecial, 3, "nav_item_obsidian"),
                    NavItem("Ajustes", Icons.Default.Settings, 4, "nav_item_settings")
                )

                navItems.forEach { item ->
                    val isSelected = selectedTab == item.index
                    NavigationBarItem(
                        selected = isSelected,
                        onClick = { viewModel.setTab(item.index) },
                        icon = {
                            Icon(
                                imageVector = item.icon,
                                contentDescription = item.label,
                                tint = if (isSelected) NovaCyan else NovaTextDim,
                                modifier = Modifier.size(20.dp)
                            )
                        },
                        label = {
                            Text(
                                text = item.label,
                                color = if (isSelected) NovaCyan else NovaTextDim,
                                fontSize = 10.sp,
                                fontWeight = if (isSelected) FontWeight.Bold else FontWeight.Normal,
                                fontFamily = FontFamily.Monospace
                            )
                        },
                        colors = NavigationBarItemDefaults.colors(
                            indicatorColor = NovaCyanGlow
                        ),
                        modifier = Modifier.testTag(item.testTag)
                    )
                }
            }
        },
        containerColor = NovaBgCanvas
    ) { innerPadding ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
        ) {
            // Main Tab View Routing
            when (selectedTab) {
                0 -> CommandCenterScreen(
                    isConnected = isCameraConnected,
                    isTrackingActive = isTrackingActive,
                    zoomLevel = zoomLevel,
                    fps = fps,
                    latencyMs = latencyMs,
                    poseAnalysisActive = poseAnalysisActive,
                    panAngle = panAngle,
                    tiltAngle = tiltAngle,
                    logs = recentLogs,
                    missions = missions,
                    commandInput = voiceCommandInput,
                    isListening = isListening,
                    onToggleTracking = { viewModel.toggleTracking() },
                    onZoomChange = { viewModel.setZoom(it) },
                    onPanTilt = { dx, dy -> viewModel.panTilt(dx, dy) },
                    onResetGimbal = { viewModel.resetGimbal() },
                    onTogglePoseAnalysis = { viewModel.togglePoseAnalysis() },
                    onRetryConnection = { viewModel.toggleCameraConnection() },
                    onCommandInputChange = { viewModel.setVoiceCommandInput(it) },
                    onSendCommand = { viewModel.executeVoiceCommand() },
                    onToggleMic = { viewModel.toggleMicMute() },
                    onToggleMission = { viewModel.toggleMission(it) },
                    onNavToMissions = { viewModel.setTab(1) },
                    onNavToStats = { viewModel.setTab(2) }
                )
                1 -> DailyMissionsScreen(
                    missions = missions,
                    focusTimeLeftSeconds = focusTimeLeftSeconds,
                    isFocusSprintRunning = isFocusSprintRunning,
                    showFocusCompleteModal = showFocusCompleteModal,
                    onToggleMission = { viewModel.toggleMission(it) },
                    onAddMission = { title, time -> viewModel.addMission(title, time) },
                    onResetMissions = { viewModel.resetMissions() },
                    onStartFocusSprint = { viewModel.startFocusSprint() },
                    onPauseFocusSprint = { viewModel.pauseFocusSprint() },
                    onResetFocusSprint = { viewModel.resetFocusSprint() },
                    onDismissFocusModal = { viewModel.dismissFocusModal() }
                )
                2 -> WarriorStatsScreen(
                    onExportToObsidian = {
                        viewModel.showToast("Métricas exportadas a Sesiones/2026-07-31.md")
                        viewModel.setTab(3)
                    }
                )
                3 -> ObsidianVaultScreen(
                    notes = allNotes,
                    searchQuery = searchQuery,
                    onSearchQueryChange = { viewModel.setSearchQuery(it) },
                    onSaveNote = { note, newContent -> viewModel.updateObsidianNote(note, newContent) }
                )
                4 -> SettingsScreen(
                    onClearLogs = { viewModel.clearLogs() },
                    onShowToast = { viewModel.showToast(it) }
                )
            }

            // HUD Toast Notifications overlay
            NovaToast(
                message = toastMessage,
                onDismiss = { viewModel.dismissToast() },
                modifier = Modifier.align(Alignment.TopCenter)
            )

            // 1:1 Floating HUD Window Popup Modal
            FloatingHudOverlayModal(
                isOpen = isFloatingHudOpen,
                isTrackingActive = isTrackingActive,
                isListening = isListening,
                zoomLevel = zoomLevel,
                isMicMuted = isMicMuted,
                onDismiss = { viewModel.toggleFloatingHud() },
                onWakeCamera = { viewModel.wakeCamera() },
                onToggleTracking = { viewModel.toggleTracking() },
                onStopCamera = { viewModel.sleepCamera() },
                onCapture = { viewModel.captureSnapshot() },
                onToggleMic = { viewModel.toggleMicMute() },
                onVolumeUp = { viewModel.adjustVolume(10) },
                onVolumeDown = { viewModel.adjustVolume(-10) },
                onOpenConfig = {
                    viewModel.toggleFloatingHud()
                    viewModel.setTab(4)
                },
                onOpenObsidian = {
                    viewModel.toggleFloatingHud()
                    viewModel.setTab(3)
                },
                onOpenHelp = {
                    viewModel.showToast("Comandos de voz: 'sígueme', 'despierta', 'parar', 'zoom in', 'busca [nota]'")
                }
            )
        }
    }
}

data class NavItem(
    val label: String,
    val icon: ImageVector,
    val index: Int,
    val testTag: String
)

