#!/usr/bin/env python3
"""Synchronise the shared Custom Splash sources across every version project.

Features implemented here: JSON config file, weighted entries, display
conditions, colour support and an extended public API.

The shared sources contain no Minecraft compile-time references (player lookup is
reflective), so the exact same files work on every supported version. Only the
mixin differs between the old ``String``-based splash API (1.16-1.19.4) and the
``SplashRenderer`` API (1.20+).
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSIONS_FILE = ROOT / "supported-versions.txt"
PACKAGE_DIR = "src/main/java/dev/arrbrants/customsplash"
MIXIN_DIR = PACKAGE_DIR + "/mixin"

SOURCES = {}

SOURCES["SplashContext.java"] = '''package dev.arrbrants.customsplash;

import net.fabricmc.loader.api.FabricLoader;

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

\tprivate SplashContext(LocalTime time, LocalDate date, String playerName, Random random) {
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

\tboolean hasMod(String modId) {
\t\treturn modId != null && FabricLoader.getInstance().isModLoaded(modId);
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

\tpublic boolean matches(SplashContext context) {
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
import net.fabricmc.loader.api.FabricLoader;

import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Optional;
import java.util.Random;

/**
 * Public API and config-backed splash store.
 *
 * <p>Texts come from the JSON config file and from {@link #add(String)}. One is
 * chosen at random (respecting per-entry weights) whenever the splash text is
 * drawn. When nothing matches, the vanilla splash is used.</p>
 */
public final class SplashRegistry {
\tprivate static final Path CONFIG_PATH = FabricLoader.getInstance().getConfigDir().resolve("custom-splash.json");
\tprivate static final Gson GSON = new GsonBuilder().setPrettyPrinting().disableHtmlEscaping().create();
\tprivate static final List<SplashEntry> REGISTERED = Collections.synchronizedList(new ArrayList<SplashEntry>());
\tprivate static final Random RNG = new Random();
\tprivate static volatile SplashConfig config = new SplashConfig();
\tprivate static volatile List<SplashEntry> resourcePackEntries = Collections.emptyList();
\tprivate static volatile long resourcePackLoadedAt;
\tprivate static final long RESOURCE_PACK_TTL_MS = 5000L;

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
\t\tint total = 0;
\t\tfor (SplashEntry entry : pool) {
\t\t\ttotal += entry.weightOrDefault();
\t\t}
\t\tint roll = RNG.nextInt(total);
\t\tSplashEntry chosen = pool.get(pool.size() - 1);
\t\tfor (SplashEntry entry : pool) {
\t\t\troll -= entry.weightOrDefault();
\t\t\tif (roll < 0) {
\t\t\t\tchosen = entry;
\t\t\t\tbreak;
\t\t\t}
\t\t}
\t\treturn Optional.of(new Picked(format(chosen.text, context), chosen.rgb()));
\t}

\t/**
\t * Reload the JSON config file, creating it with defaults when missing.
\t */
\tpublic static void reload() {
\t\tconfig = SplashConfig.load(CONFIG_PATH, GSON);
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
\t\treturn CONFIG_PATH;
\t}

\tprivate static String format(String text, SplashContext context) {
\t\tString player = context.playerName();
\t\treturn text.replace("{player}", player == null ? "player" : player);
\t}

\t/**
\t * A chosen splash ready to be rendered.
\t */
\tpublic static final class Picked {
\t\tpublic final String text;
\t\tpublic final int rgb;

\t\tPicked(String text, int rgb) {
\t\t\tthis.text = text;
\t\t\tthis.rgb = rgb;
\t\t}
\t}
}
'''

SOURCES["SplashResourcePack.java"] = '''package dev.arrbrants.customsplash;

import com.google.gson.Gson;
import net.fabricmc.loader.api.FabricLoader;

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
\t\tPath gameDir = FabricLoader.getInstance().getGameDir();
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

MIXIN_OLD = '''package dev.arrbrants.customsplash.mixin;

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
\t\tSplashRegistry.pickEntry().ifPresent(picked ->
\t\t\t\tcir.setReturnValue(picked.rgb >= 0 ? SplashColors.legacyPrefix(picked.rgb) + picked.text : picked.text));
\t}
}
'''

MIXIN_NEW = '''package dev.arrbrants.customsplash.mixin;

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
\t\tMutableComponent component = Component.literal(picked.text);
\t\tif (picked.rgb >= 0) {
\t\t\tcomponent = component.withStyle(Style.EMPTY.withColor(TextColor.fromRgb(picked.rgb)));
\t\t}
\t\ttry {
\t\t\treturn SplashRenderer.class.getConstructor(Component.class).newInstance(component);
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

\tprivate static Throwable unwrap(ReflectiveOperationException exception) {
\t\treturn exception instanceof InvocationTargetException && exception.getCause() != null
\t\t\t\t? exception.getCause() : exception;
\t}
}
'''


def uses_legacy_mixin(version: str) -> bool:
    parts = version.split(".")
    return parts[0] == "1" and int(parts[1]) <= 19


def main() -> None:
    versions = VERSIONS_FILE.read_text().splitlines()
    for version in versions:
        project = ROOT / "versions" / version
        package_dir = project / PACKAGE_DIR
        if not (project / "build.gradle").is_file():
            raise SystemExit(f"missing version project: {project}")
        for name, content in SOURCES.items():
            (package_dir / name).write_text(content)
        mixin = MIXIN_OLD if uses_legacy_mixin(version) else MIXIN_NEW
        (project / MIXIN_DIR / "SplashManagerMixin.java").write_text(mixin)
        patch_initializer(project)
        print(f"updated {version}")


def patch_initializer(project: Path) -> None:
    path = project / PACKAGE_DIR / "CustomSplash.java"
    source = path.read_text()
    if "SplashRegistry.reload()" in source:
        return
    marker = "public void onInitialize() {\n"
    if marker not in source:
        raise SystemExit(f"unexpected CustomSplash in {path}")
    source = source.replace(marker, marker + "\t\tSplashRegistry.reload();\n", 1)
    path.write_text(source)


if __name__ == "__main__":
    main()
