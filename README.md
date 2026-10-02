# Custom Splash

A Fabric mod that replaces or extends the Minecraft title screen yellow splash text.

## Supported versions

Each supported Minecraft version is an independent Gradle project under `versions/`.
The [version list](supported-versions.txt) covers every stable release from **1.16 through 26.3** (40 versions, including all patch releases in between). Snapshots and pre-releases are not included. Adding a version requires both its directory and an entry in this list.

Minecraft 1.16–1.21.x projects use `loom.officialMojangMappings()`; 26.x is
distributed with official Mojang names already, so mappings must not be applied
again. Versions before 1.20 use the `String`-returning splash API; newer versions
use `SplashRenderer`. The public `SplashRegistry.add(String)` API is unchanged.
Only Fabric Loader is required; Fabric API is not used by this mod.

Build one version from its directory:

```sh
cd versions/1.20.1
./gradlew build
```

Build every version, check each JAR, and collect them in `build/releases`:

```sh
./gradlew build
```

For smaller CI builds, `./gradlew verifyReleases -PbuildShard=0 -PbuildShardCount=5`
builds one of five non-overlapping groups. CI merges the groups and checks that
all 40 versions were built before publishing.

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
