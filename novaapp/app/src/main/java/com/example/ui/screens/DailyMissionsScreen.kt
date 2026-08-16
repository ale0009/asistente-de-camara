package com.example.ui.screens

import androidx.compose.animation.AnimatedVisibility
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
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.Pause
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.Timer
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Checkbox
import androidx.compose.material3.CheckboxDefaults
import androidx.compose.material3.FloatingActionButton
import androidx.compose.material3.Icon
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
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
import com.example.data.Mission
import com.example.ui.theme.NovaBgCanvas
import com.example.ui.theme.NovaBgDarkNavy
import com.example.ui.theme.NovaCyan
import com.example.ui.theme.NovaCyanBorder
import com.example.ui.theme.NovaCyanGlow
import com.example.ui.theme.NovaLavender
import com.example.ui.theme.NovaSuccessGreen
import com.example.ui.theme.NovaSurfaceCard
import com.example.ui.theme.NovaTextDim
import com.example.ui.theme.NovaTextWhite
import java.util.Locale

@Composable
fun DailyMissionsScreen(
    missions: List<Mission>,
    focusTimeLeftSeconds: Int,
    isFocusSprintRunning: Boolean,
    showFocusCompleteModal: Boolean,
    onToggleMission: (Mission) -> Unit,
    onAddMission: (String, String) -> Unit,
    onResetMissions: () -> Unit,
    onStartFocusSprint: () -> Unit,
    onPauseFocusSprint: () -> Unit,
    onResetFocusSprint: () -> Unit,
    onDismissFocusModal: () -> Unit,
    modifier: Modifier = Modifier
) {
    var showAddDialog by remember { mutableStateOf(false) }
    var newTitle by remember { mutableStateOf("") }
    var newTime by remember { mutableStateOf("08:00 AM") }

    Box(modifier = modifier.fillMaxSize()) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            // Focus Sprint 45:00 Card (Matching Design Specs)
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(14.dp))
                    .background(NovaSurfaceCard)
                    .border(1.dp, NovaCyanBorder, RoundedCornerShape(14.dp))
                    .padding(16.dp)
            ) {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Icon(Icons.Default.Timer, "Focus Sprint", tint = NovaCyan)
                            Spacer(modifier = Modifier.width(8.dp))
                            Text(
                                text = "FOCUS SPRINT (90 MIN)",
                                color = NovaTextWhite,
                                fontWeight = FontWeight.Bold,
                                fontSize = 13.sp,
                                fontFamily = FontFamily.Monospace
                            )
                        }

                        Box(
                            modifier = Modifier
                                .clip(RoundedCornerShape(6.dp))
                                .background(if (isFocusSprintRunning) NovaSuccessGreen.copy(alpha = 0.2f) else NovaCyanGlow)
                                .padding(horizontal = 8.dp, vertical = 3.dp)
                        ) {
                            Text(
                                text = if (isFocusSprintRunning) "EJECUTANDO" else "EN ESPERA",
                                color = if (isFocusSprintRunning) NovaSuccessGreen else NovaCyan,
                                fontSize = 10.sp,
                                fontFamily = FontFamily.Monospace,
                                fontWeight = FontWeight.Bold
                            )
                        }
                    }

                    Spacer(modifier = Modifier.height(12.dp))

                    val minutes = focusTimeLeftSeconds / 60
                    val seconds = focusTimeLeftSeconds % 60
                    val timeFormatted = String.format(Locale.getDefault(), "%02d:%02d", minutes, seconds)

                    Text(
                        text = timeFormatted,
                        color = NovaCyan,
                        fontSize = 42.sp,
                        fontWeight = FontWeight.Bold,
                        fontFamily = FontFamily.Monospace,
                        letterSpacing = 2.sp
                    )

                    Spacer(modifier = Modifier.height(12.dp))

                    Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                        Button(
                            onClick = {
                                if (isFocusSprintRunning) onPauseFocusSprint() else onStartFocusSprint()
                            },
                            colors = ButtonDefaults.buttonColors(
                                containerColor = if (isFocusSprintRunning) NovaLavender else NovaCyan,
                                contentColor = NovaBgCanvas
                            ),
                            shape = RoundedCornerShape(8.dp),
                            modifier = Modifier.testTag("focus_sprint_start_pause_button")
                        ) {
                            Icon(
                                imageVector = if (isFocusSprintRunning) Icons.Default.Pause else Icons.Default.PlayArrow,
                                contentDescription = null,
                                modifier = Modifier.size(18.dp)
                            )
                            Spacer(modifier = Modifier.width(6.dp))
                            Text(
                                text = if (isFocusSprintRunning) "Pausar" else "Iniciar Sprint",
                                fontWeight = FontWeight.Bold
                            )
                        }

                        Button(
                            onClick = onResetFocusSprint,
                            colors = ButtonDefaults.buttonColors(
                                containerColor = NovaBgDarkNavy,
                                contentColor = NovaTextDim
                            ),
                            border = androidx.compose.foundation.BorderStroke(1.dp, NovaCyanBorder.copy(alpha = 0.3f)),
                            shape = RoundedCornerShape(8.dp),
                            modifier = Modifier.testTag("focus_sprint_reset_button")
                        ) {
                            Icon(Icons.Default.Refresh, "Reset", modifier = Modifier.size(18.dp))
                            Spacer(modifier = Modifier.width(6.dp))
                            Text(text = "Reset")
                        }
                    }
                }
            }

            // Daily Missions Header & Action Row
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column {
                    Text(
                        text = "Daily Missions",
                        color = NovaTextWhite,
                        fontWeight = FontWeight.Bold,
                        fontSize = 18.sp
                    )
                    Text(
                        text = "${missions.count { it.isCompleted }}/${missions.size} Misiones completadas hoy",
                        color = NovaTextDim,
                        fontSize = 11.sp,
                        fontFamily = FontFamily.Monospace
                    )
                }

                TextButton(
                    onClick = onResetMissions,
                    modifier = Modifier.testTag("reset_missions_button")
                ) {
                    Text(text = "Reiniciar Progreso", color = NovaCyan, fontSize = 12.sp)
                }
            }

            // Missions Checklist LazyColumn
            LazyColumn(
                modifier = Modifier.fillMaxSize(),
                verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                items(missions) { mission ->
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .clip(RoundedCornerShape(10.dp))
                            .background(NovaSurfaceCard)
                            .border(
                                1.dp,
                                if (mission.isCompleted) NovaCyanBorder.copy(alpha = 0.2f) else NovaCyanBorder.copy(alpha = 0.5f),
                                RoundedCornerShape(10.dp)
                            )
                            .clickable { onToggleMission(mission) }
                            .padding(14.dp)
                    ) {
                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.SpaceBetween,
                            modifier = Modifier.fillMaxWidth()
                        ) {
                            Row(
                                verticalAlignment = Alignment.CenterVertically,
                                modifier = Modifier.weight(1f)
                            ) {
                                Checkbox(
                                    checked = mission.isCompleted,
                                    onCheckedChange = { onToggleMission(mission) },
                                    colors = CheckboxDefaults.colors(
                                        checkedColor = NovaCyan,
                                        checkmarkColor = NovaBgDarkNavy,
                                        uncheckedColor = NovaTextDim
                                    ),
                                    modifier = Modifier.testTag("missions_page_checkbox_${mission.id}")
                                )

                                Spacer(modifier = Modifier.width(10.dp))

                                Column {
                                    Text(
                                        text = mission.title,
                                        color = if (mission.isCompleted) NovaTextDim else NovaTextWhite,
                                        fontWeight = FontWeight.SemiBold,
                                        fontSize = 14.sp
                                    )
                                    Text(
                                        text = "${mission.time} • CATEGORÍA: ${mission.category}",
                                        color = NovaCyan,
                                        fontSize = 10.sp,
                                        fontFamily = FontFamily.Monospace
                                    )
                                }
                            }

                            if (mission.isCompleted) {
                                Box(
                                    modifier = Modifier
                                        .clip(RoundedCornerShape(4.dp))
                                        .background(NovaSuccessGreen.copy(alpha = 0.2f))
                                        .padding(horizontal = 8.dp, vertical = 4.dp)
                                ) {
                                    Text(
                                        text = "DONE",
                                        color = NovaSuccessGreen,
                                        fontSize = 10.sp,
                                        fontFamily = FontFamily.Monospace,
                                        fontWeight = FontWeight.Bold
                                    )
                                }
                            }
                        }
                    }
                }
            }
        }

        // Floating Action Button to Add Mission
        FloatingActionButton(
            onClick = { showAddDialog = true },
            containerColor = NovaCyan,
            contentColor = NovaBgCanvas,
            modifier = Modifier
                .align(Alignment.BottomEnd)
                .padding(24.dp)
                .testTag("add_mission_fab")
        ) {
            Icon(Icons.Default.Add, "Agregar Misión")
        }

        // Add Mission Dialog
        if (showAddDialog) {
            AlertDialog(
                onDismissRequest = { showAddDialog = false },
                title = { Text("Nueva Misión", color = NovaTextWhite) },
                text = {
                    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                        OutlinedTextField(
                            value = newTitle,
                            onValueChange = { newTitle = it },
                            label = { Text("Título de la Misión") },
                            colors = OutlinedTextFieldDefaults.colors(
                                focusedTextColor = NovaTextWhite,
                                unfocusedTextColor = NovaTextWhite,
                                focusedBorderColor = NovaCyan,
                                unfocusedBorderColor = NovaCyanBorder
                            ),
                            modifier = Modifier.testTag("new_mission_title_input")
                        )
                        OutlinedTextField(
                            value = newTime,
                            onValueChange = { newTime = it },
                            label = { Text("Hora (ej. 15:00 PM)") },
                            colors = OutlinedTextFieldDefaults.colors(
                                focusedTextColor = NovaTextWhite,
                                unfocusedTextColor = NovaTextWhite,
                                focusedBorderColor = NovaCyan,
                                unfocusedBorderColor = NovaCyanBorder
                            )
                        )
                    }
                },
                confirmButton = {
                    Button(
                        onClick = {
                            if (newTitle.isNotBlank()) {
                                onAddMission(newTitle, newTime)
                                newTitle = ""
                                showAddDialog = false
                            }
                        },
                        colors = ButtonDefaults.buttonColors(containerColor = NovaCyan, contentColor = NovaBgCanvas)
                    ) {
                        Text("Guardar Misión")
                    }
                },
                dismissButton = {
                    TextButton(onClick = { showAddDialog = false }) {
                        Text("Cancelar", color = NovaTextDim)
                    }
                },
                containerColor = NovaBgDarkNavy
            )
        }

        // Focus Complete Modal Popup
        if (showFocusCompleteModal) {
            AlertDialog(
                onDismissRequest = onDismissFocusModal,
                icon = { Icon(Icons.Default.CheckCircle, "Sprint Completed", tint = NovaSuccessGreen, modifier = Modifier.size(48.dp)) },
                title = { Text("Deep Work Session Complete!", color = NovaTextWhite, fontWeight = FontWeight.Bold) },
                text = {
                    Text(
                        text = "0 Distractions. Status: Optimized.\n\nHas completado exitosamente 45 minutos de concentración total. Todos los logs y datos de sesión han sido guardados.",
                        color = NovaTextDim,
                        fontSize = 13.sp,
                        fontFamily = FontFamily.Monospace
                    )
                },
                confirmButton = {
                    Button(
                        onClick = onDismissFocusModal,
                        colors = ButtonDefaults.buttonColors(containerColor = NovaCyan, contentColor = NovaBgCanvas)
                    ) {
                        Text("Entendido 🎯")
                    }
                },
                containerColor = NovaBgDarkNavy
            )
        }
    }
}
