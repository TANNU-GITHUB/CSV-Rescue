export function greeting(now = new Date()): { text: string; emoji: string } {
  const h = now.getHours();
  if (h >= 5 && h < 12) return { text: "Good Morning", emoji: "☀️" };
  if (h >= 12 && h < 17) return { text: "Good Afternoon", emoji: "🌤️" };
  return { text: "Good Evening", emoji: "🌙" };
}
