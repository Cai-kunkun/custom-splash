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

## Configuration

On first launch the mod creates `config/custom-splash.json`. Until you edit it,
the title screen shows `Check your custom splash config file to customize!`.

```json
{
  "splashes": [
    { "text": "Check your custom splash config file to customize!" },
    { "text": "Hello, {player}!", "weight": 5, "color": "#FFAA00" },
    { "text": "Enjoy the weekend!", "conditions": { "weekend": true } },
    { "text": "Late night coding", "conditions": { "time": "night", "chance": 0.5 } },
    { "text": "You run Fabric!", "conditions": { "mods": ["fabric"] } }
  ]
}
```

- `text` — the splash text. `{player}` is replaced with your username.
- `weight` — relative chance (default `1`). Higher shows more often.
- `color` — `#RRGGBB` (real colour on 1.20+, best-effort legacy code on older versions).
- `conditions` — all listed conditions must match:
  - `time`: `day` or `night`
  - `date`: `MM-DD` or `MM-DD..MM-DD` (ranges may wrap across new year)
  - `weekend`: `true`/`false`
  - `player`: list of usernames
  - `mods`: list of required mod ids
  - `chance`: `0.0`–`1.0` random chance

Entries from the config file and from `SplashRegistry.add(...)` are combined.
When nothing matches, the vanilla splash is used.

## Usage

Call `SplashRegistry.add(String)` (or `add(String, int)`) during mod initialization
(or any time before the title screen renders).

```java
import dev.arrbrants.customsplash.SplashRegistry;

public class MyMod implements ModInitializer {
    @Override
    public void onInitialize() {
        SplashRegistry.add("Hello! Fabric!");
        SplashRegistry.add("Powered by Mixin", 3); // weight 3
    }
}
```

The API also exposes `remove(String)`, `clear()`, `list()`, `count()`, and
`reload()` (to re-read the config file). `pick()` returns the chosen text.

When no custom splashes are configured or registered, the vanilla Minecraft
splash is displayed normally.
