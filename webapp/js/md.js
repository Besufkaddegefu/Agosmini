// Renders the bot's original Telegram-Markdown strings (kept verbatim) as safe HTML.
const esc = (s) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");

function inline(line) {
  let s = esc(line);
  const kept = [];
  const keep = (html) => `\u0000${kept.push(html) - 1}\u0000`;
  s = s.replace(/\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)/g, (_, t, u) => keep(`<a href="${u}">${t}</a>`));          // [text](url)
  s = s.replace(/https?:\/\/[^\s<)*]+/g, (u) => keep(`<a href="${u}">${u.replace(/^https?:\/\/(www\.)?/, "")}</a>`)); // bare URLs
  s = s.replace(/\+251(?:[\s-]?\d){9}/g, (p) => keep(`<a href="tel:${p.replace(/[\s-]/g, "")}">${p}</a>`));          // phone numbers
  s = s.replace(/••\s*([^•]+?)\s*••/g, "<strong>$1</strong>");   // legacy marker ••Title••
  s = s.replace(/•([^•:\n]+:)•?/g, "<strong>$1</strong>");       // legacy marker •Label:•
  s = s.replace(/\*([^*\n]+)\*/g, "<strong>$1</strong>");
  s = s.replace(/•\s*/g, "");
  return s.replace(/\u0000(\d+)\u0000/g, (_, i) => kept[+i]);
}

export function renderMd(text) {
  const out = [];
  let list = [];
  const flush = () => { if (list.length) { out.push(`<ul>${list.map((l) => `<li>${l}</li>`).join("")}</ul>`); list = []; } };
  for (const raw of String(text).split("\n")) {
    const line = raw.trimEnd();
    if (/^_{5,}$/.test(line.trim()) || /^[━─]{5,}$/.test(line.trim())) { flush(); out.push("<hr>"); continue; }
    const bullet = line.match(/^\s*[•\-]\s*(.+)$/);
    if (bullet && !/^\s*•[^•:\n]+:•?/.test(line) && !/^\s*••/.test(line)) { list.push(inline(bullet[1])); continue; }
    flush();
    if (!line.trim()) { out.push('<div class="gap"></div>'); continue; }
    const italic = line.trim().match(/^_(.+)_$/);
    out.push(italic ? `<p><em>${inline(italic[1])}</em></p>` : `<p>${inline(line)}</p>`);
  }
  flush();
  return out.join("");
}

// First bullet lines of a package text (verbatim) for the card preview.
export function previewBullets(text, max = 4) {
  const out = [];
  let started = false;
  for (const l of String(text).split("\n")) {
    const m = l.match(/^\s*•\s*(.+)$/);
    if (m) { started = true; out.push(m[1].replace(/\*/g, "")); if (out.length >= max) break; }
    else if (started) break;
  }
  return out;
}
