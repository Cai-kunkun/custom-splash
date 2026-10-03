# Custom Splash

A mod that replaces or extends the Minecraft title screen yellow splash text.
One code base is built for **Fabric**, **Forge** and **NeoForge**.

## Supported versions

Every stable Minecraft release from **1.14.4 through 26.3** is supported on the
loaders that publish it:

| Loader | Directory | Versions |
| --- | --- | --- |
| Fabric | `versions/` | 1.14.4 – 26.3 ([supported-fabric-versions.txt](supported-fabric-versions.txt)) |
| Forge | `forge/` | 1.16.5 – 1.21.4 ([supported-forge-versions.txt](supported-forge-versions.txt)) |
| NeoForge | `neoforge/` | 1.20.2 – 26.3 ([supported-neoforge-versions.txt](supported-neoforge-versions.txt)) |

Each supported Minecraft version and loader is an independent Gradle project.
Snapshots and pre-releases are not included, and adding a version requires both
its directory and an entry in the corresponding list.

Every project compiles against the official Mojang names. Mojang only started
publishing mappings in 1.14.4, so 1.14–1.14.3 on Fabric use Yarn mappings
committed under `versions/*/mappings/yarn.tiny`. Forge versions before 1.21 run
the game with the legacy SRG member names, so those projects additionally
reobfuscate their jar and generate a mixin refmap.

Versions before 1.20 use the `String`-returning splash API; newer versions use
`SplashRenderer`. Only the loader itself is required — Fabric API, Forge API and
NeoForge API are not used by this mod.

Build one version from its directory:

```sh
cd versions/1.20.1
./gradlew build
```

Build every version, check each JAR, and collect them in `build/releases`:

```sh
./gradlew build
```

For smaller CI builds, `./gradlew verifyReleases -PbuildShard=0 -PbuildShardCount=6`
builds one of six non-overlapping groups. CI merges the groups and checks that
all 85 projects (48 Fabric, 16 Forge, 21 NeoForge) were built before publishing.

Loader projects need their own toolchain, so a child build picks the JDK the
project expects: 17 for ForgeGradle 5, 21 for everything between, and 25 for
Minecraft 26.x. Locally, use the JDK each project wants.

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

Entries from the config file, enabled resource packs, and
`SplashRegistry.add(...)` are combined. When nothing matches, the vanilla splash
is used.

Conditions are evaluated through reflection, so `player` (and the `{player}`
placeholder) is unavailable on Forge versions before 1.21, where the game
renames Minecraft members in production. On those versions the entry is simply
skipped and the vanilla splash is kept.

## Resource packs

A resource pack can add splash texts by providing
`assets/custom-splash/splashes.txt`. Each non-empty line becomes a splash text;
lines starting with `#` are ignored. Enabled packs are re-read automatically, and
`SplashRegistry.reload()` forces an immediate refresh.

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
`reload()` (re-reads the config file and enabled resource packs). `pick()`
returns the chosen text and `pickEntry()` returns it together with its colour.

When no custom splashes are configured or registered, the vanilla Minecraft
splash is displayed normally.
