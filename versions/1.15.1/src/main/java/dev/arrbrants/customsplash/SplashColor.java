package dev.arrbrants.customsplash;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

/**
 * A splash colour, either a single value or a multi-character gradient.
 *
 * <p>Accepted forms: {@code #RRGGBB} for a solid colour,
 * {@code #RRGGBB,#RRGGBB[,...]} for a gradient spread over the text and
 * {@code rainbow} / {@code rainbow:degrees} for a hue cycle. Anything else
 * (including {@code null} and blank input) is rejected.</p>
 */
public final class SplashColor {
	private static final int DEFAULT_HUE_SPREAD = 15;

	private final int[] stops;
	private final boolean rainbow;
	private final int hueSpread;

	private SplashColor(int[] stops, boolean rainbow, int hueSpread) {
		this.stops = stops;
		this.rainbow = rainbow;
		this.hueSpread = hueSpread;
	}

	/**
	 * @return the parsed colour, or {@code null} when the value is missing or invalid
	 */
	public static SplashColor parse(String value) {
		if (value == null) {
			return null;
		}
		String text = value.trim();
		if (text.isEmpty()) {
			return null;
		}
		if (text.regionMatches(true, 0, "rainbow", 0, 7)) {
			return parseRainbow(text);
		}
		List<Integer> colors = new ArrayList<>();
		for (String part : text.split(",")) {
			String candidate = part.trim();
			if (candidate.regionMatches(true, 0, "gradient:", 0, 9)) {
				candidate = candidate.substring(9).trim();
			}
			int rgb = SplashColors.parse(candidate);
			if (rgb < 0) {
				return null;
			}
			colors.add(rgb);
		}
		if (colors.isEmpty()) {
			return null;
		}
		int[] stops = new int[colors.size()];
		for (int i = 0; i < stops.length; i++) {
			stops[i] = colors.get(i);
		}
		return new SplashColor(stops, false, 0);
	}

	private static SplashColor parseRainbow(String text) {
		if (text.length() == 7) {
			return new SplashColor(null, true, DEFAULT_HUE_SPREAD);
		}
		if (text.charAt(7) != ':') {
			return null;
		}
		try {
			int spread = Integer.parseInt(text.substring(8).trim());
			if (spread < 0 || spread > 360) {
				return null;
			}
			return new SplashColor(null, true, spread);
		} catch (NumberFormatException exception) {
			return null;
		}
	}

	public boolean isSolid() {
		return !rainbow && stops.length == 1;
	}

	/**
	 * @return the packed RGB value, or {@code -1} when the colour is not solid
	 */
	public int solidRgb() {
		return isSolid() ? stops[0] : -1;
	}

	/**
	 * @return one RGB value per character of {@code text}, never {@code null}
	 */
	public int[] colorsFor(String text) {
		int length = text.length();
		int[] colors = new int[length];
		if (isSolid()) {
			Arrays.fill(colors, stops[0]);
			return colors;
		}
		if (rainbow) {
			for (int i = 0; i < length; i++) {
				colors[i] = hueToRgb(i * hueSpread);
			}
			return colors;
		}
		for (int i = 0; i < length; i++) {
			colors[i] = sample(stops, length == 1 ? 0.0D : (double) i / (length - 1));
		}
		return colors;
	}

	private static int sample(int[] stops, double position) {
		double scaled = Math.max(0.0D, Math.min(1.0D, position)) * (stops.length - 1);
		int index = (int) scaled;
		double fraction = scaled - index;
		if (index >= stops.length - 1) {
			return stops[stops.length - 1];
		}
		return interpolate(stops[index], stops[index + 1], fraction);
	}

	private static int interpolate(int from, int to, double fraction) {
		int red = Math.round(lerp(from >> 16 & 0xFF, to >> 16 & 0xFF, fraction));
		int green = Math.round(lerp(from >> 8 & 0xFF, to >> 8 & 0xFF, fraction));
		int blue = Math.round(lerp(from & 0xFF, to & 0xFF, fraction));
		return red << 16 | green << 8 | blue;
	}

	private static float lerp(int from, int to, double fraction) {
		return (float) (from + (to - from) * fraction);
	}

	private static int hueToRgb(int hue) {
		float position = (((hue % 360) + 360) % 360) / 360f;
		int sector = (int) (position * 6);
		float fraction = position * 6 - sector;
		float value = 1f;
		float minuend = value * (1 - fraction);
		float descending = value * (1 - (1 - fraction));
		float red;
		float green;
		float blue;
		switch (sector % 6) {
			case 0: red = value; green = descending; blue = 0f; break;
			case 1: red = minuend; green = value; blue = 0f; break;
			case 2: red = 0f; green = value; blue = descending; break;
			case 3: red = 0f; green = minuend; blue = value; break;
			case 4: red = descending; green = 0f; blue = value; break;
			default: red = value; green = 0f; blue = minuend; break;
		}
		return toChannel(red) << 16 | toChannel(green) << 8 | toChannel(blue);
	}

	private static int toChannel(float value) {
		return Math.max(0, Math.min(255, Math.round(value * 255)));
	}
}
