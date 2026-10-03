package dev.arrbrants.customsplash.mixin;

import dev.arrbrants.customsplash.SplashColor;
import dev.arrbrants.customsplash.SplashColors;
import dev.arrbrants.customsplash.SplashRegistry;
import net.minecraft.client.resource.SplashTextResourceSupplier;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

@Mixin(SplashTextResourceSupplier.class)
public class SplashManagerMixin {
	@Inject(at = @At("HEAD"), method = "get", cancellable = true)
	private void getSplash(CallbackInfoReturnable<String> cir) {
		SplashRegistry.pickEntry().ifPresent(picked -> cir.setReturnValue(colourize(picked)));
	}

	private static String colourize(SplashRegistry.Picked picked) {
		SplashColor color = picked.color;
		if (color == null) {
			return picked.text;
		}
		if (color.isSolid()) {
			return SplashColors.legacyPrefix(color.solidRgb()) + picked.text;
		}
		int[] colors = color.colorsFor(picked.text);
		StringBuilder builder = new StringBuilder();
		for (int i = 0; i < picked.text.length(); i++) {
			builder.append(SplashColors.legacyPrefix(colors[i])).append(picked.text.charAt(i));
		}
		return builder.toString();
	}
}
