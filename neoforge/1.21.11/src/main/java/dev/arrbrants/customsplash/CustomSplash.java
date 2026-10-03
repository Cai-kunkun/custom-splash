package dev.arrbrants.customsplash;

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
