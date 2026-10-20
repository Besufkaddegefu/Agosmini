"""Extract the bot's legacy EN/AM text for comparison with the PDF catalog.

Nothing is retyped: the CONTENT dict is read with ast.literal_eval, so every
description, price and Amharic string is preserved exactly as it appeared in
the original bot. The runtime catalog is sourced from Agos_Surprise_Packages.pdf
and is stored in app/data/packages.json.

Run:  python tools/extract_content.py tools/original_main.py
"""
import ast, json, re, sys
from pathlib import Path

PACKAGES = {
    "decor_basic": "decor", "decor_deluxe": "decor", "decor_premium": "decor",
    "limo_grand": "limo", "limo_special": "limo", "limo_royal": "limo",
    "photo_digital": "photo", "photo_standard": "photo",
    "photo_premium": "photo", "videography": "photo",
}
PRICE_RE = re.compile(r"\(([\d,]+)\s*(?:ETB|ብር)\)")
LINK_RE = re.compile(r"\[[^\]]*\]\((https?://[^)\s]+)\)")


def load_content(path: Path) -> dict:
    tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            getattr(t, "id", "") == "CONTENT" for t in node.targets
        ):
            return ast.literal_eval(node.value)
    raise SystemExit("CONTENT dict not found")


def title_of(text: str) -> str:
    first = text.split("\n", 1)[0]
    first = re.sub(r"[*_]", "", first)
    first = PRICE_RE.sub("", first)
    return re.sub(r"^[^\w\u1200-\u137F]+", "", first).strip()


def main(src: str, out_dir: str = "app/data") -> None:
    content = load_content(Path(src))
    en, am = content["en"], content["am"]
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    packages = []
    for key, service in PACKAGES.items():
        m = PRICE_RE.search(en[key])
        packages.append({
            "id": key,
            "service": service,
            "price": int(m.group(1).replace(",", "")) if m else None,
            "title": {"en": title_of(en[key]), "am": title_of(am[key])},
            "text": {"en": en[key], "am": am[key]},  # verbatim originals
            "links": sorted(set(LINK_RE.findall(en[key]))),
        })
    (out / "packages_original_bot.json").write_text(
        json.dumps(packages, ensure_ascii=False, indent=2), encoding="utf-8")

    ui = {lang: {k: v for k, v in d.items() if k not in PACKAGES} for lang, d in content.items()}
    (out / "ui_strings.json").write_text(
        json.dumps(ui, ensure_ascii=False, indent=2), encoding="utf-8")

    pk = json.loads((out / "packages_original_bot.json").read_text(encoding="utf-8"))
    for p in pk:
        assert p["text"]["en"] == en[p["id"]] and p["text"]["am"] == am[p["id"]], p["id"]
    print(f"{len(pk)} packages, {len(ui['en'])} UI strings per language - verbatim check OK")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "tools/original_main.py")
