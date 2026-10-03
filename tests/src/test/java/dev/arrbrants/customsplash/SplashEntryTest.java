package dev.arrbrants.customsplash;

import static org.junit.jupiter.api.Assertions.assertDoesNotThrow;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.time.LocalDate;
import java.time.LocalTime;
import java.util.Arrays;
import java.util.Random;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

/**
 * Covers {@link SplashEntry} plus its condition matching.
 */
class SplashEntryTest {
	private static final LocalDate SATURDAY = LocalDate.of(2026, 1, 3);
	private static final LocalDate WEDNESDAY = LocalDate.of(2026, 1, 7);

	private static SplashContext context(String player) {
		return new SplashContext(LocalTime.of(12, 0), WEDNESDAY, player, new Random(1));
	}

	private static SplashContext contextAt(LocalDate date, LocalTime time, String player) {
		return new SplashContext(time, date, player, new Random(1));
	}

	private static SplashEntry.Conditions conditions() {
		return new SplashEntry.Conditions();
	}

	@Test
	@DisplayName("blank detection")
	void blankness() {
		assertTrue(new SplashEntry().isBlank());
		assertTrue(new SplashEntry(null, 1).isBlank());
		assertTrue(new SplashEntry("", 1).isBlank());
		assertFalse(new SplashEntry("hi", 1).isBlank());
	}

	@Test
	@DisplayName("a weight of zero or less falls back to one")
	void weights() {
		assertEquals(5, new SplashEntry("a", 5).weightOrDefault());
		assertEquals(1, new SplashEntry("a", 0).weightOrDefault());
		assertEquals(1, new SplashEntry("a", -3).weightOrDefault());
	}

	@Test
	@DisplayName("the parsed colour is cached")
	void colourIsCached() {
		SplashEntry entry = new SplashEntry();
		entry.color = "#FF8000";

		SplashColor first = entry.colorSpec();
		SplashColor second = entry.colorSpec();

		assertSame(first, second);
		assertEquals(0xFF8000, first.solidRgb());
	}

	@Test
	@DisplayName("an unset or invalid colour yields null")
	void missingColour() {
		assertNull(new SplashEntry().colorSpec());

		SplashEntry entry = new SplashEntry();
		entry.color = "nonsense";
		assertNull(entry.colorSpec());
	}

	@Test
	@DisplayName("rgb() stays negative when the colour is unset")
	void rgbWhenUnset() {
		assertEquals(-1, new SplashEntry().rgb());
		assertEquals(-1, new SplashEntry("x", 1).rgb());
	}

	@Test
	@DisplayName("conditions are optional")
	void noConditions() {
		assertTrue(new SplashEntry("x", 1).matches(context("Steve")));
	}

	@Test
	@DisplayName("the day condition depends on the hour")
	void dayCondition() {
		SplashEntry.Conditions day = conditions();
		day.time = "day";
		SplashEntry.Conditions night = conditions();
		night.time = "night";

		assertTrue(new SplashEntry("x", 1).matchesConditions(day, contextAt(WEDNESDAY, LocalTime.of(9, 0), null)));
		assertFalse(new SplashEntry("x", 1).matchesConditions(day, contextAt(WEDNESDAY, LocalTime.of(21, 0), null)));
		assertTrue(new SplashEntry("x", 1).matchesConditions(night, contextAt(WEDNESDAY, LocalTime.of(21, 0), null)));
	}

	@Test
	@DisplayName("an unknown time keyword matches anything")
	void unknownTimeKeyword() {
		SplashEntry.Conditions conditions = conditions();
		conditions.time = "whenever";
		assertTrue(new SplashEntry("x", 1).matchesConditions(conditions, context(null)));
	}

	@Test
	@DisplayName("the weekend condition uses the weekday")
	void weekendCondition() {
		SplashEntry.Conditions conditions = conditions();
		conditions.weekend = Boolean.TRUE;

		assertTrue(new SplashEntry("x", 1).matchesConditions(conditions, contextAt(SATURDAY, LocalTime.NOON, null)));
		assertFalse(new SplashEntry("x", 1).matchesConditions(conditions, contextAt(WEDNESDAY, LocalTime.NOON, null)));
	}

	@Test
	@DisplayName("the date condition accepts a single day and a range")
	void dateCondition() {
		SplashEntry.Conditions single = conditions();
		single.date = "01-07";
		SplashEntry.Conditions range = conditions();
		range.date = "12-24..12-26";

		assertTrue(new SplashEntry("x", 1).matchesConditions(single, context(null)));
		assertFalse(new SplashEntry("x", 1).matchesConditions(single, contextAt(LocalDate.of(2026, 1, 8), LocalTime.NOON, null)));
		assertTrue(new SplashEntry("x", 1).matchesConditions(range,
			contextAt(LocalDate.of(2026, 12, 25), LocalTime.NOON, null)));
		assertFalse(new SplashEntry("x", 1).matchesConditions(range,
			contextAt(LocalDate.of(2026, 12, 27), LocalTime.NOON, null)));
	}

	@Test
	@DisplayName("an invalid date condition never matches")
	void invalidDateCondition() {
		SplashEntry.Conditions conditions = conditions();
		conditions.date = "not-a-date";

		assertFalse(new SplashEntry("x", 1).matchesConditions(conditions, context(null)));
	}

	@Test
	@DisplayName("the player condition is case insensitive")
	void playerCondition() {
		SplashEntry.Conditions conditions = conditions();
		conditions.player = Arrays.asList("Steve", "Alex");

		assertTrue(new SplashEntry("x", 1).matchesConditions(conditions, context("steve")));
		assertTrue(new SplashEntry("x", 1).matchesConditions(conditions, context("ALEX")));
		assertFalse(new SplashEntry("x", 1).matchesConditions(conditions, context("Herobrine")));
		// Without a player name the condition cannot be satisfied.
		assertFalse(new SplashEntry("x", 1).matchesConditions(conditions, context(null)));
	}

	@Test
	@DisplayName("the mods condition needs a loader, which is absent here")
	void modsCondition() {
		SplashEntry.Conditions conditions = conditions();
		conditions.mods = Arrays.asList("fabric-api");

		// Unit tests run without Fabric, so the condition cannot be satisfied.
		assertFalse(new SplashEntry("x", 1).matchesConditions(conditions, context(null)));
	}

	@Test
	@DisplayName("every condition must match at once")
	void conditionsAreCombined() {
		SplashEntry.Conditions conditions = conditions();
		conditions.time = "day";
		conditions.player = Arrays.asList("Steve");

		assertTrue(new SplashEntry("x", 1).matchesConditions(conditions, context("Steve")));
		assertFalse(new SplashEntry("x", 1).matchesConditions(conditions, context("Alex")));
	}

	@Test
	@DisplayName("a malformed condition does not throw")
	void malformedConditionDoesNotThrow() {
		SplashEntry.Conditions conditions = conditions();
		conditions.chance = 0.5D;

		assertDoesNotThrow(() -> new SplashEntry("x", 1).matchesConditions(conditions, context("Steve")));
	}

	@Test
	@DisplayName("a null conditions block matches everything")
	void nullConditionsMatch() {
		assertTrue(new SplashEntry("x", 1).matches(context("Steve")));
		assertTrue(new SplashEntry("x", 1).matchesConditions(null, context("Steve")));
	}
}
