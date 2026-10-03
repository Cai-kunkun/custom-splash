package dev.arrbrants.customsplash;

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
