# Aurelia Reader Android

Native Android reader for Aurelia.

## V1 scope

- Server setup and Bearer login
- Session restore and logout
- Library list, search, book detail and related books
- EPUB reading with Readium
- Optional offline download
- Temporary online read cache when the user taps Lire
- Local progress restore
- Server progress sync with local queue
- Reader overlay, chapter list, themes and reading settings

## Build

```powershell
$workspace = (Resolve-Path '..').Path
$sdkRoot = Join-Path $workspace '.local\android-sdk'
$env:JAVA_HOME='C:\Program Files\Java\jdk-21'
$env:ANDROID_HOME=$sdkRoot
$env:ANDROID_SDK_ROOT=$sdkRoot
$env:Path="$env:JAVA_HOME\bin;$sdkRoot\cmdline-tools\latest\bin;$env:Path"
.\gradlew.bat assembleDebug
```

Debug APK:

```txt
app/build/outputs/apk/debug/app-debug.apk
```

## Install on device

```powershell
$sdkRoot = Join-Path (Resolve-Path '..').Path '.local\android-sdk'
$apk = Join-Path (Resolve-Path '.').Path 'app\build\outputs\apk\debug\app-debug.apk'
& "$sdkRoot\platform-tools\adb.exe" install -r $apk
```

## Device notes

- On a physical phone, do not use `127.0.0.1`; that points to the phone itself.
- Use the PC LAN IP with the server port, for example `http://192.168.2.6:3000`.
- The debug app allows cleartext HTTP for local/self-hosted development.
- `Lire` can open a non-downloaded book using a temporary cache file.
- `Telecharger` keeps the book available offline.
