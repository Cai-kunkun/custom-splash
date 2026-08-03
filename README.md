# Custom Splash

A Fabric mod that replaces or extends the Minecraft title screen yellow splash text.

## Usage

Call `SplashRegistry.add(String)` during mod initialization (or any time before the title screen renders).

```java
import dev.arrbrants.customsplash.SplashRegistry;

public class MyMod implements ModInitializer {
    @Override
    public void onInitialize() {
        SplashRegistry.add("Hello! Fabric!");
        SplashRegistry.add("Powered by Mixin");
    }
}
```

Multiple entries are stored in a list. One is chosen at random each time the splash text appears.

When no custom splashes are registered, the vanilla Minecraft splash is displayed normally.