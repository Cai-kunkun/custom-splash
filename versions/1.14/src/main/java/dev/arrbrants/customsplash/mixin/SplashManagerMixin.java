package dev.arrbrants.customsplash.mixin;

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
		SplashRegistry.pickEntry().ifPresent(picked ->
				cir.setReturnValue(picked.rgb >= 0 ? SplashColors.legacyPrefix(picked.rgb) + picked.text : picked.text));
	}
}
