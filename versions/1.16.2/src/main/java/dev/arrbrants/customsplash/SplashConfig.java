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
 * The JSON config model. A default file is written on first launch, and the same
 * schema is reused for structured resource pack files.
 */
public final class SplashConfig {
	private static final Logger LOGGER = Logger.getLogger("custom-splash");

	private static final String DEFAULT_JSON = "{\n"
		+ "\t// Custom Splash configuration.\n"
		+ "\t//\n"
		+ "\t// \"splashes\" lists the texts shown on the title screen. One entry is picked at\n"
		+ "\t// random each time the title screen is opened, and a higher \"weight\" is picked\n"
		+ "\t// more often. Comments like these are allowed anywhere in the file, so this\n"
		+ "\t// reference and the examples below can be kept for later.\n"
		+ "\t//\n"
		+ "\t// Fields - only \"text\" is required:\n"
		+ "\t//\n"
		+ "\t//   \"text\"        the splash text. Placeholders are filled in when it is drawn:\n"
		+ "\t//                 {player} {username} {date} {time} {mc_version} {mc}\n"
		+ "\t//                 {version} {mods} {mods_count}\n"
		+ "\t//   \"weight\"      relative chance, default 1.\n"
		+ "\t//   \"color\"       \"#RRGGBB\", a gradient \"#RRGGBB,#RRGGBB\" with two or more\n"
		+ "\t//                 stops, \"rainbow\", or \"rainbow:<degrees per character>\".\n"
		+ "\t//   \"conditions\"  every listed condition must match:\n"
		+ "\t//                 \"time\"     \"day\" or \"night\"\n"
		+ "\t//                 \"date\"     \"MM-DD\" or \"MM-DD..MM-DD\", may wrap the new year\n"
		+ "\t//                 \"weekend\"  true or false\n"
		+ "\t//                 \"player\"   list of usernames\n"
		+ "\t//                 \"mods\"     list of required mod ids\n"
		+ "\t//                 \"chance\"   0.0 to 1.0\n"
		+ "\t//\n"
		+ "\t// Examples - delete the leading \"//\" to enable one:\n"
		+ "\t//\n"
		+ "\t//   { \"text\": \"Hello, {player}!\", \"weight\": 5, \"color\": \"#FFAA00\" },\n"
		+ "\t//   { \"text\": \"Gradient!\", \"color\": \"#FF0000,#00FF00\" },\n"
		+ "\t//   { \"text\": \"Rainbow!\", \"color\": \"rainbow:25\" },\n"
		+ "\t//   { \"text\": \"Enjoy the weekend!\", \"conditions\": { \"weekend\": true } },\n"
		+ "\t//   { \"text\": \"Late night coding\", \"conditions\": { \"time\": \"night\", \"chance\": 0.5 } },\n"
		+ "\t//   { \"text\": \"Happy holidays!\", \"conditions\": { \"date\": \"12-20..12-26\" } },\n"
		+ "\t//   { \"text\": \"You run Fabric!\", \"conditions\": { \"mods\": [\"fabric\"] } },\n"
		+ "\t//\n"
		+ "\t\"splashes\": [\n"
		+ "\t\t{ \"text\": \"Check your custom splash config file to customize!\" }\n"
		+ "\t]\n"
		+ "}\n";

	public List<SplashEntry> splashes = new ArrayList<>();

	/**
	 * Parse the schema without touching the file system, so resource packs can
	 * reuse it. This never validates or logs, because packs are re-read
	 * periodically and one broken pack must not keep filling the log.
	 */
	static SplashConfig parse(String json, Gson gson) {
		SplashConfig parsed = gson.fromJson(json, SplashConfig.class);
		if (parsed == null) {
			parsed = new SplashConfig();
		}
		if (parsed.splashes == null) {
			parsed.splashes = new ArrayList<>();
		}
		return parsed;
	}

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
			SplashConfig parsed = parse(json, gson);
			validate(parsed);
			return parsed;
		} catch (IOException | RuntimeException exception) {
			LOGGER.log(Level.WARNING, "Failed to load splash config from " + path, exception);
			return new SplashConfig();
		}
	}

	/**
	 * Report every entry that cannot work as written. Misconfiguration used to
	 * fail silently, which made a broken config impossible to debug: an
	 * unparseable colour quietly fell back to yellow and an unparseable date
	 * quietly never matched.
	 */
	private static void validate(SplashConfig config) {
		List<SplashEntry> entries = config.splashes;
		for (int index = 0; index < entries.size(); index++) {
			SplashEntry entry = entries.get(index);
			if (entry == null) {
				LOGGER.warning("splash #" + (index + 1) + " is null and will be ignored");
				continue;
			}
			if (entry.isBlank()) {
				LOGGER.warning("splash #" + (index + 1) + " has no text and will be ignored");
				continue;
			}
			String where = "splash #" + (index + 1) + " ('" + entry.text + "')";
			if (entry.weight <= 0) {
				LOGGER.warning(where + " has weight " + entry.weight + "; using 1 instead");
			}
			if (entry.color != null && !entry.color.isEmpty() && entry.colorSpec() == null) {
				LOGGER.warning(where + " has an unrecognised color '" + entry.color
					+ "'; using the vanilla yellow");
			}
			SplashEntry.Conditions conditions = entry.conditions;
			if (conditions == null) {
				continue;
			}
			String problem = conditions.timeProblem();
			if (problem != null) {
				LOGGER.warning(where + " has an invalid time '" + conditions.time + "': " + problem
					+ "; the condition is ignored");
			}
			problem = conditions.dateProblem();
			if (problem != null) {
				LOGGER.warning(where + " has an invalid date '" + conditions.date + "': " + problem
					+ "; the splash will never be shown");
			}
			if (conditions.chance != null && (conditions.chance < 0.0D || conditions.chance > 1.0D)) {
				LOGGER.warning(where + " has a chance outside 0.0-1.0: " + conditions.chance);
			}
		}
	}
}
