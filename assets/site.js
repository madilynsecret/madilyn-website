/* ══════════════════════════════════════════════════════════
   Madilyn's Secret — shared script
   ══════════════════════════════════════════════════════════ */

/* ── 1. ภาษา / language ──────────────────────────────────
   ภาษาถูกเก็บไว้ใน URL (?lang=en) ไม่ใช้คุกกี้
   จึงไม่ต้องขึ้นแบนเนอร์ขอความยินยอม และแชร์ลิงก์ภาษาอังกฤษได้ตรง ๆ
------------------------------------------------------------ */
(function () {
  var params = new URLSearchParams(location.search);
  var lang = params.get("lang") === "en" ? "en" : "th";

  document.documentElement.setAttribute("lang", lang);

  // ปุ่มสลับภาษา
  document.querySelectorAll(".langsw button").forEach(function (b) {
    b.setAttribute("aria-pressed", String(b.dataset.lang === lang));
    b.addEventListener("click", function () {
      var u = new URL(location.href);
      if (b.dataset.lang === "en") u.searchParams.set("lang", "en");
      else u.searchParams.delete("lang");
      location.href = u.toString();
    });
  });

  // พาภาษาติดไปกับลิงก์ภายในเว็บด้วย
  if (lang === "en") {
    document.querySelectorAll('a[href$=".html"], a[href^="./"]').forEach(function (a) {
      var href = a.getAttribute("href");
      if (!href || href.indexOf("//") === 0 || href.indexOf("http") === 0) return;
      a.setAttribute("href", href + (href.indexOf("?") > -1 ? "&" : "?") + "lang=en");
    });
  }

  // เน้นเมนูของหน้าปัจจุบัน
  var here = location.pathname.split("/").pop() || "index.html";
  document.querySelectorAll("a.navlink").forEach(function (a) {
    var target = a.getAttribute("href").split("?")[0];
    if (target === here) a.setAttribute("aria-current", "page");
  });
})();

/* ── 2. เส้นทางการค้า / trade lanes ───────────────────── */
var LANES = {
  cn: {
    from: "GUANGZHOU", to: "BANGKOK",
    mode_th: ["ทางเรือ เต็มตู้และไม่เต็มตู้", "ทางอากาศสำหรับของด่วนหรือของมีมูลค่าสูง", "รถบรรทุกผ่านลาวสำหรับภาคเหนือ"],
    mode_en: ["Sea freight, FCL and LCL", "Air freight for urgent or high-value goods", "Cross-border trucking via Laos"],
    docs_th: ["Commercial Invoice และ Packing List", "ใบตราส่งสินค้า B/L หรือ AWB", "ใบขนสินค้าขาเข้า", "ใบอนุญาตเฉพาะสินค้า ถ้ามี"],
    docs_en: ["Commercial invoice and packing list", "Bill of lading or air waybill", "Import declaration", "Product-specific permits, if required"],
    risk_th: ["สำแดงพิกัดไม่ตรงกับของจริง", "สินค้าไฟฟ้าติดเงื่อนไข สมอ.", "ของเลียนแบบและเครื่องหมายการค้า", "ช่วงตรุษจีนโรงงานหยุดยาว"],
    risk_en: ["Declared tariff code not matching the goods", "Electrical goods subject to TISI standards", "Counterfeit and trademark issues", "Long factory shutdown at Chinese New Year"]
  },
  my: {
    from: "PUCHONG", to: "BANGKOK",
    mode_th: ["รถบรรทุกข้ามแดนผ่านสะเดาและปาดังเบซาร์", "ทางเรือเข้าท่าเรือกรุงเทพและแหลมฉบัง", "ทางอากาศสำหรับตัวอย่างสินค้า"],
    mode_en: ["Cross-border trucking via Sadao and Padang Besar", "Sea freight to Bangkok and Laem Chabang", "Air freight for samples"],
    docs_th: ["Commercial Invoice และ Packing List", "ใบขนสินค้าขาเข้า", "Form D สำหรับสิทธิอาเซียน", "ใบอนุญาตเฉพาะสินค้า ถ้ามี"],
    docs_en: ["Commercial invoice and packing list", "Import declaration", "Form D for ASEAN tariff privileges", "Product-specific permits, if required"],
    risk_th: ["ลืมขอ Form D ทำให้เสียสิทธิลดอากร", "อาหารและเครื่องสำอางต้องผ่าน อย.", "ข้อมูลผู้ส่งออกไม่ตรงกับใบกำกับ"],
    risk_en: ["Missing Form D forfeits the tariff reduction", "Food and cosmetics need Thai FDA clearance", "Exporter details not matching the invoice"]
  },
  la: {
    from: "VIENTIANE", to: "NONG KHAI",
    mode_th: ["รถบรรทุกข้ามสะพานมิตรภาพ", "ขนส่งต่อเนื่องเชื่อมกับเส้นทางจีน"],
    mode_en: ["Trucking across the Friendship Bridge", "Through-transport connecting to China lanes"],
    docs_th: ["Commercial Invoice และ Packing List", "ใบขนสินค้าขาเข้าหรือขาออก", "Form D สำหรับสิทธิอาเซียน", "ใบอนุญาตเฉพาะสินค้า ถ้ามี"],
    docs_en: ["Commercial invoice and packing list", "Import or export declaration", "Form D for ASEAN tariff privileges", "Product-specific permits, if required"],
    risk_th: ["สินค้าเกษตรต้องผ่านด่านตรวจพืชหรือสัตว์", "เวลาเปิดปิดด่านและวันหยุดราชการสองประเทศ", "การสำแดงมูลค่าที่ต่ำผิดปกติ"],
    risk_en: ["Agricultural goods need plant or animal inspection", "Border hours and public holidays in both countries", "Unusually low declared values"]
  },
  kh: {
    from: "PHNOM PENH", to: "BANGKOK",
    mode_th: ["รถบรรทุกข้ามแดนผ่านอรัญประเทศ", "ทางเรือสำหรับสินค้าปริมาณมาก"],
    mode_en: ["Cross-border trucking via Aranyaprathet", "Sea freight for bulk volumes"],
    docs_th: ["Commercial Invoice และ Packing List", "ใบขนสินค้าขาเข้าหรือขาออก", "Form D สำหรับสิทธิอาเซียน", "ใบอนุญาตเฉพาะสินค้า ถ้ามี"],
    docs_en: ["Commercial invoice and packing list", "Import or export declaration", "Form D for ASEAN tariff privileges", "Product-specific permits, if required"],
    risk_th: ["เอกสารต้นทางไม่ครบหรือไม่ตรงกัน", "สินค้าเกษตรและอาหารต้องขออนุญาตล่วงหน้า", "คิวรถหนาแน่นช่วงต้นและปลายเดือน"],
    risk_en: ["Incomplete or mismatched origin documents", "Food and agricultural goods need advance permits", "Heavy truck queues at month start and end"]
  },
  ex: {
    from: "THAILAND", to: "WORLDWIDE",
    mode_th: ["ทางเรือ เต็มตู้และไม่เต็มตู้", "ทางอากาศ", "ไปรษณีย์และเอ็กซ์เพรสสำหรับพัสดุย่อย"],
    mode_en: ["Sea freight, FCL and LCL", "Air freight", "Post and express for small parcels"],
    docs_th: ["Commercial Invoice และ Packing List", "ใบขนสินค้าขาออก", "ใบรับรองถิ่นกำเนิดสินค้า", "ใบรับรองสุขอนามัยสำหรับอาหารและพืช"],
    docs_en: ["Commercial invoice and packing list", "Export declaration", "Certificate of origin", "Health or phytosanitary certificates for food and plants"],
    risk_th: ["ประเทศปลายทางมีข้อกำหนดฉลากของตัวเอง", "สินค้าควบคุมการส่งออกบางรายการ", "การขอคืนภาษีต้องเก็บเอกสารให้ครบ"],
    risk_en: ["Destination countries have their own labelling rules", "Some goods are export-controlled", "Tax refunds require a complete document trail"]
  }
};

(function () {
  var tabs = document.querySelectorAll(".lane-tab");
  if (!tabs.length) return;
  var lang = document.documentElement.getAttribute("lang");
  var suffix = lang === "en" ? "_en" : "_th";

  function fill(id, items) {
    var el = document.getElementById(id);
    if (el) el.innerHTML = items.map(function (t) { return "<li>" + t + "</li>"; }).join("");
  }
  function setLane(key) {
    var d = LANES[key];
    document.getElementById("lane-from").textContent = d.from;
    document.getElementById("lane-to").textContent = d.to;
    fill("lane-mode", d["mode" + suffix]);
    fill("lane-docs", d["docs" + suffix]);
    fill("lane-risk", d["risk" + suffix]);
    tabs.forEach(function (b) { b.setAttribute("aria-selected", String(b.dataset.lane === key)); });
    var sel = document.getElementById("q-lane");
    if (sel) sel.value = key;
  }
  tabs.forEach(function (b) { b.addEventListener("click", function () { setLane(b.dataset.lane); }); });
  setLane("cn");
})();

/* ── 3. เผยเนื้อหาตอนเลื่อนถึง / scroll reveal ────────── */
(function () {
  var els = document.querySelectorAll(".reveal");
  if (!els.length || !("IntersectionObserver" in window)) {
    els.forEach(function (e) { e.classList.add("in"); });
    return;
  }
  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); }
    });
  }, { threshold: .12 });
  els.forEach(function (el) { io.observe(el); });
})();
