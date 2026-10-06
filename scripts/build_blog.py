#!/usr/bin/env python3
"""
สร้างหน้าบทความบล็อกจากข้อมูลในตาราง Content (Airtable Academy base)
Build blog article pages from Content records.

สองโหมด:
  python3 scripts/build_blog.py --airtable          ดึงจาก Airtable (ต้องมี AIRTABLE_TOKEN)
  python3 scripts/build_blog.py --preview a.json     ทดสอบจากไฟล์ JSON (ไม่แตะรายการบทความ/sitemap)

โหมด --airtable สร้างหน้าเฉพาะ record ที่ติ๊ก "Publish to Website (พี่อนุมัติ)"
และมี Body ครบ ใช้ API ประมาณ 1–4 calls ต่อรอบ เพื่อให้อยู่ในโควตาแพ็กเกจฟรี
"""
import html, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = (ROOT / "scripts" / "templates" / "blog-article.html").read_text(encoding="utf-8")

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
    out.parent.mkdir(exist_ok=True)
    out.write_text(page, encoding="utf-8")
    return out




# ───────────────────────── Airtable ─────────────────────────
import os, urllib.parse, urllib.request

BASE = "apphKdT7LJHQrMmgN"                     # Academy base
T_CONTENT, T_AGENCY, T_LEGAL, T_TOPIC = (
    "tblgJAHlj749M045c", "tblS0QvcZfd0omjj9", "tblJKehxswOhFYRvP", "tblIZL4aduR6I67pw")
F = dict(  # Content field IDs — ใช้ ID แทนชื่อ เปลี่ยนชื่อช่องใน Airtable ได้โดยไม่พัง
    title="fldhfhYkYRX2ktWO0", cid="fldOWusGpTZryrcQ6", level="fldRIWNRPkTpyx2uY",
    summary="fldy05h9cUe6DmwZH", body="fldRtik6F6zSu9dAe", basis="fldaEQS2e4Pw4aIpe",
    caution="fldZDkOiglF57YRmZ", updated="fldzoXkxZUG082Zlq", agency="fldqoReKspT83IRgO",
    topic="fldpytArkY28VX3gT", legal="fld4IDEu4CUC0WrRk", publish="fldkraLFzijOHtI22",
    pubdate="fldFcFHm8QvfnYJnB")
API_CALLS = 0


def at_list(table, formula, fields):
    """ดึง record ทั้งหมดที่ตรงสูตร (100 ต่อหน้า) — นับจำนวน call ไว้รายงาน"""
    global API_CALLS
    out, offset = [], None
    while True:
        q = [("filterByFormula", formula), ("returnFieldsByFieldId", "true"), ("pageSize", "100")]
        q += [("fields[]", f) for f in fields]
        if offset:
            q.append(("offset", offset))
        req = urllib.request.Request(
            f"https://api.airtable.com/v0/{BASE}/{table}?" + urllib.parse.urlencode(q),
            headers={"Authorization": "Bearer " + os.environ["AIRTABLE_TOKEN"]})
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.load(r)
        API_CALLS += 1
        out += data["records"]
        offset = data.get("offset")
        if not offset:
            return out


def by_ids(table, ids, fields):
    if not ids:
        return {}
    formula = "OR(" + ",".join(f"RECORD_ID()='{i}'" for i in sorted(ids)) + ")"
    return {r["id"]: r["fields"] for r in at_list(table, formula, fields)}


def fetch_airtable():
    recs = at_list(T_CONTENT,
                   "AND({fldkraLFzijOHtI22}, LEN({fldRtik6F6zSu9dAe})>0, {fldOWusGpTZryrcQ6}!='')",
                   list(F.values()))
    if not recs:
        return []
    ids = lambda key: {i for r in recs for i in r["fields"].get(F[key], [])}
    agencies = by_ids(T_AGENCY, ids("agency"), ["fldPFhADVNF32slkv"])
    legal = by_ids(T_LEGAL, ids("legal"),
                   ["fldd9MHZY8YsNhmDx", "fld5lc8mMMmOXuHah", "fldQfLsjoYY0JB0cO"])
    topics = by_ids(T_TOPIC, ids("topic"), ["fldtG5eubkp8u65kz"])

    posts = []
    for r in recs:
        f = r["fields"]
        lv = f.get(F["level"])
        funnel = next((topics[t].get("fldtG5eubkp8u65kz") for t in f.get(F["topic"], [])
                       if topics.get(t, {}).get("fldtG5eubkp8u65kz")), "TOFU")
        posts.append({
            "record_id": r["id"],
            "content_id": f[F["cid"]].strip(),
            "title": f.get(F["title"], "").strip(),
            "level": lv if isinstance(lv, str) else (lv or {}).get("name", ""),
            "summary": f.get(F["summary"], "").strip(),
            "body_md": f[F["body"]],
            "legal_basis": f.get(F["basis"], ""),
            "caution_notes": f.get(F["caution"], ""),
            "updated": f.get(F["updated"]) or r["createdTime"][:10],
            "published": f.get(F["pubdate"]) or f.get(F["updated"]) or r["createdTime"][:10],
            "agency": ", ".join(agencies[a]["fldPFhADVNF32slkv"] for a in f.get(F["agency"], [])
                                if a in agencies),
            "funnel": funnel if isinstance(funnel, str) else funnel.get("name", "TOFU"),
            "legal_refs": [{"name": legal[l].get("fldd9MHZY8YsNhmDx", ""),
                            "number": legal[l].get("fld5lc8mMMmOXuHah", ""),
                            "url": legal[l]["fldQfLsjoYY0JB0cO"]}
                           for l in f.get(F["legal"], [])
                           if l in legal and legal[l].get("fldQfLsjoYY0JB0cO")],
        })
    return posts


# ─────────────────── รายการบทความ + sitemap ───────────────────
def replace_between(text, start, end, inner):
    a, b = text.index(start) + len(start), text.index(end)
    return text[:a] + inner + text[b:]


def update_listing(posts):
    cards = "".join(
        f'\n      <a class="art" href="blog/{p["content_id"].lower()}.html">'
        f'\n        <span class="meta">{html.escape(p["agency"] or "Academy")} · {thai_date(p["updated"])}</span>'
        f'\n        <h3>{html.escape(p["title"])}</h3>'
        f'\n        <p>{html.escape(p["summary"])}</p>\n      </a>'
        for p in posts)
    art = ROOT / "articles.html"
    art.write_text(replace_between(art.read_text(encoding="utf-8"),
                                   "<!-- BLOG:START -->", "<!-- BLOG:END -->", cards + "\n      "),
                   encoding="utf-8")
    urls = "".join(
        f'\n<url>\n<loc>https://madilynsecret.com/blog/{p["content_id"].lower()}.html</loc>'
        f'\n<lastmod>{p["updated"]}</lastmod>\n<changefreq>monthly</changefreq>\n<priority>0.7</priority>\n</url>'
        for p in posts)
    sm = ROOT / "sitemap.xml"
    sm.write_text(replace_between(sm.read_text(encoding="utf-8"),
                                  "<!-- BLOG:START -->", "<!-- BLOG:END -->", urls + "\n"),
                  encoding="utf-8")


def related_for(post, posts):
    same = [p for p in posts if p is not post and p["agency"] and p["agency"] == post["agency"]]
    others = [p for p in posts if p is not post and p not in same]
    picks = (same + others)[:3]
    rel = [{"href": f'{p["content_id"].lower()}.html', "label": f'บทความ · {p["agency"] or "Academy"}',
            "title": p["title"]} for p in picks]
    if len(rel) < 2:
        rel.append({"href": "../academy/", "label": "Academy", "title": "เรียนต่อใน Academy — 8 Schools ฟรี"})
    return rel


def run_airtable():
    posts = sorted(fetch_airtable(), key=lambda p: p["published"], reverse=True)
    blog = ROOT / "blog"
    keep = set()
    for p in posts:
        p["related"] = related_for(p, posts)
        keep.add(build(p).name)
    removed = []
    if blog.exists():
        for old in blog.glob("*.html"):
            if old.name not in keep:
                old.unlink()
                removed.append(old.name)
    update_listing(posts)
    print(f"published {len(posts)} | removed {len(removed)} {removed} | Airtable API calls used: {API_CALLS}")


if __name__ == "__main__":
    if sys.argv[1:2] == ["--airtable"]:
        run_airtable()
    elif sys.argv[1:2] == ["--preview"]:
        for path in sys.argv[2:]:
            print(build(json.loads(Path(path).read_text(encoding="utf-8"))))
    else:
        raise SystemExit(__doc__)
