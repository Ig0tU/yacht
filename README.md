# Yacht: Mobile-First Docker Shim

Yacht is a Docker-compatible-leaning mobile runtime shim and cloud API.

## Project Structure

- `yacht-cloud/`: FastAPI backend for remote execution, auth, and billing.
- `yacht-mobile/`: Python CLI tool for image pull, hydration, and local/remote run.
- `yacht-android/`: Kotlin + Jetpack Compose mobile client.

## Quickstart (On-Ramper)

The easiest way to get started with Yacht is to use the provided on-ramper script. This script automates the setup of all project components, configures the environments, and launches the cloud backend locally.

```bash
./onramp.sh
```

The script will:
1.  **Setup Yacht Cloud**: Create a virtual environment, install dependencies, and initialize the database and environment variables.
2.  **Setup Yacht Mobile**: Create a virtual environment and install the CLI tool.
3.  **Configure Yacht Android**: Point the mobile app to the local cloud backend and initialize signing properties.
4.  **Launch Backend**: Start the Yacht Cloud API server on port 3000.

### Interacting with Yacht

- **Web API Docs**: Once the on-ramper is finished, visit [http://localhost:3000/docs](http://localhost:3000/docs) to explore the API.
- **Mobile CLI**: Use the CLI from its virtual environment:
    ```bash
    yacht-mobile/.venv/bin/yacht pull alpine:3.19
    yacht-mobile/.venv/bin/yacht run alpine:3.19 -- echo "Hello from Yacht"
    ```
- **Android App**: Open the `yacht-android` project in Android Studio to build and run the app on an emulator. The app is pre-configured to talk to the local backend.

## Manual Setup

See the `README.md` in each subdirectory for detailed manual setup instructions.
