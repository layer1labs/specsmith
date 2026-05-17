# SPDX-License-Identifier: MIT
"""Mobile development skills — iOS, Android, Flutter, React Native."""

from specsmith.skills import SkillDomain, SkillEntry

SKILLS: list[SkillEntry] = [
    SkillEntry(
        slug="ios-dev",
        name="iOS — Xcode, Swift, SPM, TestFlight, fastlane, code signing",
        description=(
            "iOS app development workflow: Xcode project setup, Swift Package Manager, "
            "simulator testing, Instruments profiling, TestFlight beta, and fastlane CI."
        ),
        domain=SkillDomain.MOBILE,
        tags=[
            "ios",
            "swift",
            "xcode",
            "spm",
            "testflight",
            "fastlane",
            "apple",
            "iphone",
            "ipad",
            "cocoapods",
            "signing",
        ],
        project_types=["mobile-app"],
        platforms=["macos"],
        prerequisites=["xcode", "fastlane"],
        body="""\
# iOS Development Skill

## Project setup
```bash
# Create new project: Xcode → File → New Project → iOS App
# Or via command line:
xcodegen generate   # if using XcodeGen (project.yml)

# Add Swift Package:
# Xcode → File → Add Package Dependencies → paste URL
# Or Package.swift:
dependencies: [
    .package(url: "https://github.com/Alamofire/Alamofire", from: "5.9.0"),
]
```

## Build & test from CLI
```bash
xcodebuild -scheme MyApp -destination 'platform=iOS Simulator,name=iPhone 15' build
xcodebuild test -scheme MyApp \
    -destination 'platform=iOS Simulator,name=iPhone 15 Pro' \
    -resultBundlePath TestResults
xcrun simctl list devices   # list simulators
xcrun simctl boot "iPhone 15 Pro"
```

## Code signing
```bash
# Automatic (Development): Xcode → Signing & Capabilities → Team
# Manual (Distribution):
# 1. Create App ID on developer.apple.com
# 2. Create distribution certificate + provisioning profile
# 3. Download + install provisioning profile
# 4. Set in Xcode: Provisioning Profile → Manual → select

# Verify signing:
codesign -dv --verbose=4 MyApp.app
```

## Instruments profiling
```
Xcode → Product → Profile (⌘I)
Templates: Time Profiler (CPU), Allocations (memory leaks), Network, Energy Log
```

## fastlane automation
```ruby
# Fastfile
lane :beta do
  increment_build_number
  build_ios_app(
    scheme: "MyApp",
    export_method: "app-store",
    configuration: "Release"
  )
  upload_to_testflight(skip_waiting_for_build_processing: true)
end

lane :screenshots do
  capture_ios_screenshots
  frame_screenshots
end
```
```bash
fastlane beta          # build + upload to TestFlight
fastlane deliver       # submit to App Store review
fastlane match init    # set up match for team code signing
```

## App Store submission checklist
1. Privacy manifest (`PrivacyInfo.xcprivacy`) — required from May 2024.
2. App Privacy labels in App Store Connect.
3. 6.7" + 6.5" + 5.5" screenshots minimum.
4. Release notes in all supported locales.
5. Export compliance declaration.

## Common pitfalls
- macOS only: Xcode does not run on Windows or Linux.
- Simulator ≠ device: test on physical device before App Store submission.
- Provisioning profile mismatch: always use `fastlane match` for team signing.
- Swift Package cache: `rm -rf ~/Library/Caches/org.swift.swiftpm/` to force refresh.
""",
    ),
    SkillEntry(
        slug="android-dev",
        name="Android — Gradle, ADB, emulator, Play Store, fastlane",
        description=(
            "Android app development: Gradle build system, ADB device management, "
            "emulator, ProGuard/R8 obfuscation, Play Store upload, and fastlane."
        ),
        domain=SkillDomain.MOBILE,
        tags=[
            "android",
            "kotlin",
            "java",
            "gradle",
            "adb",
            "emulator",
            "play-store",
            "fastlane",
            "jetpack-compose",
            "android-studio",
        ],
        project_types=["mobile-app"],
        platforms=["windows", "linux", "macos"],
        prerequisites=["java", "gradle"],
        body="""\
# Android Development Skill

## Gradle build commands
```bash
./gradlew assembleDebug           # build debug APK
./gradlew assembleRelease         # build release APK (needs signing config)
./gradlew bundleRelease           # build AAB (required for Play Store)
./gradlew test                    # unit tests
./gradlew connectedAndroidTest    # instrumented tests (needs device/emulator)
./gradlew lint                    # lint check
./gradlew dependencyUpdates       # check for outdated dependencies (gradle-versions-plugin)
```

## ADB device management
```bash
adb devices                        # list connected devices
adb -s <serial> install myapp.apk  # install to specific device
adb shell am start -n com.myapp/.MainActivity  # launch activity
adb logcat -s MyTag                # filter logcat by tag
adb logcat *:E                     # errors only
adb shell dumpsys meminfo com.myapp  # memory usage
adb shell input tap 540 960        # simulate tap at coordinates
adb shell screencap /sdcard/screen.png && adb pull /sdcard/screen.png
```

## Emulator management
```bash
# List available AVDs
emulator -list-avds

# Start emulator
emulator -avd Pixel_6_API_34 -no-snapshot-load

# Create AVD (headless CI)
avdmanager create avd -n test-avd -k "system-images;android-34;google_apis;x86_64"
emulator -avd test-avd -no-window -no-audio &
adb wait-for-device shell 'while [[ -z $(getprop sys.boot_completed) ]]; do sleep 1; done'
```

## Signing configuration (build.gradle.kts)
```kotlin
android {
    signingConfigs {
        create("release") {
            storeFile = file(System.getenv("KEYSTORE_PATH") ?: "keystore.jks")
            storePassword = System.getenv("KEYSTORE_PASSWORD")
            keyAlias = System.getenv("KEY_ALIAS")
            keyPassword = System.getenv("KEY_PASSWORD")
        }
    }
    buildTypes {
        release {
            signingConfig = signingConfigs["release"]
            isMinifyEnabled = true
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"))
        }
    }
}
```

## fastlane for Android
```ruby
lane :deploy do
  gradle(task: "bundle", build_type: "Release")
  upload_to_play_store(
    track: "internal",
    aab: "app/build/outputs/bundle/release/app-release.aab",
    json_key: "service-account.json"
  )
end
```

## Common pitfalls
- AAB (not APK) required for new Play Store apps since 2021.
- 64-bit requirement: all native code must have 64-bit version.
- Target SDK: must target SDK 34+ for new apps in 2024.
- Gradle cache corruption: `./gradlew clean` or delete `~/.gradle/caches/`.
- ProGuard rules: add `-keep` rules for reflection-heavy libraries (Gson, Retrofit).
""",
    ),
    SkillEntry(
        slug="flutter-mobile",
        name="Flutter — Dart, platform channels, build variants, Pub",
        description=(
            "Flutter cross-platform app development: project structure, "
            "pub package management, platform channels, build variants, and CI."
        ),
        domain=SkillDomain.MOBILE,
        tags=[
            "flutter",
            "dart",
            "cross-platform",
            "ios",
            "android",
            "pub",
            "platform-channels",
            "widget",
            "bloc",
            "riverpod",
        ],
        project_types=["mobile-app"],
        platforms=["windows", "linux", "macos"],
        prerequisites=["flutter", "dart"],
        body="""\
# Flutter Development Skill

## Setup
```bash
flutter doctor                     # check environment
flutter doctor --android-licenses  # accept Android licenses
flutter upgrade                    # upgrade Flutter SDK
```

## Project commands
```bash
flutter create myapp               # new project
flutter pub get                    # install dependencies
flutter pub upgrade                # upgrade dependencies
flutter pub outdated               # check for updates
flutter run                        # run on connected device
flutter run -d chrome              # run as web app
flutter run --flavor production    # run specific flavor
flutter test                       # unit + widget tests
flutter test integration_test/     # integration tests
```

## Build commands (cross-platform)
```bash
# Android
flutter build apk --release                    # APK
flutter build appbundle --release              # AAB for Play Store
flutter build apk --flavor staging --dart-define=ENV=staging

# iOS (macOS only)
flutter build ipa --release
flutter build ios --release

# Web
flutter build web --release --base-href /myapp/

# Desktop
flutter build windows --release
flutter build linux --release
flutter build macos --release
```

## Platform channels (native integration)
```dart
// Dart side
const channel = MethodChannel('com.myapp/native');
final result = await channel.invokeMethod<String>('getBatteryLevel');
```
```kotlin
// Android (MainActivity.kt)
MethodChannel(flutterEngine.dartExecutor.binaryMessenger, "com.myapp/native")
    .setMethodCallHandler { call, result ->
        if (call.method == "getBatteryLevel") {
            result.success(getBatteryLevel())
        }
    }
```

## Build flavors (Android + iOS)
```yaml
# pubspec.yaml — flutter_flavorizr
flavors:
  development:
    app:
      name: "MyApp Dev"
    android:
      applicationId: "com.myapp.dev"
    ios:
      bundleId: "com.myapp.dev"
  production:
    app:
      name: "MyApp"
    android:
      applicationId: "com.myapp"
    ios:
      bundleId: "com.myapp"
```

## Common pitfalls
- `flutter clean` + `flutter pub get` fixes most build cache issues.
- iOS: always run `pod install` in `ios/` after adding plugins.
- Null safety: run `dart migrate` for pre-null-safety packages.
- Web: use `--dart-define` for API keys, not `.env` files.
""",
    ),
    SkillEntry(
        slug="react-native",
        name="React Native — Expo, Metro, native modules, EAS Build",
        description=(
            "React Native cross-platform development: Expo managed and bare workflow, "
            "Metro bundler, native module bridging, and EAS Build/Submit."
        ),
        domain=SkillDomain.MOBILE,
        tags=[
            "react-native",
            "expo",
            "javascript",
            "typescript",
            "metro",
            "eas",
            "native-modules",
            "ios",
            "android",
        ],
        project_types=["mobile-app", "fullstack-js"],
        platforms=["windows", "linux", "macos"],
        prerequisites=["node", "npm"],
        body="""\
# React Native Skill

## Setup
```bash
# Expo managed workflow (recommended for new projects)
npx create-expo-app MyApp --template
cd MyApp && npx expo start

# Bare React Native
npx react-native init MyApp --template react-native-template-typescript
```

## Development commands
```bash
npx expo start                     # Expo dev server
npx expo start --ios               # iOS simulator
npx expo start --android           # Android emulator
npx expo start --web               # Web browser

# Bare RN
npx react-native run-ios
npx react-native run-android
npx react-native start --reset-cache  # clear Metro cache
```

## Expo Application Services (EAS)
```bash
npm install -g eas-cli
eas login
eas build:configure                # create eas.json
eas build --platform ios --profile production
eas build --platform android --profile production
eas submit --platform ios          # submit to App Store
eas submit --platform android      # submit to Play Store
eas update                         # OTA update (no app store needed)
```

## Native module bridge (New Architecture — TurboModules)
```typescript
// MyNativeModule.ts
import { NativeModules } from 'react-native';
const { MyNativeModule } = NativeModules;
export const getDeviceId = () => MyNativeModule.getDeviceId();
```
```java
// Android: MyNativeModuleModule.java
@ReactMethod public void getDeviceId(Promise promise) {
    promise.resolve(Settings.Secure.getString(
        getReactApplicationContext().getContentResolver(),
        Settings.Secure.ANDROID_ID));
}
```

## Performance profiling
```bash
# Flipper (desktop dev tool)
# Open Flipper → connect device → React Native plugin
# Hermes profiler: via Flipper or Chrome DevTools
npx react-native profile-hermes    # generate Hermes CPU profile
```

## Common pitfalls
- Metro cache: `npx react-native start --reset-cache` or delete `node_modules/.cache`.
- iOS build failures: `cd ios && pod install && cd ..`.
- Android: ensure ANDROID_HOME and Java 17 are set.
- EAS Build: `eas.json` credentials storage handles signing automatically.
- New Architecture (Fabric + TurboModules): requires migration for older native modules.
""",
    ),
]
