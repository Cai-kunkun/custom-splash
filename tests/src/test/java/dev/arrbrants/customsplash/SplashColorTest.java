package dev.arrbrants.customsplash;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;

/**
 * Covers {@link SplashColor} parsing plus gradient and rainbow sampling.
 */
class SplashColorTest {
	private static final int RED = 0xFF0000;
	private static final int GREEN = 0x00FF00;
	private static final int BLUE = 0x0000FF;

	@Nested
	@DisplayName("parsing")
	class Parsing {
		@Test
		@DisplayName("#RRGGBB becomes a solid colour")
		void solidHex() {
			SplashColor color = SplashColor.parse("#FF8000");
			assertNotNull(color);
			assertTrue(color.isSolid());
			assertEquals(0xFF8000, color.solidRgb());
		}

		@Test
		@DisplayName("a comma separated list becomes a gradient")
		void gradientList() {
			SplashColor color = SplashColor.parse("#FF0000,#0000FF");
			assertNotNull(color);
			assertFalse(color.isSolid());
			assertEquals(-1, color.solidRgb());
			int[] colors = color.colorsFor("ab");
			assertEquals(RED, colors[0]);
			assertEquals(BLUE, colors[1]);
		}

		@Test
		@DisplayName("the gradient: prefix is accepted on the first stop")
		void gradientPrefix() {
			SplashColor color = SplashColor.parse("gradient:#FF0000,#00FF00");
			assertNotNull(color);
			assertFalse(color.isSolid());
			int[] colors = color.colorsFor("ab");
			assertEquals(RED, colors[0]);
			assertEquals(GREEN, colors[1]);
		}

		@Test
		@DisplayName("a single stop gradient is still solid")
		void singleStopIsSolid() {
			SplashColor color = SplashColor.parse("#FF0000");
			assertNotNull(color);
			assertTrue(color.isSolid());
			assertEquals(RED, color.colorsFor("hello")[0]);
		}

		@Test
		@DisplayName("rainbow defaults to a 15 degree spread per character")
		void rainbowDefaultSpread() {
			SplashColor color = SplashColor.parse("rainbow");
			assertNotNull(color);
			assertFalse(color.isSolid());
			int[] colors = color.colorsFor("ab");
			assertEquals(RED, colors[0]);
			assertEquals(0xFF4000, colors[1]);
		}

		@Test
		@DisplayName("rainbow accepts an explicit degree spread")
		void rainbowExplicitSpread() {
			SplashColor color = SplashColor.parse("rainbow:90");
			assertNotNull(color);
			int[] colors = color.colorsFor("ab");
			assertEquals(RED, colors[0]);
			assertEquals(0x80FF00, colors[1]);
		}

		@Test
		@DisplayName("rainbow is case insensitive")
		void rainbowCaseInsensitive() {
			assertNotNull(SplashColor.parse("RAINBOW"));
			assertNotNull(SplashColor.parse("Rainbow:45"));
		}

		@Test
		@DisplayName("blank, null and malformed values are rejected")
		void rejectsInvalidInput() {
			assertNull(SplashColor.parse(null));
			assertNull(SplashColor.parse(""));
			assertNull(SplashColor.parse("   "));
			assertNull(SplashColor.parse("#GGGGGG"));
			assertNull(SplashColor.parse("#FFF"));
			assertNull(SplashColor.parse("#FF0000,not-a-colour"));
			assertNull(SplashColor.parse("rainbow:"));
			assertNull(SplashColor.parse("rainbow:abc"));
			assertNull(SplashColor.parse("rainbow:361"));
			assertNull(SplashColor.parse("rainbow:-5"));
		}

		@Test
		@DisplayName("surrounding whitespace is ignored")
		void trimsWhitespace() {
			assertNotNull(SplashColor.parse("  #FF8000  "));
			assertNotNull(SplashColor.parse(" #FF0000 , #00FF00 "));
		}

		@Test
		@DisplayName("whitespace and the gradient prefix do not change the stops")
		void equivalentInputsAgree() {
			int[] expected = SplashColor.parse("#FF0000,#00FF00").colorsFor("abc");
			assertArrayEquals(expected, SplashColor.parse("gradient:#FF0000,#00FF00").colorsFor("abc"));
			assertArrayEquals(expected, SplashColor.parse(" #FF0000 , #00FF00 ").colorsFor("abc"));
		}
	}

	@Nested
	@DisplayName("colorsFor")
	class ColorsFor {
		@Test
		@DisplayName("returns one entry per character")
		void oneEntryPerCharacter() {
			assertEquals(6, SplashColor.parse("rainbow").colorsFor("splash").length);
			assertEquals(0, SplashColor.parse("rainbow").colorsFor("").length);
		}

		@Test
		@DisplayName("a solid colour fills every slot")
		void solidFills() {
			int[] colors = SplashColor.parse("#FF0000").colorsFor("abc");
			assertEquals(RED, colors[0]);
			assertEquals(RED, colors[1]);
			assertEquals(RED, colors[2]);
		}

		@Test
		@DisplayName("the gradient endpoints match the stops exactly")
		void gradientEndpoints() {
			int[] colors = SplashColor.parse("#FF0000,#00FF00,#0000FF").colorsFor("abcde");
			assertEquals(RED, colors[0]);
			// Quarter way between red and green.
			assertEquals(0x808000, colors[1]);
			// Exactly the middle stop.
			assertEquals(GREEN, colors[2]);
			// Halfway between green and blue.
			assertEquals(0x008080, colors[3]);
			// Exactly the last stop.
			assertEquals(BLUE, colors[4]);
		}

		@Test
		@DisplayName("a single character gradient is just the first stop")
		void singleCharacterGradient() {
			int[] colors = SplashColor.parse("#FF0000,#0000FF").colorsFor("a");
			assertEquals(1, colors.length);
			assertEquals(RED, colors[0]);
		}

		@Test
		@DisplayName("interpolation stays inside the channel range")
		void staysInRange() {
			for (int rgb : SplashColor.parse("#000000,#123456,#FFFFFF").colorsFor("abcdefg")) {
				assertInRange(rgb);
			}
		}

		@Test
		@DisplayName("rainbow cycles instead of escaping the channel range")
		void rainbowCycles() {
			// 40 degrees per character times nine characters is a full turn.
			int[] colors = SplashColor.parse("rainbow:40").colorsFor("0123456789");
			assertEquals(10, colors.length);
			for (int rgb : colors) {
				assertInRange(rgb);
			}
			assertEquals(RED, colors[9]);
		}

		@Test
		@DisplayName("a rainbow with a zero spread is a flat colour")
		void rainbowZeroSpread() {
			int[] colors = SplashColor.parse("rainbow:0").colorsFor("abc");
			assertEquals(RED, colors[0]);
			assertEquals(RED, colors[1]);
			assertEquals(RED, colors[2]);
		}

		@Test
		@DisplayName("a solid colour keeps its channels through colorsFor")
		void solidThroughColorsFor() {
			int[] colors = SplashColor.parse("#3366CC").colorsFor("hi");
			assertEquals(0x3366CC, colors[0]);
			assertEquals(0x3366CC, colors[1]);
		}

		private void assertInRange(int rgb) {
			assertTrue(rgb >= 0 && rgb <= 0xFFFFFF, () -> "out of range: " + rgb);
		}
	}
}
