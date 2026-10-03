package dev.arrbrants.customsplash;

import java.nio.file.Path;

/**
 * The loader-specific bits the shared sources need. Fabric and Forge each
 * install their own implementation at mod construction time; until then a
 * no-op fallback is used, so the classes never touch a loader directly.
 */
public interface SplashPlatform {
	/**
	 * @return the config directory, or {@code null} when unavailable
	 */
	Path getConfigDir();

	/**
	 * @return the game directory, or {@code null} when unavailable
	 */
	Path getGameDir();

	/**
	 * @param modId a mod id
	 * @return whether the mod is loaded, {@code false} when no loader is present
	 */
	boolean isModLoaded(String modId);

	/**
	 * @return the number of loaded mods, or {@code -1} when unavailable
	 */
	int loadedModCount();

	/**
	 * @return the active platform, never {@code null}
	 */
	static SplashPlatform get() {
		return Holder.INSTANCE;
	}

	/**
	 * Replace the active platform. Loader entry points call this once during
	 * construction; tests may install a stub.
	 */
	static void install(SplashPlatform platform) {
		if (platform != null) {
			Holder.INSTANCE = platform;
		}
	}

	/** The fallback used before a loader installs itself. */
	enum Unavailable implements SplashPlatform {
		INSTANCE;

		@Override
		public Path getConfigDir() {
			return null;
		}

		@Override
		public Path getGameDir() {
			return null;
		}

		@Override
		public boolean isModLoaded(String modId) {
			return false;
		}

		@Override
		public int loadedModCount() {
			return -1;
		}
	}

	final class Holder {
		private static volatile SplashPlatform INSTANCE = Unavailable.INSTANCE;

		private Holder() {
		}
	}
}
