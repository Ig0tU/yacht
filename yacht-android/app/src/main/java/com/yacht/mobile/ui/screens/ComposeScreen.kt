package com.yacht.mobile.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.yacht.mobile.MainUiState
import com.yacht.mobile.ui.components.SectionHeader
import com.yacht.mobile.ui.theme.SurfaceElevated

private const val SAMPLE_COMPOSE = """
services:
  web:
    image: nginx:1.27
    ports:
      - \"8080:80\"
"""

@Composable
fun ComposeScreen(
    state: MainUiState,
    onComposeUp: (String) -> Unit
) {
    var composeYaml by rememberSaveable { mutableStateOf(SAMPLE_COMPOSE) }

    Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
        SectionHeader(title = "Compose Up", subtitle = "Launch multiple services with a single YAML")

        Card(
            colors = CardDefaults.cardColors(containerColor = SurfaceElevated.copy(alpha = 0.95f)),
            modifier = Modifier.fillMaxWidth()
        ) {
            Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                OutlinedTextField(
                    value = composeYaml,
                    onValueChange = { composeYaml = it },
                    label = { Text("Compose YAML") },
                    modifier = Modifier.fillMaxWidth(),
                    minLines = 8
                )
                Button(onClick = { onComposeUp(composeYaml) }, enabled = !state.busy) {
                    Text("Compose Up")
                }
            }
        }
        Spacer(modifier = Modifier.height(12.dp))
    }
}
