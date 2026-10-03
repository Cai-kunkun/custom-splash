package dev.arrbrants.customsplash;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import net.fabricmc.loader.api.FabricLoader;

import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Optional;
import java.time.format.DateTimeFormatter;
import java.util.Random;

/**
 * Public API and config-backed splash store.
 *
 * <p>Texts come from the JSON config file and from {@link #add(String)}. One is
 * chosen at random (respecting per-entry weights) whenever the splash text is
 * drawn. When nothing matches, the vanilla splash is used.</p>
 */
public final class SplashRegistry {
	private static Path configPathCache;
	private static final Gson GSON = new GsonBuilder().setPrettyPrinting().disableHtmlEscaping().create();
	private static final List<SplashEntry> REGISTERED = Collections.synchronizedList(new ArrayList<SplashEntry>());
	private static final Random RNG = new Random();
	private static volatile SplashConfig config = new SplashConfig();
	private static volatile List<SplashEntry> resourcePackEntries = Collections.emptyList();
	private static volatile long resourcePackLoadedAt;
	private static final long RESOURCE_PACK_TTL_MS = 5000L;
	private static final DateTimeFormatter DATE_FORMAT = DateTimeFormatter.ofPattern("yyyy-MM-dd");
	private static final DateTimeFormatter TIME_FORMAT = DateTimeFormatter.ofPattern("HH:mm");

	private SplashRegistry() {
	}

	/**
	 * Register a splash text with the default weight of 1.
	 */
	public static void add(String text) {
		add(text, 1);
	}

	/**
	 * Register a splash text with a custom relative weight.
	 */
	public static void add(String text, int weight) {
		if (text != null && !text.isEmpty()) {
			REGISTERED.add(new SplashEntry(text, weight));
		}
	}

	/**
	 * Remove every registered text equal to {@code text}.
	 *
	 * @return {@code true} if at least one entry was removed
	 */
	public static boolean remove(String text) {
		if (text == null) {
			return false;
		}
		synchronized (REGISTERED) {
			return REGISTERED.removeIf(entry -> text.equals(entry.text));
		}
	}

	/**
	 * Remove all runtime-registered texts. The config file is untouched.
	 */
	public static void clear() {
		REGISTERED.clear();
	}

	/**
	 * @return an immutable view of every currently known text (config first).
	 */
	public static List<String> list() {
		List<String> texts = new ArrayList<>();
		for (SplashEntry entry : config.splashes) {
			if (entry != null && !entry.isBlank()) {
				texts.add(entry.text);
			}
		}
		for (SplashEntry entry : resourcePackEntries) {
			if (entry != null && !entry.isBlank()) {
				texts.add(entry.text);
			}
		}
		synchronized (REGISTERED) {
			for (SplashEntry entry : REGISTERED) {
				if (!entry.isBlank()) {
					texts.add(entry.text);
				}
			}
		}
		return Collections.unmodifiableList(texts);
	}

	/**
	 * @return the number of currently known texts
	 */
	public static int count() {
		return list().size();
	}

	/**
	 * Pick a splash text, honouring weights and display conditions.
	 *
	 * @return a splash text, or empty when nothing is configured/matches
	 */
	public static Optional<String> pick() {
		return pickEntry().map(picked -> picked.text);
	}

	/**
	 * Pick a splash entry, keeping colour information for the renderer.
	 */
	public static Optional<Picked> pickEntry() {
		refreshResourcePacksIfStale();
		SplashContext context = SplashContext.create();
		List<SplashEntry> pool = new ArrayList<>();
		for (SplashEntry entry : config.splashes) {
			if (entry != null && !entry.isBlank() && entry.matches(context)) {
				pool.add(entry);
			}
		}
		for (SplashEntry entry : resourcePackEntries) {
			if (entry != null && !entry.isBlank() && entry.matches(context)) {
				pool.add(entry);
			}
		}
		synchronized (REGISTERED) {
			for (SplashEntry entry : REGISTERED) {
				if (!entry.isBlank() && entry.matches(context)) {
					pool.add(entry);
				}
			}
		}
		if (pool.isEmpty()) {
			return Optional.empty();
		}
		SplashEntry chosen = chooseWeighted(pool, RNG);
		SplashColor color = chosen.colorSpec();
		return Optional.of(new Picked(format(chosen.text, context), color == null ? -1 : color.solidRgb(), color));
	}

	/**
	 * Pick one entry using relative weights. Visible for testing.
	 */
	static SplashEntry chooseWeighted(List<SplashEntry> pool, Random random) {
		int total = 0;
		for (SplashEntry entry : pool) {
			total += entry.weightOrDefault();
		}
		int roll = random.nextInt(total);
		for (SplashEntry entry : pool) {
			roll -= entry.weightOrDefault();
			if (roll < 0) {
				return entry;
			}
		}
		return pool.get(pool.size() - 1);
	}

	/**
	 * Reload the JSON config file, creating it with defaults when missing.
	 */
	public static void reload() {
		config = SplashConfig.load(configPath(), GSON);
		refreshResourcePacks();
	}

	private static void refreshResourcePacks() {
		resourcePackEntries = SplashResourcePack.load();
		resourcePackLoadedAt = System.currentTimeMillis();
	}

	private static void refreshResourcePacksIfStale() {
		if (System.currentTimeMillis() - resourcePackLoadedAt > RESOURCE_PACK_TTL_MS) {
			refreshResourcePacks();
		}
	}

	/**
	 * @return the path of the JSON config file
	 */
	public static Path configPath() {
		Path path = configPathCache;
		if (path == null) {
			path = FabricLoader.getInstance().getConfigDir().resolve("custom-splash.json");
			configPathCache = path;
		}
		return path;
	}

	/**
		* Replace the supported placeholders. Unknown tokens are left untouched so
		* that text such as an emoticon keeps working.
	 */
	static String format(String text, SplashContext context) {
		if (text.indexOf('{') < 0) {
			return text;
		}
		String player = context.playerName();
		String name = player == null ? "player" : player;
		String[] tokens = {
			"{player}", name, "{username}", name,
			"{date}", context.date().format(DATE_FORMAT),
			"{time}", context.time().format(TIME_FORMAT),
			"{mods}", context.modCount(),
			"{mods_count}", context.modCount(),
			"{mc_version}", context.gameVersion(),
			"{mc}", context.gameVersion(),
			"{version}", context.gameVersion(),
		};
		String result = text;
		for (int i = 0; i < tokens.length; i += 2) {
			if (tokens[i + 1] != null) {
				result = result.replace(tokens[i], tokens[i + 1]);
			}
		}
		return result;
	}

	/**
	 * A chosen splash ready to be rendered.
	 */
	public static final class Picked {
		public final String text;
		/** the solid RGB value, or {@code -1} when unset or multi-coloured */
		public final int rgb;
		/** the full colour specification, or {@code null} when unset */
		public final SplashColor color;

		Picked(String text, int rgb, SplashColor color) {
			this.text = text;
			this.rgb = rgb;
			this.color = color;
		}
	}
}
