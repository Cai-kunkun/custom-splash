# Custom Splash

A mod that replaces or extends the yellow splash text on the Minecraft
title screen. Configure it with a JSON file or from code, add colours,
gradients, rainbows, placeholders and conditions — all without touching the
game files.

- **Fabric, Forge and NeoForge**, no other mods required.
- **Fabric: Minecraft 1.14 through 26.3** — every stable release, 48 versions.
- **Forge: Minecraft 1.16.1 through 1.20.6** — every release with a Forge build, 20 versions.
- **NeoForge: Minecraft 1.20.5 through 26.3** — 18 versions, including the 26.x line.

Minecraft 1.16.0 and 1.17.0 have no Forge build and stay Fabric-only; 1.20.5 is
Fabric + NeoForge (Forge never shipped for it).

Client-side only; nothing changes in multiplayer.

## Installation

Drop the JAR for your Minecraft version into `mods/`. On first launch the mod
creates `config/customsplash.json`. Until you edit it the title screen shows
`Check your custom splash config file to customize!`.

Forge downloads use the jars with `-forge-` in the filename, NeoForge downloads
the `-neoforge-` jars and Fabric downloads use the plain
`customsplash-<mc>-…` jars.

## Upgrading from 1.x

Version 2.0.0 drops the hyphen from the mod id: NeoForge rejects `custom-splash`
and Forge 1.17 and newer derive an invalid Java module name from it, so before
this release the mod could not load on NeoForge at all or on Forge 1.17–1.19.4.
Two paths have to move with the id:

- rename `config/custom-splash.json` to `config/customsplash.json` — the file
  format is unchanged, so its contents need no edits;
- if you ship a resource pack, move its `assets/custom-splash/splashes.txt` (or
  `splashes.json`) to `assets/customsplash/`.

Nothing else about the config format or the `SplashRegistry` API changed.

## Configuration

```json
{
  "splashes": [
    { "text": "Check your custom splash config file to customize!" },
    { "text": "Hello, {player}!", "weight": 5, "color": "#FFAA00" },
    { "text": "Rainbow time", "color": "rainbow:25" },
    { "text": "Enjoy the weekend!", "conditions": { "weekend": true } },
    { "text": "Late night coding", "conditions": { "time": "night", "chance": 0.5 } },
    { "text": "You run Fabric!", "conditions": { "mods": ["fabric"] } }
  ]
}
```

- **`text`** — the splash text. Placeholders are replaced when the splash is
  drawn; unknown tokens are left untouched.
- **`weight`** — relative chance, default `1`. Higher shows more often.
- **`color`** — a solid colour, a gradient or a rainbow, see below.
- **`conditions`** — every listed condition must match:
  - `time`: `day` or `night`
  - `date`: `MM-DD` or `MM-DD..MM-DD` (ranges may wrap across new year)
  - `weekend`: `true` / `false`
  - `player`: list of usernames
  - `mods`: list of required mod ids
  - `chance`: `0.0` – `1.0` random chance

Entries from the config file, from enabled resource packs and from
`SplashRegistry.add(...)` are all combined. When nothing matches, the vanilla
splash is used.

### Placeholders

| Placeholder | Expands to |
| --- | --- |
| `{player}`, `{username}` | your username, or `player` when unknown |
| `{date}` | today as `yyyy-MM-dd` |
| `{time}` | the current time as `HH:mm` |
| `{mc_version}`, `{mc}`, `{version}` | the running Minecraft version |
| `{mods}`, `{mods_count}` | the number of loaded mods |

Placeholders are expanded once, when the splash is picked, so `{time}` is the
moment the title screen renders rather than a live clock. Placeholders that
cannot be resolved stay literal instead of showing a blank space.

### Colours

| Value | Meaning |
| --- | --- |
| `#RRGGBB` | a single colour for the whole text |
| `#RRGGBB,#RRGGBB` | a gradient spread across the characters |
| `#RRGGBB,#RRGGBB,…` | a gradient with more than two stops |
| `gradient:#RRGGBB,…` | the same, spelled explicitly |
| `rainbow` | a hue cycle, 15° per character |
| `rainbow:45` | a hue cycle with a custom degrees-per-character |

Anything that does not parse is ignored and falls back to the vanilla yellow.
A gradient is sampled per character, so each character gets its own
interpolated value and the first and last characters always match the stops
exactly.

```json
{
  "splashes": [
    { "text": "Solid!", "color": "#FFAA00" },
    { "text": "Gradient!", "color": "#FF0000,#00FF00" },
    { "text": "Rainbow!", "color": "rainbow:25" }
  ]
}
```

On versions before 1.20, where the splash is a plain string that cannot carry
per-character styling, a gradient is approximated by prefixing each character
with the nearest legacy `§` code, and a solid `#RRGGBB` becomes a single `§`
code.

## Resource packs

A resource pack can add splash texts by providing
`assets/customsplash/splashes.txt`. Each non-empty line becomes a splash text
and lines starting with `#` are ignored. Enabled packs are re-read
automatically, and `SplashRegistry.reload()` forces an immediate refresh.

## For mod developers

Call `SplashRegistry.add(String)` during mod initialization (or any time
before the title screen renders):

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

For Forge mods, register splashes during mod construction:

```java
import dev.arrbrants.customsplash.SplashRegistry;

@Mod("mymod")
public class MyMod {
    public MyMod() {
        SplashRegistry.add("Hello! Forge!");
    }
}
```

NeoForge mods use the injected mod event bus:

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

The `SplashRegistry` API is identical on all loaders.
