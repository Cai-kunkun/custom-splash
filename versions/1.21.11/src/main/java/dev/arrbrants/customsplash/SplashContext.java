package dev.arrbrants.customsplash;

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
	private final LocalTime time;
	private final LocalDate date;
	private final String playerName;
	private final Random random;

	SplashContext(LocalTime time, LocalDate date, String playerName, Random random) {
		this.time = time;
		this.date = date;
		this.playerName = playerName;
		this.random = random;
	}

	static SplashContext create() {
		return new SplashContext(LocalTime.now(), LocalDate.now(), lookupPlayerName(), ThreadLocalRandom.current());
	}

	LocalTime time() {
		return time;
	}

	LocalDate date() {
		return date;
	}

	String playerName() {
		return playerName;
	}

	/**
	 * @return the running Minecraft version, or null when unavailable
	 */
	String gameVersion() {
		try {
			Class<?> minecraft = Class.forName("net.minecraft.client.Minecraft");
			Object instance = invoke(minecraft, null, "getInstance");
			if (instance == null) {
				return null;
			}
			Object version = invoke(instance.getClass(), instance, "getLaunchedVersion", "getGameVersion");
			return version instanceof String ? (String) version : null;
		} catch (Throwable ignored) {
			return null;
		}
	}

	/**
	 * @return the number of loaded mods, or null when unavailable
	 */
	String modCount() {
		try {
			return String.valueOf(FabricLoader.getInstance().getAllMods().size());
		} catch (RuntimeException | LinkageError ignored) {
			return null;
		}
	}

	boolean hasMod(String modId) {
		if (modId == null) {
			return false;
		}
		try {
			return FabricLoader.getInstance().isModLoaded(modId);
		} catch (RuntimeException | LinkageError ignored) {
			// no loader in this environment, for example unit tests
			return false;
		}
	}

	boolean roll(double probability) {
		return probability >= 1.0D || (probability > 0.0D && random.nextDouble() < probability);
	}

	private static String lookupPlayerName() {
		try {
			Class<?> minecraft = Class.forName("net.minecraft.client.Minecraft");
			Object instance = invoke(minecraft, null, "getInstance");
			if (instance == null) {
				return null;
			}
			Object user = invoke(instance.getClass(), instance, "getUser", "getGameProfile");
			if (user == null) {
				return null;
			}
			Object name = invoke(user.getClass(), user, "getName");
			return name instanceof String ? (String) name : null;
		} catch (Throwable ignored) {
			return null;
		}
	}

	private static Object invoke(Class<?> type, Object target, String... names) {
		for (String name : names) {
			try {
				Method method = type.getMethod(name);
				return method.invoke(target);
			} catch (Throwable ignored) {
				// Try the next candidate method name.
			}
		}
		return null;
	}
}
