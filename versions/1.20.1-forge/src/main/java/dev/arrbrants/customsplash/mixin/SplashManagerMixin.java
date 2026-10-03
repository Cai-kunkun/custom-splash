package dev.arrbrants.customsplash.mixin;

import dev.arrbrants.customsplash.SplashColor;
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
		try {
			return SplashRenderer.class.getConstructor(Component.class).newInstance(buildComponent(picked));
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

	private static MutableComponent buildComponent(SplashRegistry.Picked picked) {
		SplashColor color = picked.color;
		if (color == null) {
			return Component.literal(picked.text);
		}
		if (color.isSolid()) {
			return Component.literal(picked.text).withStyle(Style.EMPTY.withColor(TextColor.fromRgb(color.solidRgb())));
		}
		int[] colors = color.colorsFor(picked.text);
		MutableComponent root = Component.empty();
		for (int i = 0; i < picked.text.length(); i++) {
			root.append(Component.literal(String.valueOf(picked.text.charAt(i)))
					.withStyle(Style.EMPTY.withColor(TextColor.fromRgb(colors[i]))));
		}
		return root;
	}

	private static Throwable unwrap(ReflectiveOperationException exception) {
		return exception instanceof InvocationTargetException && exception.getCause() != null
				? exception.getCause() : exception;
	}
}
