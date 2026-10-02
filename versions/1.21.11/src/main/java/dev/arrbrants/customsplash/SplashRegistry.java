package dev.arrbrants.customsplash;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Optional;
import java.util.Random;

public final class SplashRegistry {
	private static final List<String> SPLASHES = Collections.synchronizedList(new ArrayList<>());
	private static final Random RNG = new Random();

	private SplashRegistry() {}

	public static void add(String text) {
		if (text != null && !text.isEmpty()) {
			SPLASHES.add(text);
		}
	}

	public static Optional<String> pick() {
		synchronized (SPLASHES) {
			if (SPLASHES.isEmpty()) {
				return Optional.empty();
			}
			return Optional.of(SPLASHES.get(RNG.nextInt(SPLASHES.size())));
		}
	}
}
