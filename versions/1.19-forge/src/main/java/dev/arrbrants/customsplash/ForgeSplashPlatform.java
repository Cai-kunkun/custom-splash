package dev.arrbrants.customsplash;

import net.minecraftforge.fml.ModList;
import net.minecraftforge.fml.loading.FMLPaths;

import java.nio.file.Path;

/**
 * Forge implementation of {@link SplashPlatform}, installed by
 * {@link CustomSplash} at mod construction time.
 */
public final class ForgeSplashPlatform implements SplashPlatform {

	private ForgeSplashPlatform() {
	}

	public static void install() {
		SplashPlatform.install(new ForgeSplashPlatform());
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
