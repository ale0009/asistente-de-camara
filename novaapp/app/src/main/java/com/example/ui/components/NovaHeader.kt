package com.example.ui.components

import androidx.compose.animation.core.Animatable
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.tween
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowDropDown
import androidx.compose.material.icons.filled.OpenInNew
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.ui.SceneMode
import com.example.ui.theme.NovaBgDarkNavy
import com.example.ui.theme.NovaCyan
import com.example.ui.theme.NovaCyanBorder
import com.example.ui.theme.NovaCyanGlow
import com.example.ui.theme.NovaTextDim
import com.example.ui.theme.NovaTextWhite

@Composable
fun NovaHeader(
    currentScene: SceneMode,
    isListening: Boolean,
    onSceneSelect: (SceneMode) -> Unit,
    onOpenFloatingHud: () -> Unit,
    modifier: Modifier = Modifier
) {
    var sceneMenuExpanded by remember { mutableStateOf(false) }

    // Pulsing dot animation for status pill
    val pulseAlpha = remember { Animatable(0.35f) }
    LaunchedEffect(isListening) {
        pulseAlpha.animateTo(
            targetValue = 1.0f,
            animationSpec = infiniteRepeatable(
                animation = tween(600),
                repeatMode = RepeatMode.Reverse
            )
        )
    }

    Row(
        modifier = modifier
            .fillMaxWidth()
            .background(NovaBgDarkNavy)
            .border(width = 1.dp, color = NovaCyanBorder.copy(alpha = 0.2f))
            .padding(horizontal = 16.dp, vertical = 12.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        // Left: Logo Badge & Title
        Row(verticalAlignment = Alignment.CenterVertically) {
            Box(
                modifier = Modifier
                    .size(32.dp)
                    .clip(RoundedCornerShape(8.dp))
                    .background(NovaCyanGlow)
                    .border(1.dp, NovaCyanBorder, RoundedCornerShape(8.dp)),
                contentAlignment = Alignment.Center
            ) {
                Text(
                    text = "N",
                    color = NovaCyan,
                    fontWeight = FontWeight.Bold,
                    fontSize = 16.sp,
                    fontFamily = FontFamily.Monospace
                )
            }
            Spacer(modifier = Modifier.width(12.dp))
            Column {
                Text(
                    text = "NOVA",
                    color = NovaTextWhite,
                    fontWeight = FontWeight.Bold,
                    fontSize = 16.sp,
                    letterSpacing = 2.sp
                )
                Text(
                    text = "COMMAND CENTER",
                    color = NovaCyan,
                    fontSize = 9.sp,
                    fontFamily = FontFamily.Monospace,
                    letterSpacing = 1.sp
                )
            }
        }

        // Right: Status Pill & Scene Selector Dropdown & HUD Trigger
        Row(
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            // Scene Selector Chip
            Box {
                Row(
                    modifier = Modifier
                        .clip(RoundedCornerShape(12.dp))
                        .background(NovaCyanGlow.copy(alpha = 0.5f))
                        .border(1.dp, NovaCyanBorder.copy(alpha = 0.4f), RoundedCornerShape(12.dp))
                        .clickable { sceneMenuExpanded = true }
                        .padding(horizontal = 10.dp, vertical = 6.dp)
                        .testTag("scene_selector_chip"),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "${currentScene.icon} ${currentScene.label}",
                        color = NovaTextWhite,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Medium
                    )
                    Icon(
                        imageVector = Icons.Default.ArrowDropDown,
                        contentDescription = "Select Scene",
                        tint = NovaCyan,
                        modifier = Modifier.size(16.dp)
                    )
                }

                DropdownMenu(
                    expanded = sceneMenuExpanded,
                    onDismissRequest = { sceneMenuExpanded = false },
                    modifier = Modifier
                        .background(NovaBgDarkNavy)
                        .border(1.dp, NovaCyanBorder, RoundedCornerShape(8.dp))
                ) {
                    SceneMode.entries.forEach { scene ->
                        DropdownMenuItem(
                            text = {
                                Column {
                                    Text(
                                        text = "${scene.icon} ${scene.label}",
                                        color = if (scene == currentScene) NovaCyan else NovaTextWhite,
                                        fontWeight = if (scene == currentScene) FontWeight.Bold else FontWeight.Normal,
                                        fontSize = 13.sp
                                    )
                                    Text(
                                        text = scene.description,
                                        color = NovaTextDim,
                                        fontSize = 10.sp
                                    )
                                }
                            },
                            onClick = {
                                onSceneSelect(scene)
                                sceneMenuExpanded = false
                            }
                        )
                    }
                }
            }

            // Listening / Status Pill
            Row(
                modifier = Modifier
                    .clip(RoundedCornerShape(12.dp))
                    .background(NovaCyanGlow.copy(alpha = 0.3f))
                    .border(1.dp, NovaCyanBorder.copy(alpha = 0.3f), RoundedCornerShape(12.dp))
                    .padding(horizontal = 8.dp, vertical = 6.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Box(
                    modifier = Modifier
                        .size(8.dp)
                        .clip(CircleShape)
                        .background(NovaCyan.copy(alpha = if (isListening) pulseAlpha.value else 0.3f))
                )
                Spacer(modifier = Modifier.width(6.dp))
                Text(
                    text = if (isListening) "Escuchando" else "Standby",
                    color = if (isListening) NovaCyan else NovaTextDim,
                    fontSize = 10.sp,
                    fontFamily = FontFamily.Monospace,
                    fontWeight = FontWeight.Medium
                )
            }

            // Floating HUD Overlay Trigger Icon Button
            IconButton(
                onClick = onOpenFloatingHud,
                modifier = Modifier
                    .size(32.dp)
                    .clip(RoundedCornerShape(8.dp))
                    .background(NovaCyanGlow)
                    .border(1.dp, NovaCyanBorder, RoundedCornerShape(8.dp))
                    .testTag("hud_trigger_button")
            ) {
                Icon(
                    imageVector = Icons.Default.OpenInNew,
                    contentDescription = "Abrir HUD Flotante",
                    tint = NovaCyan,
                    modifier = Modifier.size(18.dp)
                )
            }
        }
    }
}
