package com.example.ui.components

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.ArrowDownward
import androidx.compose.material.icons.filled.ArrowForward
import androidx.compose.material.icons.filled.ArrowUpward
import androidx.compose.material.icons.filled.CenterFocusStrong
import androidx.compose.material.icons.filled.CenterFocusWeak
import androidx.compose.material.icons.filled.Remove
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Slider
import androidx.compose.material3.SliderDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.ui.theme.NovaBgDarkNavy
import com.example.ui.theme.NovaCyan
import com.example.ui.theme.NovaCyanBorder
import com.example.ui.theme.NovaCyanGlow
import com.example.ui.theme.NovaDangerBg
import com.example.ui.theme.NovaDangerBorder
import com.example.ui.theme.NovaDangerText
import com.example.ui.theme.NovaLavender
import com.example.ui.theme.NovaSurfaceCard
import com.example.ui.theme.NovaTextDim
import com.example.ui.theme.NovaTextWhite

@Composable
fun CameraVideoFeed(
    isConnected: Boolean,
    isTrackingActive: Boolean,
    zoomLevel: Float,
    fps: Int,
    latencyMs: Int,
    poseAnalysisActive: Boolean,
    panAngle: Float,
    tiltAngle: Float,
    onToggleTracking: () -> Unit,
    onZoomChange: (Float) -> Unit,
    onPanTilt: (Float, Float) -> Unit,
    onResetGimbal: () -> Unit,
    onTogglePoseAnalysis: () -> Unit,
    onRetryConnection: () -> Unit,
    modifier: Modifier = Modifier
) {
    var showGimbalControls by remember { mutableStateOf(false) }

    Column(
        modifier = modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(12.dp))
            .background(NovaSurfaceCard)
            .border(1.dp, NovaCyanBorder.copy(alpha = 0.3f), RoundedCornerShape(12.dp))
            .padding(12.dp)
    ) {
        // Video Title Bar
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(
                    text = "FEED CÁMARA 16:9",
                    color = NovaTextWhite,
                    fontWeight = FontWeight.Bold,
                    fontSize = 12.sp,
                    fontFamily = FontFamily.Monospace,
                    letterSpacing = 1.sp
                )
                Spacer(modifier = Modifier.width(8.dp))
                Box(
                    modifier = Modifier
                        .clip(RoundedCornerShape(4.dp))
                        .background(if (isConnected) NovaCyanGlow else NovaDangerBg)
                        .padding(horizontal = 6.dp, vertical = 2.dp)
                ) {
                    Text(
                        text = if (isConnected) "DirectShow OBSBOT" else "Sin Señal",
                        color = if (isConnected) NovaCyan else NovaDangerText,
                        fontSize = 9.sp,
                        fontFamily = FontFamily.Monospace
                    )
                }
            }

            Row(verticalAlignment = Alignment.CenterVertically) {
                Box(
                    modifier = Modifier
                        .clip(RoundedCornerShape(6.dp))
                        .background(if (poseAnalysisActive) NovaCyanGlow else NovaBgDarkNavy)
                        .border(1.dp, if (poseAnalysisActive) NovaCyanBorder else NovaCyanBorder.copy(alpha = 0.2f), RoundedCornerShape(6.dp))
                        .clickable { onTogglePoseAnalysis() }
                        .padding(horizontal = 8.dp, vertical = 4.dp)
                ) {
                    Text(
                        text = if (poseAnalysisActive) "Pose: ON" else "Pose: OFF",
                        color = if (poseAnalysisActive) NovaCyan else NovaTextDim,
                        fontSize = 10.sp,
                        fontFamily = FontFamily.Monospace
                    )
                }

                Spacer(modifier = Modifier.width(6.dp))

                Box(
                    modifier = Modifier
                        .clip(RoundedCornerShape(6.dp))
                        .background(if (showGimbalControls) NovaCyanGlow else NovaBgDarkNavy)
                        .border(1.dp, NovaCyanBorder, RoundedCornerShape(6.dp))
                        .clickable { showGimbalControls = !showGimbalControls }
                        .padding(horizontal = 8.dp, vertical = 4.dp)
                ) {
                    Text(
                        text = if (showGimbalControls) "Gimbal ✖" else "Gimbal PTZ",
                        color = NovaCyan,
                        fontSize = 10.sp,
                        fontFamily = FontFamily.Monospace
                    )
                }
            }
        }

        Spacer(modifier = Modifier.height(8.dp))

        // 16:9 Video Canvas Box
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .aspectRatio(16f / 9f)
                .clip(RoundedCornerShape(8.dp))
                .background(Color(0xFF0A1326))
                .border(1.dp, NovaCyanBorder.copy(alpha = 0.25f), RoundedCornerShape(8.dp))
        ) {
            if (isConnected) {
                // Interactive HUD Canvas Drawing Keypoints & Target Mesh
                Canvas(modifier = Modifier.fillMaxSize()) {
                    val w = size.width
                    val h = size.height

                    // Corner HUD Reticle Lines
                    val reticleLen = 20.dp.toPx()
                    val reticleColor = Color(0x6600E5FF)
                    val strokeW = 1.5.dp.toPx()

                    // Top Left
                    drawLine(reticleColor, Offset(12.dp.toPx(), 12.dp.toPx()), Offset(12.dp.toPx() + reticleLen, 12.dp.toPx()), strokeW)
                    drawLine(reticleColor, Offset(12.dp.toPx(), 12.dp.toPx()), Offset(12.dp.toPx(), 12.dp.toPx() + reticleLen), strokeW)

                    // Top Right
                    drawLine(reticleColor, Offset(w - 12.dp.toPx(), 12.dp.toPx()), Offset(w - 12.dp.toPx() - reticleLen, 12.dp.toPx()), strokeW)
                    drawLine(reticleColor, Offset(w - 12.dp.toPx(), 12.dp.toPx()), Offset(w - 12.dp.toPx(), 12.dp.toPx() + reticleLen), strokeW)

                    // Bottom Left
                    drawLine(reticleColor, Offset(12.dp.toPx(), h - 12.dp.toPx()), Offset(12.dp.toPx() + reticleLen, h - 12.dp.toPx()), strokeW)
                    drawLine(reticleColor, Offset(12.dp.toPx(), h - 12.dp.toPx()), Offset(12.dp.toPx(), h - 12.dp.toPx() - reticleLen), strokeW)

                    // Bottom Right
                    drawLine(reticleColor, Offset(w - 12.dp.toPx(), h - 12.dp.toPx()), Offset(w - 12.dp.toPx() - reticleLen, h - 12.dp.toPx()), strokeW)
                    drawLine(reticleColor, Offset(w - 12.dp.toPx(), h - 12.dp.toPx()), Offset(w - 12.dp.toPx(), h - 12.dp.toPx() - reticleLen), strokeW)

                    // Human Subject AI Bounding Box & Target Mesh
                    if (isTrackingActive) {
                        val boxLeft = w * 0.35f + (panAngle * 0.8f)
                        val boxTop = h * 0.20f + (tiltAngle * 0.8f)
                        val boxW = w * 0.30f / (zoomLevel * 0.8f).coerceAtLeast(0.5f)
                        val boxH = h * 0.65f / (zoomLevel * 0.8f).coerceAtLeast(0.5f)

                        // Outer Cyan Bounding Box
                        drawRect(
                            color = Color(0x9900E5FF),
                            topLeft = Offset(boxLeft, boxTop),
                            size = Size(boxW, boxH),
                            style = Stroke(width = 2.dp.toPx())
                        )

                        // Target Lock Corners
                        val cornerSize = 12.dp.toPx()
                        drawRect(Color(0xFF00E5FF), Offset(boxLeft - 2, boxTop - 2), Size(cornerSize, 3.dp.toPx()))
                        drawRect(Color(0xFF00E5FF), Offset(boxLeft - 2, boxTop - 2), Size(3.dp.toPx(), cornerSize))

                        drawRect(Color(0xFF00E5FF), Offset(boxLeft + boxW - cornerSize + 2, boxTop - 2), Size(cornerSize, 3.dp.toPx()))
                        drawRect(Color(0xFF00E5FF), Offset(boxLeft + boxW - 2, boxTop - 2), Size(3.dp.toPx(), cornerSize))

                        // Head Landmark Dot
                        drawCircle(Color(0xFF00E5FF), radius = 4.dp.toPx(), center = Offset(boxLeft + boxW * 0.5f, boxTop + boxH * 0.2f))

                        if (poseAnalysisActive) {
                            // Pose Skeleton Overlay Lines (Shoulders, Arms, Hands)
                            val leftShoulder = Offset(boxLeft + boxW * 0.25f, boxTop + boxH * 0.35f)
                            val rightShoulder = Offset(boxLeft + boxW * 0.75f, boxTop + boxH * 0.35f)
                            val headCenter = Offset(boxLeft + boxW * 0.5f, boxTop + boxH * 0.2f)
                            val leftElbow = Offset(boxLeft + boxW * 0.15f, boxTop + boxH * 0.55f)
                            val rightElbow = Offset(boxLeft + boxW * 0.85f, boxTop + boxH * 0.55f)
                            val leftWrist = Offset(boxLeft + boxW * 0.20f, boxTop + boxH * 0.75f)
                            val rightWrist = Offset(boxLeft + boxW * 0.80f, boxTop + boxH * 0.75f)

                            val skeletonColor = Color(0xB3BED2FF)
                            val nodeColor = Color(0xFF00E5FF)

                            drawLine(skeletonColor, headCenter, Offset(boxLeft + boxW * 0.5f, boxTop + boxH * 0.35f), 1.5.dp.toPx())
                            drawLine(skeletonColor, leftShoulder, rightShoulder, 1.5.dp.toPx())
                            drawLine(skeletonColor, leftShoulder, leftElbow, 1.5.dp.toPx())
                            drawLine(skeletonColor, rightShoulder, rightElbow, 1.5.dp.toPx())
                            drawLine(skeletonColor, leftElbow, leftWrist, 1.5.dp.toPx())
                            drawLine(skeletonColor, rightElbow, rightWrist, 1.5.dp.toPx())

                            // Draw Skeleton Nodes
                            drawCircle(nodeColor, 3.dp.toPx(), leftShoulder)
                            drawCircle(nodeColor, 3.dp.toPx(), rightShoulder)
                            drawCircle(nodeColor, 3.dp.toPx(), leftElbow)
                            drawCircle(nodeColor, 3.dp.toPx(), rightElbow)
                            drawCircle(nodeColor, 4.dp.toPx(), leftWrist)
                            drawCircle(nodeColor, 4.dp.toPx(), rightWrist)
                        }
                    }
                }

                // Top Left Overlay Chips: FPS & Latency
                Row(
                    modifier = Modifier
                        .align(Alignment.TopStart)
                        .padding(8.dp),
                    horizontalArrangement = Arrangement.spacedBy(6.dp)
                ) {
                    Box(
                        modifier = Modifier
                            .clip(RoundedCornerShape(4.dp))
                            .background(Color(0xCC000000))
                            .border(1.dp, NovaCyanBorder.copy(alpha = 0.3f), RoundedCornerShape(4.dp))
                            .padding(horizontal = 6.dp, vertical = 2.dp)
                    ) {
                        Text(
                            text = "FPS: $fps",
                            color = NovaCyan,
                            fontSize = 9.sp,
                            fontFamily = FontFamily.Monospace
                        )
                    }

                    Box(
                        modifier = Modifier
                            .clip(RoundedCornerShape(4.dp))
                            .background(Color(0xCC000000))
                            .border(1.dp, NovaCyanBorder.copy(alpha = 0.3f), RoundedCornerShape(4.dp))
                            .padding(horizontal = 6.dp, vertical = 2.dp)
                    ) {
                        Text(
                            text = "Latency: ${latencyMs}ms",
                            color = NovaCyan,
                            fontSize = 9.sp,
                            fontFamily = FontFamily.Monospace
                        )
                    }
                }

                // Top Right Overlay Badge: Activity
                Box(
                    modifier = Modifier
                        .align(Alignment.TopEnd)
                        .padding(8.dp)
                        .clip(RoundedCornerShape(4.dp))
                        .background(Color(0xCC000000))
                        .border(1.dp, NovaCyanBorder.copy(alpha = 0.3f), RoundedCornerShape(4.dp))
                        .padding(horizontal = 8.dp, vertical = 3.dp)
                ) {
                    Text(
                        text = "Activity: Deep Work",
                        color = NovaLavender,
                        fontSize = 9.sp,
                        fontFamily = FontFamily.Monospace
                    )
                }

                // Bottom Left Overlay Chips: Tracking & Zoom (Matching Design Spec Images 1:1)
                Row(
                    modifier = Modifier
                        .align(Alignment.BottomStart)
                        .padding(8.dp),
                    horizontalArrangement = Arrangement.spacedBy(6.dp)
                ) {
                    // Tracking Chip
                    Row(
                        modifier = Modifier
                            .clip(RoundedCornerShape(6.dp))
                            .background(Color(0xCC000000))
                            .border(
                                1.dp,
                                if (isTrackingActive) NovaCyanBorder else NovaCyanBorder.copy(alpha = 0.2f),
                                RoundedCornerShape(6.dp)
                            )
                            .clickable { onToggleTracking() }
                            .padding(horizontal = 8.dp, vertical = 4.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(
                            text = "▶ Tracking: ",
                            color = NovaTextDim,
                            fontSize = 10.sp,
                            fontFamily = FontFamily.Monospace
                        )
                        Text(
                            text = if (isTrackingActive) "Humano" else "Inactivo",
                            color = if (isTrackingActive) NovaCyan else NovaTextDim,
                            fontSize = 10.sp,
                            fontFamily = FontFamily.Monospace,
                            fontWeight = FontWeight.Bold
                        )
                    }

                    // Zoom Chip
                    Row(
                        modifier = Modifier
                            .clip(RoundedCornerShape(6.dp))
                            .background(Color(0xCC000000))
                            .border(1.dp, NovaCyanBorder.copy(alpha = 0.3f), RoundedCornerShape(6.dp))
                            .padding(horizontal = 8.dp, vertical = 4.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(
                            text = "⊕ Zoom: ",
                            color = NovaTextDim,
                            fontSize = 10.sp,
                            fontFamily = FontFamily.Monospace
                        )
                        Text(
                            text = "${String.format("%.1f", zoomLevel)}x",
                            color = NovaCyan,
                            fontSize = 10.sp,
                            fontFamily = FontFamily.Monospace,
                            fontWeight = FontWeight.Bold
                        )
                    }
                }
            } else {
                // Connection Error State overlay (Matching Design Spec Image)
                Column(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(16.dp),
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.Center
                ) {
                    Icon(
                        imageVector = Icons.Default.Warning,
                        contentDescription = "Camera Warning",
                        tint = NovaDangerText,
                        modifier = Modifier.size(36.dp)
                    )
                    Spacer(modifier = Modifier.height(8.dp))
                    Text(
                        text = "Camera Connection Lost",
                        color = NovaTextWhite,
                        fontWeight = FontWeight.Bold,
                        fontSize = 14.sp
                    )
                    Spacer(modifier = Modifier.height(4.dp))
                    Text(
                        text = "Check your USB connection or driver status [ERR_DEVICE_TIMEOUT]",
                        color = NovaTextDim,
                        fontSize = 11.sp,
                        fontFamily = FontFamily.Monospace
                    )
                    Spacer(modifier = Modifier.height(12.dp))
                    Button(
                        onClick = onRetryConnection,
                        colors = ButtonDefaults.buttonColors(
                            containerColor = NovaDangerBg,
                            contentColor = NovaDangerText
                        ),
                        border = BorderStroke(1.dp, NovaDangerBorder),
                        shape = RoundedCornerShape(6.dp)
                    ) {
                        Text(text = "Retry", fontSize = 12.sp, fontFamily = FontFamily.Monospace)
                    }
                }
            }
        }

        // Optional Gimbal D-Pad & Zoom Controller Expandable Panel
        AnimatedVisibility(visible = showGimbalControls && isConnected) {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(top = 12.dp)
                    .clip(RoundedCornerShape(8.dp))
                    .background(NovaBgDarkNavy)
                    .border(1.dp, NovaCyanBorder.copy(alpha = 0.3f), RoundedCornerShape(8.dp))
                    .padding(12.dp)
            ) {
                Text(
                    text = "CONTROL GIMBAL PTZ (Pan: ${panAngle.toInt()}° | Tilt: ${tiltAngle.toInt()}°)",
                    color = NovaCyan,
                    fontSize = 10.sp,
                    fontFamily = FontFamily.Monospace,
                    fontWeight = FontWeight.Bold
                )

                Spacer(modifier = Modifier.height(8.dp))

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    // D-Pad Gimbal Navigation
                    Box(
                        modifier = Modifier
                            .size(100.dp)
                            .background(NovaSurfaceCard, CircleShape)
                            .border(1.dp, NovaCyanBorder.copy(alpha = 0.4f), CircleShape),
                        contentAlignment = Alignment.Center
                    ) {
                        // Up
                        IconButton(
                            onClick = { onPanTilt(0f, 5f) },
                            modifier = Modifier.align(Alignment.TopCenter).size(28.dp)
                        ) {
                            Icon(Icons.Default.ArrowUpward, "Tilt Up", tint = NovaCyan)
                        }
                        // Down
                        IconButton(
                            onClick = { onPanTilt(0f, -5f) },
                            modifier = Modifier.align(Alignment.BottomCenter).size(28.dp)
                        ) {
                            Icon(Icons.Default.ArrowDownward, "Tilt Down", tint = NovaCyan)
                        }
                        // Left
                        IconButton(
                            onClick = { onPanTilt(-5f, 0f) },
                            modifier = Modifier.align(Alignment.CenterStart).size(28.dp)
                        ) {
                            Icon(Icons.Default.ArrowBack, "Pan Left", tint = NovaCyan)
                        }
                        // Right
                        IconButton(
                            onClick = { onPanTilt(5f, 0f) },
                            modifier = Modifier.align(Alignment.CenterEnd).size(28.dp)
                        ) {
                            Icon(Icons.Default.ArrowForward, "Pan Right", tint = NovaCyan)
                        }
                        // Center Reset
                        IconButton(
                            onClick = onResetGimbal,
                            modifier = Modifier.align(Alignment.Center).size(24.dp)
                        ) {
                            Icon(Icons.Default.CenterFocusStrong, "Reset Gimbal", tint = NovaLavender)
                        }
                    }

                    // Zoom Slider Controls
                    Column(
                        modifier = Modifier
                            .weight(1f)
                            .padding(start = 16.dp)
                    ) {
                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.SpaceBetween,
                            modifier = Modifier.fillMaxWidth()
                        ) {
                            Text(text = "Zoom Analógico", color = NovaTextWhite, fontSize = 11.sp)
                            Text(text = "${String.format("%.1f", zoomLevel)}x", color = NovaCyan, fontSize = 11.sp, fontFamily = FontFamily.Monospace)
                        }
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            IconButton(onClick = { onZoomChange(zoomLevel - 0.2f) }, modifier = Modifier.size(24.dp)) {
                                Icon(Icons.Default.Remove, "Zoom Out", tint = NovaCyan)
                            }
                            Slider(
                                value = zoomLevel,
                                onValueChange = onZoomChange,
                                valueRange = 1.0f..4.0f,
                                modifier = Modifier.weight(1f),
                                colors = SliderDefaults.colors(
                                    thumbColor = NovaCyan,
                                    activeTrackColor = NovaCyan,
                                    inactiveTrackColor = NovaCyanGlow
                                )
                            )
                            IconButton(onClick = { onZoomChange(zoomLevel + 0.2f) }, modifier = Modifier.size(24.dp)) {
                                Icon(Icons.Default.Add, "Zoom In", tint = NovaCyan)
                            }
                        }
                    }
                }
            }
        }
    }
}
