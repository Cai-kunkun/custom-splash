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
 * <p>A pack may provide {@code assets/custom-splash/splashes.txt}; every
 * non-empty line that does not start with {@code #} becomes a splash text.</p>
 */
public final class SplashResourcePack {
	private static final Logger LOGGER = Logger.getLogger("custom-splash");
	private static final Gson GSON = new Gson();
	private static final String PACK_FILE = "assets/custom-splash/splashes.txt";

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
			for (String line : readLines(packsDir.resolve(name))) {
				String text = line.trim();
				if (!text.isEmpty() && !text.startsWith("#")) {
					SplashEntry entry = new SplashEntry();
					entry.text = text;
					entries.add(entry);
				}
			}
		}
		return entries;
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

	private static List<String> readLines(Path pack) {
		try {
			if (Files.isDirectory(pack)) {
				Path file = pack.resolve(PACK_FILE);
				return Files.isRegularFile(file)
						? Files.readAllLines(file, StandardCharsets.UTF_8)
						: Collections.emptyList();
			}
			if (Files.isRegularFile(pack)) {
				try (ZipFile zip = new ZipFile(pack.toFile())) {
					ZipEntry entry = zip.getEntry(PACK_FILE);
					if (entry == null) {
						return Collections.emptyList();
					}
					try (InputStream stream = zip.getInputStream(entry)) {
						return splitLines(readAll(stream));
					}
				}
			}
		} catch (IOException | RuntimeException exception) {
			LOGGER.log(Level.FINE, "Could not read resource pack " + pack, exception);
		}
		return Collections.emptyList();
	}

	private static List<String> splitLines(byte[] data) {
		List<String> lines = new ArrayList<>();
		for (String line : new String(data, StandardCharsets.UTF_8).split("\\r?\\n")) {
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
