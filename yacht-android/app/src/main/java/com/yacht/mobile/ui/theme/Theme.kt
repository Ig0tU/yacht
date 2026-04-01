package com.yacht.mobile.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

private val YachtColorScheme = darkColorScheme(
    primary = ElectricBlue,
    secondary = NeonCyan,
    tertiary = Ember,
    background = DeepNavy,
    surface = SurfaceDark,
    surfaceVariant = SurfaceElevated,
    onPrimary = DeepNavy,
    onSecondary = DeepNavy,
    onTertiary = DeepNavy,
    onBackground = Color.White,
    onSurface = Color.White,
    onSurfaceVariant = Slate,
    error = Ember,
    onError = Color.Black
)

@Composable
fun YachtTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = YachtColorScheme,
        typography = YachtTypography,
        content = content
    )
}
