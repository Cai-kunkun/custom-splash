#!/usr/bin/env python3
"""Create the Forge and NeoForge projects for every supported version.

Fabric supports versions that the other two loaders never published, so each
loader keeps its own version list (``supported-<loader>-versions.txt``).  The
lists are maintained by hand because availability has to be confirmed against
the corresponding maven repository.
"""

from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]

# Minecraft versions that each loader actually publishes. Forge stops at 1.21.x
# because NeoForge took over from 1.20.2 onwards, and NeoForge starts at 1.20.2.
FORGE_VERSIONS = [
    "1.16.5",
    "1.17.1",
    "1.18",
    "1.18.1",
    "1.18.2",
    "1.19",
    "1.19.1",
    "1.19.2",
    "1.19.3",
    "1.19.4",
    "1.20",
    "1.20.1",
    "1.21",
    "1.21.1",
    "1.21.4",
]

NEOFORGE_VERSIONS = [
    # NeoForge only ships stable builds for some patch releases, so the ones
    # that are beta-only (1.20.3, 1.20.5, 1.21.6, 1.21.7, 1.21.9 and 26.3) are
    # left out instead of tracking beta versions that may move.
    "1.20.2",
    "1.20.4",
    "1.20.6",
    "1.21",
    "1.21.1",
    "1.21.3",
    "1.21.4",
    "1.21.5",
    "1.21.8",
    "1.21.10",
    "1.21.11",
    "26.1",
    "26.1.1",
    "26.1.2",
    "26.2",
]

# Latest published loader version per Minecraft version.
FORGE_LOADER_VERSION = {
    "1.16.5": "36.2.42",
    "1.17.1": "37.1.1",
    "1.18": "38.0.17",
    "1.18.1": "39.1.2",
    "1.18.2": "40.3.12",
    "1.19": "41.1.0",
    "1.19.1": "42.0.9",
    "1.19.2": "43.5.2",
    "1.19.3": "44.1.23",
    "1.19.4": "45.4.5",
    "1.20": "46.0.14",
    "1.20.1": "47.4.26",
    "1.21": "51.0.33",
    "1.21.1": "52.1.16",
    "1.21.4": "54.1.18",
}

NEOFORGE_LOADER_VERSION = {
    "1.20.2": "20.2.93",
    "1.20.4": "20.4.251",
    "1.20.6": "20.6.141",
    "1.21": "21.0.167",
    "1.21.1": "21.1.252",
    "1.21.3": "21.3.97",
    "1.21.4": "21.4.158",
    "1.21.5": "21.5.98",
    "1.21.8": "21.8.54",
    "1.21.10": "21.10.64",
    "1.21.11": "21.11.45",
    "26.1": "26.1.2.114",
    "26.1.1": "26.1.2.114",
    "26.1.2": "26.1.2.114",
    "26.2": "26.2.0.88",
}

# Mixin toolchain: ForgeGradle rewrites the mod jar to SRG names, and the Mixin
# annotation processor writes the refmap the mixin annotations need at runtime.
MIXIN_VERSION = "0.8.7"
MIXIN_GRADLE_VERSION_FORGE_5 = "0.7.38"
MIXIN_GRADLE_VERSION_FORGE_6 = "0.7.38"

JAVA_VERSION = {
    "1.16.5": "8",
    "1.17": "16",
    "1.17.1": "16",
    "1.18": "17",
    "1.18.1": "17",
    "1.18.2": "17",
    "1.19": "17",
    "1.19.1": "17",
    "1.19.2": "17",
    "1.19.3": "17",
    "1.19.4": "17",
    "1.20": "17",
    "1.20.1": "17",
    "1.20.2": "17",
    "1.20.3": "17",
    "1.20.4": "17",
    "1.20.5": "17",
    "1.20.6": "21",
    "1.21": "21",
    "1.21.1": "21",
    "1.21.3": "21",
    "1.21.4": "21",
    "1.21.5": "21",
    "1.21.6": "21",
    "1.21.7": "21",
    "1.21.8": "21",
    "1.21.9": "21",
    "1.21.10": "21",
    "1.21.11": "21",
    "26.1": "25",
    "26.1.1": "25",
    "26.1.2": "25",
    "26.2": "25",
    "26.3": "25",
}

# ForgeGradle 6 requires newer Minecraft versions; 1.16-1.20.x use ForgeGradle 5.
FORGE_GRADLE_VERSION = {
    "1.16.5": "5.1.+",
    "1.17": "5.1.+",
    "1.17.1": "5.1.+",
    "1.18": "5.1.+",
    "1.18.1": "5.1.+",
    "1.18.2": "5.1.+",
    "1.19": "5.1.+",
    "1.19.1": "5.1.+",
    "1.19.2": "5.1.+",
    "1.19.3": "5.1.+",
    "1.19.4": "5.1.+",
    "1.20": "5.1.+",
    "1.20.1": "5.1.+",
    "1.21": "6.0.+",
    "1.21.1": "6.0.+",
    "1.21.4": "6.0.+",
}

# ModDevGradle 2.0 dropped support for the earliest NeoForge releases.
MODDEV_VERSION_LEGACY = "1.0.24"
MODDEV_VERSION = "2.0.+"

PACKAGE_DIR = "src/main/java/dev/arrbrants/customsplash"
MIXIN_DIR = PACKAGE_DIR + "/mixin"

FORGE_BUILD = """plugins {{
	id 'net.minecraftforge.gradle' version '{forge_gradle_version}'
	id 'org.spongepowered.mixin' version '{mixin_gradle_version}'
	id 'maven-publish'
}}

def gitCommit = providers.exec {{
	commandLine 'git', 'rev-parse', '--short=8', 'HEAD'
}}.standardOutput.asText.getOrElse('').trim()

version = "${{rootProject.mod_version}}+mc{minecraft_version}+forge" + (gitCommit.isEmpty() ? '' : ".${{gitCommit}}")
group = rootProject.maven_group
base.archivesName = "custom-splash-${{minecraft_version}}-forge"

minecraft {{
	mappings channel: 'official', version: '{minecraft_version}'

	runs {{
		client {{
			workingDirectory project.file('run')
			property 'forge.logging.console.level', 'debug'
			mods {{
				custom_splash {{
					source sourceSets.main
				}}
			}}
		}}
	}}

	{copy_ide_resources}
}}

dependencies {{
	minecraft 'net.minecraftforge:forge:{minecraft_version}-{loader_version}'
}}

// Older ForgeGradle releases run the game with SRG member names in production.
// The built jar has to be converted back to those names and the mixin
// annotations need a refmap to find their target. ForgeGradle 6 (Minecraft
// 1.21 and newer) runs the game with the official Mojang names the mod is
// compiled against, so no reobfuscation or refmap is required.
def srgRuntime = Boolean.parseBoolean(findProperty('srg_runtime') ?: 'false')
if (srgRuntime) {{
	dependencies {{
		add('annotationProcessor', 'org.spongepowered:mixin:{mixin_version}:processor')
	}}

	mixin {{
		add sourceSets.main, 'customsplash.refmap.json'
		config 'customsplash.mixins.json'
	}}

	reobf {{
		jar {{}}
	}}
}}

processResources {{
	inputs.property 'version', project.version
	inputs.property 'minecraft_version', minecraft_version
	inputs.property 'loader_version', loader_version
	filesMatching('META-INF/mods.toml') {{
		expand version: project.version, minecraft_version: minecraft_version, loader_min_version: loader_min_version
	}}
}}

tasks.withType(JavaCompile).configureEach {{
	options.release = Integer.parseInt(java_version)
}}

java {{
	withSourcesJar()
}}

jar {{
	from(rootProject.file('LICENSE')) {{
		rename {{ "${{it}}_${{base.archivesName.get()}}" }}
	}}
}}
"""

NEOFORGE_BUILD = """plugins {{
	id 'net.neoforged.moddev' version '{moddev_version}'
	id 'maven-publish'
}}

def gitCommit = providers.exec {{
	commandLine 'git', 'rev-parse', '--short=8', 'HEAD'
}}.standardOutput.asText.getOrElse('').trim()

version = "${{rootProject.mod_version}}+mc{minecraft_version}+neoforge" + (gitCommit.isEmpty() ? '' : ".${{gitCommit}}")
group = rootProject.maven_group
base.archivesName = "custom-splash-${{minecraft_version}}-neoforge"

neoForge {{
	version = "{neoforge_version}"

	mods {{
		"custom_splash" {{
			sourceSet(sourceSets.main)
		}}
	}}

	runs {{
		client {{
			client()
			gameDirectory = project.file('run')
			systemProperty 'neoforge.enabledGameTestNamespaces', 'custom-splash'
		}}
	}}
}}

processResources {{
	inputs.property 'version', project.version
	inputs.property 'minecraft_version', minecraft_version
	inputs.property 'neoforge_version', neoforge_version
	filesMatching('META-INF/neoforge.mods.toml') {{
		expand version: project.version, minecraft_version: minecraft_version, loader_min_version: loader_min_version
	}}
}}

tasks.withType(JavaCompile).configureEach {{
	options.release = Integer.parseInt(java_version)
}}

java {{
	withSourcesJar()
}}

jar {{
	from(rootProject.file('LICENSE')) {{
		rename {{ "${{it}}_${{base.archivesName.get()}}" }}
	}}
}}
"""

SETTINGS = """pluginManagement {{
	 repositories {{
		 maven {{ url = '{maven_url}' }}
		 maven {{ url = 'https://repo.spongepowered.org/repository/maven-public/' }}
		 mavenCentral()
		 gradlePluginPortal()
	 }}
}}

plugins {{
	 id 'org.gradle.toolchains.foojay-resolver-convention' version '1.0.0'
}}

rootProject.name = 'custom-splash-{mc}-{loader}'
"""

MODS_TOML = """modLoader = "javafml"
loaderVersion = "[4,)"
license = "MIT"
issueTrackerURL = "https://github.com/Cai-kunkun/custom-splash/issues"
[[mods]]
modId = "custom-splash"
version = "${{version}}"
displayName = "Custom Splash"
authors = "ArrBrants"
description = "A mod that extends splash texts."
[[dependencies.custom-splash]]
modId = "{loader_dependency}"
mandatory = true
versionRange = "[${{loader_min_version}},)"
ordering = "NONE"
side = "CLIENT"
[[mixins]]
config = "customsplash.mixins.json"
[[dependencies.custom-splash]]
modId = "minecraft"
mandatory = true
versionRange = "[${{minecraft_version}}]"
ordering = "NONE"
side = "CLIENT"
"""

MIXIN_CONFIG = """{{
	"required": true,
	"package": "dev.arrbrants.customsplash.mixin",
	"compatibilityLevel": "JAVA_{mixin_java}",
	"minVersion": "0.8",
	"client": ["SplashManagerMixin"],
	"injectors": {{"defaultRequire": 1}}{refmap}
}}
"""

MIXIN_OLD = """package dev.arrbrants.customsplash.mixin;

import dev.arrbrants.customsplash.SplashColors;
import dev.arrbrants.customsplash.SplashRegistry;
import net.minecraft.client.resources.SplashManager;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

@Mixin(SplashManager.class)
public class SplashManagerMixin {
	@Inject(at = @At("HEAD"), method = "getSplash", cancellable = true)
	private void getSplash(CallbackInfoReturnable<String> cir) {
		SplashRegistry.pickEntry().ifPresent(picked ->
				cir.setReturnValue(picked.rgb >= 0 ? SplashColors.legacyPrefix(picked.rgb) + picked.text : picked.text));
	}
}
"""

MIXIN_NEW = """package dev.arrbrants.customsplash.mixin;

import dev.arrbrants.customsplash.SplashRegistry;
import net.minecraft.client.gui.components.SplashRenderer;
import net.minecraft.client.resources.SplashManager;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.MutableComponent;
import net.minecraft.network.chat.Style;
import net.minecraft.network.chat.TextColor;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

import java.lang.reflect.InvocationTargetException;

@Mixin(SplashManager.class)
public class SplashManagerMixin {
	@Inject(at = @At("HEAD"), method = "getSplash", cancellable = true)
	private void getSplash(CallbackInfoReturnable<SplashRenderer> cir) {
		SplashRegistry.pickEntry().ifPresent(picked -> cir.setReturnValue(createRenderer(picked)));
	}

	private static SplashRenderer createRenderer(SplashRegistry.Picked picked) {
		MutableComponent component = Component.literal(picked.text);
		if (picked.rgb >= 0) {
			component = component.withStyle(Style.EMPTY.withColor(TextColor.fromRgb(picked.rgb)));
		}
		try {
			return SplashRenderer.class.getConstructor(Component.class).newInstance(component);
		} catch (NoSuchMethodException ignored) {
			try {
				return SplashRenderer.class.getConstructor(String.class).newInstance(picked.text);
			} catch (ReflectiveOperationException exception) {
				throw new IllegalStateException("Unable to create splash renderer", unwrap(exception));
			}
		} catch (ReflectiveOperationException exception) {
			throw new IllegalStateException("Unable to create splash renderer", unwrap(exception));
		}
	}

	private static Throwable unwrap(ReflectiveOperationException exception) {
		return exception instanceof InvocationTargetException && exception.getCause() != null
				? exception.getCause() : exception;
	}
}
"""

FORGE_MOD = """package dev.arrbrants.customsplash;

import net.minecraftforge.fml.common.Mod;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@Mod("custom-splash")
public final class CustomSplash {
	public static final String MOD_ID = "custom-splash";
	public static final Logger LOGGER = LoggerFactory.getLogger(MOD_ID);

	private CustomSplash() {
	}

	public static void init() {
		SplashPlatforms.install(SplashForgePlatform.INSTANCE);
		SplashRegistry.reload();
		LOGGER.info("Custom Splash has initialized successfully");
	}
}
"""

FORGE_MOD_LEGACY = """package dev.arrbrants.customsplash;

import net.minecraftforge.fml.common.Mod;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@Mod("custom-splash")
public final class CustomSplash {
	public static final String MOD_ID = "custom-splash";
	public static final Logger LOGGER = LoggerFactory.getLogger(MOD_ID);

	@SuppressWarnings("unused")
	public CustomSplash() {
		SplashPlatforms.install(SplashForgePlatform.INSTANCE);
		SplashRegistry.reload();
		LOGGER.info("Custom Splash has initialized successfully");
	}
}
"""

NEOFORGE_MOD = """package dev.arrbrants.customsplash;

import net.neoforged.fml.common.Mod;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@Mod("custom-splash")
public final class CustomSplash {
	public static final String MOD_ID = "custom-splash";
	public static final Logger LOGGER = LoggerFactory.getLogger(MOD_ID);

	public CustomSplash() {
		SplashPlatforms.install(SplashForgePlatform.INSTANCE);
		SplashRegistry.reload();
		LOGGER.info("Custom Splash has initialized successfully");
	}
}
"""

PLATFORM_FILE = {
    "forge": "SplashForgePlatform.java",
    "neoforge": "SplashForgePlatform.java",
    "fabric": "SplashFabricPlatform.java",
}

SHARED_FILES = [
    "SplashColors.java",
    "SplashConfig.java",
    "SplashContext.java",
    "SplashEntry.java",
    "SplashPlatform.java",
    "SplashPlatforms.java",
    "SplashRegistry.java",
    "SplashResourcePack.java",
]


def minecraft_version_order(version: str) -> int:
    """Order versions by the NeoForge generation they belong to."""
    parts = version.split(".")
    if parts[0] != "1":
        return 999
    minor = int(parts[1])
    patch = int(parts[2]) if len(parts) > 2 else 0
    return minor * 100 + patch


def uses_legacy_mixin(version: str) -> bool:
    parts = version.split(".")
    return parts[0] == "1" and int(parts[1]) <= 19


def mixin_java(java_version: str) -> str:
    return "8" if java_version == "8" else "17"


FORGE_PLATFORM = """package dev.arrbrants.customsplash;

import java.lang.reflect.Method;
import java.nio.file.Path;
import java.nio.file.Paths;

/** Forge and NeoForge platform hooks. */
public enum SplashForgePlatform implements SplashPlatform {
\tINSTANCE;

\t@Override
\tpublic Path configDir() {
\t\treturn gameDir().resolve("config");
\t}

\t@Override
\tpublic Path gameDir() {
\t\tString value = System.getProperty("user.dir");
\t\treturn value == null ? Paths.get(".") : Paths.get(value);
\t}

\t@Override
\tpublic boolean isModLoaded(String modId) {
\t\ttry {
\t\t\tClass<?> type = Class.forName("net.minecraftforge.fml.loading.FMLLoader");
\t\t\tObject loadingModList = invoke(type, null, "getLoadingModList");
\t\t\tif (loadingModList == null) {
\t\t\t\treturn false;
\t\t\t}
\t\t\tObject mods = invoke(loadingModList.getClass(), loadingModList, "getMods");
\t\t\tif (mods instanceof Iterable) {
\t\t\t\tfor (Object mod : (Iterable<?>) mods) {
\t\t\t\t\tObject id = invoke(mod.getClass(), mod, "getModId");
\t\t\t\t\tif (modId.equals(id)) {
\t\t\t\t\t\treturn true;
\t\t\t\t\t}
\t\t\t\t}
\t\t\t}
\t\t\treturn false;
\t\t} catch (ReflectiveOperationException | RuntimeException ignored) {
\t\t\treturn false;
\t\t}
\t}

\t@Override
\tpublic String platformName() {
\t\treturn "Forge";
\t}

\tprivate static Object invoke(Class<?> type, Object target, String name) throws ReflectiveOperationException {
\t\tMethod method = type.getMethod(name);
\t\treturn method.invoke(target);
\t}
}
"""


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_text() == content:
        return
    path.write_text(content)


def scaffold(loader: str, minecraft: str, versions: dict, extra: dict) -> None:
    project = ROOT / loader / minecraft
    if (project / "build.gradle").exists():
        print(f"exists {loader}/{minecraft}")
        return

    project.mkdir(parents=True, exist_ok=True)

    # ForgeGradle 5 rejects Gradle 8 and newer, so those versions use the
    # Gradle 7 wrapper instead of the Gradle 8 one used by the other loaders.
    wrapper_distribution = "gradle-8.8-bin.zip"
    if loader == "forge" and not extra.get("forge_gradle_version", "").startswith("6."):
        wrapper_distribution = "gradle-7.6.4-bin.zip"

    # Copy the Gradle wrapper from an existing Fabric project.
    reference = ROOT / "versions" / "1.16.1"
    for name in ("gradlew", "gradlew.bat"):
        source = reference / name
        if source.exists():
            (project / name).write_text(source.read_text())
    (project / "gradle" / "wrapper").mkdir(parents=True, exist_ok=True)
    wrapper_properties = reference / "gradle" / "wrapper" / "gradle-wrapper.properties"
    if wrapper_properties.exists():
        write(
            project / "gradle" / "wrapper" / "gradle-wrapper.properties",
            wrapper_properties.read_text().replace(
                "gradle-8.8-bin.zip", wrapper_distribution
            ),
        )
    wrapper_jar = reference / "gradle" / "wrapper" / "gradle-wrapper.jar"
    if wrapper_jar.exists():
        shutil.copy2(wrapper_jar, project / "gradle" / "wrapper" / "gradle-wrapper.jar")

    java = JAVA_VERSION.get(minecraft, "17")
    values = {
        "java_version": java,
        "minecraft_version": minecraft,
        "maven_group": "dev.arrbrants.customsplash",
        "mod_version": "1.2.0",
    }
    values.update(extra)

    if loader == "forge":
        gradle_family = "6" if FORGE_GRADLE_VERSION[minecraft].startswith("6") else "5"
        # ForgeGradle 5 renames Minecraft members to SRG for the production game,
        # ForgeGradle 6 keeps the official Mojang names the mod compiles against.
        srg_runtime = gradle_family == "5"
        values["srg_runtime"] = "true" if srg_runtime else "false"
        values["mixin_gradle_version"] = (
            MIXIN_GRADLE_VERSION_FORGE_6 if gradle_family == "6" else MIXIN_GRADLE_VERSION_FORGE_5
        )
        values["mixin_version"] = MIXIN_VERSION
        # Only ForgeGradle 6 knows the copyIdeResources property.
        values["copy_ide_resources"] = "" if srg_runtime else "	copyIdeResources = true"
        template = FORGE_BUILD
    else:
        # ModDevGradle 2.0 dropped support for the earliest NeoForge releases.
        needs_legacy_moddev = minecraft in ("1.20.2", "1.20.4")
        values["moddev_version"] = MODDEV_VERSION_LEGACY if needs_legacy_moddev else MODDEV_VERSION
        template = NEOFORGE_BUILD

    # Minimum loader version declared in mods.toml.
    values.setdefault("loader_min_version", "4")
    # Keys that only exist in a rendered build.gradle must not leak into the
    # property file the build reads.
    properties = {key: value for key, value in values.items() if key != "copy_ide_resources"}
    write(
        project / "gradle.properties",
        "\n".join(f"{key}={value}" for key, value in properties.items()) + "\n",
    )

    write(
        project / "settings.gradle",
        SETTINGS.format(maven_url=extra["maven_url"], mc=minecraft, loader=loader),
    )

    write(project / "build.gradle", template.format(**values))

    # Shared sources come from the Fabric project of the same version, reusing the
    # generator output so the two trees cannot drift apart.
    fabric_project = ROOT / "versions" / minecraft
    for name in SHARED_FILES + [PLATFORM_FILE["fabric"]]:
        source = fabric_project / PACKAGE_DIR / name
        if not source.exists():
            raise SystemExit(f"missing shared source {source}")
        write(project / PACKAGE_DIR / name, source.read_text())

    mod_source = NEOFORGE_MOD if loader == "neoforge" else FORGE_MOD_LEGACY
    write(project / PACKAGE_DIR / "CustomSplash.java", mod_source)
    # Forge/NeoForge need the Forge platform implementation, not the Fabric one.
    fabric_platform = project / PACKAGE_DIR / PLATFORM_FILE["fabric"]
    if fabric_platform.exists():
        fabric_platform.unlink()
    write(project / PACKAGE_DIR / "SplashForgePlatform.java", FORGE_PLATFORM)

    mixin = MIXIN_OLD if uses_legacy_mixin(minecraft) else MIXIN_NEW
    write(project / MIXIN_DIR / "SplashManagerMixin.java", mixin)

    (project / "src" / "main" / "resources").mkdir(parents=True, exist_ok=True)
    # Forge builds the refmap with the Mixin annotation processor; NeoForge runs
    # on human readable names so it must not reference a refmap file.
    needs_refmap = loader == "forge" and srg_runtime
    refmap = ",\n\t\"refmap\": \"customsplash.refmap.json\"" if needs_refmap else ""
    write(
        project / "src" / "main" / "resources" / "customsplash.mixins.json",
        MIXIN_CONFIG.format(mixin_java=mixin_java(java), refmap=refmap),
    )
    toml = MODS_TOML.format(loader_dependency="neoforge" if loader == "neoforge" else "forge")
    toml_name = "neoforge.mods.toml" if loader == "neoforge" else "mods.toml"
    write(project / "src" / "main" / "resources" / "META-INF" / toml_name, toml)
    print(f"created {loader}/{minecraft}")


def write_version_list(name: str, versions: list) -> None:
    path = ROOT / name
    write(path, "\n".join(versions) + "\n")


def main() -> None:
    write_version_list("supported-forge-versions.txt", FORGE_VERSIONS)
    write_version_list("supported-neoforge-versions.txt", NEOFORGE_VERSIONS)

    for minecraft in FORGE_VERSIONS:
        scaffold(
            "forge",
            minecraft,
            FORGE_LOADER_VERSION,
            {
                "loader_version": FORGE_LOADER_VERSION[minecraft],
                "forge_gradle_version": FORGE_GRADLE_VERSION[minecraft],
                "maven_url": "https://maven.minecraftforge.net/",
            },
        )

    for minecraft in NEOFORGE_VERSIONS:
        scaffold(
            "neoforge",
            minecraft,
            NEOFORGE_LOADER_VERSION,
            {
                "neoforge_version": NEOFORGE_LOADER_VERSION[minecraft],
                "moddev_version": MODDEV_VERSION,
                "maven_url": "https://maven.neoforged.net/releases/",
            },
        )


if __name__ == "__main__":
    main()
