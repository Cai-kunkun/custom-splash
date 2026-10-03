package dev.arrbrants.customsplash;

import java.lang.reflect.Method;
import java.nio.file.Path;
import java.nio.file.Paths;

/** Forge and NeoForge platform hooks. */
public enum SplashForgePlatform implements SplashPlatform {
	INSTANCE;

	@Override
	public Path configDir() {
		return gameDir().resolve("config");
	}

	@Override
	public Path gameDir() {
		String value = System.getProperty("user.dir");
		return value == null ? Paths.get(".") : Paths.get(value);
	}

	@Override
	public boolean isModLoaded(String modId) {
		try {
			Class<?> type = Class.forName("net.minecraftforge.fml.loading.FMLLoader");
			Object loadingModList = invoke(type, null, "getLoadingModList");
			if (loadingModList == null) {
				return false;
			}
			Object mods = invoke(loadingModList.getClass(), loadingModList, "getMods");
			if (mods instanceof Iterable) {
				for (Object mod : (Iterable<?>) mods) {
					Object id = invoke(mod.getClass(), mod, "getModId");
					if (modId.equals(id)) {
						return true;
					}
				}
			}
			return false;
		} catch (ReflectiveOperationException | RuntimeException ignored) {
			return false;
		}
	}

	@Override
	public String platformName() {
		return "Forge";
	}

	private static Object invoke(Class<?> type, Object target, String name) throws ReflectiveOperationException {
		Method method = type.getMethod(name);
		return method.invoke(target);
	}
}
