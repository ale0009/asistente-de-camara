package com.example.ui.screens

import androidx.compose.foundation.Canvas
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
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.FileDownload
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
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

@Composable
fun WarriorStatsScreen(
    onExportToObsidian: () -> Unit,
    modifier: Modifier = Modifier
) {
    Column(
        modifier = modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        // Title Row
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column {
                Text(
                    text = "Warrior Stats & Metrics",
                    color = NovaTextWhite,
                    fontWeight = FontWeight.Bold,
                    fontSize = 18.sp
                )
                Text(
                    text = "Métricas biológicas, hábito y rendimiento agéntico",
                    color = NovaTextDim,
                    fontSize = 11.sp,
                    fontFamily = FontFamily.Monospace
                )
            }

            Button(
                onClick = onExportToObsidian,
                colors = ButtonDefaults.buttonColors(
                    containerColor = NovaCyanGlow,
                    contentColor = NovaCyan
                ),
                border = androidx.compose.foundation.BorderStroke(1.dp, NovaCyanBorder),
                shape = RoundedCornerShape(8.dp),
                modifier = Modifier.testTag("export_stats_button")
            ) {
                Icon(Icons.Default.FileDownload, "Exportar", modifier = Modifier.size(16.dp))
                Spacer(modifier = Modifier.width(6.dp))
                Text(text = "Exportar a Vault", fontSize = 11.sp, fontFamily = FontFamily.Monospace)
            }
        }

        // Hero Master Gauge & Focus Streak Row
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            // Overall Mastery Gauge Ring Card
            Box(
                modifier = Modifier
                    .weight(1f)
                    .clip(RoundedCornerShape(14.dp))
                    .background(NovaSurfaceCard)
                    .border(1.dp, NovaCyanBorder, RoundedCornerShape(14.dp))
                    .padding(16.dp)
            ) {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Text(
                        text = "Overall Mastery",
                        color = NovaTextWhite,
                        fontWeight = FontWeight.Bold,
                        fontSize = 14.sp
                    )

                    Spacer(modifier = Modifier.height(14.dp))

                    Box(
                        modifier = Modifier.size(100.dp),
                        contentAlignment = Alignment.Center
                    ) {
                        Canvas(modifier = Modifier.fillMaxSize()) {
                            drawCircle(
                                color = Color(0x1A00E5FF),
                                style = Stroke(width = 10.dp.toPx())
                            )
                            drawArc(
                                color = Color(0xFF00E5FF),
                                startAngle = -90f,
                                sweepAngle = 360f * 0.78f,
                                useCenter = false,
                                style = Stroke(width = 10.dp.toPx())
                            )
                        }

                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                            Text(
                                text = "78%",
                                color = NovaCyan,
                                fontWeight = FontWeight.Bold,
                                fontSize = 24.sp,
                                fontFamily = FontFamily.Monospace
                            )
                            Text(
                                text = "OPTIMAL",
                                color = NovaSuccessGreen,
                                fontSize = 9.sp,
                                fontFamily = FontFamily.Monospace,
                                fontWeight = FontWeight.Bold
                            )
                        }
                    }

                    Spacer(modifier = Modifier.height(14.dp))

                    Column(
                        modifier = Modifier.fillMaxWidth(),
                        verticalArrangement = Arrangement.spacedBy(4.dp)
                    ) {
                        StatProgressItem(label = "Strength", valStr = "82%", percent = 0.82f)
                        StatProgressItem(label = "Focus", valStr = "75%", percent = 0.75f)
                        StatProgressItem(label = "Endurance", valStr = "79%", percent = 0.79f)
                    }
                }
            }

            // Focus Streak & Consistency Badge Card
            Box(
                modifier = Modifier
                    .weight(1f)
                    .clip(RoundedCornerShape(14.dp))
                    .background(NovaSurfaceCard)
                    .border(1.dp, NovaCyanBorder, RoundedCornerShape(14.dp))
                    .padding(16.dp)
            ) {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Text(
                        text = "Focus Streak",
                        color = NovaTextWhite,
                        fontWeight = FontWeight.Bold,
                        fontSize = 14.sp
                    )

                    Spacer(modifier = Modifier.height(14.dp))

                    Box(
                        modifier = Modifier
                            .size(100.dp)
                            .clip(CircleShape)
                            .background(NovaCyanGlow)
                            .border(2.dp, NovaLavender, CircleShape),
                        contentAlignment = Alignment.Center
                    ) {
                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                            Text(text = "💎", fontSize = 36.sp)
                            Text(text = "14 DAYS", color = NovaCyan, fontSize = 11.sp, fontWeight = FontWeight.Bold, fontFamily = FontFamily.Monospace)
                        }
                    }

                    Spacer(modifier = Modifier.height(14.dp))

                    Column(
                        modifier = Modifier.fillMaxWidth(),
                        verticalArrangement = Arrangement.spacedBy(4.dp)
                    ) {
                        StatProgressItem(label = "Weekly Consistency", valStr = "94%", percent = 0.94f)
                        StatProgressItem(label = "Deep Work Hours", valStr = "6.5h/d", percent = 0.80f)
                        StatProgressItem(label = "Distraction Rate", valStr = "0.2/h", percent = 0.95f)
                    }
                }
            }
        }

        // Trends Line Chart Canvas Box
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(14.dp))
                .background(NovaSurfaceCard)
                .border(1.dp, NovaCyanBorder.copy(alpha = 0.3f), RoundedCornerShape(14.dp))
                .padding(16.dp)
        ) {
            Column {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "Rendimiento Semanal (Últimos 7 días)",
                        color = NovaTextWhite,
                        fontWeight = FontWeight.Bold,
                        fontSize = 13.sp
                    )

                    Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Box(modifier = Modifier.size(8.dp).background(NovaCyan, CircleShape))
                            Spacer(modifier = Modifier.width(4.dp))
                            Text("Enfoque", color = NovaTextDim, fontSize = 10.sp)
                        }
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Box(modifier = Modifier.size(8.dp).background(NovaLavender, CircleShape))
                            Spacer(modifier = Modifier.width(4.dp))
                            Text("Postura", color = NovaTextDim, fontSize = 10.sp)
                        }
                    }
                }

                Spacer(modifier = Modifier.height(16.dp))

                // Line Chart Canvas
                Canvas(
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(140.dp)
                ) {
                    val w = size.width
                    val h = size.height

                    // Grid Lines
                    val gridColor = Color(0x1AFFFFFF)
                    for (i in 1..4) {
                        val y = h * (i / 5f)
                        drawLine(gridColor, Offset(0f, y), Offset(w, y), 1.dp.toPx())
                    }

                    // Cyan Line (Enfoque Trend)
                    val cyanPoints = listOf(
                        Offset(0f, h * 0.7f),
                        Offset(w * 0.16f, h * 0.5f),
                        Offset(w * 0.33f, h * 0.6f),
                        Offset(w * 0.50f, h * 0.3f),
                        Offset(w * 0.66f, h * 0.4f),
                        Offset(w * 0.83f, h * 0.2f),
                        Offset(w, h * 0.15f)
                    )

                    val cyanPath = Path().apply {
                        moveTo(cyanPoints[0].x, cyanPoints[0].y)
                        for (i in 1 until cyanPoints.size) {
                            lineTo(cyanPoints[i].x, cyanPoints[i].y)
                        }
                    }

                    drawPath(cyanPath, Color(0xFF00E5FF), style = Stroke(width = 3.dp.toPx()))
                    cyanPoints.forEach { pt ->
                        drawCircle(Color(0xFF00E5FF), radius = 4.dp.toPx(), center = pt)
                    }

                    // Lavender Line (Postura Trend)
                    val lavenderPoints = listOf(
                        Offset(0f, h * 0.8f),
                        Offset(w * 0.16f, h * 0.65f),
                        Offset(w * 0.33f, h * 0.45f),
                        Offset(w * 0.50f, h * 0.5f),
                        Offset(w * 0.66f, h * 0.35f),
                        Offset(w * 0.83f, h * 0.3f),
                        Offset(w, h * 0.25f)
                    )

                    val lavenderPath = Path().apply {
                        moveTo(lavenderPoints[0].x, lavenderPoints[0].y)
                        for (i in 1 until lavenderPoints.size) {
                            lineTo(lavenderPoints[i].x, lavenderPoints[i].y)
                        }
                    }

                    drawPath(lavenderPath, Color(0xFF946EF0), style = Stroke(width = 2.dp.toPx()))
                    lavenderPoints.forEach { pt ->
                        drawCircle(Color(0xFF946EF0), radius = 3.dp.toPx(), center = pt)
                    }
                }

                Spacer(modifier = Modifier.height(8.dp))

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    val days = listOf("Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom")
                    days.forEach { day ->
                        Text(text = day, color = NovaTextDim, fontSize = 10.sp, fontFamily = FontFamily.Monospace)
                    }
                }
            }
        }
    }
}

@Composable
fun StatProgressItem(label: String, valStr: String, percent: Float) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text(text = label, color = NovaTextDim, fontSize = 10.sp)
        Text(text = valStr, color = NovaCyan, fontSize = 10.sp, fontWeight = FontWeight.Bold, fontFamily = FontFamily.Monospace)
    }
    Box(
        modifier = Modifier
            .fillMaxWidth()
            .height(4.dp)
            .clip(RoundedCornerShape(2.dp))
            .background(Color(0x1A00E5FF))
    ) {
        Box(
            modifier = Modifier
                .fillMaxWidth(percent)
                .height(4.dp)
                .clip(RoundedCornerShape(2.dp))
                .background(NovaCyan)
        )
    }
}
