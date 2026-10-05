package dev.arrbrants.customsplash;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import java.util.Random;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

/**
 * Covers the weighted picker in {@link SplashRegistry}.
 */
class SplashRegistryChooseTest {
	private static SplashEntry entry(String text, int weight) {
		return new SplashEntry(text, weight);
	}

	private static int countOf(String text, int rollouts, int weight) {
		SplashEntry first = entry("keep", 1);
		SplashEntry second = entry(text, weight);
		List<SplashEntry> pool = Arrays.asList(first, second);
		int hits = 0;
		Random random = new Random(rollouts * 977L + 13);
		for (int i = 0; i < rollouts; i++) {
			if (SplashRegistry.chooseWeighted(pool, random) == first) {
				hits++;
			}
		}
		return hits;
	}

	@Test
	@DisplayName("a pool of one always yields that entry")
	void singleEntry() {
		SplashEntry only = entry("only", 1);
		assertSame(only, SplashRegistry.chooseWeighted(Collections.singletonList(only), new Random(0)));
	}

	@Test
	@DisplayName("equal weights are picked roughly evenly")
	void equalWeights() {
		SplashEntry first = entry("first", 1);
		SplashEntry second = entry("second", 1);
		List<SplashEntry> pool = Arrays.asList(first, second);
		Random random = new Random(1);
		int counted = 0;
		for (int i = 0; i < 2000; i++) {
			if (SplashRegistry.chooseWeighted(pool, random) == first) {
				counted = counted + 1;
			}
		}
		int firsts = counted;
		assertTrue(firsts > 800 && firsts < 1200, () -> "unexpected split: " + firsts);
	}

	@Test
	@DisplayName("heavier entries are picked more often")
	void heavierEntriesWin() {
		// weight 1 against weight 9 gives roughly one hit in ten.
		int hits = countOf("rare", 20000, 9);
		assertTrue(hits > 1600 && hits < 2400, () -> "unexpected ratio: " + hits);
	}

	@Test
	@DisplayName("a non positive weight behaves like one")
	void nonPositiveWeightBecomesOne() {
		SplashEntry first = entry("first", 0);
		SplashEntry second = entry("second", 0);
		List<SplashEntry> pool = Arrays.asList(first, second);
		Random random = new Random(3);
		int counted = 0;
		for (int i = 0; i < 1000; i++) {
			if (SplashRegistry.chooseWeighted(pool, random) == first) {
				counted = counted + 1;
			}
		}
		int firsts = counted;
		assertTrue(firsts > 300 && firsts < 700, () -> "unexpected split: " + firsts);
	}

	@Test
	@DisplayName("the most common outcome is the mode of the distribution")
	void returnsMembersOfThePool() {
		List<SplashEntry> pool = Arrays.asList(entry("a", 1), entry("b", 2), entry("c", 3));
		Random random = new Random(5);
		int[] seen = new int[3];
		for (int i = 0; i < 6000; i++) {
			seen[pool.indexOf(SplashRegistry.chooseWeighted(pool, random))]++;
		}
		// Expect roughly 1000 / 2000 / 3000 with a generous band.
		assertTrue(seen[0] > 700 && seen[0] < 1300, () -> "a: " + seen[0]);
		assertTrue(seen[1] > 1700 && seen[1] < 2300, () -> "b: " + seen[1]);
		assertTrue(seen[2] > 2700 && seen[2] < 3300, () -> "c: " + seen[2]);
		assertEquals(6000, seen[0] + seen[1] + seen[2]);
	}

	@Test
	@DisplayName("absurd weights cannot overflow the picker")
	void hugeWeightsDoNotOverflow() {
		// Two int-sized weights used to overflow the running total into a
		// negative bound, and Random.nextInt threw on the title screen.
		SplashEntry first = entry("first", Integer.MAX_VALUE);
		SplashEntry second = entry("second", Integer.MAX_VALUE);
		List<SplashEntry> pool = Arrays.asList(first, second);
		Random random = new Random(11);
		for (int i = 0; i < 2000; i++) {
			SplashEntry chosen = SplashRegistry.chooseWeighted(pool, random);
			assertTrue(chosen == first || chosen == second, "picked outside the pool");
		}
	}
}
