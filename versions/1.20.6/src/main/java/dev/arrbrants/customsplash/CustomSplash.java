package dev.arrbrants.customsplash;

import net.fabricmc.api.ModInitializer;
import net.fabricmc.loader.api.FabricLoader;
import net.fabricmc.loader.api.ModContainer;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class CustomSplash implements ModInitializer {
	public static final String MOD_ID = "custom-splash";
	public static final Logger LOGGER = LoggerFactory.getLogger(MOD_ID);

	@Override
	public void onInitialize() {
		String name = FabricLoader.getInstance().getModContainer(MOD_ID)
				.map(ModContainer::getMetadata).map(meta -> meta.getName()).orElse(MOD_ID);
		LOGGER.info("{} has initialized successfully", name);
	}
}
