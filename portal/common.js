// Madilyn's Secret — member portal shared module (Firebase + tiers + rates)
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.2/firebase-app.js";
import { getAuth } from "https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js";
import { getFirestore } from "https://www.gstatic.com/firebasejs/10.12.2/firebase-firestore.js";

export const firebaseConfig = {
  apiKey: "AIzaSyDOfGo0c6RW16UOROQjMl494xpP8CqKk40",
  authDomain: "madilyn-freight-portal.firebaseapp.com",
  projectId: "madilyn-freight-portal",
  storageBucket: "madilyn-freight-portal.firebasestorage.app",
  messagingSenderId: "1041385261197",
  appId: "1:1041385261197:web:e5c543e0afabc0dda63ac4"
};

export const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const db = getFirestore(app);

export const LINE_OA = "https://lin.ee/JryPwpiH";
export const MEMBER_DOMAIN = "member.madilynsecret.com";
export const codeToEmail = (code) => `${String(code).trim().toLowerCase()}@${MEMBER_DOMAIN}`;
export const emailToCode = (email) => String(email || "").split("@")[0].toUpperCase();
export const isMemberEmail = (email) => String(email || "").endsWith("@" + MEMBER_DOMAIN);

// ---------------------------------------------------------------- membership tiers
// Same rule for both routes. Spend = shipping charges (freight + fee) in THB over the last 12 months.
export const TIERS = {
  order: ["Silver", "Gold", "Platinum"],
  min: { Silver: 0, Gold: 20000, Platinum: 60000 },   // reach this 12-month spend -> upgrade
  keep: { Silver: 0, Gold: 10000, Platinum: 30000 },  // annual review (January): below this -> down one level
  firstReview: "2028-01-01",
  label: { Silver: "สมาชิกทั่วไป", Gold: "ลูกค้าประจำ", Platinum: "ลูกค้าคนสำคัญ" },
  perks: {
    Silver: ["เรตค่าขนส่งระดับ Silver", "ติดตามสถานะพัสดุออนไลน์"],
    Gold: ["เรตค่าขนส่งระดับ Gold (ถูกกว่า Silver)", "ตอบแชท LINE ก่อน", "ติดตามสถานะพัสดุออนไลน์"],
    Platinum: ["เรตค่าขนส่งต่ำสุด", "ผู้ดูแลเฉพาะ", "ปรึกษาพิกัดศุลกากร/ใบอนุญาตเบื้องต้นฟรี", "ติดตามสถานะพัสดุออนไลน์"]
  }
};
export const tierRank = (t) => Math.max(0, TIERS.order.indexOf(t));
export const tierFromSpend = (s) => (s >= TIERS.min.Platinum ? "Platinum" : s >= TIERS.min.Gold ? "Gold" : "Silver");

export function daysAgoISO(days, now = new Date()) {
  const d = new Date(now.getTime() - days * 86400000);
  return d.toISOString().slice(0, 10);
}
export function spend12(shipments, now = new Date()) {
  const from = daysAgoISO(365, now);
  return shipments.filter((s) => (s.receivedDate || "") >= from).reduce((a, s) => a + (Number(s.total) || 0), 0);
}
export function nextTierInfo(tier, s12) {
  const i = tierRank(tier);
  if (i >= TIERS.order.length - 1) return null;
  const next = TIERS.order[i + 1];
  const need = Math.max(0, TIERS.min[next] - s12);
  const pct = Math.min(100, Math.round((s12 / TIERS.min[next]) * 100));
  return { next, need, pct };
}

// ---------------------------------------------------------------- rates (THB) — keep in sync with the workbook
export const RATES = {
  TWM: { // category: [kg, cbm] per tier
    "สินค้าทั่วไป (By Sea)": { Silver: [35, 5500], Gold: [30, 5200], Platinum: [25, 4500] },
    "สินค้ามอก. อย. (By Sea)": { Silver: [75, 8500], Gold: [38, 7500], Platinum: [55, 6500] },
    "สินค้าพิเศษ (By Sea)": { Silver: [95, 13500], Gold: [65, 12500], Platinum: [65, 11500] },
    "สินค้าทั่วไป (By Land)": { Silver: [45, 8000], Gold: [35, 7500], Platinum: [30, 7000] },
    "สินค้ามอก. อย. (By Land)": { Silver: [85, 11900], Gold: [70, 10000], Platinum: [65, 9000] },
    "สินค้าพิเศษ (By Land)": { Silver: [120, 17500], Gold: [90, 14500], Platinum: [100, 13500] }
  },
  TWM_FEE_PER_KG: 10,
  MSL: { // truck only, both directions
    "General (ทางรถ)": { Silver: [26, 6400], Gold: [23, 5700], Platinum: [21, 5200] },
    "Restrict / Fragile (ทางรถ)": { Silver: [34, 8400], Gold: [30, 7500], Platinum: [28, 6800] }
  },
  MSL_MIN_CBM: 0.5,
  MSL_KG_PER_CBM: 250
};

export function calcCharge(route, kg, cbm, rateKg, rateCbm) {
  kg = Number(kg) || 0; cbm = Number(cbm) || 0;
  if (route === "MSL") {
    const chargeable = Math.max(cbm, kg / RATES.MSL_KG_PER_CBM, RATES.MSL_MIN_CBM);
    const freight = Math.round(chargeable * rateCbm * 100) / 100;
    return { freight, fee: 0, total: freight, chargeableCbm: Math.round(chargeable * 10000) / 10000 };
  }
  const freight = Math.round(Math.max(kg * rateKg, cbm * rateCbm) * 100) / 100;
  const fee = Math.round(kg * RATES.TWM_FEE_PER_KG * 100) / 100;
  return { freight, fee, total: Math.round((freight + fee) * 100) / 100 };
}

export const STATUSES = ["รับของเข้าโกดังต้นทาง", "กำลังขนส่ง", "ถึงโกดังปลายทาง", "รอจัดส่ง", "จัดส่งแล้ว"];
export const ROUTE_NAME = { TWM: "จีน → ไทย", MSL: "ไทย ↔ มาเลเซีย" };

export const fmt = (n, d = 0) => Number(n || 0).toLocaleString("th-TH", { minimumFractionDigits: d, maximumFractionDigits: Math.max(d, 2) });
export function fmtDate(iso) {
  if (!iso) return "—";
  const [y, m, d] = iso.split("-");
  return `${d}/${m}/${y}`;
}
export function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
export function $(sel, root = document) { return root.querySelector(sel); }
export function show(el, on = true) { (typeof el === "string" ? $(el) : el).hidden = !on; }

export function authErrorTH(e) {
  const c = e && e.code ? e.code : "";
  if (c.includes("invalid-credential") || c.includes("wrong-password") || c.includes("user-not-found") || c.includes("invalid-email"))
    return "รหัสสมาชิกหรือรหัสผ่านไม่ถูกต้อง";
  if (c.includes("too-many-requests")) return "ลองผิดหลายครั้งเกินไป กรุณารอสักครู่แล้วลองใหม่";
  if (c.includes("weak-password")) return "รหัสผ่านสั้นเกินไป (อย่างน้อย 8 ตัวอักษร)";
  if (c.includes("requires-recent-login")) return "กรุณาออกจากระบบแล้วเข้าใหม่ก่อนเปลี่ยนรหัสผ่าน";
  if (c.includes("network")) return "เชื่อมต่ออินเทอร์เน็ตไม่ได้ กรุณาลองใหม่";
  if (c.includes("permission-denied")) return "ไม่มีสิทธิ์เข้าถึงข้อมูลนี้";
  return "เกิดข้อผิดพลาด: " + (e && e.message ? e.message : c);
}
