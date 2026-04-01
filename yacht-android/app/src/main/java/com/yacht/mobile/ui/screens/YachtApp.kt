package com.yacht.mobile.ui.screens

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.AccountCircle
import androidx.compose.material.icons.outlined.Home
import androidx.compose.material.icons.outlined.Layers
import androidx.compose.material.icons.outlined.Terminal
import androidx.compose.material3.CenterAlignedTopAppBar
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import androidx.navigation.NavGraph.Companion.findStartDestination
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import com.yacht.mobile.MainUiState
import com.yacht.mobile.ui.components.MessageBanner
import com.yacht.mobile.ui.theme.NeonCyan

sealed class YachtDestination(val route: String, val label: String, val icon: androidx.compose.ui.graphics.vector.ImageVector) {
    data object Dashboard : YachtDestination("dashboard", "Home", Icons.Outlined.Home)
    data object Run : YachtDestination("run", "Run", Icons.Outlined.Terminal)
    data object Compose : YachtDestination("compose", "Compose", Icons.Outlined.Layers)
    data object Account : YachtDestination("account", "Account", Icons.Outlined.AccountCircle)
}

private val destinations = listOf(
    YachtDestination.Dashboard,
    YachtDestination.Run,
    YachtDestination.Compose,
    YachtDestination.Account
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun YachtApp(
    state: MainUiState,
    onRefreshQuota: () -> Unit,
    onRefreshRemote: () -> Unit,
    onPullImage: (String) -> Unit,
    onRunImage: (String, String, String) -> Unit,
    onComposeUp: (String) -> Unit,
    onUpgrade: () -> Unit,
    onLogout: () -> Unit
) {
    val navController = rememberNavController()
    val navBackStackEntry by navController.currentBackStackEntryAsState()
    val currentRoute = navBackStackEntry?.destination?.route
    val title = destinations.firstOrNull { it.route == currentRoute }?.label ?: "Yacht"

    Scaffold(
        containerColor = Color.Transparent,
        topBar = {
            CenterAlignedTopAppBar(title = { Text(text = title) })
        },
        bottomBar = {
            NavigationBar(containerColor = Color.Transparent) {
                destinations.forEach { destination ->
                    val selected = currentRoute == destination.route
                    NavigationBarItem(
                        selected = selected,
                        onClick = {
                            navController.navigate(destination.route) {
                                popUpTo(navController.graph.findStartDestination().id) { saveState = true }
                                launchSingleTop = true
                                restoreState = true
                            }
                        },
                        icon = { Icon(destination.icon, contentDescription = destination.label) },
                        label = { Text(destination.label) }
                    )
                }
            }
        }
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(horizontal = 20.dp, vertical = 12.dp)
        ) {
            if (state.busy) {
                LinearProgressIndicator(
                    modifier = Modifier.fillMaxWidth(),
                    color = NeonCyan
                )
                Spacer(modifier = Modifier.height(8.dp))
            }
            if (state.message.isNotBlank()) {
                MessageBanner(state.message)
                Spacer(modifier = Modifier.height(12.dp))
            }
            NavHost(
                navController = navController,
                startDestination = YachtDestination.Dashboard.route,
                modifier = Modifier.weight(1f)
            ) {
                composable(YachtDestination.Dashboard.route) {
                    DashboardScreen(state = state, onRefreshQuota = onRefreshQuota, onRefreshRemote = onRefreshRemote)
                }
                composable(YachtDestination.Run.route) {
                    RunScreen(state = state, onPullImage = onPullImage, onRunImage = onRunImage)
                }
                composable(YachtDestination.Compose.route) {
                    ComposeScreen(state = state, onComposeUp = onComposeUp)
                }
                composable(YachtDestination.Account.route) {
                    AccountScreen(state = state, onUpgrade = onUpgrade, onLogout = onLogout)
                }
            }
        }
    }
}
