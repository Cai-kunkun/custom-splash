package dev.arrbrants.customsplash;

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
 * <p>A pack may provide {@code assets/customsplash/splashes.txt}, where every
 * non-empty line that does not start with {@code #} becomes a splash text, or
 * {@code assets/customsplash/splashes.json}, which uses the same schema as the
 * config file and therefore supports weights, colours and conditions too. Both
 * files may be present; their entries are combined.</p>
 */
public final class SplashResourcePack {
	private static final Logger LOGGER = Logger.getLogger("customsplash");
	private static final Gson GSON = new Gson();
	private static final String PACK_TEXT_FILE = "assets/customsplash/splashes.txt";
	private static final String PACK_JSON_FILE = "assets/customsplash/splashes.json";

	private SplashResourcePack() {
	}

	static List<SplashEntry> load() {
		Path gameDir = SplashPlatform.get().getGameDir();
		if (gameDir == null) {
			return Collections.emptyList();
		}
		Path packsDir = gameDir.resolve("resourcepacks");
		if (!Files.isDirectory(packsDir)) {
			return Collections.emptyList();
		}
		List<SplashEntry> entries = new ArrayList<>();
		for (String name : enabledPacks(gameDir)) {
			Path pack = packsDir.resolve(name);
			entries.addAll(readTextEntries(pack));
			entries.addAll(readJsonEntries(pack));
		}
		return entries;
	}

	private static List<SplashEntry> readTextEntries(Path pack) {
		byte[] data = read(pack, PACK_TEXT_FILE);
		if (data == null) {
			return Collections.emptyList();
		}
		List<SplashEntry> entries = new ArrayList<>();
		for (String line : splitLines(data)) {
			String text = line.trim();
			if (!text.isEmpty() && !text.startsWith("#")) {
				SplashEntry entry = new SplashEntry();
				entry.text = text;
				entries.add(entry);
			}
		}
		return entries;
	}

	private static List<SplashEntry> readJsonEntries(Path pack) {
		byte[] data = read(pack, PACK_JSON_FILE);
		if (data == null) {
			return Collections.emptyList();
		}
		try {
			return SplashConfig.parse(new String(data, StandardCharsets.UTF_8), GSON).splashes;
		} catch (RuntimeException exception) {
			LOGGER.log(Level.WARNING, "Could not parse " + PACK_JSON_FILE + " in " + pack, exception);
			return Collections.emptyList();
		}
	}

	private static List<String> enabledPacks(Path gameDir) {
		Path options = gameDir.resolve("options.txt");
		try {
			for (String line : Files.readAllLines(options, StandardCharsets.UTF_8)) {
				if (line.startsWith("resourcePacks:")) {
					String[] names = GSON.fromJson(line.substring("resourcePacks:".length()).trim(), String[].class);
					if (names == null) {
						return Collections.emptyList();
					}
					List<String> result = new ArrayList<>();
					for (String name : names) {
						if (name == null || name.isEmpty()) {
							continue;
						}
						result.add(name.startsWith("file/") ? name.substring("file/".length()) : name);
					}
					return result;
				}
			}
		} catch (IOException | RuntimeException exception) {
			LOGGER.log(Level.FINE, "Could not read enabled resource packs", exception);
		}
		return Collections.emptyList();
	}

	/**
	 * @return the bytes of {@code resource} inside the pack, or {@code null} when absent
	 */
	private static byte[] read(Path pack, String resource) {
		try {
			if (Files.isDirectory(pack)) {
				Path file = pack.resolve(resource);
				return Files.isRegularFile(file) ? Files.readAllBytes(file) : null;
			}
			if (Files.isRegularFile(pack)) {
				try (ZipFile zip = new ZipFile(pack.toFile())) {
					ZipEntry entry = zip.getEntry(resource);
					if (entry == null) {
						return null;
					}
					try (InputStream stream = zip.getInputStream(entry)) {
						return readAll(stream);
					}
				}
			}
		} catch (IOException | RuntimeException exception) {
			LOGGER.log(Level.FINE, "Could not read " + resource + " from " + pack, exception);
		}
		return null;
	}

	private static List<String> splitLines(byte[] data) {
		List<String> lines = new ArrayList<>();
		for (String line : new String(data, StandardCharsets.UTF_8).split("\r?\n")) {
			lines.add(line);
		}
		return lines;
	}

	private static byte[] readAll(InputStream stream) throws IOException {
		ByteArrayOutputStream buffer = new ByteArrayOutputStream();
		byte[] chunk = new byte[8192];
		int read;
		while ((read = stream.read(chunk)) != -1) {
			buffer.write(chunk, 0, read);
		}
		return buffer.toByteArray();
	}
}
