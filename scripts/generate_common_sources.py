#!/usr/bin/env python3
"""Synchronise the shared Custom Splash sources across every version project.

Features implemented here: JSON config file, weighted entries, display
conditions, colour support and an extended public API.

The shared sources contain no Minecraft compile-time references (player lookup is
reflective) and touch the loader only through SplashPlatform, so the exact same
files work on every Fabric, Forge and NeoForge version. Only the mixin differs
between versions: up to 1.19 the splash is a plain String, read from
SplashTextResourceSupplier#get under Yarn (1.14-1.14.3) or
SplashManager#getSplash under Mojang mappings (1.14.4-1.19.4); 1.20+ uses
SplashRenderer.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSIONS_FILE = ROOT / "supported-versions.txt"
PACKAGE_DIR = "src/main/java/dev/arrbrants/customsplash"
MIXIN_DIR = PACKAGE_DIR + "/mixin"
RESOURCES_DIR = "src/main/resources"
# Loaders look the mod icon up under the mod id, so the resource path must use
# "custom-splash". This repository-level source image is copied into every
# version project by write_icon().
ICON_RESOURCE = "assets/custom-splash/icon.png"
ICON_SOURCE = ROOT / RESOURCES_DIR / ICON_RESOURCE

SOURCES = {}

SOURCES["SplashPlatform.java"] = '''package dev.arrbrants.customsplash;

import java.nio.file.Path;

/**
 * The loader-specific bits the shared sources need. Fabric and Forge each
 * install their own implementation at mod construction time; until then a
 * no-op fallback is used, so the classes never touch a loader directly.
 */
public interface SplashPlatform {
	/**
	 * @return the config directory, or {@code null} when unavailable
	 */
	Path getConfigDir();

	/**
	 * @return the game directory, or {@code null} when unavailable
	 */
	Path getGameDir();

	/**
	 * @param modId a mod id
	 * @return whether the mod is loaded, {@code false} when no loader is present
	 */
	boolean isModLoaded(String modId);

	/**
	 * @return the number of loaded mods, or {@code -1} when unavailable
	 */
	int loadedModCount();

	/**
	 * @return the active platform, never {@code null}
	 */
	static SplashPlatform get() {
		return Holder.INSTANCE;
	}

	/**
	 * Replace the active platform. Loader entry points call this once during
	 * construction; tests may install a stub.
	 */
	static void install(SplashPlatform platform) {
		if (platform != null) {
			Holder.INSTANCE = platform;
		}
	}

	/** The fallback used before a loader installs itself. */
	enum Unavailable implements SplashPlatform {
		INSTANCE;

		@Override
		public Path getConfigDir() {
			return null;
		}

		@Override
		public Path getGameDir() {
			return null;
		}

		@Override
		public boolean isModLoaded(String modId) {
			return false;
		}

		@Override
		public int loadedModCount() {
			return -1;
		}
	}

	final class Holder {
		private static volatile SplashPlatform INSTANCE = Unavailable.INSTANCE;

		private Holder() {
		}
	}
}
'''

SOURCES["SplashContext.java"] = '''package dev.arrbrants.customsplash;


import java.lang.reflect.Method;
import java.time.LocalDate;
import java.time.LocalTime;
import java.util.Random;
import java.util.concurrent.ThreadLocalRandom;

/**
 * Runtime information used to evaluate splash conditions.
 * Minecraft is accessed reflectively so this class loads on every supported version.
 */
final class SplashContext {
\tprivate final LocalTime time;
\tprivate final LocalDate date;
\tprivate final String playerName;
\tprivate final Random random;

\tSplashContext(LocalTime time, LocalDate date, String playerName, Random random) {
\t\tthis.time = time;
\t\tthis.date = date;
\t\tthis.playerName = playerName;
\t\tthis.random = random;
\t}

\tstatic SplashContext create() {
\t\treturn new SplashContext(LocalTime.now(), LocalDate.now(), lookupPlayerName(), ThreadLocalRandom.current());
\t}

\tLocalTime time() {
\t\treturn time;
\t}

\tLocalDate date() {
\t\treturn date;
\t}

\tString playerName() {
\t\treturn playerName;
\t}

\t/**
\t * @return the running Minecraft version, or null when unavailable
\t */
\tString gameVersion() {
\t\ttry {
\t\t\tClass<?> minecraft = Class.forName("net.minecraft.client.Minecraft");
\t\t\tObject instance = invoke(minecraft, null, "getInstance");
\t\t\tif (instance == null) {
\t\t\t\treturn null;
\t\t\t}
\t\t\tObject version = invoke(instance.getClass(), instance, "getLaunchedVersion", "getGameVersion");
\t\t\treturn version instanceof String ? (String) version : null;
\t\t} catch (Throwable ignored) {
\t\t\treturn null;
\t\t}
\t}

\t/**
\t * @return the number of loaded mods, or null when unavailable
\t */
\tString modCount() {
\t\tint count = SplashPlatform.get().loadedModCount();
\t\treturn count < 0 ? null : String.valueOf(count);
\t}

\tboolean hasMod(String modId) {
\t\treturn modId != null && SplashPlatform.get().isModLoaded(modId);
\t}

\tboolean roll(double probability) {
\t\treturn probability >= 1.0D || (probability > 0.0D && random.nextDouble() < probability);
\t}

\tprivate static String lookupPlayerName() {
\t\ttry {
\t\t\tClass<?> minecraft = Class.forName("net.minecraft.client.Minecraft");
\t\t\tObject instance = invoke(minecraft, null, "getInstance");
\t\t\tif (instance == null) {
\t\t\t\treturn null;
\t\t\t}
\t\t\tObject user = invoke(instance.getClass(), instance, "getUser", "getGameProfile");
\t\t\tif (user == null) {
\t\t\t\treturn null;
\t\t\t}
\t\t\tObject name = invoke(user.getClass(), user, "getName");
\t\t\treturn name instanceof String ? (String) name : null;
\t\t} catch (Throwable ignored) {
\t\t\treturn null;
\t\t}
\t}

\tprivate static Object invoke(Class<?> type, Object target, String... names) {
\t\tfor (String name : names) {
\t\t\ttry {
\t\t\t\tMethod method = type.getMethod(name);
\t\t\t\treturn method.invoke(target);
\t\t\t} catch (Throwable ignored) {
\t\t\t\t// Try the next candidate method name.
\t\t\t}
\t\t}
\t\treturn null;
\t}
}
'''

SOURCES["SplashColors.java"] = '''package dev.arrbrants.customsplash;

/**
 * Parses ``#RRGGBB`` colours and maps them onto the legacy 16-colour palette.
 */
public final class SplashColors {
\tprivate static final int[] PALETTE = {
\t\t0x000000, 0x0000AA, 0x00AA00, 0x00AAAA, 0xAA0000, 0xAA00AA, 0xFFAA00, 0xAAAAAA,
\t\t0x555555, 0x5555FF, 0x55FF55, 0x55FFFF, 0xFF5555, 0xFF55FF, 0xFFFF55, 0xFFFFFF
\t};
\tprivate static final char[] CODES = {
\t\t'0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c', 'd', 'e', 'f'
\t};

\tprivate SplashColors() {
\t}

\t/**
\t * @return the packed RGB value, or {@code -1} when the input is missing/invalid
\t */
\tpublic static int parse(String value) {
\t\tif (value == null) {
\t\t\treturn -1;
\t\t}
\t\tString hex = value.trim();
\t\tif (hex.startsWith("#")) {
\t\t\thex = hex.substring(1);
\t\t}
\t\tif (hex.length() != 6) {
\t\t\treturn -1;
\t\t}
\t\ttry {
\t\t\treturn Integer.parseInt(hex, 16);
\t\t} catch (NumberFormatException exception) {
\t\t\treturn -1;
\t\t}
\t}

\tpublic static String legacyPrefix(int rgb) {
\t\treturn "\\u00a7" + legacyCode(rgb);
\t}

\tpublic static char legacyCode(int rgb) {
\t\tint red = (rgb >> 16) & 0xFF;
\t\tint green = (rgb >> 8) & 0xFF;
\t\tint blue = rgb & 0xFF;
\t\tint best = 0;
\t\tlong bestDistance = Long.MAX_VALUE;
\t\tfor (int i = 0; i < PALETTE.length; i++) {
\t\t\tint r = (PALETTE[i] >> 16) & 0xFF;
\t\t\tint g = (PALETTE[i] >> 8) & 0xFF;
\t\t\tint b = PALETTE[i] & 0xFF;
\t\t\tlong distance = (long) (red - r) * (red - r)
\t\t\t\t+ (long) (green - g) * (green - g)
\t\t\t\t+ (long) (blue - b) * (blue - b);
\t\t\tif (distance < bestDistance) {
\t\t\t\tbestDistance = distance;
\t\t\t\tbest = i;
\t\t\t}
\t\t}
\t\treturn CODES[best];
\t}
}
'''

SOURCES["SplashColor.java"] = '''package dev.arrbrants.customsplash;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

/**
 * A splash colour, either a single value or a multi-character gradient.
 *
 * <p>Accepted forms: {@code #RRGGBB} for a solid colour,
 * {@code #RRGGBB,#RRGGBB[,...]} for a gradient spread over the text and
 * {@code rainbow} / {@code rainbow:degrees} for a hue cycle. Anything else
 * (including {@code null} and blank input) is rejected.</p>
 */
public final class SplashColor {
\tprivate static final int DEFAULT_HUE_SPREAD = 15;

\tprivate final int[] stops;
\tprivate final boolean rainbow;
\tprivate final int hueSpread;

\tprivate SplashColor(int[] stops, boolean rainbow, int hueSpread) {
\t\tthis.stops = stops;
\t\tthis.rainbow = rainbow;
\t\tthis.hueSpread = hueSpread;
\t}

\t/**
\t * @return the parsed colour, or {@code null} when the value is missing or invalid
\t */
\tpublic static SplashColor parse(String value) {
\t\tif (value == null) {
\t\t\treturn null;
\t\t}
\t\tString text = value.trim();
\t\tif (text.isEmpty()) {
\t\t\treturn null;
\t\t}
\t\tif (text.regionMatches(true, 0, "rainbow", 0, 7)) {
\t\t\treturn parseRainbow(text);
\t\t}
\t\tList<Integer> colors = new ArrayList<>();
\t\tfor (String part : text.split(",")) {
\t\t\tString candidate = part.trim();
\t\t\tif (candidate.regionMatches(true, 0, "gradient:", 0, 9)) {
\t\t\t\tcandidate = candidate.substring(9).trim();
\t\t\t}
\t\t\tint rgb = SplashColors.parse(candidate);
\t\t\tif (rgb < 0) {
\t\t\t\treturn null;
\t\t\t}
\t\t\tcolors.add(rgb);
\t\t}
\t\tif (colors.isEmpty()) {
\t\t\treturn null;
\t\t}
\t\tint[] stops = new int[colors.size()];
\t\tfor (int i = 0; i < stops.length; i++) {
\t\t\tstops[i] = colors.get(i);
\t\t}
\t\treturn new SplashColor(stops, false, 0);
\t}

\tprivate static SplashColor parseRainbow(String text) {
\t\tif (text.length() == 7) {
\t\t\treturn new SplashColor(null, true, DEFAULT_HUE_SPREAD);
\t\t}
\t\tif (text.charAt(7) != \':\') {
\t\t\treturn null;
\t\t}
\t\ttry {
\t\t\tint spread = Integer.parseInt(text.substring(8).trim());
\t\t\tif (spread < 0 || spread > 360) {
\t\t\t\treturn null;
\t\t\t}
\t\t\treturn new SplashColor(null, true, spread);
\t\t} catch (NumberFormatException exception) {
\t\t\treturn null;
\t\t}
\t}

\tpublic boolean isSolid() {
\t\treturn !rainbow && stops.length == 1;
\t}

\t/**
\t * @return the packed RGB value, or {@code -1} when the colour is not solid
\t */
\tpublic int solidRgb() {
\t\treturn isSolid() ? stops[0] : -1;
\t}

\t/**
\t * @return one RGB value per character of {@code text}, never {@code null}
\t */
\tpublic int[] colorsFor(String text) {
\t\tint length = text.length();
\t\tint[] colors = new int[length];
\t\tif (isSolid()) {
\t\t\tArrays.fill(colors, stops[0]);
\t\t\treturn colors;
\t\t}
\t\tif (rainbow) {
\t\t\tfor (int i = 0; i < length; i++) {
\t\t\t\tcolors[i] = hueToRgb(i * hueSpread);
\t\t\t}
\t\t\treturn colors;
\t\t}
\t\tfor (int i = 0; i < length; i++) {
\t\t\tcolors[i] = sample(stops, length == 1 ? 0.0D : (double) i / (length - 1));
\t\t}
\t\treturn colors;
\t}

\tprivate static int sample(int[] stops, double position) {
\t\tdouble scaled = Math.max(0.0D, Math.min(1.0D, position)) * (stops.length - 1);
\t\tint index = (int) scaled;
\t\tdouble fraction = scaled - index;
\t\tif (index >= stops.length - 1) {
\t\t\treturn stops[stops.length - 1];
\t\t}
\t\treturn interpolate(stops[index], stops[index + 1], fraction);
\t}

\tprivate static int interpolate(int from, int to, double fraction) {
\t\tint red = Math.round(lerp(from >> 16 & 0xFF, to >> 16 & 0xFF, fraction));
\t\tint green = Math.round(lerp(from >> 8 & 0xFF, to >> 8 & 0xFF, fraction));
\t\tint blue = Math.round(lerp(from & 0xFF, to & 0xFF, fraction));
\t\treturn red << 16 | green << 8 | blue;
\t}

\tprivate static float lerp(int from, int to, double fraction) {
\t\treturn (float) (from + (to - from) * fraction);
\t}

\tprivate static int hueToRgb(int hue) {
\t\tfloat position = (((hue % 360) + 360) % 360) / 360f;
\t\tint sector = (int) (position * 6);
\t\tfloat fraction = position * 6 - sector;
\t\tfloat value = 1f;
\t\tfloat minuend = value * (1 - fraction);
\t\tfloat descending = value * (1 - (1 - fraction));
\t\tfloat red;
\t\tfloat green;
\t\tfloat blue;
\t\tswitch (sector % 6) {
\t\t\tcase 0: red = value; green = descending; blue = 0f; break;
\t\t\tcase 1: red = minuend; green = value; blue = 0f; break;
\t\t\tcase 2: red = 0f; green = value; blue = descending; break;
\t\t\tcase 3: red = 0f; green = minuend; blue = value; break;
\t\t\tcase 4: red = descending; green = 0f; blue = value; break;
\t\t\tdefault: red = value; green = 0f; blue = minuend; break;
\t\t}
\t\treturn toChannel(red) << 16 | toChannel(green) << 8 | toChannel(blue);
\t}

\tprivate static int toChannel(float value) {
\t\treturn Math.max(0, Math.min(255, Math.round(value * 255)));
\t}
}
'''

SOURCES["SplashEntry.java"] = '''package dev.arrbrants.customsplash;

import java.util.List;

/**
 * A single configurable splash text with an optional weight and display conditions.
 */
public final class SplashEntry {
\tpublic String text;
\tpublic int weight = 1;
\tpublic String color;
\tpublic Conditions conditions;
\tprivate SplashColor colorSpec;

\tpublic SplashEntry() {
\t}

\tpublic SplashEntry(String text, int weight) {
\t\tthis.text = text;
\t\tthis.weight = weight;
\t}

\tpublic boolean isBlank() {
\t\treturn text == null || text.isEmpty();
\t}

\tpublic int weightOrDefault() {
\t\treturn weight > 0 ? weight : 1;
\t}

\t/**
\t * @return the parsed colour, or {@code -1} when unset/invalid
\t */
\tpublic int rgb() {
\t\treturn SplashColors.parse(color);
\t}

\t/**
\t * @return the parsed colour specification, or {@code null} when unset/invalid
\t */
\tpublic SplashColor colorSpec() {
\t\tif (colorSpec == null) {
\t\t\tcolorSpec = SplashColor.parse(color);
\t\t}
\t\treturn colorSpec;
\t}

\tpublic boolean matches(SplashContext context) {
\t\treturn matchesConditions(conditions, context);
\t}

\t/**
\t * Evaluate the supplied conditions without needing a stored entry.
\t * Visible for testing; a {@code null} block matches everything.
\t */
\tstatic boolean matchesConditions(Conditions conditions, SplashContext context) {
\t\treturn conditions == null || conditions.matches(context);
\t}

\t/**
\t * All fields are optional. When several are present, every one must match.
\t */
\tpublic static final class Conditions {
\t\tpublic String time;
\t\tpublic String date;
\t\tpublic Boolean weekend;
\t\tpublic List<String> player;
\t\tpublic List<String> mods;
\t\tpublic Double chance;

\t\tpublic boolean matches(SplashContext context) {
\t\t\treturn matchesTime(context)
\t\t\t\t&& matchesDate(context)
\t\t\t\t&& matchesWeekend(context)
\t\t\t\t&& matchesPlayer(context)
\t\t\t\t&& matchesMods(context)
\t\t\t\t&& matchesChance(context);
\t\t}

\t\tprivate boolean matchesTime(SplashContext context) {
\t\t\tif (time == null || time.isEmpty()) {
\t\t\t\treturn true;
\t\t\t}
\t\t\tboolean day = context.time().getHour() >= 6 && context.time().getHour() < 18;
\t\t\tif ("day".equalsIgnoreCase(time)) {
\t\t\t\treturn day;
\t\t\t}
\t\t\tif ("night".equalsIgnoreCase(time)) {
\t\t\t\treturn !day;
\t\t\t}
\t\t\treturn true;
\t\t}

\t\tprivate boolean matchesDate(SplashContext context) {
\t\t\tif (date == null || date.isEmpty()) {
\t\t\t\treturn true;
\t\t\t}
\t\t\ttry {
\t\t\t\tint today = context.date().getMonthValue() * 100 + context.date().getDayOfMonth();
\t\t\t\tString[] range = date.split("\\\\.\\\\.");
\t\t\t\tint start = parseMonthDay(range[0]);
\t\t\t\tint end = range.length > 1 ? parseMonthDay(range[1]) : start;
\t\t\t\treturn start <= end ? today >= start && today <= end : today >= start || today <= end;
\t\t\t} catch (RuntimeException exception) {
\t\t\t\treturn false;
\t\t\t}
\t\t}

\t\tprivate static int parseMonthDay(String value) {
\t\t\tString[] parts = value.trim().split("-");
\t\t\treturn Integer.parseInt(parts[0]) * 100 + Integer.parseInt(parts[1]);
\t\t}

\t\tprivate boolean matchesWeekend(SplashContext context) {
\t\t\tif (weekend == null) {
\t\t\t\treturn true;
\t\t\t}
\t\t\tboolean isWeekend = context.date().getDayOfWeek().getValue() >= 6;
\t\t\treturn weekend == isWeekend;
\t\t}

\t\tprivate boolean matchesPlayer(SplashContext context) {
\t\t\tif (player == null || player.isEmpty()) {
\t\t\t\treturn true;
\t\t\t}
\t\t\tString name = context.playerName();
\t\t\tif (name == null) {
\t\t\t\treturn false;
\t\t\t}
\t\t\tfor (String candidate : player) {
\t\t\t\tif (candidate != null && candidate.equalsIgnoreCase(name)) {
\t\t\t\t\treturn true;
\t\t\t\t}
\t\t\t}
\t\t\treturn false;
\t\t}

\t\tprivate boolean matchesMods(SplashContext context) {
\t\t\tif (mods == null || mods.isEmpty()) {
\t\t\t\treturn true;
\t\t\t}
\t\t\tfor (String mod : mods) {
\t\t\t\tif (!context.hasMod(mod)) {
\t\t\t\t\treturn false;
\t\t\t\t}
\t\t\t}
\t\t\treturn true;
\t\t}

\t\tprivate boolean matchesChance(SplashContext context) {
\t\t\treturn chance == null || context.roll(chance);
\t\t}
\t}
}
'''

SOURCES["SplashConfig.java"] = '''package dev.arrbrants.customsplash;

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
\tprivate static final Logger LOGGER = Logger.getLogger("custom-splash");

\tprivate static final String DEFAULT_JSON = "{\\n"
\t\t+ "\\t\\"splashes\\": [\\n"
\t\t+ "\\t\\t{ \\"text\\": \\"Check your custom splash config file to customize!\\" }\\n"
\t\t+ "\\t]\\n"
\t\t+ "}\\n";

\tpublic List<SplashEntry> splashes = new ArrayList<>();

\tstatic SplashConfig load(Path path, Gson gson) {
\t\ttry {
\t\t\tif (path.getParent() != null) {
\t\t\t\tFiles.createDirectories(path.getParent());
\t\t\t}
\t\t\tif (!Files.exists(path)) {
\t\t\t\tFiles.write(path, DEFAULT_JSON.getBytes(StandardCharsets.UTF_8));
\t\t\t\tLOGGER.info("Created default splash config at " + path);
\t\t\t}
\t\t\tString json = new String(Files.readAllBytes(path), StandardCharsets.UTF_8);
\t\t\tSplashConfig parsed = gson.fromJson(json, SplashConfig.class);
\t\t\tif (parsed == null) {
\t\t\t\tparsed = new SplashConfig();
\t\t\t}
\t\t\tif (parsed.splashes == null) {
\t\t\t\tparsed.splashes = new ArrayList<>();
\t\t\t}
\t\t\treturn parsed;
\t\t} catch (IOException | RuntimeException exception) {
\t\t\tLOGGER.log(Level.WARNING, "Failed to load splash config from " + path, exception);
\t\t\treturn new SplashConfig();
\t\t}
\t}
}
'''

SOURCES["SplashRegistry.java"] = '''package dev.arrbrants.customsplash;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;

import java.nio.file.Path;
import java.nio.file.Paths;
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
\tprivate static Path configPathCache;
\tprivate static final Gson GSON = new GsonBuilder().setPrettyPrinting().disableHtmlEscaping().create();
\tprivate static final List<SplashEntry> REGISTERED = Collections.synchronizedList(new ArrayList<SplashEntry>());
\tprivate static final Random RNG = new Random();
\tprivate static volatile SplashConfig config = new SplashConfig();
\tprivate static volatile List<SplashEntry> resourcePackEntries = Collections.emptyList();
\tprivate static volatile long resourcePackLoadedAt;
\tprivate static final long RESOURCE_PACK_TTL_MS = 5000L;
\tprivate static final DateTimeFormatter DATE_FORMAT = DateTimeFormatter.ofPattern("yyyy-MM-dd");
\tprivate static final DateTimeFormatter TIME_FORMAT = DateTimeFormatter.ofPattern("HH:mm");

\tprivate SplashRegistry() {
\t}

\t/**
\t * Register a splash text with the default weight of 1.
\t */
\tpublic static void add(String text) {
\t\tadd(text, 1);
\t}

\t/**
\t * Register a splash text with a custom relative weight.
\t */
\tpublic static void add(String text, int weight) {
\t\tif (text != null && !text.isEmpty()) {
\t\t\tREGISTERED.add(new SplashEntry(text, weight));
\t\t}
\t}

\t/**
\t * Remove every registered text equal to {@code text}.
\t *
\t * @return {@code true} if at least one entry was removed
\t */
\tpublic static boolean remove(String text) {
\t\tif (text == null) {
\t\t\treturn false;
\t\t}
\t\tsynchronized (REGISTERED) {
\t\t\treturn REGISTERED.removeIf(entry -> text.equals(entry.text));
\t\t}
\t}

\t/**
\t * Remove all runtime-registered texts. The config file is untouched.
\t */
\tpublic static void clear() {
\t\tREGISTERED.clear();
\t}

\t/**
\t * @return an immutable view of every currently known text (config first).
\t */
\tpublic static List<String> list() {
\t\tList<String> texts = new ArrayList<>();
\t\tfor (SplashEntry entry : config.splashes) {
\t\t\tif (entry != null && !entry.isBlank()) {
\t\t\t\ttexts.add(entry.text);
\t\t\t}
\t\t}
\t\tfor (SplashEntry entry : resourcePackEntries) {
\t\t\tif (entry != null && !entry.isBlank()) {
\t\t\t\ttexts.add(entry.text);
\t\t\t}
\t\t}
\t\tsynchronized (REGISTERED) {
\t\t\tfor (SplashEntry entry : REGISTERED) {
\t\t\t\tif (!entry.isBlank()) {
\t\t\t\t\ttexts.add(entry.text);
\t\t\t\t}
\t\t\t}
\t\t}
\t\treturn Collections.unmodifiableList(texts);
\t}

\t/**
\t * @return the number of currently known texts
\t */
\tpublic static int count() {
\t\treturn list().size();
\t}

\t/**
\t * Pick a splash text, honouring weights and display conditions.
\t *
\t * @return a splash text, or empty when nothing is configured/matches
\t */
\tpublic static Optional<String> pick() {
\t\treturn pickEntry().map(picked -> picked.text);
\t}

\t/**
\t * Pick a splash entry, keeping colour information for the renderer.
\t */
\tpublic static Optional<Picked> pickEntry() {
\t\trefreshResourcePacksIfStale();
\t\tSplashContext context = SplashContext.create();
\t\tList<SplashEntry> pool = new ArrayList<>();
\t\tfor (SplashEntry entry : config.splashes) {
\t\t\tif (entry != null && !entry.isBlank() && entry.matches(context)) {
\t\t\t\tpool.add(entry);
\t\t\t}
\t\t}
\t\tfor (SplashEntry entry : resourcePackEntries) {
\t\t\tif (entry != null && !entry.isBlank() && entry.matches(context)) {
\t\t\t\tpool.add(entry);
\t\t\t}
\t\t}
\t\tsynchronized (REGISTERED) {
\t\t\tfor (SplashEntry entry : REGISTERED) {
\t\t\t\tif (!entry.isBlank() && entry.matches(context)) {
\t\t\t\t\tpool.add(entry);
\t\t\t\t}
\t\t\t}
\t\t}
\t\tif (pool.isEmpty()) {
\t\t\treturn Optional.empty();
\t\t}
\t\tSplashEntry chosen = chooseWeighted(pool, RNG);
\t\tSplashColor color = chosen.colorSpec();
\t\treturn Optional.of(new Picked(format(chosen.text, context), color == null ? -1 : color.solidRgb(), color));
\t}

\t/**
\t * Pick one entry using relative weights. Visible for testing.
\t */
\tstatic SplashEntry chooseWeighted(List<SplashEntry> pool, Random random) {
\t\tint total = 0;
\t\tfor (SplashEntry entry : pool) {
\t\t\ttotal += entry.weightOrDefault();
\t\t}
\t\tint roll = random.nextInt(total);
\t\tfor (SplashEntry entry : pool) {
\t\t\troll -= entry.weightOrDefault();
\t\t\tif (roll < 0) {
\t\t\t\treturn entry;
\t\t\t}
\t\t}
\t\treturn pool.get(pool.size() - 1);
\t}

\t/**
\t * Reload the JSON config file, creating it with defaults when missing.
\t */
\tpublic static void reload() {
\t\tconfig = SplashConfig.load(configPath(), GSON);
\t\trefreshResourcePacks();
\t}

\tprivate static void refreshResourcePacks() {
\t\tresourcePackEntries = SplashResourcePack.load();
\t\tresourcePackLoadedAt = System.currentTimeMillis();
\t}

\tprivate static void refreshResourcePacksIfStale() {
\t\tif (System.currentTimeMillis() - resourcePackLoadedAt > RESOURCE_PACK_TTL_MS) {
\t\t\trefreshResourcePacks();
\t\t}
\t}

\t/**
\t * @return the path of the JSON config file
\t */
\tpublic static Path configPath() {
\t\tPath path = configPathCache;
\t\tif (path == null) {
\t\t\tPath dir = SplashPlatform.get().getConfigDir();
\t\t\tpath = dir == null ? Paths.get("config") : dir.resolve("custom-splash.json");
\t\t\tconfigPathCache = path;
\t\t}
\t\treturn path;
\t}

\t/**
\t\t* Replace the supported placeholders. Unknown tokens are left untouched so
\t\t* that text such as an emoticon keeps working.
\t */
\tstatic String format(String text, SplashContext context) {
\t\tif (text.indexOf('{') < 0) {
\t\t\treturn text;
\t\t}
\t\tString player = context.playerName();
\t\tString name = player == null ? "player" : player;
\t\tString[] tokens = {
\t\t\t"{player}", name, "{username}", name,
\t\t\t"{date}", context.date().format(DATE_FORMAT),
\t\t\t"{time}", context.time().format(TIME_FORMAT),
\t\t\t"{mods}", context.modCount(),
\t\t\t"{mods_count}", context.modCount(),
\t\t\t"{mc_version}", context.gameVersion(),
\t\t\t"{mc}", context.gameVersion(),
\t\t\t"{version}", context.gameVersion(),
\t\t};
\t\tString result = text;
\t\tfor (int i = 0; i < tokens.length; i += 2) {
\t\t\tif (tokens[i + 1] != null) {
\t\t\t\tresult = result.replace(tokens[i], tokens[i + 1]);
\t\t\t}
\t\t}
\t\treturn result;
\t}

\t/**
\t * A chosen splash ready to be rendered.
\t */
\tpublic static final class Picked {
\t\tpublic final String text;
\t\t/** the solid RGB value, or {@code -1} when unset or multi-coloured */
\t\tpublic final int rgb;
\t\t/** the full colour specification, or {@code null} when unset */
\t\tpublic final SplashColor color;

\t\tPicked(String text, int rgb, SplashColor color) {
\t\t\tthis.text = text;
\t\t\tthis.rgb = rgb;
\t\t\tthis.color = color;
\t\t}
\t}
}
'''

SOURCES["SplashResourcePack.java"] = '''package dev.arrbrants.customsplash;

import com.google.gson.Gson;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.logging.Level;
import java.util.logging.Logger;
import java.util.zip.ZipEntry;
import java.util.zip.ZipFile;

/**
 * Reads splash texts from enabled resource packs.
 *
 * <p>A pack may provide {@code assets/custom-splash/splashes.txt}; every
 * non-empty line that does not start with {@code #} becomes a splash text.</p>
 */
public final class SplashResourcePack {
\tprivate static final Logger LOGGER = Logger.getLogger("custom-splash");
\tprivate static final Gson GSON = new Gson();
\tprivate static final String PACK_FILE = "assets/custom-splash/splashes.txt";

\tprivate SplashResourcePack() {
\t}

\tstatic List<SplashEntry> load() {
\t\tPath gameDir = SplashPlatform.get().getGameDir();
\t\tif (gameDir == null) {
\t\t\treturn Collections.emptyList();
\t\t}
\t\tPath packsDir = gameDir.resolve("resourcepacks");
\t\tif (!Files.isDirectory(packsDir)) {
\t\t\treturn Collections.emptyList();
\t\t}
\t\tList<SplashEntry> entries = new ArrayList<>();
\t\tfor (String name : enabledPacks(gameDir)) {
\t\t\tfor (String line : readLines(packsDir.resolve(name))) {
\t\t\t\tString text = line.trim();
\t\t\t\tif (!text.isEmpty() && !text.startsWith("#")) {
\t\t\t\t\tSplashEntry entry = new SplashEntry();
\t\t\t\t\tentry.text = text;
\t\t\t\t\tentries.add(entry);
\t\t\t\t}
\t\t\t}
\t\t}
\t\treturn entries;
\t}

\tprivate static List<String> enabledPacks(Path gameDir) {
\t\tPath options = gameDir.resolve("options.txt");
\t\ttry {
\t\t\tfor (String line : Files.readAllLines(options, StandardCharsets.UTF_8)) {
\t\t\t\tif (line.startsWith("resourcePacks:")) {
\t\t\t\t\tString[] names = GSON.fromJson(line.substring("resourcePacks:".length()).trim(), String[].class);
\t\t\t\t\tif (names == null) {
\t\t\t\t\t\treturn Collections.emptyList();
\t\t\t\t\t}
\t\t\t\t\tList<String> result = new ArrayList<>();
\t\t\t\t\tfor (String name : names) {
\t\t\t\t\t\tif (name == null || name.isEmpty()) {
\t\t\t\t\t\t\tcontinue;
\t\t\t\t\t\t}
\t\t\t\t\t\tresult.add(name.startsWith("file/") ? name.substring("file/".length()) : name);
\t\t\t\t\t}
\t\t\t\t\treturn result;
\t\t\t\t}
\t\t\t}
\t\t} catch (IOException | RuntimeException exception) {
\t\t\tLOGGER.log(Level.FINE, "Could not read enabled resource packs", exception);
\t\t}
\t\treturn Collections.emptyList();
\t}

\tprivate static List<String> readLines(Path pack) {
\t\ttry {
\t\t\tif (Files.isDirectory(pack)) {
\t\t\t\tPath file = pack.resolve(PACK_FILE);
\t\t\t\treturn Files.isRegularFile(file)
\t\t\t\t\t\t? Files.readAllLines(file, StandardCharsets.UTF_8)
\t\t\t\t\t\t: Collections.emptyList();
\t\t\t}
\t\t\tif (Files.isRegularFile(pack)) {
\t\t\t\ttry (ZipFile zip = new ZipFile(pack.toFile())) {
\t\t\t\t\tZipEntry entry = zip.getEntry(PACK_FILE);
\t\t\t\t\tif (entry == null) {
\t\t\t\t\t\treturn Collections.emptyList();
\t\t\t\t\t}
\t\t\t\t\ttry (InputStream stream = zip.getInputStream(entry)) {
\t\t\t\t\t\treturn splitLines(readAll(stream));
\t\t\t\t\t}
\t\t\t\t}
\t\t\t}
\t\t} catch (IOException | RuntimeException exception) {
\t\t\tLOGGER.log(Level.FINE, "Could not read resource pack " + pack, exception);
\t\t}
\t\treturn Collections.emptyList();
\t}

\tprivate static List<String> splitLines(byte[] data) {
\t\tList<String> lines = new ArrayList<>();
\t\tfor (String line : new String(data, StandardCharsets.UTF_8).split("\\\\r?\\\\n")) {
\t\t\tlines.add(line);
\t\t}
\t\treturn lines;
\t}

\tprivate static byte[] readAll(InputStream stream) throws IOException {
\t\tByteArrayOutputStream buffer = new ByteArrayOutputStream();
\t\tbyte[] chunk = new byte[8192];
\t\tint read;
\t\twhile ((read = stream.read(chunk)) != -1) {
\t\t\tbuffer.write(chunk, 0, read);
\t\t}
\t\treturn buffer.toByteArray();
\t}
}
'''

MIXIN_YARN = '''package dev.arrbrants.customsplash.mixin;

import dev.arrbrants.customsplash.SplashColor;
import dev.arrbrants.customsplash.SplashColors;
import dev.arrbrants.customsplash.SplashRegistry;
import net.minecraft.client.resource.SplashTextResourceSupplier;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

@Mixin(SplashTextResourceSupplier.class)
public class SplashManagerMixin {
\t@Inject(at = @At("HEAD"), method = "get", cancellable = true)
\tprivate void getSplash(CallbackInfoReturnable<String> cir) {
\t\tSplashRegistry.pickEntry().ifPresent(picked -> cir.setReturnValue(colourize(picked)));
\t}

\tprivate static String colourize(SplashRegistry.Picked picked) {
\t\tSplashColor color = picked.color;
\t\tif (color == null) {
\t\t\treturn picked.text;
\t\t}
\t\tif (color.isSolid()) {
\t\t\treturn SplashColors.legacyPrefix(color.solidRgb()) + picked.text;
\t\t}
\t\tint[] colors = color.colorsFor(picked.text);
\t\tStringBuilder builder = new StringBuilder();
\t\tfor (int i = 0; i < picked.text.length(); i++) {
\t\t\tbuilder.append(SplashColors.legacyPrefix(colors[i])).append(picked.text.charAt(i));
\t\t}
\t\treturn builder.toString();
\t}
}
'''

MIXIN_OLD = '''package dev.arrbrants.customsplash.mixin;

import dev.arrbrants.customsplash.SplashColor;
import dev.arrbrants.customsplash.SplashColors;
import dev.arrbrants.customsplash.SplashRegistry;
import net.minecraft.client.resources.SplashManager;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

@Mixin(SplashManager.class)
public class SplashManagerMixin {
\t@Inject(at = @At("HEAD"), method = "getSplash", cancellable = true)
\tprivate void getSplash(CallbackInfoReturnable<String> cir) {
\t\tSplashRegistry.pickEntry().ifPresent(picked -> cir.setReturnValue(colourize(picked)));
\t}

\tprivate static String colourize(SplashRegistry.Picked picked) {
\t\tSplashColor color = picked.color;
\t\tif (color == null) {
\t\t\treturn picked.text;
\t\t}
\t\tif (color.isSolid()) {
\t\t\treturn SplashColors.legacyPrefix(color.solidRgb()) + picked.text;
\t\t}
\t\tint[] colors = color.colorsFor(picked.text);
\t\tStringBuilder builder = new StringBuilder();
\t\tfor (int i = 0; i < picked.text.length(); i++) {
\t\t\tbuilder.append(SplashColors.legacyPrefix(colors[i])).append(picked.text.charAt(i));
\t\t}
\t\treturn builder.toString();
\t}
}
'''

MIXIN_NEW = '''package dev.arrbrants.customsplash.mixin;

import dev.arrbrants.customsplash.SplashColor;
import dev.arrbrants.customsplash.SplashRegistry;
import net.minecraft.client.gui.components.SplashRenderer;
import net.minecraft.client.resources.SplashManager;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.MutableComponent;
import net.minecraft.network.chat.Style;
import net.minecraft.network.chat.TextColor;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

import java.lang.reflect.InvocationTargetException;

@Mixin(SplashManager.class)
public class SplashManagerMixin {
\t@Inject(at = @At("HEAD"), method = "getSplash", cancellable = true)
\tprivate void getSplash(CallbackInfoReturnable<SplashRenderer> cir) {
\t\tSplashRegistry.pickEntry().ifPresent(picked -> cir.setReturnValue(createRenderer(picked)));
\t}

\tprivate static SplashRenderer createRenderer(SplashRegistry.Picked picked) {
\t\ttry {
\t\t\treturn SplashRenderer.class.getConstructor(Component.class).newInstance(buildComponent(picked));
\t\t} catch (NoSuchMethodException ignored) {
\t\t\ttry {
\t\t\t\treturn SplashRenderer.class.getConstructor(String.class).newInstance(picked.text);
\t\t\t} catch (ReflectiveOperationException exception) {
\t\t\t\tthrow new IllegalStateException("Unable to create splash renderer", unwrap(exception));
\t\t\t}
\t\t} catch (ReflectiveOperationException exception) {
\t\t\tthrow new IllegalStateException("Unable to create splash renderer", unwrap(exception));
\t\t}
\t}

\tprivate static MutableComponent buildComponent(SplashRegistry.Picked picked) {
\t\tSplashColor color = picked.color;
\t\tif (color == null) {
\t\t\treturn Component.literal(picked.text);
\t\t}
\t\tif (color.isSolid()) {
\t\t\treturn Component.literal(picked.text).withStyle(Style.EMPTY.withColor(TextColor.fromRgb(color.solidRgb())));
\t\t}
\t\tint[] colors = color.colorsFor(picked.text);
\t\tMutableComponent root = Component.empty();
\t\tfor (int i = 0; i < picked.text.length(); i++) {
\t\t\troot.append(Component.literal(String.valueOf(picked.text.charAt(i)))
\t\t\t\t\t.withStyle(Style.EMPTY.withColor(TextColor.fromRgb(colors[i]))));
\t\t}
\t\treturn root;
\t}

\tprivate static Throwable unwrap(ReflectiveOperationException exception) {
\t\treturn exception instanceof InvocationTargetException && exception.getCause() != null
\t\t\t\t? exception.getCause() : exception;
\t}
}
'''


def uses_legacy_mixin(version: str) -> bool:
    parts = version.split(".")
    return parts[0] == "1" and int(parts[1]) <= 19


# Mojang only publishes official client mappings from 1.14.4 onwards, so the
# earliest supported versions build against Yarn instead. Under Yarn the splash
# supplier is SplashTextResourceSupplier#get rather than SplashManager#getSplash.
YARN_MIXIN_VERSIONS = ("1.14", "1.14.1", "1.14.2", "1.14.3")


def uses_yarn_mixin(version: str) -> bool:
    return version in YARN_MIXIN_VERSIONS


def mixin_for(version: str) -> str:
    if uses_yarn_mixin(version):
        return MIXIN_YARN
    return MIXIN_OLD if uses_legacy_mixin(version) else MIXIN_NEW


def main() -> None:
    versions = VERSIONS_FILE.read_text().splitlines()
    for version in versions:
        project = ROOT / "versions" / version
        package_dir = project / PACKAGE_DIR
        if not (project / "build.gradle").is_file():
            raise SystemExit(f"missing version project: {project}")
        for name, content in SOURCES.items():
            (package_dir / name).write_text(content)
        (project / MIXIN_DIR / "SplashManagerMixin.java").write_text(mixin_for(version))
        write_fabric_platform(project)
        patch_initializer(project)
        write_icon(project)
        print(f"updated {version}")


def patch_initializer(project: Path) -> None:
    path = project / PACKAGE_DIR / "CustomSplash.java"
    source = path.read_text()
    marker = "public void onInitialize() {\n"
    if marker not in source:
        raise SystemExit(f"unexpected CustomSplash in {path}")
    if "FabricSplashPlatform.install()" not in source:
        source = source.replace(marker, marker + "\t\tFabricSplashPlatform.install();\n", 1)
    if "SplashRegistry.reload()" not in source:
        source = source.replace(marker, marker + "\t\tSplashRegistry.reload();\n", 1)
    path.write_text(source)


FABRIC_PLATFORM = '''package dev.arrbrants.customsplash;

import net.fabricmc.loader.api.FabricLoader;

import java.nio.file.Path;
import java.nio.file.Paths;

/**
 * Fabric implementation of {@link SplashPlatform}, installed by
 * {@link CustomSplash#onInitialize()}.
 */
public final class FabricSplashPlatform implements SplashPlatform {
	private static final Path FALLBACK_CONFIG = Paths.get("config");

	private FabricSplashPlatform() {
	}

	public static void install() {
		SplashPlatform.install(new FabricSplashPlatform());
	}

	@Override
	public Path getConfigDir() {
		try {
			return FabricLoader.getInstance().getConfigDir();
		} catch (RuntimeException | LinkageError ignored) {
			return FALLBACK_CONFIG;
		}
	}

	@Override
	public Path getGameDir() {
		try {
			return FabricLoader.getInstance().getGameDir();
		} catch (RuntimeException | LinkageError ignored) {
			return null;
		}
	}

	@Override
	public boolean isModLoaded(String modId) {
		try {
			return FabricLoader.getInstance().isModLoaded(modId);
		} catch (RuntimeException | LinkageError ignored) {
			return false;
		}
	}

	@Override
	public int loadedModCount() {
		try {
			return FabricLoader.getInstance().getAllMods().size();
		} catch (RuntimeException | LinkageError ignored) {
			return -1;
		}
	}
}
'''


def write_fabric_platform(project: Path) -> None:
    """Emit the Fabric-only platform implementation, which is not shared."""
    path = project / PACKAGE_DIR / "FabricSplashPlatform.java"
    if not path.exists() or path.read_text() != FABRIC_PLATFORM:
        path.write_text(FABRIC_PLATFORM)


def write_icon(project: Path) -> None:
    """Ship the canonical mod icon as ``assets/custom-splash/icon.png``.

    Loaders resolve the mod icon under the mod id, so the resource path must use
    ``custom-splash``; the single source image lives in this repository's own
    ``src/main/resources`` (which no Gradle build consumes) and is copied into
    every version project here. Shared with the Forge and NeoForge generators.
    """
    if not ICON_SOURCE.is_file():
        raise SystemExit(f"missing canonical mod icon: {ICON_SOURCE}")
    icon = ICON_SOURCE.read_bytes()
    target = project / RESOURCES_DIR / ICON_RESOURCE
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.is_file() or target.read_bytes() != icon:
        target.write_bytes(icon)




if __name__ == "__main__":
    main()
