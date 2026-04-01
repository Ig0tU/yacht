package com.yacht.mobile

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.yacht.mobile.data.AppRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import retrofit2.HttpException

data class MainUiState(
    val loggedIn: Boolean = false,
    val tier: String = "free",
    val runsUsed: Int = 0,
    val pullsUsed: Int = 0,
    val composeUsed: Int = 0,
    val runsLimit: String = "-",
    val pullsLimit: String = "-",
    val composeLimit: String = "-",
    val message: String = "",
    val busy: Boolean = false,
    val remoteStatus: RemoteStatusUi? = null,
    val activity: List<String> = emptyList()
)

data class RemoteStatusUi(
    val host: String,
    val ping: String
)

class MainViewModel(private val repo: AppRepository) : ViewModel() {
    private val _state = MutableStateFlow(MainUiState())
    val state: StateFlow<MainUiState> = _state.asStateFlow()

    init {
        viewModelScope.launch { refreshQuotaInternal() }
    }

    fun authenticate(email: String, password: String, createAccount: Boolean) = viewModelScope.launch {
        runCatching {
            _state.value = _state.value.copy(busy = true, message = "")
            repo.authenticate(email, password, createAccount)
            refreshQuotaInternal(if (createAccount) "Account created" else "Logged in")
        }.onFailure {
            val msg = when (it) {
                is HttpException -> when (it.code()) {
                    401 -> "Invalid credentials"
                    409 -> "Email already exists"
                    else -> "Auth failed: ${it.message()}"
                }
                else -> "Auth failed: ${it.message}"
            }
            _state.value = _state.value.copy(message = msg)
        }.also {
            _state.value = _state.value.copy(busy = false)
        }
    }

    fun refreshQuota() = viewModelScope.launch {
        _state.value = _state.value.copy(busy = true)
        refreshQuotaInternal()
        _state.value = _state.value.copy(busy = false)
    }

    fun refreshRemoteStatus() = viewModelScope.launch {
        runCatching {
            _state.value = _state.value.copy(busy = true, message = "")
            val status = repo.getRemoteStatus()
            _state.value = _state.value.copy(
                remoteStatus = RemoteStatusUi(host = status.host, ping = status.ping),
                message = ""
            )
        }.onFailure {
            _state.value = _state.value.copy(message = "Status failed: ${it.message}")
        }.also {
            _state.value = _state.value.copy(busy = false)
        }
    }

    fun pullImage(image: String) = viewModelScope.launch {
        runCatching {
            _state.value = _state.value.copy(busy = true, message = "")
            val pulled = repo.pullImage(image)
            refreshQuotaInternal("Pulled: $pulled")
            pushActivity("Pulled $pulled")
        }.onFailure {
            val msg = when (it) {
                is HttpException -> when (it.code()) {
                    401 -> "Session expired. Please log in again."
                    402 -> "Free limit reached. Upgrade to Pro."
                    else -> "Pull failed: ${it.message()}"
                }
                else -> "Pull failed: ${it.message}"
            }
            _state.value = _state.value.copy(message = msg)
        }.also {
            _state.value = _state.value.copy(busy = false)
        }
    }

    fun runImage(image: String, command: String, env: String) = viewModelScope.launch {
        runCatching {
            _state.value = _state.value.copy(busy = true, message = "")
            val cmd = parseCommand(command)
            val envList = parseEnv(env)
            val cid = repo.runContainer(image, cmd, envList)
            refreshQuotaInternal("Started: $cid")
            pushActivity("Run $image -> ${cid.take(12)}")
        }.onFailure {
            val msg = when (it) {
                is HttpException -> when (it.code()) {
                    401 -> "Session expired. Please log in again."
                    402 -> "Free limit reached. Upgrade to Pro."
                    else -> "Run failed: ${it.message()}"
                }
                else -> "Run failed: ${it.message}"
            }
            _state.value = _state.value.copy(message = msg)
        }.also {
            _state.value = _state.value.copy(busy = false)
        }
    }

    fun composeUp(composeYaml: String) = viewModelScope.launch {
        runCatching {
            _state.value = _state.value.copy(busy = true, message = "")
            val result = repo.composeUp(composeYaml)
            refreshQuotaInternal("Compose started: ${result.count} services")
            pushActivity("Compose up: ${result.count} services")
        }.onFailure {
            val msg = when (it) {
                is HttpException -> when (it.code()) {
                    400 -> "Compose YAML is invalid."
                    401 -> "Session expired. Please log in again."
                    402 -> "Free limit reached. Upgrade to Pro."
                    else -> "Compose failed: ${it.message()}"
                }
                else -> "Compose failed: ${it.message}"
            }
            _state.value = _state.value.copy(message = msg)
        }.also {
            _state.value = _state.value.copy(busy = false)
        }
    }

    fun beginCheckout(launch: (String) -> Unit) = viewModelScope.launch {
        runCatching {
            _state.value = _state.value.copy(busy = true, message = "")
            val url = repo.checkoutUrl()
            launch(url)
        }.onFailure {
            val msg = when (it) {
                is HttpException -> when (it.code()) {
                    400 -> "Billing is not configured."
                    401 -> "Session expired. Please log in again."
                    else -> "Checkout failed: ${it.message()}"
                }
                else -> "Checkout failed: ${it.message}"
            }
            _state.value = _state.value.copy(message = msg)
        }.also {
            _state.value = _state.value.copy(busy = false)
        }
    }

    fun logout() {
        repo.logout()
        _state.value = MainUiState(message = "Logged out")
    }

    private suspend fun refreshQuotaInternal(successMessage: String? = null) {
        runCatching {
            val q = repo.getQuota()
            _state.value = _state.value.copy(
                loggedIn = repo.hasToken(),
                tier = q.tier,
                runsUsed = q.usedToday.run,
                pullsUsed = q.usedToday.pull,
                composeUsed = q.usedToday.composeUp,
                runsLimit = q.limits.run?.toString() ?: "unlimited",
                pullsLimit = q.limits.pull?.toString() ?: "unlimited",
                composeLimit = q.limits.composeUp?.toString() ?: "unlimited",
                message = successMessage ?: ""
            )
        }.onFailure {
            _state.value = _state.value.copy(
                loggedIn = repo.hasToken(),
                message = if (repo.hasToken()) "Failed to refresh: ${it.message}" else "Login required"
            )
        }
    }

    private fun pushActivity(entry: String) {
        val next = listOf(entry) + _state.value.activity
        _state.value = _state.value.copy(activity = next.take(5))
    }

    private fun parseCommand(raw: String): List<String>? {
        val trimmed = raw.trim()
        if (trimmed.isEmpty()) return null
        return trimmed.split(Regex("\\s+")).filter { it.isNotBlank() }
    }

    private fun parseEnv(raw: String): List<String>? {
        val lines = raw.lines().map { it.trim() }.filter { it.isNotBlank() }
        return if (lines.isEmpty()) null else lines
    }

    companion object {
        fun factory(repo: AppRepository): ViewModelProvider.Factory =
            object : ViewModelProvider.Factory {
                @Suppress("UNCHECKED_CAST")
                override fun <T : ViewModel> create(modelClass: Class<T>): T {
                    return MainViewModel(repo) as T
                }
            }
    }
}
