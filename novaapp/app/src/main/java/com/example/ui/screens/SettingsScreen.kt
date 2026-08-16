package com.example.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.border
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
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.Save
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Switch
import androidx.compose.material3.SwitchDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
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
import com.example.ui.theme.NovaSurfaceCard
import com.example.ui.theme.NovaTextDim
import com.example.ui.theme.NovaTextWhite

@Composable
fun SettingsScreen(
    onClearLogs: () -> Unit,
    onShowToast: (String) -> Unit,
    modifier: Modifier = Modifier
) {
    var oscIp by remember { mutableStateOf("127.0.0.1") }
    var oscPort by remember { mutableStateOf("16284") }
    var ollamaUrl by remember { mutableStateOf("http://127.0.0.1:11434") }
    var modelName by remember { mutableStateOf("qwen3:8b") }
    var vramLimit by remember { mutableStateOf("8 GB (NVIDIA RTX 5060)") }
    var autoWakeWord by remember { mutableStateOf(true) }
    var poseMeshActive by remember { mutableStateOf(true) }

    Column(
        modifier = modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        // Title Header
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column {
                Text(
                    text = "Ajustes & Configuración Hardware",
                    color = NovaTextWhite,
                    fontWeight = FontWeight.Bold,
                    fontSize = 18.sp
                )
                Text(
                    text = "OSC Bridge, Ollama Local Server, Whisper STT & Hardware DirectShow",
                    color = NovaTextDim,
                    fontSize = 11.sp,
                    fontFamily = FontFamily.Monospace
                )
            }

            Button(
                onClick = { onShowToast("Ajustes de sistema guardados correctamente") },
                colors = ButtonDefaults.buttonColors(containerColor = NovaCyan, contentColor = com.example.ui.theme.NovaBgCanvas),
                shape = RoundedCornerShape(8.dp),
                modifier = Modifier.testTag("save_settings_button")
            ) {
                Icon(Icons.Default.Save, "Save", modifier = Modifier.size(16.dp))
                Spacer(modifier = Modifier.width(6.dp))
                Text(text = "Guardar", fontWeight = FontWeight.Bold)
            }
        }

        // Section 1: OBSBOT Center OSC Bridge
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(14.dp))
                .background(NovaSurfaceCard)
                .border(1.dp, NovaCyanBorder.copy(alpha = 0.3f), RoundedCornerShape(14.dp))
                .padding(16.dp)
        ) {
            Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                Text(
                    text = "1. OBSBOT Center OSC UDP Bridge Target",
                    color = NovaCyan,
                    fontWeight = FontWeight.Bold,
                    fontSize = 14.sp,
                    fontFamily = FontFamily.Monospace
                )

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    OutlinedTextField(
                        value = oscIp,
                        onValueChange = { oscIp = it },
                        label = { Text("OSC Target IP") },
                        modifier = Modifier.weight(1f).testTag("osc_ip_input"),
                        textStyle = androidx.compose.ui.text.TextStyle(color = NovaTextWhite, fontFamily = FontFamily.Monospace),
                        colors = OutlinedTextFieldDefaults.colors(
                            focusedBorderColor = NovaCyan,
                            unfocusedBorderColor = NovaCyanBorder
                        )
                    )

                    OutlinedTextField(
                        value = oscPort,
                        onValueChange = { oscPort = it },
                        label = { Text("UDP Port") },
                        modifier = Modifier.weight(1f).testTag("osc_port_input"),
                        textStyle = androidx.compose.ui.text.TextStyle(color = NovaTextWhite, fontFamily = FontFamily.Monospace),
                        colors = OutlinedTextFieldDefaults.colors(
                            focusedBorderColor = NovaCyan,
                            unfocusedBorderColor = NovaCyanBorder
                        )
                    )
                }

                Text(
                    text = "Endpoints configurados: /OBSBOT/WebCam/Tiny/ToggleAILock, /SetZoom, /SetPanTilt, /Sleep",
                    color = NovaTextDim,
                    fontSize = 10.sp,
                    fontFamily = FontFamily.Monospace
                )
            }
        }

        // Section 2: Ollama Local Agentic Inference Engine
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(14.dp))
                .background(NovaSurfaceCard)
                .border(1.dp, NovaCyanBorder.copy(alpha = 0.3f), RoundedCornerShape(14.dp))
                .padding(16.dp)
        ) {
            Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                Text(
                    text = "2. Ollama LLM Inference Endpoint",
                    color = NovaCyan,
                    fontWeight = FontWeight.Bold,
                    fontSize = 14.sp,
                    fontFamily = FontFamily.Monospace
                )

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    OutlinedTextField(
                        value = ollamaUrl,
                        onValueChange = { ollamaUrl = it },
                        label = { Text("Ollama URL") },
                        modifier = Modifier.weight(1f),
                        textStyle = androidx.compose.ui.text.TextStyle(color = NovaTextWhite, fontFamily = FontFamily.Monospace),
                        colors = OutlinedTextFieldDefaults.colors(
                            focusedBorderColor = NovaCyan,
                            unfocusedBorderColor = NovaCyanBorder
                        )
                    )

                    OutlinedTextField(
                        value = modelName,
                        onValueChange = { modelName = it },
                        label = { Text("Modelo Agéntico") },
                        modifier = Modifier.weight(1f),
                        textStyle = androidx.compose.ui.text.TextStyle(color = NovaTextWhite, fontFamily = FontFamily.Monospace),
                        colors = OutlinedTextFieldDefaults.colors(
                            focusedBorderColor = NovaCyan,
                            unfocusedBorderColor = NovaCyanBorder
                        )
                    )
                }

                OutlinedTextField(
                    value = vramLimit,
                    onValueChange = { vramLimit = it },
                    label = { Text("GPU VRAM Hardware Profile") },
                    modifier = Modifier.fillMaxWidth(),
                    textStyle = androidx.compose.ui.text.TextStyle(color = NovaTextWhite, fontFamily = FontFamily.Monospace),
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedBorderColor = NovaCyan,
                        unfocusedBorderColor = NovaCyanBorder
                    )
                )
            }
        }

        // Section 3: Toggles & Maintenance
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(14.dp))
                .background(NovaSurfaceCard)
                .border(1.dp, NovaCyanBorder.copy(alpha = 0.3f), RoundedCornerShape(14.dp))
                .padding(16.dp)
        ) {
            Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                Text(
                    text = "3. Reconocimiento & Mantenimiento",
                    color = NovaCyan,
                    fontWeight = FontWeight.Bold,
                    fontSize = 14.sp,
                    fontFamily = FontFamily.Monospace
                )

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(text = "OpenWakeWord (Detección continua de 'NOVA')", color = NovaTextWhite, fontSize = 13.sp)
                    Switch(
                        checked = autoWakeWord,
                        onCheckedChange = { autoWakeWord = it },
                        colors = SwitchDefaults.colors(checkedThumbColor = NovaCyan, checkedTrackColor = NovaCyanGlow)
                    )
                }

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(text = "MediaPipe Pose & Hand Gesture Detection", color = NovaTextWhite, fontSize = 13.sp)
                    Switch(
                        checked = poseMeshActive,
                        onCheckedChange = { poseMeshActive = it },
                        colors = SwitchDefaults.colors(checkedThumbColor = NovaCyan, checkedTrackColor = NovaCyanGlow)
                    )
                }

                Spacer(modifier = Modifier.height(8.dp))

                Button(
                    onClick = {
                        onClearLogs()
                        onShowToast("Terminal de logs vaciada")
                    },
                    colors = ButtonDefaults.buttonColors(
                        containerColor = NovaDangerBg,
                        contentColor = NovaDangerText
                    ),
                    border = androidx.compose.foundation.BorderStroke(1.dp, NovaDangerBorder),
                    shape = RoundedCornerShape(8.dp),
                    modifier = Modifier.testTag("clear_logs_button")
                ) {
                    Icon(Icons.Default.Delete, "Clear Logs", modifier = Modifier.size(16.dp))
                    Spacer(modifier = Modifier.width(6.dp))
                    Text(text = "Vaciar Logs de Terminal")
                }
            }
        }
    }
}
