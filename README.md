# Custom Splash

A Fabric mod that replaces or extends the Minecraft title screen yellow splash text.

## Supported versions

Each supported Minecraft version is an independent Gradle project under `versions/`.
The [version list](supported-versions.txt) covers every stable release from **1.14 through 26.3** (48 versions, including all patch releases in between). Snapshots and pre-releases are not included. Adding a version requires both its directory and an entry in this list.

Minecraft 1.16–1.21.x projects use `loom.officialMojangMappings()`; 26.x is
distributed with official Mojang names already, so mappings must not be applied
again. Mojang only started publishing official mappings with 1.14.4, so 1.14
through 1.14.3 build against Yarn: 1.14.3 takes the published `yarn:v2`
artifact, while 1.14–1.14.2 use a corrected `mappings/yarn.tiny` committed to
the project because the published Yarn v2 archives for those versions declare
the intermediary/named namespaces in the wrong order (see
`scripts/update_yarn_mappings.py`). Versions before 1.20 use the
`String`-returning splash API; newer versions use `SplashRenderer`. The public
`SplashRegistry.add(String)` API is unchanged.
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
all 48 versions were built before publishing.

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

- `text` — the splash text. Placeholders (see below) are replaced when the
  splash is drawn; unknown tokens such as `{emote}` are left untouched.
- `weight` — relative chance (default `1`). Higher shows more often.
- `color` — solid, gradient or rainbow (see below). Real colour on 1.20+;
  older versions approximate with the closest legacy `§` code, which for a
  gradient becomes one code per character.
- `conditions` — all listed conditions must match:
  - `time`: `day` or `night`
  - `date`: `MM-DD` or `MM-DD..MM-DD` (ranges may wrap across new year)
  - `weekend`: `true`/`false`
  - `player`: list of usernames
  - `mods`: list of required mod ids
  - `chance`: `0.0`–`1.0` random chance

### Placeholders

| Placeholder | Expands to |
| --- | --- |
| `{player}`, `{username}` | the current player name, or `player` when unknown |
| `{date}` | today as `yyyy-MM-dd` |
| `{time}` | the current time as `HH:mm` |
| `{mc_version}`, `{mc}`, `{version}` | the running Minecraft version |
| `{mods}`, `{mods_count}` | the number of loaded mods |

They are expanded once when the splash is picked, so `{time}` is the moment
the title screen renders rather than a live clock. Placeholders that cannot be
resolved on the current version (or outside a game) stay literal instead of
showing a blank space.

### Colours

`color` accepts four forms:

| Value | Meaning |
| --- | --- |
| `#RRGGBB` | a single colour for the whole text |
| `#RRGGBB,#RRGGBB` | a gradient spread across the characters |
| `#RRGGBB,#RRGGBB,…` | a gradient with more than two stops |
| `gradient:#RRGGBB,…` | the same, spelled explicitly |
| `rainbow` | a hue cycle, 15° per character |
| `rainbow:45` | a hue cycle with a custom degrees-per-character |

Anything that does not parse is ignored, falling back to the vanilla yellow.
A gradient colour is sampled per character, so each character gets its own
interpolated value; the first and last characters always match the stops
exactly. On versions older than 1.20, where the splash is a plain `String`
styling per character is not possible, the gradient is approximated by
prefixing each character with the nearest legacy `§` code, and `#RRGGBB`
becomes a single `§` code.

```json
{
  "splashes": [
    { "text": "Solid!", "color": "#FFAA00" },
    { "text": "Gradient!", "color": "#FF0000,#00FF00" },
    { "text": "Rainbow!", "color": "rainbow:25" }
  ]
}
```

Entries from the config file, enabled resource packs, and
`SplashRegistry.add(...)` are combined. When nothing matches, the vanilla splash
is used.

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

## Development

Every Java class shared between versions is generated by
`scripts/generate_common_sources.py`, which is the single source of truth. After
editing it, run the generator so all 48 version directories stay identical:

```sh
python3 scripts/generate_common_sources.py
```

Running it twice must not change anything, which CI checks before building.

### Unit tests

The `tests/` project compiles the newest copy of the shared sources (no Minecraft
or Fabric API needed) and runs JUnit 5 tests against the pure logic: colour
parsing, gradient and rainbow sampling, config loading, condition matching,
placeholder expansion and the weighted picker.

```sh
./gradlew test          # or: ./gradlew :tests:test
```

The tests compile against `--release 8`, matching the lowest Java target in the
project, so they double as a portability check. `./gradlew build` runs them
after the release jars are verified, and CI runs them in every job.

## Repository layout

- `versions/<mc>` — one standalone Fabric project per Minecraft version
- `scripts/generate_common_sources.py` — writes the shared Java sources
- `scripts/update_yarn_mappings.py` — refreshes the Yarn v2 mappings
- `scripts/verify_release_artifacts.py` — validates a complete release set
- `tests/` — JUnit 5 unit tests for the shared sources
- `supported-versions.txt` — the single list of built versions
