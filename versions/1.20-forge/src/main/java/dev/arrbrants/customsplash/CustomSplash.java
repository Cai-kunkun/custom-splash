package dev.arrbrants.customsplash;

import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.fml.event.lifecycle.FMLCommonSetupEvent;
import net.minecraftforge.fml.javafmlmod.FMLJavaModLoadingContext;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

@Mod(CustomSplash.MOD_ID)
public class CustomSplash {
	public static final String MOD_ID = "custom-splash";
	public static final Logger LOGGER = LogManager.getLogger(MOD_ID);

	public CustomSplash() {
		ForgeSplashPlatform.install();
		FMLJavaModLoadingContext.get().getModEventBus().addListener(this::onCommonSetup);
		LOGGER.info("Custom Splash has initialized");
	}

	private void onCommonSetup(FMLCommonSetupEvent event) {
		SplashRegistry.reload();
	}
}
