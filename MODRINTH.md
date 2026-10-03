# Custom Splash

Replace or extend the yellow splash text on the Minecraft title screen, with
weights, colours and display conditions. Everything is configured in a single
JSON file, so you never have to touch a resource pack.

Built for **Fabric**, **Forge** and **NeoForge** from one code base.

## Supported versions

| Loader | Minecraft versions |
| --- | --- |
| Fabric | 1.14.4 – 26.3 |
| Forge | 1.16.5 – 1.21.4 (1.17.1 and later; Forge 1.17 is no longer published) |
| NeoForge | 1.20.2 – 26.2 |

Only the loader itself is needed. Fabric API, Forge and NeoForge APIs are not
used.

## Configuration

`config/custom-splash.json` is created on first launch. Until you edit it, the
title screen shows `Check your custom splash config file to customize!`.

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

Entries from the config file, enabled resource packs and other mods are
combined. When nothing matches, the vanilla splash is used.

## Resource packs

A resource pack can add splash texts by providing
`assets/custom-splash/splashes.txt`. Each non-empty line becomes a splash text;
lines starting with `#` are ignored.

## API

Call `SplashRegistry.add(String)` (or `add(String, int)`) during mod
initialization or any time before the title screen renders.

```java
import dev.arrbrants.customsplash.SplashRegistry;

public class MyMod implements ModInitializer {
    @Override
    public void onInitialize() {
        SplashRegistry.add("Hello!");
        SplashRegistry.add("Powered by Mixin", 3); // weight 3
    }
}
```

`remove(String)`, `clear()`, `list()`, `count()` and `reload()` are available as
well. `pick()` returns the chosen text and `pickEntry()` returns it together
with its colour.

## Notes

On Forge versions before 1.21 the game renames Minecraft members in production,
so `player` conditions and the `{player}` placeholder fall back to the plain
text on those versions.
