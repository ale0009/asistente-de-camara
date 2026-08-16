package com.example.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxHeight
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
import androidx.compose.material.icons.filled.Description
import androidx.compose.material.icons.filled.Lock
import androidx.compose.material.icons.filled.Save
import androidx.compose.material.icons.filled.Search
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Text
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
import com.example.data.ObsidianNote
import com.example.ui.theme.NovaBgCanvas
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
fun ObsidianVaultScreen(
    notes: List<ObsidianNote>,
    searchQuery: String,
    onSearchQueryChange: (String) -> Unit,
    onSaveNote: (ObsidianNote, String) -> Unit,
    modifier: Modifier = Modifier
) {
    var selectedNote by remember(notes) { mutableStateOf(notes.firstOrNull()) }
    var editedContent by remember(selectedNote) { mutableStateOf(selectedNote?.content ?: "") }

    Column(
        modifier = modifier
            .fillMaxSize()
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        // Search & Vault Status Bar
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column {
                Text(
                    text = "Obsidian Vault (MCP Local Integration)",
                    color = NovaTextWhite,
                    fontWeight = FontWeight.Bold,
                    fontSize = 18.sp
                )
                Text(
                    text = "D:\\Documentos\\Obsidian Vault\\NOVA\\",
                    color = NovaCyan,
                    fontSize = 11.sp,
                    fontFamily = FontFamily.Monospace
                )
            }

            Box(
                modifier = Modifier
                    .clip(RoundedCornerShape(6.dp))
                    .background(NovaCyanGlow)
                    .border(1.dp, NovaCyanBorder, RoundedCornerShape(6.dp))
                    .padding(horizontal = 8.dp, vertical = 4.dp)
            ) {
                Text(
                    text = "vault_status: READY",
                    color = NovaCyan,
                    fontSize = 10.sp,
                    fontFamily = FontFamily.Monospace
                )
            }
        }

        // Search Field
        OutlinedTextField(
            value = searchQuery,
            onValueChange = onSearchQueryChange,
            placeholder = { Text("Buscar notas en Vault (ej. Charter, ADRs, reporte_addons)...", color = NovaTextDim, fontSize = 12.sp) },
            leadingIcon = { Icon(Icons.Default.Search, "Search", tint = NovaCyan) },
            modifier = Modifier
                .fillMaxWidth()
                .testTag("obsidian_search_input"),
            singleLine = true,
            colors = OutlinedTextFieldDefaults.colors(
                focusedTextColor = NovaTextWhite,
                unfocusedTextColor = NovaTextWhite,
                focusedContainerColor = NovaBgDarkNavy,
                unfocusedContainerColor = NovaBgDarkNavy,
                focusedBorderColor = NovaCyan,
                unfocusedBorderColor = NovaCyanBorder.copy(alpha = 0.4f)
            ),
            shape = RoundedCornerShape(10.dp)
        )

        // Main 2-Column Layout (Notes List & Note Editor)
        Row(
            modifier = Modifier.fillMaxSize(),
            horizontalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            // Note List Sidebar (120dp wide equivalent)
            LazyColumn(
                modifier = Modifier
                    .weight(0.4f)
                    .fillMaxHeight()
                    .clip(RoundedCornerShape(12.dp))
                    .background(NovaSurfaceCard)
                    .border(1.dp, NovaCyanBorder.copy(alpha = 0.3f), RoundedCornerShape(12.dp))
                    .padding(8.dp),
                verticalArrangement = Arrangement.spacedBy(6.dp)
            ) {
                items(notes) { note ->
                    val isSelected = note.id == selectedNote?.id
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .clip(RoundedCornerShape(8.dp))
                            .background(if (isSelected) NovaCyanGlow else Color.Transparent)
                            .border(
                                1.dp,
                                if (isSelected) NovaCyanBorder else Color.Transparent,
                                RoundedCornerShape(8.dp)
                            )
                            .clickable {
                                selectedNote = note
                                editedContent = note.content
                            }
                            .padding(10.dp)
                            .testTag("obsidian_note_item_${note.id}")
                    ) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Icon(
                                imageVector = if (note.isProtected) Icons.Default.Lock else Icons.Default.Description,
                                contentDescription = null,
                                tint = if (note.isProtected) NovaDangerText else NovaCyan,
                                modifier = Modifier.size(16.dp)
                            )
                            Spacer(modifier = Modifier.width(6.dp))
                            Column {
                                Text(
                                    text = note.title,
                                    color = if (isSelected) NovaCyan else NovaTextWhite,
                                    fontWeight = if (isSelected) FontWeight.Bold else FontWeight.Normal,
                                    fontSize = 11.sp,
                                    fontFamily = FontFamily.Monospace
                                )
                                if (note.isProtected) {
                                    Text(
                                        text = "PROTEGIDO",
                                        color = NovaDangerText,
                                        fontSize = 8.sp,
                                        fontFamily = FontFamily.Monospace
                                    )
                                }
                            }
                        }
                    }
                }
            }

            // Note Content Editor View (Right Pane)
            Box(
                modifier = Modifier
                    .weight(0.6f)
                    .fillMaxHeight()
                    .clip(RoundedCornerShape(12.dp))
                    .background(NovaSurfaceCard)
                    .border(1.dp, NovaCyanBorder.copy(alpha = 0.3f), RoundedCornerShape(12.dp))
                    .padding(14.dp)
            ) {
                if (selectedNote != null) {
                    val curr = selectedNote!!
                    Column(modifier = Modifier.fillMaxSize()) {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Text(
                                    text = curr.title,
                                    color = NovaTextWhite,
                                    fontWeight = FontWeight.Bold,
                                    fontSize = 14.sp
                                )
                                if (curr.isProtected) {
                                    Spacer(modifier = Modifier.width(8.dp))
                                    Box(
                                        modifier = Modifier
                                            .clip(RoundedCornerShape(4.dp))
                                            .background(NovaDangerBg)
                                            .border(1.dp, NovaDangerBorder, RoundedCornerShape(4.dp))
                                            .padding(horizontal = 6.dp, vertical = 2.dp)
                                    ) {
                                        Text(
                                            text = "🔒 Protection Lock: Active",
                                            color = NovaDangerText,
                                            fontSize = 9.sp,
                                            fontFamily = FontFamily.Monospace
                                        )
                                    }
                                }
                            }

                            Button(
                                onClick = { onSaveNote(curr, editedContent) },
                                colors = ButtonDefaults.buttonColors(
                                    containerColor = if (curr.isProtected) NovaDangerBg else NovaCyan,
                                    contentColor = if (curr.isProtected) NovaDangerText else NovaBgCanvas
                                ),
                                shape = RoundedCornerShape(6.dp),
                                modifier = Modifier.testTag("save_note_button")
                            ) {
                                Icon(Icons.Default.Save, "Save", modifier = Modifier.size(16.dp))
                                Spacer(modifier = Modifier.width(4.dp))
                                Text(text = "Guardar", fontSize = 11.sp)
                            }
                        }

                        Text(
                            text = curr.path,
                            color = NovaTextDim,
                            fontSize = 10.sp,
                            fontFamily = FontFamily.Monospace,
                            modifier = Modifier.padding(vertical = 4.dp)
                        )

                        Spacer(modifier = Modifier.height(8.dp))

                        OutlinedTextField(
                            value = editedContent,
                            onValueChange = { editedContent = it },
                            modifier = Modifier
                                .fillMaxSize()
                                .testTag("note_content_editor"),
                            textStyle = androidx.compose.ui.text.TextStyle(
                                color = NovaTextWhite,
                                fontSize = 12.sp,
                                fontFamily = FontFamily.Monospace
                            ),
                            colors = OutlinedTextFieldDefaults.colors(
                                focusedContainerColor = Color(0xFF020610),
                                unfocusedContainerColor = Color(0xFF020610),
                                focusedBorderColor = NovaCyan,
                                unfocusedBorderColor = NovaCyanBorder.copy(alpha = 0.3f)
                            ),
                            shape = RoundedCornerShape(8.dp)
                        )
                    }
                } else {
                    Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                        Text(text = "Selecciona una nota del Vault", color = NovaTextDim)
                    }
                }
            }
        }
    }
}
