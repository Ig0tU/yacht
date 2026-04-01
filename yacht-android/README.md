# Yacht Android App

Kotlin + Jetpack Compose mobile client for Yacht Cloud.

## Configure API

Set API base URL in:

- `app/build.gradle.kts` -> `BuildConfig.API_BASE_URL`

Example for local dev:

```kotlin
buildConfigField("String", "API_BASE_URL", "\"http://10.0.2.2:8090/\"")
```

## Features wired

- Register/login (`/v1/auth/register`, `/v1/auth/login`)
- Token refresh (`/v1/auth/refresh`)
- Quota display (`/v1/quota`)
- Remote status (`/v1/remote/status`)
- Image pull (`/v1/images/pull`)
- Container run (`/v1/containers/run`)
- Compose up (`/v1/compose/up`)
- Upgrade flow (`/v1/billing/checkout-session`) opens Stripe hosted checkout URL

Notes:
- Debug builds allow cleartext traffic for local dev; release builds do not.
- Tokens are stored using encrypted shared preferences when available.

## Play Store release checklist

1. Create release keystore and set signing config in `app/build.gradle.kts`.
   - Copy `keystore.properties.example` -> `keystore.properties` and fill real values.
2. Replace API URL with production HTTPS domain.
3. Enable minify/shrink and add crash reporting.
4. Upload AAB in Play Console (internal track first).
5. Validate billing + webhook events in production.
