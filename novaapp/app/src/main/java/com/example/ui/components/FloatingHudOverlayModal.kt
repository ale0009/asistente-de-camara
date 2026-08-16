package com.example.ui.components

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
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CameraAlt
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.HelpOutline
import androidx.compose.material.icons.filled.Mic
import androidx.compose.material.icons.filled.MicOff
import androidx.compose.material.icons.filled.PauseCircle
import androidx.compose.material.icons.filled.PlayCircle
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material.icons.filled.StopCircle
import androidx.compose.material.icons.filled.VolumeDown
import androidx.compose.material.icons.filled.VolumeUp
import androidx.compose.material.icons.filled.WbSunny
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.window.Dialog
import com.example.ui.theme.NovaBgCanvas
import com.example.ui.theme.NovaBgDarkNavy
import com.example.ui.theme.NovaCyan
import com.example.ui.theme.NovaCyanBorder
import com.example.ui.theme.NovaCyanGlow
import com.example.ui.theme.NovaDangerBg
import com.example.ui.theme.NovaDangerBorder
import com.example.ui.theme.NovaDangerText
import com.example.ui.theme.NovaLavender
import com.example.ui.theme.NovaPurpleContainer
import com.example.ui.theme.NovaSurfaceCard
import com.example.ui.theme.NovaTextDim
import com.example.ui.theme.NovaTextWhite

@Composable
fun FloatingHudOverlayModal(
    isOpen: Boolean,
    isTrackingActive: Boolean,
    isListening: Boolean,
    zoomLevel: Float,
    isMicMuted: Boolean,
    onDismiss: () -> Unit,
    onWakeCamera: () -> Unit,
    onToggleTracking: () -> Unit,
    onStopCamera: () -> Unit,
    onCapture: () -> Unit,
    onToggleMic: () -> Unit,
    onVolumeUp: () -> Unit,
    onVolumeDown: () -> Unit,
    onOpenConfig: () -> Unit,
    onOpenObsidian: () -> Unit,
    onOpenHelp: () -> Unit,
    modifier: Modifier = Modifier
) {
    if (!isOpen) return

    Dialog(onDismissRequest = onDismiss) {
        Surface(
            modifier = modifier
                .width(340.dp)
                .shadow(
                    elevation = 24.dp,
                    shape = RoundedCornerShape(16.dp),
                    spotColor = NovaCyan,
                    ambientColor = NovaCyan
                )
                .clip(RoundedCornerShape(16.dp))
                .background(NovaBgCanvas.copy(alpha = 0.94f))
                .border(1.dp, NovaCyanBorder, RoundedCornerShape(16.dp))
                .padding(14.dp),
            color = Color.Transparent
        ) {
            Column(modifier = Modifier.fillMaxWidth()) {
                // Header (52px equivalent)
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(bottom = 10.dp),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Box(
                            modifier = Modifier
                                .size(28.dp)
                                .clip(RoundedCornerShape(7.dp))
                                .background(NovaCyanGlow)
                                .border(1.dp, NovaCyanBorder, RoundedCornerShape(7.dp)),
                            contentAlignment = Alignment.Center
                        ) {
                            Text(
                                text = "N",
                                color = NovaCyan,
                                fontWeight = FontWeight.Bold,
                                fontSize = 12.sp,
                                fontFamily = FontFamily.Monospace
                            )
                        }
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(
                            text = "NOVA",
                            color = NovaTextWhite,
                            fontWeight = FontWeight.Bold,
                            fontSize = 14.sp,
                            letterSpacing = 2.sp
                        )
                    }

                    Row(verticalAlignment = Alignment.CenterVertically) {
                        // Listening Pill
                        Row(
                            modifier = Modifier
                                .clip(RoundedCornerShape(12.dp))
                                .background(NovaCyanGlow.copy(alpha = 0.4f))
                                .border(1.dp, NovaCyanBorder.copy(alpha = 0.3f), RoundedCornerShape(12.dp))
                                .padding(horizontal = 8.dp, vertical = 4.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Box(
                                modifier = Modifier
                                    .size(6.dp)
                                    .clip(CircleShape)
                                    .background(NovaCyan)
                            )
                            Spacer(modifier = Modifier.width(4.dp))
                            Text(
                                text = if (isListening) "Escuchando" else "Standby",
                                color = NovaCyan,
                                fontSize = 9.sp,
                                fontFamily = FontFamily.Monospace
                            )
                        }

                        Spacer(modifier = Modifier.width(6.dp))

                        IconButton(
                            onClick = onDismiss,
                            modifier = Modifier.size(24.dp)
                        ) {
                            Icon(
                                imageVector = Icons.Default.Close,
                                contentDescription = "Cerrar HUD",
                                tint = NovaTextDim
                            )
                        }
                    }
                }

                // Video Feed Container (316px x 178px equivalent)
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .aspectRatio(16f / 9f)
                        .clip(RoundedCornerShape(8.dp))
                        .background(Color(0xFF0D162E))
                        .border(1.dp, NovaCyanBorder.copy(alpha = 0.3f), RoundedCornerShape(8.dp))
                ) {
                    // Simulated Human Face Target Vector Graphic
                    Box(
                        modifier = Modifier
                            .fillMaxSize()
                            .padding(16.dp),
                        contentAlignment = Alignment.Center
                    ) {
                        Box(
                            modifier = Modifier
                                .size(64.dp)
                                .border(1.5.dp, NovaCyan, CircleShape)
                                .padding(12.dp),
                            contentAlignment = Alignment.Center
                        ) {
                            Box(
                                modifier = Modifier
                                    .size(16.dp)
                                    .background(NovaCyanGlow, CircleShape)
                                    .border(1.dp, NovaCyan, CircleShape)
                            )
                        }
                    }

                    // Chips Overlay (Top & Bottom)
                    Row(
                        modifier = Modifier
                            .align(Alignment.BottomStart)
                            .padding(6.dp),
                        horizontalArrangement = Arrangement.spacedBy(4.dp)
                    ) {
                        Box(
                            modifier = Modifier
                                .clip(RoundedCornerShape(4.dp))
                                .background(Color(0xCC000000))
                                .border(1.dp, NovaCyanBorder, RoundedCornerShape(4.dp))
                                .padding(horizontal = 6.dp, vertical = 2.dp)
                        ) {
                            Text(
                                text = "▶ Tracking: ${if (isTrackingActive) "Humano" else "Off"}",
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
                                text = "⊕ Zoom: ${String.format("%.1f", zoomLevel)}x",
                                color = NovaCyan,
                                fontSize = 9.sp,
                                fontFamily = FontFamily.Monospace
                            )
                        }
                    }
                }

                Spacer(modifier = Modifier.height(10.dp))

                // Action Log Terminal (316px x 76px equivalent)
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(64.dp)
                        .clip(RoundedCornerShape(8.dp))
                        .background(Color(0x66000000))
                        .border(1.dp, Color(0x1AFFFFFF), RoundedCornerShape(8.dp))
                        .padding(6.dp)
                ) {
                    Column {
                        Text(text = "17:36:48 Despertar Humano", color = NovaTextDim, fontSize = 9.sp, fontFamily = FontFamily.Monospace)
                        Text(text = "17:36:46 Tracking: Humano", color = NovaCyan, fontSize = 9.sp, fontFamily = FontFamily.Monospace)
                        Text(text = "17:38:42 Terminal log", color = NovaTextDim, fontSize = 9.sp, fontFamily = FontFamily.Monospace)
                        Text(text = "17:38:59 Parar Tracking", color = NovaDangerText, fontSize = 9.sp, fontFamily = FontFamily.Monospace)
                    }
                }

                Spacer(modifier = Modifier.height(10.dp))

                // 10-Button Grid (Exact match to specification image)
                LazyVerticalGrid(
                    columns = GridCells.Fixed(3),
                    horizontalArrangement = Arrangement.spacedBy(6.dp),
                    verticalArrangement = Arrangement.spacedBy(6.dp),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    item {
                        HudGridButton(
                            title = "Despertar",
                            icon = Icons.Default.WbSunny,
                            onClick = onWakeCamera,
                            testTag = "hud_despertar_btn"
                        )
                    }
                    item {
                        HudGridButton(
                            title = "Trackear",
                            icon = Icons.Default.PlayCircle,
                            isPrimary = true,
                            onClick = onToggleTracking,
                            testTag = "hud_trackear_btn"
                        )
                    }
                    item {
                        HudGridButton(
                            title = "Parar",
                            icon = Icons.Default.StopCircle,
                            isDanger = true,
                            onClick = onStopCamera,
                            testTag = "hud_parar_btn"
                        )
                    }
                    item {
                        HudGridButton(
                            title = "Captura",
                            icon = Icons.Default.CameraAlt,
                            onClick = onCapture,
                            testTag = "hud_captura_btn"
                        )
                    }
                    item {
                        HudGridButton(
                            title = "Config",
                            icon = Icons.Default.Settings,
                            onClick = onOpenConfig,
                            testTag = "hud_config_btn"
                        )
                    }
                    item {
                        HudGridButton(
                            title = "Obsidian",
                            icon = Icons.Default.PauseCircle,
                            isObsidian = true,
                            onClick = onOpenObsidian,
                            testTag = "hud_obsidian_btn"
                        )
                    }
                    item {
                        HudGridButton(
                            title = if (isMicMuted) "Unmute" else "Silencio",
                            icon = if (isMicMuted) Icons.Default.MicOff else Icons.Default.Mic,
                            onClick = onToggleMic,
                            testTag = "hud_silencio_btn"
                        )
                    }
                    item {
                        HudGridButton(
                            title = "Vol+",
                            icon = Icons.Default.VolumeUp,
                            onClick = onVolumeUp,
                            testTag = "hud_volup_btn"
                        )
                    }
                    item {
                        HudGridButton(
                            title = "Vol-",
                            icon = Icons.Default.VolumeDown,
                            onClick = onVolumeDown,
                            testTag = "hud_voldown_btn"
                        )
                    }
                }
            }
        }
    }
}

@Composable
fun HudGridButton(
    title: String,
    icon: ImageVector,
    onClick: () -> Unit,
    testTag: String,
    isPrimary: Boolean = false,
    isDanger: Boolean = false,
    isObsidian: Boolean = false,
) {
    val bgColor = when {
        isPrimary -> NovaCyanGlow.copy(alpha = 0.8f)
        isDanger -> NovaDangerBg
        isObsidian -> NovaPurpleContainer
        else -> Color(0x0DFFFFFF)
    }

    val borderColor = when {
        isPrimary -> NovaCyanBorder
        isDanger -> NovaDangerBorder
        isObsidian -> Color(0x3D946EF0)
        else -> Color(0x1AFFFFFF)
    }

    val contentColor = when {
        isPrimary -> NovaCyan
        isDanger -> NovaDangerText
        isObsidian -> NovaLavender
        else -> NovaTextWhite
    }

    Box(
        modifier = Modifier
            .height(50.dp)
            .clip(RoundedCornerShape(8.dp))
            .background(bgColor)
            .border(1.dp, borderColor, RoundedCornerShape(8.dp))
            .clickable { onClick() }
            .padding(4.dp)
            .testTag(testTag),
        contentAlignment = Alignment.Center
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
            Icon(
                imageVector = icon,
                contentDescription = title,
                tint = contentColor,
                modifier = Modifier.size(16.dp)
            )
            Spacer(modifier = Modifier.height(2.dp))
            Text(
                text = title,
                color = contentColor,
                fontSize = 9.sp,
                fontWeight = FontWeight.Medium
            )
        }
    }
}
