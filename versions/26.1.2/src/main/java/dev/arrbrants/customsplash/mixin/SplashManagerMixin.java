package dev.arrbrants.customsplash.mixin;

import dev.arrbrants.customsplash.SplashRegistry;
import net.minecraft.client.gui.components.SplashRenderer;
import net.minecraft.client.resources.SplashManager;
import net.minecraft.network.chat.Component;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

import java.lang.reflect.InvocationTargetException;

@Mixin(SplashManager.class)
public class SplashManagerMixin {
	@Inject(at = @At("HEAD"), method = "getSplash", cancellable = true)
	private void getSplash(CallbackInfoReturnable<SplashRenderer> cir) {
		SplashRegistry.pick().ifPresent(text -> cir.setReturnValue(createRenderer(text)));
	}

	private static SplashRenderer createRenderer(String text) {
		try {
			return SplashRenderer.class.getConstructor(String.class).newInstance(text);
		} catch (NoSuchMethodException ignored) {
			try {
				return SplashRenderer.class.getConstructor(Component.class).newInstance(Component.literal(text));
			} catch (ReflectiveOperationException exception) {
				throw new IllegalStateException("Unable to create splash renderer", unwrap(exception));
			}
		} catch (ReflectiveOperationException exception) {
			throw new IllegalStateException("Unable to create splash renderer", unwrap(exception));
		}
	}

	private static Throwable unwrap(ReflectiveOperationException exception) {
		return exception instanceof InvocationTargetException && exception.getCause() != null
				? exception.getCause() : exception;
	}
}
