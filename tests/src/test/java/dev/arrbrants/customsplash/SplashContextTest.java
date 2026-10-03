package dev.arrbrants.customsplash;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.time.LocalDate;
import java.time.LocalTime;
import java.util.Random;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

/**
 * Covers the runtime information holder used by conditions and placeholders.
 *
 * <p>The tests construct a context directly: the constructor is never called by
 * the mod (it goes through {@link SplashContext#create()}), so it is free to be
 * widened without any risk of being used from outside.</p>
 */
class SplashContextTest {
	private static final LocalDate SATURDAY = LocalDate.of(2026, 1, 3);
	private static final LocalDate WEDNESDAY = LocalDate.of(2026, 1, 7);

	private static SplashContext context(LocalDate date, LocalTime time, String player) {
		return new SplashContext(time, date, player, new Random(7));
	}

	@Test
	@DisplayName("exposes the values it was built with")
	void exposesValues() {
		SplashContext context = context(WEDNESDAY, LocalTime.of(13, 30), "Steve");

		assertEquals(LocalTime.of(13, 30), context.time());
		assertEquals(WEDNESDAY, context.date());
		assertEquals("Steve", context.playerName());
	}

	@Test
	@DisplayName("a missing player name is reported as null")
	void missingPlayer() {
		assertNull(context(WEDNESDAY, LocalTime.NOON, null).playerName());
	}

	@Test
	@DisplayName("hasMod accepts a null id")
	void nullModId() {
		assertFalse(context(WEDNESDAY, LocalTime.NOON, null).hasMod(null));
		assertFalse(context(WEDNESDAY, LocalTime.NOON, null).hasMod(""));
	}

	@Test
	@DisplayName("headless lookups degrade instead of throwing")
	void headlessLookupsDegrade() {
		SplashContext context = context(WEDNESDAY, LocalTime.NOON, null);

		// No FabricLoader or Minecraft in this process: every lookup reports
		// "unknown" rather than crashing the title screen.
		assertFalse(context.hasMod("fabric-api"));
		assertNull(context.gameVersion());
		assertNull(context.modCount());
	}

	@Test
	@DisplayName("roll() is certain for 1 and impossible for 0")
	void rollExtremes() {
		SplashContext context = context(WEDNESDAY, LocalTime.NOON, null);

		assertTrue(context.roll(1.0D));
		assertFalse(context.roll(0.0D));
		assertFalse(context.roll(-0.5D));
	}

	@Test
	@DisplayName("roll() follows the probability it is given")
	void rollDistribution() {
		SplashContext context = context(WEDNESDAY, LocalTime.NOON, null);
		int hits = 0;
		for (int i = 0; i < 1000; i++) {
			if (context.roll(0.5D)) {
				hits = hits + 1;
			}
		}
		int observed = hits;
		// Statistically 500, allow a generous band so the test is stable.
		assertTrue(observed > 350 && observed < 650, () -> "unexpected distribution: " + observed);
	}

	@Test
	@DisplayName("roll() is deterministic for a given seed")
	void rollIsDeterministic() {
		assertEquals(rollsWithSeed(42), rollsWithSeed(42));
	}

	private static int rollsWithSeed(int seed) {
		SplashContext context = new SplashContext(LocalTime.NOON, WEDNESDAY, "Steve", new Random(seed));
		int hits = 0;
		for (int i = 0; i < 100; i++) {
			if (context.roll(0.3D)) {
				hits++;
			}
		}
		return hits;
	}

	@Test
	@DisplayName("create() never throws even without a running game")
	void createNeverThrows() {
		assertNotNull(SplashContext.create());
	}
}
