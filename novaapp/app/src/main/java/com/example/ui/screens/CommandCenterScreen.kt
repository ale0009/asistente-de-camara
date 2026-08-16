package com.example.ui.screens

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.RadioButtonUnchecked
import androidx.compose.material3.Checkbox
import androidx.compose.material3.CheckboxDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.data.ActionLogEntry
import com.example.data.Mission
import com.example.ui.components.ActionLogTerminal
import com.example.ui.components.CameraVideoFeed
import com.example.ui.theme.NovaBgDarkNavy
import com.example.ui.theme.NovaCyan
import com.example.ui.theme.NovaCyanBorder
import com.example.ui.theme.NovaCyanGlow
import com.example.ui.theme.NovaLavender
import com.example.ui.theme.NovaSurfaceCard
import com.example.ui.theme.NovaTextDim
import com.example.ui.theme.NovaTextWhite

@Composable
fun CommandCenterScreen(
    isConnected: Boolean,
    isTrackingActive: Boolean,
    zoomLevel: Float,
    fps: Int,
    latencyMs: Int,
    poseAnalysisActive: Boolean,
    panAngle: Float,
    tiltAngle: Float,
    logs: List<ActionLogEntry>,
    missions: List<Mission>,
    commandInput: String,
    isListening: Boolean,
    onToggleTracking: () -> Unit,
    onZoomChange: (Float) -> Unit,
    onPanTilt: (Float, Float) -> Unit,
    onResetGimbal: () -> Unit,
    onTogglePoseAnalysis: () -> Unit,
    onRetryConnection: () -> Unit,
    onCommandInputChange: (String) -> Unit,
    onSendCommand: () -> Unit,
    onToggleMic: () -> Unit,
    onToggleMission: (Mission) -> Unit,
    onNavToMissions: () -> Unit,
    onNavToStats: () -> Unit,
    modifier: Modifier = Modifier
) {
    Column(
        modifier = modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        // Top Cards Grid: Overall Mastery & Focus Streak
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            // Overall Mastery Card (Ring Gauge)
            Box(
                modifier = Modifier
                    .weight(1f)
                    .clip(RoundedCornerShape(14.dp))
                    .background(NovaSurfaceCard)
                    .border(1.dp, NovaCyanBorder.copy(alpha = 0.3f), RoundedCornerShape(14.dp))
                    .clickable { onNavToStats() }
                    .padding(14.dp)
            ) {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Text(
                        text = "Overall Mastery",
                        color = NovaTextWhite,
                        fontWeight = FontWeight.Bold,
                        fontSize = 13.sp
                    )

                    Spacer(modifier = Modifier.height(10.dp))

                    // Gauge Ring Canvas
                    Box(
                        modifier = Modifier.size(72.dp),
                        contentAlignment = Alignment.Center
                    ) {
                        Canvas(modifier = Modifier.fillMaxSize()) {
                            // Inactive Ring Track
                            drawCircle(
                                color = Color(0x1A00E5FF),
                                style = Stroke(width = 8.dp.toPx())
                            )
                            // Active 78% Arc
                            drawArc(
                                color = Color(0xFF00E5FF),
                                startAngle = -90f,
                                sweepAngle = 360f * 0.78f,
                                useCenter = false,
                                style = Stroke(width = 8.dp.toPx())
                            )
                        }

                        Text(
                            text = "78%",
                            color = NovaCyan,
                            fontWeight = FontWeight.Bold,
                            fontSize = 18.sp,
                            fontFamily = FontFamily.Monospace
                        )
                    }

                    Spacer(modifier = Modifier.height(10.dp))

                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceAround
                    ) {
                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                            Text(text = "Strength", color = NovaTextDim, fontSize = 9.sp)
                            Text(text = "82%", color = NovaTextWhite, fontSize = 10.sp, fontWeight = FontWeight.Bold)
                        }
                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                            Text(text = "Focus", color = NovaTextDim, fontSize = 9.sp)
                            Text(text = "75%", color = NovaTextWhite, fontSize = 10.sp, fontWeight = FontWeight.Bold)
                        }
                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                            Text(text = "Endurance", color = NovaTextDim, fontSize = 9.sp)
                            Text(text = "79%", color = NovaTextWhite, fontSize = 10.sp, fontWeight = FontWeight.Bold)
                        }
                    }
                }
            }

            // Focus Streak Crystal Card
            Box(
                modifier = Modifier
                    .weight(1f)
                    .clip(RoundedCornerShape(14.dp))
                    .background(NovaSurfaceCard)
                    .border(1.dp, NovaCyanBorder.copy(alpha = 0.3f), RoundedCornerShape(14.dp))
                    .padding(14.dp)
            ) {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Text(
                        text = "Focus Streak",
                        color = NovaTextWhite,
                        fontWeight = FontWeight.Bold,
                        fontSize = 13.sp
                    )

                    Spacer(modifier = Modifier.height(10.dp))

                    // Crystal Badge Graphic Box
                    Box(
                        modifier = Modifier
                            .size(72.dp)
                            .clip(CircleShape)
                            .background(NovaCyanGlow)
                            .border(1.dp, NovaLavender, CircleShape),
                        contentAlignment = Alignment.Center
                    ) {
                        Text(
                            text = "💎",
                            fontSize = 32.sp
                        )
                    }

                    Spacer(modifier = Modifier.height(10.dp))

                    Text(
                        text = "Current: 14 Days",
                        color = NovaCyan,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold,
                        fontFamily = FontFamily.Monospace
                    )
                    Text(
                        text = "Best: 30 Days",
                        color = NovaTextDim,
                        fontSize = 10.sp,
                        fontFamily = FontFamily.Monospace
                    )
                }
            }
        }

        // Live Video Feed Container
        CameraVideoFeed(
            isConnected = isConnected,
            isTrackingActive = isTrackingActive,
            zoomLevel = zoomLevel,
            fps = fps,
            latencyMs = latencyMs,
            poseAnalysisActive = poseAnalysisActive,
            panAngle = panAngle,
            tiltAngle = tiltAngle,
            onToggleTracking = onToggleTracking,
            onZoomChange = onZoomChange,
            onPanTilt = onPanTilt,
            onResetGimbal = onResetGimbal,
            onTogglePoseAnalysis = onTogglePoseAnalysis,
            onRetryConnection = onRetryConnection
        )

        // Action Log Terminal
        ActionLogTerminal(
            logs = logs,
            commandInput = commandInput,
            isListening = isListening,
            onCommandInputChange = onCommandInputChange,
            onSendCommand = onSendCommand,
            onToggleMic = onToggleMic
        )

        // Daily Missions Checklist Summary Card
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(14.dp))
                .background(NovaSurfaceCard)
                .border(1.dp, NovaCyanBorder.copy(alpha = 0.3f), RoundedCornerShape(14.dp))
                .padding(14.dp)
        ) {
            Column {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "Daily Missions",
                        color = NovaTextWhite,
                        fontWeight = FontWeight.Bold,
                        fontSize = 14.sp
                    )

                    Text(
                        text = "Ver Todo →",
                        color = NovaCyan,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold,
                        modifier = Modifier
                            .clickable { onNavToMissions() }
                            .padding(4.dp)
                    )
                }

                Spacer(modifier = Modifier.height(10.dp))

                missions.take(5).forEach { mission ->
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .clickable { onToggleMission(mission) }
                            .padding(vertical = 4.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Checkbox(
                            checked = mission.isCompleted,
                            onCheckedChange = { onToggleMission(mission) },
                            colors = CheckboxDefaults.colors(
                                checkedColor = NovaCyan,
                                checkmarkColor = NovaBgDarkNavy,
                                uncheckedColor = NovaTextDim
                            ),
                            modifier = Modifier.size(20.dp).testTag("mission_checkbox_${mission.id}")
                        )

                        Spacer(modifier = Modifier.width(10.dp))

                        Text(
                            text = mission.time,
                            color = NovaCyan,
                            fontSize = 11.sp,
                            fontFamily = FontFamily.Monospace,
                            fontWeight = FontWeight.Bold
                        )

                        Spacer(modifier = Modifier.width(8.dp))

                        Text(
                            text = " - ${mission.title}",
                            color = if (mission.isCompleted) NovaTextDim else NovaTextWhite,
                            fontSize = 12.sp
                        )
                    }
                }
            }
        }
    }
}
