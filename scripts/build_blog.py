#!/usr/bin/env python3
"""
สร้างหน้าบทความบล็อกจากข้อมูลในตาราง Content (Airtable Academy base)
Build blog article pages from Content records.

ตอนนี้ (ร่างเทมเพลต) อ่านข้อมูลจากไฟล์ JSON ใน blog/_data/
ขั้นถัดไปจะเปลี่ยนให้ดึงจาก Airtable เฉพาะบทความที่ Status = Published
และดึงแค่ตอนมีบทความใหม่ เพื่อประหยัดโควตา API แพ็กเกจฟรี

usage: python3 scripts/build_blog.py blog/_data/ct-cus-0001.json [more.json ...]
"""
import html, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = (ROOT / "blog" / "_template.html").read_text(encoding="utf-8")

TH_MONTHS = ["", "ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.",
             "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."]

CTA = {
    # TOFU = กำลังหาข้อมูล → ของฟรีก่อน ไม่ขายตรง
    "TOFU": ('<div class="box" style="text-align:center">'
             '<h2>อยากได้เช็กลิสต์เอกสารนำเข้าฉบับเต็ม (ฟรี)</h2>'
             '<p>ทักแชตมาทาง LINE หรือ Facebook แล้วพิมพ์คำว่า <strong>"เช็กลิสต์"</strong> เราจะส่งไฟล์ PDF ให้</p>'
             '<div class="cta-row" style="justify-content:center;margin-top:1rem">'
             '<a class="btn btn-teal" href="https://lin.ee/JryPwpiH" target="_blank" rel="noopener">ทักทาง LINE</a>'
             '<a class="btn btn-ghost" href="https://m.me/madilynsecretimportexport" target="_blank" rel="noopener">ทักทาง Facebook</a>'
             '</div></div>'),
    # MOFU = กำลังเปรียบเทียบ → บทเรียนต่อยอดใน Academy
    "MOFU": ('<div class="cta-row" style="margin-top:2rem">'
             '<a class="btn btn-teal" href="../academy/">เรียนต่อใน Academy</a>'
             '<a class="btn btn-ghost" href="../articles.html">บทความอื่น</a></div>'),
    # BOFU = พร้อมใช้บริการ → ใบเสนอราคา
    "BOFU": ('<div class="cta-row" style="margin-top:2rem">'
             '<a class="btn btn-gold" href="../services.html#quote">ให้เราช่วยดูสินค้าของคุณ</a>'
             '<a class="btn btn-ghost" href="../articles.html">บทความอื่น</a></div>'),
}


def thai_date(iso):
    y, m, d = (int(x) for x in iso.split("-"))
    return f"{d} {TH_MONTHS[m]} {y + 543}"


def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"\[(.+?)\]\((https?://[^)\s]+)\)",
               r'<a href="\2" target="_blank" rel="noopener">\1</a>', s)
    return s


def md_to_html(md):
    """Markdown แบบย่อ: หัวข้อ ## / ###, รายการ 1. / - / •, ตัวหนา, ลิงก์, ย่อหน้า"""
    out, lst = [], None
    def close():
        nonlocal lst
        if lst:
            out.append(f"</{lst}>")
            lst = None
    for raw in md.splitlines():
        line = raw.strip()
        if not line:
            close(); continue
        m = re.match(r"^(#{2,3})\s+(.*)", line)
        if m:
            close()
            n = len(m.group(1))
            out.append(f"<h{n}>{inline(m.group(2))}</h{n}>"); continue
        m = re.match(r"^\d+[.)]\s+(.*)", line)
        if m:
            if lst != "ol": close(); out.append("<ol>"); lst = "ol"
            out.append(f"<li>{inline(m.group(1))}</li>"); continue
        m = re.match(r"^[-•*]\s+(.*)", line)
        if m:
            if lst != "ul": close(); out.append("<ul>"); lst = "ul"
            out.append(f"<li>{inline(m.group(1))}</li>"); continue
        close()
        out.append(f"<p>{inline(line)}</p>")
    close()
    return "\n".join(out)


def build(rec):
    slug = rec["content_id"].lower()
    refs = rec.get("legal_refs", [])

    verify = ('<span class="chip ok">✓ มีแหล่งอ้างอิงทางการ</span>' if refs else
              '<span class="chip check">ต้องตรวจสอบเพิ่มเติมรายกรณี</span>')

    legal = ""
    if rec.get("legal_basis") or refs:
        items = "".join(
            f'<li><a href="{html.escape(r["url"])}" target="_blank" rel="noopener">{html.escape(r["name"])}</a>'
            + (f'<br><small style="opacity:.6">{html.escape(r["number"])}</small>' if r.get("number") else "")
            + "</li>" for r in refs)
        legal = ('<div class="box legal"><h2>หลักกฎหมายที่เกี่ยวข้อง</h2>'
                 + (f"<p>{inline(rec['legal_basis'])}</p>" if rec.get("legal_basis") else "")
                 + (f'<p class="small" style="margin:.8rem 0 .2rem">แหล่งอ้างอิง (อ่านฉบับเต็มได้ที่ต้นทาง)</p><ul class="sources">{items}</ul>' if refs else "")
                 + "</div>")

    caution = ""
    if rec.get("caution_notes"):
        # ตัดย่อหน้า disclaimer ที่ซ้ำกับกล่อง disclaimer มาตรฐานด้านล่างออก
        lines = [l for l in rec["caution_notes"].splitlines()
                 if "ไม่ใช่คำแนะนำทางกฎหมาย" not in l]
        caution = ('<div class="box caution"><h2>ข้อควรระวัง</h2>'
                   + md_to_html("\n".join(lines)) + "</div>")

    related = ""
    if rec.get("related"):
        links = "".join(
            f'<a href="{html.escape(r["href"])}"><small>{html.escape(r.get("label", "บทความ"))}</small>{html.escape(r["title"])}</a>'
            for r in rec["related"])
        related = f'<div style="margin-top:2.6rem"><h2 style="font-size:var(--fs-h3)">อ่านต่อ</h2><div class="related">{links}</div></div>'

    jsonld = json.dumps({
        "@context": "https://schema.org", "@type": "Article",
        "headline": rec["title"], "description": rec["summary"],
        "inLanguage": "th", "dateModified": rec["updated"],
        "datePublished": rec.get("published", rec["updated"]),
        "mainEntityOfPage": f"https://madilynsecret.com/blog/{slug}.html",
        "image": "https://madilynsecret.com/og-image.png",
        "author": {"@type": "Organization", "name": "Madilyn's Secret Academy"},
        "publisher": {"@type": "Organization", "name": "Madilyn's Secret (Thailand) Co., Ltd.",
                      "logo": {"@type": "ImageObject", "url": "https://madilynsecret.com/apple-touch-icon-180.png"}},
        "citation": [r["url"] for r in refs],
    }, ensure_ascii=False, indent=1)

    level = rec.get("level", "").replace("Level 1 - Foundation", "ระดับพื้นฐาน") \
        .replace("Level 2 - Professional", "ระดับมืออาชีพ") \
        .replace("Level 3 - Specialist", "ระดับเชี่ยวชาญ") \
        .replace("Level 4 - Expert", "ระดับผู้เชี่ยวชาญ")

    page = TEMPLATE
    for k, v in {
        "title": html.escape(rec["title"]),
        "summary_attr": html.escape(rec["summary"]),
        "summary": html.escape(rec["summary"]),
        "slug": slug,
        "agency": html.escape(rec.get("agency", "")),
        "level": html.escape(level),
        "verify_chip": verify,
        "updated_th": thai_date(rec["updated"]),
        "content_id": html.escape(rec["content_id"]),
        "body_html": md_to_html(rec["body_md"]),
        "legal_box": legal,
        "caution_box": caution,
        "cta_block": CTA.get(rec.get("funnel", "TOFU"), CTA["TOFU"]),
        "related_block": related,
        "jsonld": jsonld,
    }.items():
        page = page.replace("{{" + k + "}}", v)
    left = re.findall(r"\{\{\w+\}\}", page)
    if left:
        raise SystemExit(f"placeholders not filled: {left}")
    out = ROOT / "blog" / f"{slug}.html"
    out.write_text(page, encoding="utf-8")
    return out


if __name__ == "__main__":
    for p in sys.argv[1:]:
        print(build(json.loads(Path(p).read_text(encoding="utf-8"))))
