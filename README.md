# Custom Splash

A Fabric mod that replaces or extends the Minecraft title screen yellow splash text.

## Supported versions

Each supported Minecraft version is an independent Gradle project under `versions/`.
The current release set is:

`1.20.1`, `1.20.2`, `1.20.4`, `1.20.6`, `1.21`, `1.21.1`, `1.21.4`, `1.21.5`, `1.21.8`, `26.1`, and `26.2`.

The 1.20.x and 1.21.x projects explicitly use `loom.officialMojangMappings()`.
Minecraft 26.x is distributed in the official Mojang namespace already, so Loom
must not apply the mappings a second time.

Build one version from its directory:

```sh
cd versions/1.20.1
./gradlew build
```

Build every version and collect the remapped jars in `build/releases`:

```sh
./gradlew buildAll
./gradlew collectJars
```

## Usage

Call `SplashRegistry.add(String)` during mod initialization (or any time before the title screen renders).

```java
import dev.arrbrants.customsplash.SplashRegistry;

public class MyMod implements ModInitializer {
    @Override
    public void onInitialize() {
        SplashRegistry.add("Hello! Fabric!");
        SplashRegistry.add("Powered by Mixin");
    }
}
```

Multiple entries are stored in a list. One is chosen at random each time the splash text appears.

When no custom splashes are registered, the vanilla Minecraft splash is displayed normally.
