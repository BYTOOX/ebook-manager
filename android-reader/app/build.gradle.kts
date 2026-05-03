plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("org.jetbrains.kotlin.plugin.compose")
    id("org.jetbrains.kotlin.kapt")
}

val aureliaKeystorePath = providers.gradleProperty("AURELIA_KEYSTORE_PATH")
    .orElse(providers.environmentVariable("AURELIA_KEYSTORE_PATH"))
val aureliaKeystorePassword = providers.gradleProperty("AURELIA_KEYSTORE_PASSWORD")
    .orElse(providers.environmentVariable("AURELIA_KEYSTORE_PASSWORD"))
val aureliaKeyAlias = providers.gradleProperty("AURELIA_KEY_ALIAS")
    .orElse(providers.environmentVariable("AURELIA_KEY_ALIAS"))
val aureliaKeyPassword = providers.gradleProperty("AURELIA_KEY_PASSWORD")
    .orElse(providers.environmentVariable("AURELIA_KEY_PASSWORD"))

val releaseSigningInputs = listOf(
    aureliaKeystorePath.orNull,
    aureliaKeystorePassword.orNull,
    aureliaKeyAlias.orNull,
    aureliaKeyPassword.orNull
)
val hasAnyReleaseSigningInput = releaseSigningInputs.any { !it.isNullOrBlank() }
val hasCompleteReleaseSigningInput = releaseSigningInputs.all { !it.isNullOrBlank() }

if (hasAnyReleaseSigningInput && !hasCompleteReleaseSigningInput) {
    throw GradleException(
        "Release signing requires AURELIA_KEYSTORE_PATH, AURELIA_KEYSTORE_PASSWORD, " +
            "AURELIA_KEY_ALIAS and AURELIA_KEY_PASSWORD."
    )
}

android {
    namespace = "ch.bytoox.aureliareader"
    compileSdk = 35
    buildToolsVersion = "35.0.0"

    defaultConfig {
        applicationId = "ch.bytoox.aureliareader"
        minSdk = 26
        targetSdk = 35
        versionCode = 8
        versionName = "0.2.1"
    }

    signingConfigs {
        create("release") {
            if (hasCompleteReleaseSigningInput) {
                storeFile = file(aureliaKeystorePath.get())
                storePassword = aureliaKeystorePassword.get()
                keyAlias = aureliaKeyAlias.get()
                keyPassword = aureliaKeyPassword.get()
            }
        }
    }

    buildTypes {
        debug {
            buildConfigField("boolean", "ALLOW_CLEARTEXT_SERVER", "true")
        }

        release {
            buildConfigField("boolean", "ALLOW_CLEARTEXT_SERVER", "false")
            isMinifyEnabled = true
            isShrinkResources = true
            if (hasCompleteReleaseSigningInput) {
                signingConfig = signingConfigs.getByName("release")
            }
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
    }

    sourceSets {
        getByName("androidTest").assets.srcDir("$projectDir/schemas")
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
        isCoreLibraryDesugaringEnabled = true
    }

    kotlin {
        jvmToolchain(21)
        compilerOptions {
            jvmTarget.set(org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_17)
        }
    }

    buildFeatures {
        compose = true
        buildConfig = true
    }
}

kapt {
    arguments {
        arg("room.schemaLocation", "$projectDir/schemas")
        arg("room.incremental", "true")
    }
}

dependencies {
    implementation(platform("androidx.compose:compose-bom:2024.10.01"))

    coreLibraryDesugaring("com.android.tools:desugar_jdk_libs:2.1.5")

    implementation("androidx.activity:activity-compose:1.9.3")
    implementation("androidx.core:core-ktx:1.13.1")
    implementation("androidx.datastore:datastore-preferences:1.1.1")
    implementation("androidx.fragment:fragment-ktx:1.8.5")
    implementation("androidx.compose.foundation:foundation")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.compose.material:material-icons-extended")
    implementation("androidx.compose.runtime:runtime")
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.ui:ui-tooling-preview")
    implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.8.6")
    implementation("androidx.lifecycle:lifecycle-viewmodel-ktx:2.8.6")
    implementation("androidx.navigation:navigation-compose:2.8.3")
    implementation("androidx.room:room-ktx:2.6.1")
    implementation("androidx.room:room-runtime:2.6.1")
    implementation("androidx.work:work-runtime-ktx:2.9.1")
    implementation("io.coil-kt:coil-compose:2.7.0")
    implementation("com.squareup.okhttp3:okhttp:4.12.0")
    implementation("org.readium.kotlin-toolkit:readium-shared:3.0.3")
    implementation("org.readium.kotlin-toolkit:readium-streamer:3.0.3")
    implementation("org.readium.kotlin-toolkit:readium-navigator:3.0.3")

    kapt("androidx.room:room-compiler:2.6.1")
    testImplementation("junit:junit:4.13.2")
    testImplementation("com.squareup.okhttp3:mockwebserver:4.12.0")
    androidTestImplementation("androidx.room:room-testing:2.6.1")

    debugImplementation("androidx.compose.ui:ui-tooling")
    debugImplementation("androidx.compose.ui:ui-test-manifest")
}
