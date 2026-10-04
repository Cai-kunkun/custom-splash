package dev.arrbrants.customsplash;

import net.neoforged.fml.ModList;
import net.neoforged.fml.loading.FMLPaths;

import java.nio.file.Path;

/**
 * NeoForge implementation of {@link SplashPlatform}, installed by
 * {@link CustomSplash} at mod construction time.
 */
public final class NeoForgeSplashPlatform implements SplashPlatform {

	private NeoForgeSplashPlatform() {
	}

	public static void install() {
		SplashPlatform.install(new NeoForgeSplashPlatform());
	}

	@Override
	public Path getConfigDir() {
		return FMLPaths.CONFIGDIR.get();
	}

	@Override
	public Path getGameDir() {
		return FMLPaths.GAMEDIR.get();
	}

	@Override
	public boolean isModLoaded(String modId) {
		return ModList.get().isLoaded(modId);
	}

	@Override
	public int loadedModCount() {
		return ModList.get().getMods().size();
	}
}
