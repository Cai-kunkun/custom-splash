package dev.arrbrants.customsplash;

import static org.junit.jupiter.api.Assertions.assertEquals;

import java.time.LocalDate;
import java.time.LocalTime;
import java.util.Random;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

/**
 * Covers the placeholder expansion in {@link SplashRegistry#format}.
 */
class SplashRegistryFormatTest {
	private static SplashContext context(String player) {
		return new SplashContext(LocalTime.of(14, 5), LocalDate.of(2026, 1, 7), player, new Random(1));
	}

	@Test
	@DisplayName("text without a brace is returned unchanged")
	void noPlaceholders() {
		assertEquals("Hello world!", SplashRegistry.format("Hello world!", context("Steve")));
		assertEquals("", SplashRegistry.format("", context("Steve")));
	}

	@Test
	@DisplayName("{player} and {username} expand to the player name")
	void player() {
		assertEquals("Hi Steve!", SplashRegistry.format("Hi {player}!", context("Steve")));
		assertEquals("Hi Steve!", SplashRegistry.format("Hi {username}!", context("Steve")));
	}

	@Test
	@DisplayName("a missing player name falls back to the word player")
	void playerFallback() {
		assertEquals("Hi player!", SplashRegistry.format("Hi {player}!", context(null)));
		assertEquals("Hi player!", SplashRegistry.format("Hi {username}!", context(null)));
	}

	@Test
	@DisplayName("{date} and {time} come from the supplied context")
	void dateAndTime() {
		assertEquals("Today is 2026-01-07", SplashRegistry.format("Today is {date}", context(null)));
		assertEquals("Now 14:05", SplashRegistry.format("Now {time}", context(null)));
	}

	@Test
	@DisplayName("unknown placeholders are left untouched")
	void unknownPlaceholders() {
		assertEquals("{unknown} {also unknown}", SplashRegistry.format("{unknown} {also unknown}", context(null)));
		assertEquals("A } stray brace", SplashRegistry.format("A } stray brace", context(null)));
	}

	@Test
	@DisplayName("placeholders may be repeated")
	void repeatedPlaceholders() {
		assertEquals("Steve, Steve!", SplashRegistry.format("{player}, {player}!", context("Steve")));
	}

	@Test
	@DisplayName("several placeholders combine in one text")
	void combined() {
		assertEquals("Steve at 14:05 on 2026-01-07",
			SplashRegistry.format("{player} at {time} on {date}", context("Steve")));
	}

	@Test
	@DisplayName("loader dependent placeholders stay literal without a game")
	void loaderPlaceholdersStayLiteral() {
		// There is no Minecraft or Fabric in a unit test, so these resolve to
		// nothing and the token must survive untouched.
		assertEquals("Version {mc_version}", SplashRegistry.format("Version {mc_version}", context(null)));
		assertEquals("Version {mc}", SplashRegistry.format("Version {mc}", context(null)));
		assertEquals("Version {version}", SplashRegistry.format("Version {version}", context(null)));
		assertEquals("Mods {mods}", SplashRegistry.format("Mods {mods}", context(null)));
		assertEquals("Mods {mods_count}", SplashRegistry.format("Mods {mods_count}", context(null)));
	}

	@Test
	@DisplayName("{mc_version} does not accidentally match {mc}")
	void mcIsNotAPrefixOfMcVersion() {
		// Replacing {mc} first would corrupt "{mc_version}" into "1.21.11_version}".
		assertEquals("A {mc_version} B", SplashRegistry.format("A {mc_version} B", context(null)));
		assertEquals("A {mc_version} B {mc}", SplashRegistry.format("A {mc_version} B {mc}", context(null)));
	}

	@Test
	@DisplayName("a player name containing braces does not break the pass")
	void bracesInPlayerName() {
		assertEquals("< {weird} >", SplashRegistry.format("< {player} >", context("{weird}")));
	}
}
