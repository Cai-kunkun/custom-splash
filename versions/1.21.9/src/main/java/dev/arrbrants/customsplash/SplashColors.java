package dev.arrbrants.customsplash;

/**
 * Parses ``#RRGGBB`` colours and maps them onto the legacy 16-colour palette.
 */
public final class SplashColors {
	private static final int[] PALETTE = {
		0x000000, 0x0000AA, 0x00AA00, 0x00AAAA, 0xAA0000, 0xAA00AA, 0xFFAA00, 0xAAAAAA,
		0x555555, 0x5555FF, 0x55FF55, 0x55FFFF, 0xFF5555, 0xFF55FF, 0xFFFF55, 0xFFFFFF
	};
	private static final char[] CODES = {
		'0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c', 'd', 'e', 'f'
	};

	private SplashColors() {
	}

	/**
	 * @return the packed RGB value, or {@code -1} when the input is missing/invalid
	 */
	public static int parse(String value) {
		if (value == null) {
			return -1;
		}
		String hex = value.trim();
		if (hex.startsWith("#")) {
			hex = hex.substring(1);
		}
		if (hex.length() != 6) {
			return -1;
		}
		try {
			return Integer.parseInt(hex, 16);
		} catch (NumberFormatException exception) {
			return -1;
		}
	}

	public static String legacyPrefix(int rgb) {
		return "\u00a7" + legacyCode(rgb);
	}

	public static char legacyCode(int rgb) {
		int red = (rgb >> 16) & 0xFF;
		int green = (rgb >> 8) & 0xFF;
		int blue = rgb & 0xFF;
		int best = 0;
		long bestDistance = Long.MAX_VALUE;
		for (int i = 0; i < PALETTE.length; i++) {
			int r = (PALETTE[i] >> 16) & 0xFF;
			int g = (PALETTE[i] >> 8) & 0xFF;
			int b = PALETTE[i] & 0xFF;
			long distance = (long) (red - r) * (red - r)
				+ (long) (green - g) * (green - g)
				+ (long) (blue - b) * (blue - b);
			if (distance < bestDistance) {
				bestDistance = distance;
				best = i;
			}
		}
		return CODES[best];
	}
}
