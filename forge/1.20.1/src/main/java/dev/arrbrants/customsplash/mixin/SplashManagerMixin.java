package dev.arrbrants.customsplash.mixin;

import dev.arrbrants.customsplash.SplashRegistry;
import net.minecraft.client.gui.components.SplashRenderer;
import net.minecraft.client.resources.SplashManager;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.MutableComponent;
import net.minecraft.network.chat.Style;
import net.minecraft.network.chat.TextColor;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

import java.lang.reflect.InvocationTargetException;

@Mixin(SplashManager.class)
public class SplashManagerMixin {
	@Inject(at = @At("HEAD"), method = "getSplash", cancellable = true)
	private void getSplash(CallbackInfoReturnable<SplashRenderer> cir) {
		SplashRegistry.pickEntry().ifPresent(picked -> cir.setReturnValue(createRenderer(picked)));
	}

	private static SplashRenderer createRenderer(SplashRegistry.Picked picked) {
		MutableComponent component = Component.literal(picked.text);
		if (picked.rgb >= 0) {
			component = component.withStyle(Style.EMPTY.withColor(TextColor.fromRgb(picked.rgb)));
		}
		try {
			return SplashRenderer.class.getConstructor(Component.class).newInstance(component);
		} catch (NoSuchMethodException ignored) {
			try {
				return SplashRenderer.class.getConstructor(String.class).newInstance(picked.text);
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
