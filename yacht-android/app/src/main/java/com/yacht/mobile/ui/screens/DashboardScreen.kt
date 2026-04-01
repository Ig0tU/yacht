package com.yacht.mobile.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.yacht.mobile.MainUiState
import com.yacht.mobile.ui.components.InlineTag
import com.yacht.mobile.ui.components.LabeledValue
import com.yacht.mobile.ui.components.SectionHeader
import com.yacht.mobile.ui.components.StatCard
import com.yacht.mobile.ui.components.StatRow
import com.yacht.mobile.ui.theme.Ember
import com.yacht.mobile.ui.theme.NeonCyan
import com.yacht.mobile.ui.theme.Success
import com.yacht.mobile.ui.theme.SurfaceElevated

@Composable
fun DashboardScreen(
    state: MainUiState,
    onRefreshQuota: () -> Unit,
    onRefreshRemote: () -> Unit
) {
    LazyColumn(verticalArrangement = Arrangement.spacedBy(12.dp)) {
        item {
            SectionHeader(
                title = "Command Center",
                subtitle = "Quota, tier, and remote health at a glance"
            )
        }
        item {
            Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                InlineTag(text = state.tier.uppercase(), color = if (state.tier == "pro") Success else Ember)
                Text(text = "Runs today: ${state.runsUsed}", style = MaterialTheme.typography.bodyMedium)
            }
        }
        item {
            StatCard(
                title = "Runs",
                value = "${state.runsUsed} / ${state.runsLimit}",
                accent = NeonCyan
            )
        }
        item {
            StatCard(
                title = "Pulls",
                value = "${state.pullsUsed} / ${state.pullsLimit}",
                accent = Ember
            )
        }
        item {
            StatCard(
                title = "Compose Up",
                value = "${state.composeUsed} / ${state.composeLimit}",
                accent = Success
            )
        }
        item {
            Card(
                colors = CardDefaults.cardColors(containerColor = SurfaceElevated.copy(alpha = 0.95f)),
                modifier = Modifier.fillMaxWidth()
            ) {
                Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                    LabeledValue(label = "Remote Docker", value = state.remoteStatus?.host ?: "Not checked")
                    StatRow(label = "Ping", value = state.remoteStatus?.ping ?: "-")
                    Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                        Button(onClick = onRefreshRemote, enabled = !state.busy) { Text("Check status") }
                        OutlinedButton(onClick = onRefreshQuota, enabled = !state.busy) { Text("Refresh quota") }
                    }
                }
            }
        }
        if (state.activity.isNotEmpty()) {
            item {
                Text(text = "Recent activity", style = MaterialTheme.typography.titleMedium)
            }
            items(state.activity) { entry ->
                Card(
                    colors = CardDefaults.cardColors(containerColor = SurfaceElevated.copy(alpha = 0.9f)),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text(
                        text = entry,
                        style = MaterialTheme.typography.bodyMedium,
                        modifier = Modifier.padding(12.dp)
                    )
                }
            }
        }
        item { Spacer(modifier = Modifier.height(12.dp)) }
    }
}
