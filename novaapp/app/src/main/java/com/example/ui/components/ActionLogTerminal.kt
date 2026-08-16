package com.example.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
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
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.Send
import androidx.compose.material.icons.filled.Mic
import androidx.compose.material.icons.filled.MicOff
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.data.ActionLogEntry
import com.example.ui.theme.NovaBgDarkNavy
import com.example.ui.theme.NovaCyan
import com.example.ui.theme.NovaCyanBorder
import com.example.ui.theme.NovaCyanGlow
import com.example.ui.theme.NovaDangerText
import com.example.ui.theme.NovaLavender
import com.example.ui.theme.NovaSuccessGreen
import com.example.ui.theme.NovaSurfaceCard
import com.example.ui.theme.NovaTextDim
import com.example.ui.theme.NovaTextWhite
import com.example.ui.theme.NovaWarningAmber

@Composable
fun ActionLogTerminal(
    logs: List<ActionLogEntry>,
    commandInput: String,
    isListening: Boolean,
    onCommandInputChange: (String) -> Unit,
    onSendCommand: () -> Unit,
    onToggleMic: () -> Unit,
    modifier: Modifier = Modifier
) {
    Column(
        modifier = modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(12.dp))
            .background(NovaSurfaceCard)
            .border(1.dp, NovaCyanBorder.copy(alpha = 0.3f), RoundedCornerShape(12.dp))
            .padding(12.dp)
    ) {
        // Log Header
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = "ACTION LOG / TERMINAL",
                color = NovaTextWhite,
                fontWeight = FontWeight.Bold,
                fontSize = 12.sp,
                fontFamily = FontFamily.Monospace,
                letterSpacing = 1.sp
            )

            Box(
                modifier = Modifier
                    .clip(RoundedCornerShape(4.dp))
                    .background(NovaCyanGlow)
                    .padding(horizontal = 6.dp, vertical = 2.dp)
            ) {
                Text(
                    text = "${logs.size} eventos",
                    color = NovaCyan,
                    fontSize = 9.sp,
                    fontFamily = FontFamily.Monospace
                )
            }
        }

        Spacer(modifier = Modifier.height(8.dp))

        // Terminal Log List Container (Black background, monospace text)
        LazyColumn(
            modifier = Modifier
                .fillMaxWidth()
                .height(110.dp)
                .clip(RoundedCornerShape(8.dp))
                .background(Color(0xFF020610))
                .border(1.dp, Color(0x33FFFFFF), RoundedCornerShape(8.dp))
                .padding(8.dp),
            reverseLayout = false
        ) {
            items(logs) { entry ->
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(vertical = 2.dp)
                ) {
                    Text(
                        text = "[${entry.timestamp}] ",
                        color = NovaTextDim,
                        fontSize = 10.sp,
                        fontFamily = FontFamily.Monospace
                    )

                    val sourceColor = when (entry.source) {
                        "SYSTEM" -> NovaTextDim
                        "CAMERA_1" -> NovaLavender
                        "AI_CORE" -> NovaCyan
                        "COMMAND", "CMD" -> NovaCyan
                        "OBSBOT" -> NovaWarningAmber
                        "MCP" -> NovaSuccessGreen
                        "NOVA" -> NovaCyan
                        else -> NovaTextWhite
                    }

                    Text(
                        text = "${entry.source}: ",
                        color = sourceColor,
                        fontSize = 10.sp,
                        fontFamily = FontFamily.Monospace,
                        fontWeight = FontWeight.Bold
                    )

                    val messageColor = when (entry.logType) {
                        "SUCCESS" -> NovaSuccessGreen
                        "ERROR" -> NovaDangerText
                        "WARNING" -> NovaWarningAmber
                        else -> NovaTextWhite
                    }

                    Text(
                        text = entry.message,
                        color = messageColor,
                        fontSize = 10.sp,
                        fontFamily = FontFamily.Monospace
                    )
                }
            }
        }

        Spacer(modifier = Modifier.height(10.dp))

        // Voice & Text Command Input Bar
        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically
        ) {
            IconButton(
                onClick = onToggleMic,
                modifier = Modifier
                    .size(38.dp)
                    .clip(RoundedCornerShape(8.dp))
                    .background(if (isListening) NovaCyanGlow else NovaBgDarkNavy)
                    .border(1.dp, if (isListening) NovaCyanBorder else Color(0x33FFFFFF), RoundedCornerShape(8.dp))
                    .testTag("terminal_mic_toggle")
            ) {
                Icon(
                    imageVector = if (isListening) Icons.Default.Mic else Icons.Default.MicOff,
                    contentDescription = "Microphone Toggle",
                    tint = if (isListening) NovaCyan else NovaTextDim,
                    modifier = Modifier.size(20.dp)
                )
            }

            Spacer(modifier = Modifier.width(8.dp))

            OutlinedTextField(
                value = commandInput,
                onValueChange = onCommandInputChange,
                placeholder = {
                    Text(
                        text = "Escribe o di un comando (ej. 'sígueme', 'busca en obsidian')...",
                        color = NovaTextDim,
                        fontSize = 11.sp,
                        fontFamily = FontFamily.Monospace
                    )
                },
                modifier = Modifier
                    .weight(1f)
                    .height(44.dp)
                    .testTag("command_input_field"),
                singleLine = true,
                textStyle = androidx.compose.ui.text.TextStyle(
                    color = NovaTextWhite,
                    fontSize = 11.sp,
                    fontFamily = FontFamily.Monospace
                ),
                colors = OutlinedTextFieldDefaults.colors(
                    focusedContainerColor = Color(0xFF020610),
                    unfocusedContainerColor = Color(0xFF020610),
                    focusedBorderColor = NovaCyan,
                    unfocusedBorderColor = NovaCyanBorder.copy(alpha = 0.4f)
                ),
                shape = RoundedCornerShape(8.dp),
                keyboardOptions = KeyboardOptions(imeAction = ImeAction.Send),
                keyboardActions = KeyboardActions(onSend = { onSendCommand() })
            )

            Spacer(modifier = Modifier.width(8.dp))

            IconButton(
                onClick = onSendCommand,
                modifier = Modifier
                    .size(38.dp)
                    .clip(RoundedCornerShape(8.dp))
                    .background(NovaCyanGlow)
                    .border(1.dp, NovaCyanBorder, RoundedCornerShape(8.dp))
                    .testTag("command_send_button")
            ) {
                Icon(
                    imageVector = Icons.AutoMirrored.Filled.Send,
                    contentDescription = "Enviar Comando",
                    tint = NovaCyan,
                    modifier = Modifier.size(18.dp)
                )
            }
        }
    }
}
