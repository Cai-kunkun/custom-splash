package dev.arrbrants.customsplash;

import java.nio.file.Path;

/** Holds the platform implementation chosen at build time. */
public final class SplashPlatforms {
	private static volatile SplashPlatform platform;

	private SplashPlatforms() {
	}

	/** Installs the implementation for the current platform. */
	public static void install(SplashPlatform implementation) {
		platform = implementation;
	}

	/** @throws IllegalStateException when the platform has not been installed yet */
	public static SplashPlatform get() {
		SplashPlatform installed = platform;
		if (installed == null) {
			throw new IllegalStateException("Splash platform has not been installed");
		}
		return installed;
	}
}
