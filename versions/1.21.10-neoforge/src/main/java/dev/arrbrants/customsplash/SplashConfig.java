package dev.arrbrants.customsplash;

import com.google.gson.Gson;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.logging.Level;
import java.util.logging.Logger;

/**
 * The JSON config model. A default file is written on first launch.
 */
public final class SplashConfig {
	private static final Logger LOGGER = Logger.getLogger("custom-splash");

	private static final String DEFAULT_JSON = "{\n"
		+ "\t\"splashes\": [\n"
		+ "\t\t{ \"text\": \"Check your custom splash config file to customize!\" }\n"
		+ "\t]\n"
		+ "}\n";

	public List<SplashEntry> splashes = new ArrayList<>();

	static SplashConfig load(Path path, Gson gson) {
		try {
			if (path.getParent() != null) {
				Files.createDirectories(path.getParent());
			}
			if (!Files.exists(path)) {
				Files.write(path, DEFAULT_JSON.getBytes(StandardCharsets.UTF_8));
				LOGGER.info("Created default splash config at " + path);
			}
			String json = new String(Files.readAllBytes(path), StandardCharsets.UTF_8);
			SplashConfig parsed = gson.fromJson(json, SplashConfig.class);
			if (parsed == null) {
				parsed = new SplashConfig();
			}
			if (parsed.splashes == null) {
				parsed.splashes = new ArrayList<>();
			}
			return parsed;
		} catch (IOException | RuntimeException exception) {
			LOGGER.log(Level.WARNING, "Failed to load splash config from " + path, exception);
			return new SplashConfig();
		}
	}
}
