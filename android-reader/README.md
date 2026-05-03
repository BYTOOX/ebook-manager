# Aurelia Reader Android

Native Android reader for Aurelia.

## Scope

- Server setup and Bearer login
- Session restore and logout
- Library list, search, book detail and related books
- EPUB reading with Readium
- Optional offline download
- Temporary online read cache when the user taps Lire
- Local progress restore
- Server progress sync with a per-install device id
- Reader overlay, chapter list, themes and reading settings

## Debug build

```powershell
$workspace = (Resolve-Path '..').Path
$sdkRoot = Join-Path $workspace '.local\android-sdk'
$env:JAVA_HOME='C:\Program Files\Java\jdk-21'
$env:ANDROID_HOME=$sdkRoot
$env:ANDROID_SDK_ROOT=$sdkRoot
$env:Path="$env:JAVA_HOME\bin;$sdkRoot\cmdline-tools\latest\bin;$env:Path"
.\gradlew.bat :app:assembleDebug
```

Debug APK:

```txt
app/build/outputs/apk/debug/app-debug.apk
```

Debug builds allow cleartext HTTP so a phone can connect to a local or LAN Aurelia server during development.

## Release build

Release builds are HTTPS-only, disable Android backup, and enable R8/resource shrinking.

```powershell
.\gradlew.bat :app:assembleRelease
.\gradlew.bat :app:bundleRelease
```

Release outputs:

```txt
app/build/outputs/apk/release/
app/build/outputs/bundle/release/
```

If no signing variables are provided, Gradle can produce unsigned release artifacts for validation. Provide all signing variables below to create signed artifacts.

## Release signing

Create a keystore outside the repository:

```powershell
keytool -genkeypair `
  -v `
  -keystore aurelia-reader-release.jks `
  -alias aurelia-reader `
  -keyalg RSA `
  -keysize 4096 `
  -validity 10000
```

Set all variables before building a signed release:

```powershell
$env:AURELIA_KEYSTORE_PATH="C:\secure\aurelia-reader-release.jks"
$env:AURELIA_KEYSTORE_PASSWORD="..."
$env:AURELIA_KEY_ALIAS="aurelia-reader"
$env:AURELIA_KEY_PASSWORD="..."
.\gradlew.bat :app:assembleRelease :app:bundleRelease
```

Do not commit keystores, passwords, tokens, or local signing paths.

## Install on device

```powershell
$sdkRoot = Join-Path (Resolve-Path '..').Path '.local\android-sdk'
$apk = Join-Path (Resolve-Path '.').Path 'app\build\outputs\apk\debug\app-debug.apk'
& "$sdkRoot\platform-tools\adb.exe" install -r $apk
```

## Network behavior

- Debug accepts `http://` and `https://` server URLs.
- Release rejects `http://` server URLs before sending requests.
- Release requires a server URL beginning with `https://`.
- Bearer tokens are only attached to requests targeting the configured Aurelia API origin.
- External cover downloads use an unauthenticated HTTP client.

On a physical phone, do not use `127.0.0.1`; that points to the phone itself. Use the PC LAN IP with the server port, for example `http://192.168.2.6:3000`, in debug builds only.

## Validation

Run from `android-reader/`:

```powershell
.\gradlew.bat clean
.\gradlew.bat :app:assembleDebug
.\gradlew.bat :app:testDebugUnitTest
.\gradlew.bat :app:lint
.\gradlew.bat :app:assembleRelease
.\gradlew.bat :app:bundleRelease
```

Manual release smoke tests:

- Fresh install release APK.
- HTTPS login works.
- HTTP server URL is rejected in release.
- Book list, search and detail load.
- EPUB opens in release with R8 enabled.
- Reading progress saves and syncs.
- Offline download and offline read work.
- Logout clears the local session.
- External cover URLs do not receive the Authorization header.

## CI

GitHub Actions runs debug assemble, unit tests and lint on Android reader changes. Tag pushes matching `v*` or `android-reader-v*` build release APK and AAB artifacts. Configure these optional repository secrets for signed release artifacts:

- `AURELIA_KEYSTORE_BASE64`
- `AURELIA_KEYSTORE_PASSWORD`
- `AURELIA_KEY_ALIAS`
- `AURELIA_KEY_PASSWORD`

## Release notes

Suggested first hardened tag: `v0.2.1-beta.1`.

Known limitations:

- Self-hosted Aurelia server required.
- Debug builds may allow HTTP for local development.
- Release builds require HTTPS.
- Token storage still uses DataStore preferences; backup is disabled for the first release.
- Migration and reader lifecycle testing still need broad real-device coverage.
