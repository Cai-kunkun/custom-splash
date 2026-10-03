package dev.arrbrants.customsplash;

import java.nio.file.Path;

/**
 * Loader specific hooks. The implementation is generated per platform so the
 * shared sources stay free of loader imports.
 */
public interface SplashPlatform {
	/** Directory holding the mod configuration file. */
	Path configDir();

	/** Game installation directory. */
	Path gameDir();

	/** Whether another mod is currently loaded. */
	boolean isModLoaded(String modId);

	/** Platform name used in log messages, for example {@code "Fabric"}. */
	String platformName();
}
