package dev.arrbrants.customsplash;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

/**
 * Covers the hex parsing and the legacy palette mapping in {@link SplashColors}.
 */
class SplashColorsTest {
	@Test
	@DisplayName("accepts a leading hash and both cases")
	void acceptsHashAndCase() {
		assertEquals(0xFF8000, SplashColors.parse("#FF8000"));
		assertEquals(0xFF8000, SplashColors.parse("ff8000"));
		assertEquals(0xFF8000, SplashColors.parse("FF8000"));
	}

	@Test
	@DisplayName("trims surrounding whitespace")
	void trims() {
		assertEquals(0xFF8000, SplashColors.parse("  #FF8000  "));
	}

	@Test
	@DisplayName("rejects anything that is not exactly six hex digits")
	void rejectsMalformed() {
		assertEquals(-1, SplashColors.parse(null));
		assertEquals(-1, SplashColors.parse(""));
		assertEquals(-1, SplashColors.parse("#"));
		assertEquals(-1, SplashColors.parse("#FFF"));
		assertEquals(-1, SplashColors.parse("#FFFFFFF"));
		assertEquals(-1, SplashColors.parse("#GGGGGG"));
		assertEquals(-1, SplashColors.parse("#12345G"));
	}

	@Test
	@DisplayName("pure black and white round trip")
	void extremes() {
		assertEquals(0x000000, SplashColors.parse("#000000"));
		assertEquals(0xFFFFFF, SplashColors.parse("#FFFFFF"));
	}

	@Test
	@DisplayName("pure primaries snap onto the dark palette entries")
	void legacyCodes() {
		assertEquals('4', SplashColors.legacyCode(0xFF0000));
		assertEquals('2', SplashColors.legacyCode(0x00FF00));
		assertEquals('1', SplashColors.legacyCode(0x0000FF));
	}

	@Test
	@DisplayName("black and white map onto the legacy palette")
	void legacyGreys() {
		assertEquals('0', SplashColors.legacyCode(0x000000));
		assertEquals('f', SplashColors.legacyCode(0xFFFFFF));
		assertEquals('8', SplashColors.legacyCode(0x555555));
	}

	@Test
	@DisplayName("the nearest palette entry wins")
	void legacyNearest() {
		// 0xFA0000 is one step from dark red and two from any bright red.
		assertEquals('4', SplashColors.legacyCode(0xFA0000));
	}

	@Test
	@DisplayName("legacyPrefix prefixes the section sign")
	void legacyPrefix() {
		assertEquals("\u00a74", SplashColors.legacyPrefix(0xFF0000));
		assertTrue(SplashColors.legacyPrefix(0xFFFFFF).endsWith("f"));
	}

	@Test
	@DisplayName("every palette colour maps back to its own code")
	void paletteRoundTrip() {
		int[] palette = {
			0x000000, 0x0000AA, 0x00AA00, 0x00AAAA, 0xAA0000, 0xAA00AA, 0xFFAA00, 0xAAAAAA,
			0x555555, 0x5555FF, 0x55FF55, 0x55FFFF, 0xFF5555, 0xFF55FF, 0xFFFF55, 0xFFFFFF
		};
		char[] codes = {
			'0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c', 'd', 'e', 'f'
		};
		for (int i = 0; i < palette.length; i++) {
			int rgb = palette[i];
			char expected = codes[i];
			assertEquals(expected, SplashColors.legacyCode(rgb), () -> "colour " + rgb);
		}
	}

	@Test
	@DisplayName("negative input is clamped into the palette")
	void handlesNegativeInput() {
		// The legacy path is only reached with values produced by parse(), but the
		// method must never throw for callers using -1 as "unset".
		assertTrue(SplashColors.legacyCode(-1) >= '0' && SplashColors.legacyCode(-1) <= 'f');
	}
}
