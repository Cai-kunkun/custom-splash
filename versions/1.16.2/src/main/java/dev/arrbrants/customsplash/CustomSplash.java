package dev.arrbrants.customsplash;

import net.fabricmc.api.ModInitializer;
import net.fabricmc.loader.api.FabricLoader;
import net.fabricmc.loader.api.ModContainer;
import java.util.logging.Logger;

public class CustomSplash implements ModInitializer {
	public static final String MOD_ID = "custom-splash";
	public static final Logger LOGGER = Logger.getLogger(MOD_ID);

	@Override
	public void onInitialize() {
		String name = FabricLoader.getInstance().getModContainer(MOD_ID)
				.map(ModContainer::getMetadata).map(meta -> meta.getName()).orElse(MOD_ID);
		LOGGER.info(name + " has initialized successfully");
	}
}
