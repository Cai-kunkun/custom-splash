package dev.arrbrants.customsplash;

import net.neoforged.bus.api.IEventBus;
import net.neoforged.fml.common.Mod;
import net.neoforged.fml.event.lifecycle.FMLCommonSetupEvent;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@Mod(CustomSplash.MOD_ID)
public class CustomSplash {
	public static final String MOD_ID = "custom-splash";
	public static final Logger LOGGER = LoggerFactory.getLogger(MOD_ID);

	public CustomSplash(IEventBus modEventBus) {
		NeoForgeSplashPlatform.install();
		modEventBus.addListener(this::onCommonSetup);
		LOGGER.info("Custom Splash has initialized");
	}

	private void onCommonSetup(FMLCommonSetupEvent event) {
		SplashRegistry.reload();
	}
}
