package dev.arrbrants.customsplash;

import net.fabricmc.loader.api.FabricLoader;

import java.nio.file.Path;
import java.nio.file.Paths;

/**
 * Fabric implementation of {@link SplashPlatform}, installed by
 * {@link CustomSplash#onInitialize()}.
 */
public final class FabricSplashPlatform implements SplashPlatform {
	private static final Path FALLBACK_CONFIG = Paths.get("config");

	private FabricSplashPlatform() {
	}

	public static void install() {
		SplashPlatform.install(new FabricSplashPlatform());
	}

	@Override
	public Path getConfigDir() {
		try {
			return FabricLoader.getInstance().getConfigDir();
		} catch (RuntimeException | LinkageError ignored) {
			return FALLBACK_CONFIG;
		}
	}

	@Override
	public Path getGameDir() {
		try {
			return FabricLoader.getInstance().getGameDir();
		} catch (RuntimeException | LinkageError ignored) {
			return null;
		}
	}

	@Override
	public boolean isModLoaded(String modId) {
		try {
			return FabricLoader.getInstance().isModLoaded(modId);
		} catch (RuntimeException | LinkageError ignored) {
			return false;
		}
	}

	@Override
	public int loadedModCount() {
		try {
			return FabricLoader.getInstance().getAllMods().size();
		} catch (RuntimeException | LinkageError ignored) {
			return -1;
		}
	}
}
