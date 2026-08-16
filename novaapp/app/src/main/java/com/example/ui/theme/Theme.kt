package com.example.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable

private val NovaColorScheme =
  darkColorScheme(
    primary = NovaCyan,
    onPrimary = NovaBgCanvas,
    primaryContainer = NovaCyanGlow,
    onPrimaryContainer = NovaCyan,
    secondary = NovaLavender,
    onSecondary = NovaBgCanvas,
    secondaryContainer = NovaPurpleContainer,
    onSecondaryContainer = NovaLavender,
    background = NovaBgCanvas,
    onBackground = NovaTextWhite,
    surface = NovaBgDarkNavy,
    onSurface = NovaTextWhite,
    surfaceVariant = NovaSurfaceCard,
    onSurfaceVariant = NovaTextDim,
    outline = NovaCyanBorder,
    error = NovaDangerText,
    onError = NovaBgCanvas,
  )

@Composable
fun MyApplicationTheme(
  content: @Composable () -> Unit,
) {
  MaterialTheme(
    colorScheme = NovaColorScheme,
    typography = Typography,
    content = content
  )
}
