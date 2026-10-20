// Ethiopian calendar helpers (mirror of app/ethcal.py).
export const MONTHS = [
  ["Meskerem", "መስከረም"], ["Tikimt", "ጥቅምት"], ["Hidar", "ኅዳር"], ["Tahsas", "ታኅሣሥ"], ["Tir", "ጥር"],
  ["Yekatit", "የካቲት"], ["Megabit", "መጋቢት"], ["Miazia", "ሚያዝያ"], ["Ginbot", "ግንቦት"], ["Sene", "ሰኔ"],
  ["Hamle", "ሐምሌ"], ["Nehase", "ነሐሴ"], ["Pagume", "ጳጉሜን"],
];
export const PERIODS = [
  ["morning", "Morning", "ጥዋት"], ["afternoon", "Afternoon", "ከሰዓት"], ["evening", "Evening", "ማታ"], ["night", "Night", "ሌሊት"],
];
const OFFSET = 1723856, DAY_MS = 86400000, JDN_UNIX_EPOCH = 2440588; // JDN of 1970-01-01

export const isLeap = (y) => y % 4 === 3;
export const daysIn = (y, m) => (m <= 12 ? 30 : isLeap(y) ? 6 : 5);

export function toGregorian(y, m, d) {            // returns a Date at UTC midnight
  const jdn = OFFSET + 365 * y + Math.floor(y / 4) + 30 * m + d - 31;
  return new Date((jdn - JDN_UNIX_EPOCH) * DAY_MS);
}
export function fromGregorian(date) {             // local calendar date -> Ethiopian
  const jdn = Math.floor(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()) / DAY_MS) + JDN_UNIX_EPOCH;
  const r = (jdn - OFFSET) % 1461;
  const n = (r % 365) + 365 * Math.floor(r / 1460);
  return { year: 4 * Math.floor((jdn - OFFSET) / 1461) + Math.floor(r / 365) - Math.floor(r / 1460), month: Math.floor(n / 30) + 1, day: (n % 30) + 1 };
}
export const fmtGregorian = (d) => d.toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric", timeZone: "UTC" });
