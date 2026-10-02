package dev.arrbrants.customsplash;

import java.util.List;

/**
 * A single configurable splash text with an optional weight and display conditions.
 */
public final class SplashEntry {
	public String text;
	public int weight = 1;
	public String color;
	public Conditions conditions;

	public SplashEntry() {
	}

	public SplashEntry(String text, int weight) {
		this.text = text;
		this.weight = weight;
	}

	public boolean isBlank() {
		return text == null || text.isEmpty();
	}

	public int weightOrDefault() {
		return weight > 0 ? weight : 1;
	}

	/**
	 * @return the parsed colour, or {@code -1} when unset/invalid
	 */
	public int rgb() {
		return SplashColors.parse(color);
	}

	public boolean matches(SplashContext context) {
		return conditions == null || conditions.matches(context);
	}

	/**
	 * All fields are optional. When several are present, every one must match.
	 */
	public static final class Conditions {
		public String time;
		public String date;
		public Boolean weekend;
		public List<String> player;
		public List<String> mods;
		public Double chance;

		public boolean matches(SplashContext context) {
			return matchesTime(context)
				&& matchesDate(context)
				&& matchesWeekend(context)
				&& matchesPlayer(context)
				&& matchesMods(context)
				&& matchesChance(context);
		}

		private boolean matchesTime(SplashContext context) {
			if (time == null || time.isEmpty()) {
				return true;
			}
			boolean day = context.time().getHour() >= 6 && context.time().getHour() < 18;
			if ("day".equalsIgnoreCase(time)) {
				return day;
			}
			if ("night".equalsIgnoreCase(time)) {
				return !day;
			}
			return true;
		}

		private boolean matchesDate(SplashContext context) {
			if (date == null || date.isEmpty()) {
				return true;
			}
			try {
				int today = context.date().getMonthValue() * 100 + context.date().getDayOfMonth();
				String[] range = date.split("\\.\\.");
				int start = parseMonthDay(range[0]);
				int end = range.length > 1 ? parseMonthDay(range[1]) : start;
				return start <= end ? today >= start && today <= end : today >= start || today <= end;
			} catch (RuntimeException exception) {
				return false;
			}
		}

		private static int parseMonthDay(String value) {
			String[] parts = value.trim().split("-");
			return Integer.parseInt(parts[0]) * 100 + Integer.parseInt(parts[1]);
		}

		private boolean matchesWeekend(SplashContext context) {
			if (weekend == null) {
				return true;
			}
			boolean isWeekend = context.date().getDayOfWeek().getValue() >= 6;
			return weekend == isWeekend;
		}

		private boolean matchesPlayer(SplashContext context) {
			if (player == null || player.isEmpty()) {
				return true;
			}
			String name = context.playerName();
			if (name == null) {
				return false;
			}
			for (String candidate : player) {
				if (candidate != null && candidate.equalsIgnoreCase(name)) {
					return true;
				}
			}
			return false;
		}

		private boolean matchesMods(SplashContext context) {
			if (mods == null || mods.isEmpty()) {
				return true;
			}
			for (String mod : mods) {
				if (!context.hasMod(mod)) {
					return false;
				}
			}
			return true;
		}

		private boolean matchesChance(SplashContext context) {
			return chance == null || context.roll(chance);
		}
	}
}
