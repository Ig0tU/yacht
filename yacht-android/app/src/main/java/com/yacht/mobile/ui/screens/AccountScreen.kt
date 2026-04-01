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
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.yacht.mobile.BuildConfig
import com.yacht.mobile.MainUiState
import com.yacht.mobile.ui.components.InlineTag
import com.yacht.mobile.ui.components.LabeledValue
import com.yacht.mobile.ui.components.SectionHeader
import com.yacht.mobile.ui.theme.Ember
import com.yacht.mobile.ui.theme.Success
import com.yacht.mobile.ui.theme.SurfaceElevated

@Composable
fun AccountScreen(
    state: MainUiState,
    onUpgrade: () -> Unit,
    onLogout: () -> Unit
) {
    Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
        SectionHeader(title = "Account", subtitle = "Billing, API host, and session")

        Card(
            colors = CardDefaults.cardColors(containerColor = SurfaceElevated.copy(alpha = 0.95f)),
            modifier = Modifier.fillMaxWidth()
        ) {
            Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                    Text(text = "Tier", style = MaterialTheme.typography.labelLarge)
                    InlineTag(text = state.tier.uppercase(), color = if (state.tier == "pro") Success else Ember)
                }
                LabeledValue(label = "API base", value = BuildConfig.API_BASE_URL)
                if (state.tier == "free") {
                    Button(onClick = onUpgrade, enabled = !state.busy, modifier = Modifier.fillMaxWidth()) {
                        Text("Upgrade to Pro")
                    }
                }
                OutlinedButton(onClick = onLogout, enabled = !state.busy, modifier = Modifier.fillMaxWidth()) {
                    Text("Logout")
                }
            }
        }
        Spacer(modifier = Modifier.height(12.dp))
    }
}
