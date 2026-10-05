# Custom Splash

A mod that replaces or extends the Minecraft title screen yellow splash text,
available for **Fabric**, **Forge** and **NeoForge**.

The mod is client-side only. Fabric and NeoForge declare that, so a dedicated
server disables it; the Forge port has no equivalent metadata field and simply
does nothing there.

## Supported versions

Every loader is built once per release line rather than once per release, so the
86 supported releases ship as **16 jars**. Each loader has a targets file mapping
a project to the whole range its single jar covers, all in the same format:

```
<project> <compile-against> <covered minecraft versions...>
```

| Targets file | Covers | Targets |
| --- | --- | --- |
| [fabric-targets.txt](fabric-targets.txt) | 1.14 – 26.3 | 6 |
| [forge-targets.txt](forge-targets.txt) | 1.16.1 – 1.20.6 | 6 |
| [neoforge-targets.txt](neoforge-targets.txt) | 1.20.5 – 26.3 | 4 |

Adding a release means adding it to the matching `supported-*-versions.txt` list
and to the targets file line it belongs on; a new API era needs its own project
directory as well.

Membership is a runtime claim, not just a build one: every release on a line has
to resolve the mixin to the same name. A green build only proves it compiles.

- **Fabric** resolves against intermediary mappings. SplashManager is
  `net/minecraft/class_4008` and getSplash is `method_18174` from 1.14.4 through
  1.21.11, and SplashRenderer is `net/minecraft/class_8519` from 1.20 through
  1.21.11, so those releases can share a jar.
- **Forge** up to 1.20.4 ships a mixin refmap, so a line must resolve getSplash to
  the same SRG name. CI's `report mixin refmap targets` step prints the name each
  jar bakes in.
- **NeoForge** and **Forge 1.20.6** carry no refmap at all, so their mixins resolve
  by literal name and the grouping is limited only by the build era.

The [Fabric version list](supported-versions.txt) covers every stable release from
**1.14 through 26.3** (48 versions, including all patch releases in between).
Snapshots and pre-releases are not included.

The [Forge version list](supported-forge-versions.txt) covers every Minecraft
release with a Forge build from **1.16.1 through 1.20.6** (20 versions). Forge
never shipped for 1.16.0 or 1.17.0, so those two releases are Fabric-only; for
1.20.5 no Forge build exists either (see NeoForge below). Each Forge project
lives in `versions/<mc>-forge`.

The [NeoForge version list](supported-neoforge-versions.txt) covers **1.20.5
and every 1.21.x and 26.x release through 26.3** (18 versions). NeoForge is the
successor of the Forge line from 1.21 on, and it is the only loader besides
Fabric with a build for 1.20.5. A few of the newest lines (1.21.2, 1.21.6,
1.21.7, 1.21.9, 26.1, 26.1.1 and 26.3) only ship official beta builds, which
the projects pin. Each NeoForge project lives in `versions/<mc>-neoforge`.

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
Only Fabric Loader is required; Fabric API is not used by this mod. The Forge
and NeoForge ports require no external dependencies either (only the loader
itself plus Mixin, which the build resolves).

Build one Fabric target from its directory. Its jar covers every release on that
target's `fabric-targets.txt` line:

```sh
cd versions/1.20          # one jar for 1.20 through 1.21.11
./gradlew build
```

Build a Forge or NeoForge target the same way from its directory:

```sh
cd versions/1.20-forge      # one jar for 1.20 through 1.20.4
./gradlew build          # ForgeGradle resolves Forge + Mixin as build deps
cd versions/1.21-neoforge   # one jar for 1.21 through 1.21.4
./gradlew build          # ModDevGradle resolves NeoForge + Mixin as build deps
```

The Forge ports for 1.16.1–1.19.4 use ForgeGradle 5 (Gradle 7.6.4), which does
**not** run on Java 21: set `JAVA_HOME` to a JDK 17 before building them.
ForgeGradle then compiles with the JDK matching each Minecraft version (Java 8
for 1.16.x, Java 16 for 1.17.1, Java 17 for the rest), which it discovers
through the `JAVA_HOME_8_X64`, `JAVA_HOME_16_X64` and `JAVA_HOME_17_X64`
environment variables. The 1.20.x ports use ForgeGradle 6 (Gradle 8.13) and
accept Java 17–21; the 1.20.6 port uses ForgeGradle 7 (Gradle 9.6.0) on Java 21.
The NeoForge ports use ModDevGradle (Gradle 9.6.0) on Java 21, with a Java 25
toolchain for the 26.x line; 1.20.5 uses the legacy NeoGradle plugin instead,
because ModDevGradle 2.x needs the newer NeoForge metadata that 20.5 predates.

Every project therefore uses one of exactly three Gradle releases, one per Gradle
major line, and each is pinned by the oldest build plugin on that line rather
than by drift:

| Gradle | Projects | Pinned by |
| --- | --- | --- |
| 7.6.4 | Forge 1.16.1–1.19.4 (4) | ForgeGradle 5, which does not support Gradle 8 |
| 8.8 | Fabric 1.14–1.20 (3) | Fabric Loom 1.6, which fails on 8.13 |
| 8.13 | Forge 1.20–1.20.4 (1) | ForgeGradle 6 |
| 9.6.0 | Forge 1.20.6, NeoForge, Fabric 26.x (8) | ForgeGradle 7, ModDevGradle and Loom 1.17 |

Four releases remain and each is pinned by a build plugin rather than left to
drift. The remaining differences cannot be collapsed without migrating a plugin:
ForgeGradle 5 does not run on Gradle 8, Loom 1.6 fails on 8.13, and the Fabric
26.x line needs a newer Loom than the older Fabric releases.

Build every version, check each JAR, and collect them in `build/releases`:

```sh
./gradlew build
```

For smaller CI builds, `./gradlew verifyReleases -PbuildShard=0 -PbuildShardCount=9`
builds one of nine non-overlapping groups. CI merges the groups and checks that
all 16 targets were built before publishing. On CI, `FORGE_JAVA_HOME` points at
a JDK 17 that the aggregator forwards to the ForgeGradle 5/6 child builds while
the rest of the build runs on Java 21, and additionally installed JDK 8/16/25
plus the runner's JDK 21 satisfy the per-version toolchains.

## Configuration

On first launch the mod creates `config/custom-splash.json`, written with a full
commented reference so the file documents itself. `//` and `/* */` comments are
allowed anywhere in it, which is also why the examples below can be kept in place
until you want one. Until you edit the file, the title screen shows
`Check your custom splash config file to customize!`.

Values that cannot work are reported in the log when the config is loaded: an
unparseable `color`, an unparseable `date`, an unknown `time`, a `chance` outside
`0.0`–`1.0`, or a non-positive `weight`. They used to fail silently, which made a
broken config impossible to debug.

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

A resource pack can add splash texts in two ways.

`assets/custom-splash/splashes.txt` — each non-empty line becomes a splash text,
and lines starting with `#` are ignored.

`assets/custom-splash/splashes.json` — the same schema as the config file, so
these entries can carry a `weight`, a `color` and `conditions` too.

Both files may be present and their entries are combined. Enabled packs are
re-read automatically, and `SplashRegistry.reload()` forces an immediate refresh.

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

For Forge mods, register splashes during mod construction (the Forge port
installs its platform automatically):

```java
import dev.arrbrants.customsplash.SplashRegistry;

@Mod("mymod")
public class MyMod {
    public MyMod() {
        SplashRegistry.add("Hello! Forge!");
    }
}
```

NeoForge mods use the same pattern with the injected mod event bus:

```java
import dev.arrbrants.customsplash.SplashRegistry;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.fml.common.Mod;

@Mod("mymod")
public class MyMod {
    public MyMod(IEventBus modEventBus) {
        SplashRegistry.add("Hello! NeoForge!");
    }
}
```

The shared `SplashRegistry` API is identical on all loaders; only the entry
point and platform plumbing differ (see `SplashPlatform` and the
`FabricSplashPlatform` / `ForgeSplashPlatform` / `NeoForgeSplashPlatform`
implementations).

When no custom splashes are configured or registered, the vanilla Minecraft
splash is displayed normally.

## Development

Every Java class shared between versions is generated by
`scripts/generate_common_sources.py`, which is the single source of truth. After
editing it, run the generators so the Fabric, Forge and NeoForge directories
stay identical (the latter two embed the same shared sources plus their
loader-specific platform and entry point):

```sh
python3 scripts/generate_common_sources.py
python3 scripts/generate_forge_projects.py
python3 scripts/generate_neoforge_projects.py
```

Running the generators twice must not change anything, which CI checks before building.

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

### Smoke tests

A merged Fabric jar is only *compiled* by the build job, which says nothing about
whether its mixin can actually be applied on every release the jar claims. The
CI `smoke` job therefore launches a real Minecraft client with the built jar,
using [MC-Runtime-Test](https://github.com/headlesshq/mc-runtime-test) on top of
[HeadlessMC](https://github.com/headlesshq/headlessmc), and runs the oldest and
newest release of every merged range. Booting the client reaches the title screen,
which calls `SplashManager#getSplash`, so a mixin that cannot be applied crashes
the client and fails the job. `release` depends on `smoke`, so a jar that does
not boot cannot be published.

MC-Runtime-Test supports 1.16.5 and newer, so the 1.14–1.15.2 releases and 26.3
are outside it and still need a manual smoke test before a release. Forge and
NeoForge build one jar per release and are not part of the smoke matrix.

## Repository layout

- `versions/<era>` — one standalone Fabric project per API line; its single jar covers every release on its `fabric-targets.txt` line
- `versions/<mc>-forge` — one standalone Forge project per Forge line
- `versions/<mc>-neoforge` — one standalone NeoForge project per NeoForge line
- `fabric-targets.txt`, `forge-targets.txt`, `neoforge-targets.txt` — the target lists: project, compile version and covered releases
- `scripts/generate_common_sources.py` — writes the shared (loader-agnostic) Java sources
- `scripts/generate_forge_projects.py` — scaffolds the Forge projects
- `scripts/generate_neoforge_projects.py` — scaffolds the NeoForge projects
- `src/main/resources/assets/custom-splash/icon.png` — the canonical mod icon, copied into every version project by the generators
- `scripts/update_yarn_mappings.py` — refreshes the Yarn v2 mappings
- `scripts/verify_release_artifacts.py` — validates a complete release set
- `tests/` — JUnit 5 unit tests for the shared sources
- `supported-versions.txt` — the Fabric version list
- `supported-forge-versions.txt` — the Forge version list
- `supported-neoforge-versions.txt` — the NeoForge version list
