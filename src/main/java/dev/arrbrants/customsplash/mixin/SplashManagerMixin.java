package dev.arrbrants.customsplash.mixin;

import dev.arrbrants.customsplash.SplashRegistry;
import net.minecraft.client.gui.components.SplashRenderer;
import net.minecraft.client.resources.SplashManager;
import net.minecraft.network.chat.Component;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

import java.util.Optional;

@Mixin(SplashManager.class)
public class SplashManagerMixin {
	@Inject(at = @At("HEAD"), method = "getSplash", cancellable = true)
	private void getSplash(CallbackInfoReturnable<SplashRenderer> cir) {
		Optional<String> custom = SplashRegistry.pick();
        custom.ifPresent(s -> cir.setReturnValue(new SplashRenderer(Component.literal(s))));
	}
}
