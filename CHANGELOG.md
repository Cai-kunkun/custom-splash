# Changelog

Each released version gets a `## <version>` section here. The release job extracts
the section matching the version it is publishing and sends it to Modrinth as the
version changelog, so anything written here shows up on the Modrinth version page.

## 2.0.0

**Breaking: the mod id is `customsplash` now, without the hyphen.**

NeoForge validates mod ids against
`^(?=.{2,64}$)[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)*$` and Forge 1.17 and newer
derive a Java module name from the id, which cannot contain a hyphen either. A jar
built with the old id was rejected by both, so `custom-splash` had to go. To
upgrade:

- rename `config/custom-splash.json` to `config/customsplash.json`. The format is
  unchanged, so the contents need no edits.
- if you ship a resource pack, move its `assets/custom-splash/splashes.txt` (or
  `splashes.json`) to `assets/customsplash/`.

### Fixed

- The mod could not load on NeoForge at all: the loader reported
  `Invalid modId found : custom-splash`.
- Forge 1.17–1.19.4 could not load either: `Invalid module name: 'custom-splash'
  is not a Java identifier`.
- Forge jars shipped no `pack.mcmeta`, which Forge needs before it finishes
  loading a mod whose resources it exposes as a resource pack. 1.20.4 stopped with
  `Missing metadata in pack` and older Forge showed a loading error screen.
- Forge 1.20.6 aborted on startup because its bundled Mixin 0.8.5 does not
  recognise the `JAVA_21` compatibility level.
- The 1.20–1.20.4 jar no longer offers itself on 1.20.6, where Forge resolves
  official names and its mixin cannot find its target.

### Changed

- One jar per release line instead of one per release: the 86 supported releases
  now ship as 14 downloads, and every one of them was booted in CI before release.
- The generated config file is a full commented reference, so it documents itself.
- Values that cannot work — an unparseable `color` or `date`, an unknown `time`, a
  `chance` outside `0.0`–`1.0`, a non-positive `weight` — are reported in the log
  instead of failing silently.
- The mod declares itself client-side only, so a dedicated server disables it.

### Added

- Resource packs may provide `assets/customsplash/splashes.json` in addition to
  `splashes.txt`, using the same schema as the config file, so a pack no longer has
  to reduce its splashes to one plain line each.
