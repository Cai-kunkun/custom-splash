package dev.arrbrants.customsplash;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Optional;
import java.util.Random;
/**
 * Manage custom splash text list, you can use {@link #add(String)} to register one.
 * If list is not empty，{@link #pick()} return one randomly；or return empty，and uses original splash texts.
 */
public final class SplashRegistry {

	private static final List<String> SPLASHES = Collections.synchronizedList(new ArrayList<>());
	private static final Random RNG = new Random();

	private SplashRegistry() {}

	/**
	 * Register a splash text.
	 * @param text The text you wanna show.
	 */
	public static void add(String text) {
		if (text != null && !text.isEmpty()) {
			SPLASHES.add(text);
		}
	}

	/**
	 * Pick a registered splash text randomly。
	 * @return a splash text，if texts are empty then return {@link Optional#empty()}
	 */
	public static Optional<String> pick() {
		synchronized (SPLASHES) {
			if (SPLASHES.isEmpty()) {
				return Optional.empty();
			}
			return Optional.of(SPLASHES.get(RNG.nextInt(SPLASHES.size())));
		}
	}
}