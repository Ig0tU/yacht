package com.yacht.mobile.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.MaterialTheme
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

@Composable
fun RunScreen(
    state: MainUiState,
    onPullImage: (String) -> Unit,
    onRunImage: (String, String, String) -> Unit
) {
    var image by rememberSaveable { mutableStateOf("alpine:3.19") }
    var command by rememberSaveable { mutableStateOf("") }
    var env by rememberSaveable { mutableStateOf("") }

    Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
        SectionHeader(title = "Run Images", subtitle = "Pull or run containers on the remote host")

        Card(
            colors = CardDefaults.cardColors(containerColor = SurfaceElevated.copy(alpha = 0.95f)),
            modifier = Modifier.fillMaxWidth()
        ) {
            Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                OutlinedTextField(
                    value = image,
                    onValueChange = { image = it },
                    label = { Text("Image") },
                    modifier = Modifier.fillMaxWidth()
                )
                Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                    Button(onClick = { onPullImage(image) }, enabled = !state.busy) { Text("Pull") }
                    Button(onClick = { onRunImage(image, command, env) }, enabled = !state.busy) { Text("Run") }
                }
            }
        }

        Card(
            colors = CardDefaults.cardColors(containerColor = SurfaceElevated.copy(alpha = 0.95f)),
            modifier = Modifier.fillMaxWidth()
        ) {
            Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                Text(text = "Advanced options", style = MaterialTheme.typography.titleMedium)
                OutlinedTextField(
                    value = command,
                    onValueChange = { command = it },
                    label = { Text("Command (optional)") },
                    modifier = Modifier.fillMaxWidth()
                )
                OutlinedTextField(
                    value = env,
                    onValueChange = { env = it },
                    label = { Text("Env (one KEY=VALUE per line)") },
                    modifier = Modifier.fillMaxWidth(),
                    minLines = 3
                )
            }
        }
        Spacer(modifier = Modifier.height(12.dp))
    }
}
