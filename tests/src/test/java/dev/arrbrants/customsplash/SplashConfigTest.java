package dev.arrbrants.customsplash;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;

import com.google.gson.Gson;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/**
 * Covers the JSON config model behind {@link SplashConfig}.
 */
class SplashConfigTest {
	private static final Gson GSON = new Gson();

	@TempDir
	Path dir;

	private Path config() {
		return dir.resolve("custom-splash.json");
	}

	private void write(String json) {
		try {
			Files.write(config(), json.getBytes(StandardCharsets.UTF_8));
		} catch (IOException exception) {
			throw new IllegalStateException(exception);
		}
	}

	private SplashEntry onlyEntry() {
		return SplashConfig.load(config(), GSON).splashes.get(0);
	}

	@Test
	@DisplayName("reads text, weight, colour and every condition")
	void readsEveryField() {
		write("{\"splashes\":[{\"text\":\"Hello\",\"weight\":3,\"color\":\"#FF0000\","
			+ "\"conditions\":{\"time\":\"night\",\"weekend\":true,\"player\":[\"Steve\"],"
			+ "\"mods\":[\"fabric-api\"],\"chance\":0.5,\"date\":\"12-24..12-26\"}}]}");

		SplashEntry entry = onlyEntry();

		assertEquals("Hello", entry.text);
		assertEquals(3, entry.weight);
		assertEquals(3, entry.weightOrDefault());
		assertEquals("#FF0000", entry.color);
		assertEquals(0xFF0000, entry.rgb());
		assertEquals("night", entry.conditions.time);
		assertEquals(Boolean.TRUE, entry.conditions.weekend);
		assertEquals(1, entry.conditions.player.size());
		assertEquals("Steve", entry.conditions.player.get(0));
		assertEquals(1, entry.conditions.mods.size());
		assertEquals("fabric-api", entry.conditions.mods.get(0));
		assertEquals(0.5D, entry.conditions.chance);
		assertEquals("12-24..12-26", entry.conditions.date);
	}

	@Test
	@DisplayName("a missing file is created with the default text")
	void createsDefaultFile() throws IOException {
		assertTrue(Files.exists(config()) == false);

		SplashConfig config = SplashConfig.load(config(), GSON);

		assertTrue(Files.isRegularFile(config()));
		assertEquals(1, config.splashes.size());
		assertEquals("Check your custom splash config file to customize!", config.splashes.get(0).text);
		assertEquals(1, config.splashes.get(0).weightOrDefault());
	}

	@Test
	@DisplayName("a missing parent directory is created")
	void createsParentDirectory() {
		Path nested = dir.resolve("nested").resolve("dir").resolve("custom-splash.json");

		SplashConfig.load(nested, GSON);

		assertTrue(Files.isRegularFile(nested));
	}

	@Test
	@DisplayName("an empty list stays an empty list")
	void emptyList() {
		write("{\"splashes\":[]}");

		assertTrue(SplashConfig.load(config(), GSON).splashes.isEmpty());
	}

	@Test
	@DisplayName("a missing splashes array is normalised to an empty list")
	void missingListNormalised() {
		write("{}");

		assertTrue(SplashConfig.load(config(), GSON).splashes.isEmpty());
	}

	@Test
	@DisplayName("a null splashes array is normalised to an empty list")
	void nullListNormalised() {
		write("{\"splashes\":null}");

		assertTrue(SplashConfig.load(config(), GSON).splashes.isEmpty());
	}

	@Test
	@DisplayName("malformed json falls back to an empty config instead of throwing")
	void malformedJsonFallsBack() {
		write("{ this is not json");

		assertTrue(SplashConfig.load(config(), GSON).splashes.isEmpty());
	}

	@Test
	@DisplayName("a path that cannot be read does not crash the loader")
	void unreadablePathFallsBack() {
		// The directory itself stands in for the config file, so reading fails.
		assertTrue(SplashConfig.load(dir, GSON).splashes.isEmpty());
	}

	@Test
	@DisplayName("optional entry fields keep their defaults")
	void optionalEntryFieldsDefault() {
		write("{\"splashes\":[{\"text\":\"Just text\"}]}");

		SplashEntry entry = onlyEntry();

		assertEquals(1, entry.weightOrDefault());
		assertEquals(-1, entry.rgb());
		assertFalse(entry.isBlank());
	}

	@Test
	@DisplayName("comments are allowed, so the shipped config documents itself")
	void commentsAreAllowed() {
		write("{\n// a line comment\n/* and a block comment */\n\"splashes\":[{\"text\":\"Hi\"}]}");

		assertEquals("Hi", onlyEntry().text);
	}

	@Test
	@DisplayName("the schema can also be parsed without touching the file system")
	void parsesWithoutFileSystem() {
		SplashConfig parsed = SplashConfig.parse("{\"splashes\":[{\"text\":\"Packed\",\"weight\":4}]}", GSON);

		assertEquals(1, parsed.splashes.size());
		assertEquals("Packed", parsed.splashes.get(0).text);
		assertEquals(4, parsed.splashes.get(0).weightOrDefault());
	}

	@Test
	@DisplayName("parsing normalises a missing splashes array")
	void parseNormalisesMissingList() {
		assertTrue(SplashConfig.parse("{}", GSON).splashes.isEmpty());
	}
}
