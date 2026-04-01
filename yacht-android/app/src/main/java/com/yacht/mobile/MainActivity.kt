package com.yacht.mobile

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.viewModels
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.yacht.mobile.data.AppRepository
import com.yacht.mobile.data.TokenStore
import com.yacht.mobile.ui.components.YachtBackground
import com.yacht.mobile.ui.screens.AuthScreen
import com.yacht.mobile.ui.screens.YachtApp
import com.yacht.mobile.ui.theme.YachtTheme

class MainActivity : ComponentActivity() {
    private val vm: MainViewModel by viewModels {
        MainViewModel.factory(AppRepository(TokenStore(this)))
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            YachtTheme {
                val state = vm.state.collectAsStateWithLifecycle().value
                YachtBackground {
                    if (!state.loggedIn) {
                        AuthScreen(state = state, onAuth = vm::authenticate)
                    } else {
                        YachtApp(
                            state = state,
                            onRefreshQuota = vm::refreshQuota,
                            onRefreshRemote = vm::refreshRemoteStatus,
                            onPullImage = vm::pullImage,
                            onRunImage = vm::runImage,
                            onComposeUp = vm::composeUp,
                            onUpgrade = {
                                vm.beginCheckout { url ->
                                    startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url)))
                                }
                            },
                            onLogout = vm::logout
                        )
                    }
                }
            }
        }
    }
}
