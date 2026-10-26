import { renderMd, previewBullets } from "./md.js";
import * as E from "./ethcal.js";
import * as api from "./api.js";

const tg = window.Telegram?.WebApp;
const $ = (s, el = document) => el.querySelector(s);
const esc = (s) => String(s ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
const app = $("#app");
const SERVICES = ["decor", "limo", "photo"];

// New UI labels only. Every original bot text (packages, welcome, contact, notices) comes from /api/config.
const T = {
  en: { next: "Next", back: "Back", submit: "Submit booking", sending: "Sending…", s1: "Your info", s2: "Details", s3: "Payment", details: "Details",
    day: "Day", month: "Month", year: "Year", hour: "Hour", period: "Time of day", gregorian: "Gregorian date",
    req: "This field is required", badphone: "Enter a valid phone number", baduser: "Enter a valid Telegram username (e.g. @username)",
    past: "The date can't be in the past", baddate: "Please choose a valid date", needpkg: "Please select a package", needshot: "Please upload your payment screenshot",
    pkgprice: "Package price", deposit: "Deposit to pay now (50%)", balance: "Balance on the day of service", copy: "Copy", copied: "Copied ✓",
    acct: "Account number", acctname: "Account name", bank: "Bank", tap: "Tap to choose a screenshot", change: "Change photo",
    received: "Booking received!", pdfsent: "Your booking summary (PDF) was sent to this chat.",
    pdfno: "We couldn't send the PDF to your chat. Please press Start in the bot chat, or contact us.", catsent: "Catalog sent to your chat ✅",
    failed: "Something went wrong. Please try again.", delivery: "We couldn't reach our team just now. Please call us.", rate: "Too many bookings. Please try again later.",
    unauth: "Please open this app from Telegram.", retry: "Try again", checkagain: "🔄 Check Again", call: "📞 Call", from: "From",
    choosepkg: "👇 Choose a package to book:", bookingClosed: "Booking unavailable during working hours", fixfields: "Please check the highlighted fields", dev: "Dev" },
  am: { next: "ቀጣይ", back: "ተመለስ", submit: "ትዕዛዙን ላክ", sending: "በመላክ ላይ…", s1: "የእርስዎ መረጃ", s2: "ዝርዝር", s3: "ክፍያ", details: "ዝርዝር",
    day: "ቀን", month: "ወር", year: "ዓመት", hour: "ሰዓት", period: "የቀኑ ክፍል", gregorian: "የግሪጎሪያን ቀን",
    req: "ይህ መስክ ያስፈልጋል", badphone: "ትክክለኛ ስልክ ቁጥር ያስገቡ", baduser: "ትክክለኛ የቴሌግራም መለያ ያስገቡ (ለምሳሌ፡ @username)",
    past: "ያለፈ ቀን መምረጥ አይቻልም", baddate: "ትክክለኛ ቀን ይምረጡ", needpkg: "እባክዎ ፓኬጅ ይምረጡ", needshot: "እባክዎ የክፍያ ስክሪን ሾት ይላኩ",
    pkgprice: "የፓኬጅ ዋጋ", deposit: "አሁን የሚከፈል ተቀማጭ (50%)", balance: "በአገልግሎቱ ቀን የሚከፈል ቀሪ", copy: "ቅዳ", copied: "ተቀድቷል ✓",
    acct: "የአካውንት ቁጥር", acctname: "የአካውንት ስም", bank: "ባንክ", tap: "ስክሪን ሾት ለመምረጥ ይንኩ", change: "ፎቶ ቀይር",
    received: "ትዕዛዝዎ ደርሶናል!", pdfsent: "የትዕዛዝዎ ማጠቃለያ (PDF) ወደዚህ ቻት ተልኳል።",
    pdfno: "PDFውን ወደ ቻትዎ መላክ አልተቻለም። እባክዎ በቦቱ ቻት Start ይጫኑ ወይም ያግኙን።", catsent: "የአገልግሎት ዝርዝሩ ወደ ቻትዎ ተልኳል ✅",
    failed: "ችግር ተፈጥሯል። እባክዎ እንደገና ይሞክሩ።", delivery: "አሁን ቡድናችንን ማግኘት አልተቻለም። እባክዎ ይደውሉልን።", rate: "ብዙ ትዕዛዞች ተልከዋል። እባክዎ ቆየት ብለው ይሞክሩ።",
    unauth: "እባክዎ ይህንን መተግበሪያ ከቴሌግራም ይክፈቱ።", retry: "እንደገና ይሞክሩ", checkagain: "🔄 እንደገና ይፈትሹ", call: "📞 ይደውሉ", from: "ከ",
    choosepkg: "👇 ለማዘዝ አንዱን ይምረጡ፦", bookingClosed: "በስራ ሰዓት ማዘዝ አይቻልም", fixfields: "እባክዎ ምልክት የተደረገባቸውን መስኮች ያስተካክሉ", dev: "Dev" },
};

const S = {
  cfg: null, cfgAt: 0, form: null, done: null,
  lang: localStorage.getItem("agos_lang") || (tg?.initDataUnsafe?.user?.language_code === "am" ? "am" : "en"),
  booked: JSON.parse(localStorage.getItem("agos_booked") || "[]"),
};
const t = (k) => T[S.lang][k] ?? T.en[k] ?? k;
const ui = (k) => S.cfg.ui[S.lang][k];
const stripEmoji = (s) => s.replace(/^[^\p{L}\p{N}]+/u, "");
const money = (n) => (S.lang === "am" ? `${n.toLocaleString("en-US")} ብር` : `${n.toLocaleString("en-US")} ETB`);
const pkgs = (svc) => S.cfg.packages.filter((p) => p.service === svc);
const pkg = (id) => S.cfg.packages.find((p) => p.id === id);
const buzz = () => { try { tg?.HapticFeedback?.impactOccurred("light"); } catch { /* old client */ } };
const nav = (path) => { location.hash = "#/" + path; };

// ---- Telegram chrome ----
if (tg) { tg.ready(); tg.expand(); try { tg.disableVerticalSwipes?.(); } catch { /* old client */ } }
const scheme = () => tg?.colorScheme || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
function applyTheme() {
  document.documentElement.dataset.theme = scheme();
  const bg = getComputedStyle(document.documentElement).getPropertyValue("--bg").trim();
  try { tg?.setHeaderColor?.(bg); tg?.setBackgroundColor?.(bg); } catch { /* old client */ }
}
applyTheme(); tg?.onEvent?.("themeChanged", applyTheme);

function toast(msg, bad = false) {
  const el = $("#toast"); el.textContent = msg; el.className = "toast" + (bad ? " err" : ""); el.hidden = false;
  clearTimeout(toast.t); toast.t = setTimeout(() => (el.hidden = true), 3200);
}

async function loadConfig(force = false) {
  if (S.cfg && !force && Date.now() - S.cfgAt < 60000) return;
  S.cfg = await api.getConfig(); S.cfgAt = Date.now();
}
const offline = () => S.cfg?.hours?.offline;
function route() { const [view = "", a, b, c] = location.hash.replace(/^#\/?/, "").split("/"); return { view, a, b, c }; }
const curStep = () => Math.min(3, Math.max(1, +route().c || 1));

// ---- render ----
async function render(keep = false) {
  const r = route(), y = window.scrollY;
  if (!keep) {
    app.innerHTML = '<div class="skel"></div><div class="skel"></div><div class="skel"></div>';
    try { await loadConfig(r.view === ""); } catch (e) { return renderError(e); }
  }
  document.querySelectorAll(".seg button").forEach((b) => b.classList.toggle("on", b.dataset.lang === S.lang));
  document.documentElement.lang = S.lang;
  let html = "", bar = null;
  if (offline() && r.view === "book") ({ html, bar } = screenClosed());
  else if (r.view === "svc" && SERVICES.includes(r.a)) html = screenService(r.a);
  else if (r.view === "pkg" && pkg(r.a)) ({ html, bar } = screenPackage(r.a));
  else if (r.view === "book" && SERVICES.includes(r.a) && pkg(r.b) && pkg(r.b).service === r.a) ({ html, bar } = screenBooking(r.a, r.b, curStep()));
  else if (r.view === "contact") html = screenContact();
  else if (r.view === "done" && S.done) ({ html, bar } = screenDone());
  else html = screenHome();
  app.innerHTML = `<div class="screen${keep ? " still" : ""}">${html}</div>`;
  setBar(bar);
  if (r.view === "book" && !offline()) hydrateDate();
  window.scrollTo(0, keep ? y : 0);
  const home = !["svc", "pkg", "book", "contact"].includes(r.view);
  try { home ? tg?.BackButton?.hide() : tg?.BackButton?.show(); } catch { /* old client */ }
}

function renderError(e) {
  app.innerHTML = `<div class="card center"><h2>⚠️</h2><p>${esc(e.status === 401 ? t("unauth") : t("failed"))}</p><button class="btn" data-act="reload">${t("retry")}</button></div>`;
  setBar(null);
}
function setBar(b) {
  const bar = $("#bar");
  if (!b) { bar.hidden = true; document.body.classList.remove("has-bar"); return; }
  bar.innerHTML = `<div>${b}</div>`; bar.hidden = false; document.body.classList.add("has-bar");
}

// ---- screens ----
const crumb = (to, label) => `<div class="crumb"><button data-go="${to}">← ${esc(label)}</button></div>`;

function screenHome() {
  const b = ui("btns");
  const from = (svc) => `${t("from")} ${money(Math.min(...pkgs(svc).map((p) => p.price)))}`;
  const tile = (svc, i, ic) => `<button class="tile" data-go="svc/${svc}"><span class="ic">${ic}</span><span><b>${esc(stripEmoji(b[i]))}</b><small>${from(svc)}</small></span><span class="chev">›</span></button>`;
  return `${offline() ? offlineNotice() : ""}<section class="card hero rich">${renderMd(ui("welcome"))}</section>
    <div class="tiles">${tile("decor", 0, "🎁")}${tile("limo", 1, "🚗")}${tile("photo", 2, "📸")}</div>
    <div class="duo"><button class="mini" data-go="contact">${esc(b[3])}</button><button class="mini" data-act="catalog">${esc(b[4])}</button></div>`;
}

function pkgCard(p) {
  const bullets = previewBullets(p.text[S.lang]).map((x) => `<li>${esc(x)}</li>`).join("");
  const cover = p.media?.images?.[0];
  const coverHtml = cover ? `<img class="pkg-cover" src="${esc(cover.src)}" alt="${esc(cover.alt?.[S.lang] || p.title[S.lang])}" loading="lazy">` : "";
  const action = offline()
    ? `<button class="btn primary" disabled title="${esc(t("bookingClosed"))}">${esc(ui("book_now"))}</button>`
    : `<button class="btn primary" data-act="book" data-pkg="${p.id}">${esc(ui("book_now"))}</button>`;
  return `<article class="card pkg">${coverHtml}<div class="top2"><h3>${esc(p.title[S.lang])}</h3><span class="price">${money(p.price)}</span></div>
    <ul class="pre">${bullets}</ul>
    <div class="row"><button class="btn" data-go="pkg/${p.id}">${t("details")}</button>${action}</div></article>`;
}

function mediaHtml(p) {
  const images = (p.media?.images || []).filter((item) => item?.src);
  const videos = (p.media?.videos || []).filter((item) => /^https:\/\//.test(item?.url || ""));
  const gallery = images.length ? `<div class="media-gallery">${images.map((item, i) =>
    `<img src="${esc(item.src)}" alt="${esc(item.alt?.[S.lang] || p.title[S.lang])}" loading="${i ? "lazy" : "eager"}">`).join("")}</div>` : "";
  const videoCards = videos.map((item) => {
    const title = item.title?.[S.lang] || (S.lang === "am" ? "ቀደም ሲል የተሰራ አገልግሎት" : "Previous service");
    const url = item.url;
    const youtube = url.match(/(?:youtube\.com\/watch\?v=|youtu\.be\/)([A-Za-z0-9_-]+)/);
    const vimeo = url.match(/vimeo\.com\/(\d+)/);
    const tiktok = url.match(/tiktok\.com\/@[^/]+\/video\/(\d+)/);
    if (youtube || vimeo || tiktok) {
      const embed = youtube ? `https://www.youtube.com/embed/${youtube[1]}`
        : vimeo ? `https://player.vimeo.com/video/${vimeo[1]}`
        : `https://www.tiktok.com/player/v1/${tiktok[1]}?description=1`;
      return `<div class="media-video"><iframe src="${esc(embed)}" title="${esc(title)}" loading="lazy" allow="accelerometer; autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture" allowfullscreen></iframe><p>${esc(title)}</p></div>`;
    }
    if (/tiktok\.com\//.test(url)) {
      return `<div class="media-video media-external"><div class="media-external-icon">▶</div><p>${esc(title)}</p><a class="btn" href="${esc(url)}" target="_blank" rel="noopener noreferrer">${S.lang === "am" ? "ቪዲዮውን ይክፈቱ" : "Open video"}</a></div>`;
    }
    return `<div class="media-video"><video controls playsinline preload="metadata"${item.poster ? ` poster="${esc(item.poster)}"` : ""}><source src="${esc(url)}"></video><p>${esc(title)}</p></div>`;
  }).join("");
  return gallery || videoCards ? `<section class="media">${gallery}${videoCards ? `<div class="media-videos">${videoCards}</div>` : ""}</section>` : "";
}

function screenService(svc) {
  return `${crumb("", stripEmoji(ui("back")))}${offlineNotice()}<h1>${esc(ui("btns")[SERVICES.indexOf(svc)])}</h1><p class="lead">${esc(t("choosepkg"))}</p>${pkgs(svc).map(pkgCard).join("")}`;
}

function screenPackage(id) {
  const p = pkg(id);
  const action = offline()
    ? `<button class="btn primary" disabled title="${esc(t("bookingClosed"))}">${esc(ui("book_now"))}</button>`
    : `<button class="btn primary" data-act="book" data-pkg="${p.id}">${esc(ui("book_now"))}</button>`;
  return {
    html: `${crumb("svc/" + p.service, stripEmoji(S.cfg.strings.back_to_packages[S.lang]))}${offlineNotice()}${mediaHtml(p)}<article class="card rich">${renderMd(p.text[S.lang])}</article>
      <button class="btn ghost" data-go="">${esc(ui("back"))}</button>`,
    bar: action,
  };
}

// ---- booking form ----
function startForm(svc, pkgId) {
  const draft = JSON.parse(localStorage.getItem("agos_draft_" + svc) || "{}");
  const u = tg?.initDataUnsafe?.user ?? S.cfg.user;
  const f = S.form && S.form.svc === svc ? S.form : { svc, values: { ...draft }, file: null, previewUrl: null, errors: {}, sending: false };
  if (!f.values.name && u?.first_name) f.values.name = [u.first_name, u.last_name].filter(Boolean).join(" ");
  if (!f.values.username && u?.username) f.values.username = "@" + u.username;
  f.values.package = pkgId; S.form = f;
}
const saveDraft = () => {
  const { svc, values } = S.form;
  localStorage.setItem("agos_draft_" + svc, JSON.stringify(values));
  try { tg?.enableClosingConfirmation?.(); } catch { /* old client */ }
};

function fieldHtml(f) {
  const v = S.form.values, err = S.form.errors[f.id];
  const hint = f.hint ? `<span class="hint">${esc(f.hint[S.lang])}</span>` : "";
  let body = "";
  if (["text", "phone", "username"].includes(f.type)) {
    const mode = f.type === "phone" ? 'type="tel" inputmode="tel" placeholder="09XX XXX XXX"' : f.type === "username" ? 'type="text" placeholder="@username" autocapitalize="none"' : 'type="text"';
    body = `<input ${mode} data-f="${f.id}" value="${esc(v[f.id] || "")}" autocomplete="${f.id === "name" ? "name" : "off"}" maxlength="80">`;
  } else if (f.type === "textarea") {
    body = `<textarea data-f="${f.id}" maxlength="400">${esc(v[f.id] || "")}</textarea>`;
  } else if (f.type === "choice") {
    body = `<div class="chips">${f.options.map((o) => `<button type="button" class="chip ${v[f.id] === o.v ? "on" : ""}" data-act="chip" data-f="${f.id}" data-v="${esc(o.v)}">${esc(o[S.lang])}</button>`).join("")}</div>`;
  } else if (f.type === "package") {
    body = `<div class="opts">${pkgs(S.form.svc).map((p) => `<button type="button" class="opt ${v.package === p.id ? "on" : ""}" data-act="opt" data-v="${p.id}"><span class="dot"></span><span>${esc(p.title[S.lang])}</span><span class="p">${money(p.price)}</span></button>`).join("")}</div>`;
  } else if (f.type === "datetime") body = `<div id="dtbox"></div>`;
  return `<div class="field${err ? " bad" : ""}" data-field="${f.id}"><span class="lbl">${esc(f.label[S.lang])}</span>${hint}${body}<div class="err">${esc(err || "")}</div></div>`;
}

function screenBooking(svc, pkgId, step) {
  startForm(svc, pkgId);
  const form = S.cfg.forms[svc];
  const stepper = `<div class="steps">${[t("s1"), t("s2"), t("s3")].map((l, i) => `<div class="${i < step ? "on" : ""}"><i></i>${esc(l)}</div>`).join("")}</div>`;
  const inner = step < 3 ? form.steps[step - 1].map((id) => fieldHtml(form.fields.find((f) => f.id === id))).join("") : paymentHtml(svc);
  const back = step > 1 ? `<button class="btn" data-act="prev">${t("back")}</button>` : "";
  const next = step < 3 ? `<button class="btn primary" data-act="next">${t("next")}</button>`
    : `<button class="btn primary" data-act="submit" ${S.form.sending ? "disabled" : ""}>${S.form.sending ? t("sending") : t("submit")}</button>`;
  return { html: `${crumb(step > 1 ? `book/${svc}/${pkgId}/${step - 1}` : "pkg/" + pkgId, pkg(pkgId).title[S.lang])}<h2>${form.icon} ${esc(form.title[S.lang])}</h2><div style="height:12px"></div>${stepper}${inner}`, bar: back + next };
}

function paymentHtml(svc) {
  const p = pkg(S.form.values.package), dep = Math.round(p.price / 2), bank = S.cfg.bank;
  const notice = S.cfg.strings.payment_notice.replace("{account_name}", bank.account_name).replace("{account_number}", bank.account_number);
  const bad = S.form.errors.screenshot;
  return `<div class="card"><div class="sum"><div><span class="k">${t("pkgprice")}</span><b>${esc(p.title[S.lang])} · ${money(p.price)}</b></div>
      <div><span class="k">${t("balance")}</span><span>${money(p.price - dep)}</span></div>
      <div><span class="k">${t("deposit")}</span><span class="big">${money(dep)}</span></div></div></div>
    <div class="card">
      <div class="bank"><div><small>${t("bank")}</small>${esc(bank.name)}</div></div>
      <div class="bank"><div><small>${t("acctname")}</small>${esc(bank.account_name)}</div></div>
      <div class="bank"><div><small>${t("acct")}</small><b>${esc(bank.account_number)}</b></div><button class="copy" data-act="copy" data-v="${esc(bank.account_number)}">${t("copy")}</button></div>
    </div>
    <div class="card rich">${renderMd(notice)}</div>
    <div class="field"><span class="lbl">${esc(S.cfg.strings.upload_prompt[svc])}</span>
      <label class="drop${bad ? " bad" : ""}" id="drop"><input type="file" accept="image/*" id="shot">
        ${S.form.previewUrl ? `<img src="${S.form.previewUrl}" alt=""><span class="hint">${t("change")}</span>` : `<span style="font-size:34px">📤</span><span class="hint">${t("tap")}</span>`}</label>
      <div class="err" style="display:${bad ? "block" : "none"}">${esc(bad || "")}</div></div>`;
}

// Ethiopian-calendar date picker with the Gregorian equivalent underneath
function hydrateDate() {
  const box = $("#dtbox"); if (!box) return;
  const d = (S.form.values.date ||= {});
  const now = E.fromGregorian(new Date());
  const years = [0, 1, 2, 3].map((i) => now.year + i);
  const maxDay = d.month && d.year ? E.daysIn(+d.year, +d.month) : 30;
  if (d.day > maxDay) d.day = maxDay;
  const sel = (key, ph, opts, val) => `<select data-d="${key}" aria-label="${esc(ph)}"><option value="">${esc(ph)}</option>${opts.map(([v, l]) => `<option value="${v}" ${String(val) === String(v) ? "selected" : ""}>${esc(l)}</option>`).join("")}</select>`;
  const days = Array.from({ length: maxDay }, (_, i) => [i + 1, String(i + 1)]);
  const months = E.MONTHS.map((m, i) => [i + 1, S.lang === "am" ? m[1] : m[0]]);
  const hrs = Array.from({ length: 12 }, (_, i) => [i + 1, `${i + 1}:00`]);
  const periods = E.PERIODS.map((p) => [p[0], S.lang === "am" ? p[2] : p[1]]);
  const gc = d.day && d.month && d.year ? `<div class="gc">${t("gregorian")}: ${E.fmtGregorian(E.toGregorian(+d.year, +d.month, +d.day))}</div>` : "";
  box.innerHTML = `<div class="dt">${sel("day", t("day"), days, d.day)}${sel("month", t("month"), months, d.month)}${sel("year", t("year"), years.map((y) => [y, y]), d.year)}</div>
    <div class="dt2">${sel("hour", t("hour"), hrs, d.hour)}${sel("period", t("period"), periods, d.period)}</div>${gc}`;
}

// ---- validation (mirrors the server) ----
const PHONE_ET = /^(?:\+?251|0)?([79]\d{8})$/;
const phoneOk = (raw) => { const s = (raw || "").replace(/[\s\-().]/g, ""); return PHONE_ET.test(s) || /^\+?\d{8,15}$/.test(s); };
function validateFields(ids) {
  const form = S.cfg.forms[S.form.svc], v = S.form.values, errs = {};
  for (const id of ids) {
    const f = form.fields.find((x) => x.id === id), val = (v[id] ?? "").toString().trim();
    if (f.type === "datetime") {
      const d = v.date || {};
      if (!d.day || !d.month || !d.year || !d.hour || !d.period || d.day > E.daysIn(+d.year, +d.month)) { errs[id] = t("baddate"); continue; }
      const g = E.toGregorian(+d.year, +d.month, +d.day), n = new Date();
      if (g < new Date(Date.UTC(n.getFullYear(), n.getMonth(), n.getDate()))) errs[id] = t("past");
    } else if (f.type === "package") { if (!pkg(v.package)) errs[id] = t("needpkg"); }
    else if (f.type === "choice") { if (!val) errs[id] = t("req"); }
    else if (f.type === "phone") { if (!val && !f.optional) errs[id] = t("req"); else if (val && !phoneOk(val)) errs[id] = t("badphone"); }
    else if (f.type === "username") { if (val && !/^@?[A-Za-z0-9_]{3,32}$/.test(val.replace("https://t.me/", ""))) errs[id] = t("baduser"); }
    else if (val.length < (f.type === "textarea" ? 3 : 2)) errs[id] = t("req");
  }
  return errs;
}
function showErrors(errs) {
  S.form.errors = errs;
  render(true).then(() => $(".field.bad, .drop.bad")?.scrollIntoView({ block: "center", behavior: "smooth" }));
  try { tg?.HapticFeedback?.notificationOccurred("error"); } catch { /* old client */ }
  toast(t("fixfields"), true);
}

// ---- done / closed / contact ----
function screenDone() {
  const d = S.done, st = S.cfg.strings, B = st.discover_buttons, L = S.lang;
  const avail = SERVICES.filter((s) => !S.booked.includes(s));
  let msg;
  if (avail.length === 2) msg = !avail.includes("decor") ? ui("discover_after_decor") : !avail.includes("limo") ? ui("discover_after_limo") : ui("discover_after_photo");
  else if (avail.length === 1) msg = st.discover_single[avail[0]][L];
  else if (avail.length === 0) msg = ui("discover_complete").replace("{booked_services}", S.booked.map((s) => "✓ " + s[0].toUpperCase() + s.slice(1)).join("\n"));
  else msg = st.discover_generic[L];
  const btns = avail.map((s) => `<button class="btn" data-go="svc/${s}">${esc(B[s][L])}</button>`);
  if (!avail.length) btns.push(`<button class="btn" data-go="contact">${esc(B.contact[L])}</button>`);
  btns.push(`<button class="btn dark" data-go="">${esc(ui("back"))}</button>`);
  return { html: `<div class="card center"><div class="check">✓</div><h1>${t("received")}</h1><div class="ref">${esc(d.ref)}</div>
      <p>${esc(st.client_caption)}</p><p class="hint">${d.pdf_sent ? t("pdfsent") : t("pdfno")}</p></div>
      <div class="card rich">${renderMd(msg)}</div><div class="stack">${btns.join("")}</div>`, bar: null };
}

function screenClosed() {
  const phone = S.cfg.hours.phone;
  const reason = S.lang === "am" ? S.cfg.hours.reason_am : S.cfg.hours.reason_en;
  return { html: `<div class="card rich">${renderMd(S.cfg.strings.offline.replaceAll("{phone}", phone))}</div>
    <div class="card closed-reason"><strong>${esc(reason)}</strong></div><div class="stack">
      <a class="btn primary" href="tel:${phone.replace(/\s/g, "")}">${t("call")} ${esc(phone)}</a>
      <button class="btn" data-act="check">${t("checkagain")}</button><button class="btn ghost" data-go="contact">${esc(ui("btns")[3])}</button></div>`, bar: null };
}

function offlineNotice() {
  const reason = S.lang === "am" ? S.cfg.hours.reason_am : S.cfg.hours.reason_en;
  return `<div class="card closed-reason"><strong>${esc(reason)}</strong><br><span class="hint">${esc(t("bookingClosed"))}</span></div>`;
}

function screenContact() {
  const calls = S.cfg.contact.phones.map((p) => `<a class="btn primary" href="tel:${p.replace(/\s/g, "")}">${t("call")} ${esc(p)}</a>`).join("");
  return `${crumb("", stripEmoji(ui("back")))}<div class="card rich">${renderMd(ui("contact_text"))}</div><div class="stack">${calls}</div>`;
}

// ---- actions ----
async function compress(file) {
  const bmp = await createImageBitmap(file);
  const k = Math.min(1, 1600 / Math.max(bmp.width, bmp.height));
  const c = document.createElement("canvas"); c.width = Math.round(bmp.width * k); c.height = Math.round(bmp.height * k);
  c.getContext("2d").drawImage(bmp, 0, 0, c.width, c.height);
  return new Promise((res, rej) => c.toBlob((b) => (b ? res(b) : rej(new Error("blob"))), "image/jpeg", 0.82));
}
const gotoStep = (step) => nav(`book/${S.form.svc}/${S.form.values.package}/${step}`);
const stepWith = (form, errs) => form.steps.findIndex((ids) => ids.some((id) => errs[id])) + 1 || 3;

async function submit() {
  const f = S.form, form = S.cfg.forms[f.svc];
  const errs = validateFields(form.steps.flat());
  if (Object.keys(errs).length) { S.form.errors = errs; toast(t("fixfields"), true); return gotoStep(stepWith(form, errs)); }
  if (!f.file) return showErrors({ screenshot: t("needshot") });
  f.sending = true; render(true);
  const v = f.values, d = v.date;
  const payload = { service: f.svc, package: v.package, name: v.name, phone: v.phone, username: v.username || "", alt_phone: v.alt_phone || "",
    address: v.address, gender: v.gender || null, house: v.house || null, lang: S.lang,
    date: { day: +d.day, month: +d.month, year: +d.year, hour: +d.hour, period: d.period } };
  try {
    const r = await api.submitBooking(payload, f.file);
    if (!S.booked.includes(f.svc)) S.booked.push(f.svc);
    localStorage.setItem("agos_booked", JSON.stringify(S.booked));
    localStorage.removeItem("agos_draft_" + f.svc);
    try { tg?.disableClosingConfirmation?.(); tg?.HapticFeedback?.notificationOccurred("success"); } catch { /* old client */ }
    S.done = { ref: r.ref, pdf_sent: r.pdf_sent !== false, svc: f.svc }; S.form = null;
    nav("done/" + r.ref);
  } catch (e) {
    f.sending = false;
    const b = e.body || {};
    if (e.status === 401) return renderError(e);
    if (e.status === 403 && b.error === "offline") { S.cfg.hours = b.hours; return render(); }
    if (e.status === 422 && b.errors) {
      const m = { phone: t("badphone"), alt_phone: t("badphone"), username: t("baduser"), date: b.errors.date === "past" ? t("past") : t("baddate"), package: t("needpkg"), screenshot: t("needshot") };
      f.errors = Object.fromEntries(Object.keys(b.errors).map((k) => [k, m[k] || t("req")]));
      return gotoStep(stepWith(form, f.errors));
    }
    toast(e.status === 429 ? t("rate") : e.status === 502 ? t("delivery") : t("failed"), true);
    render(true);
  }
}

document.addEventListener("click", async (e) => {
  const link = e.target.closest("a[href]");
  if (link && /^https?:/.test(link.href)) {
    e.preventDefault();
    if (/^https:\/\/t\.me\//.test(link.href) && tg?.openTelegramLink) tg.openTelegramLink(link.href);
    else if (tg?.openLink) tg.openLink(link.href); else window.open(link.href, "_blank");
    return;
  }
  const lang = e.target.closest("[data-lang]");
  if (lang) { S.lang = lang.dataset.lang; localStorage.setItem("agos_lang", S.lang); buzz(); return render(true); }
  const go = e.target.closest("[data-go]");
  if (go) { buzz(); return nav(go.dataset.go); }
  const el = e.target.closest("[data-act]"); if (!el) return;
  const act = el.dataset.act; buzz();
  if (act === "book") { S.form = null; return nav(`book/${pkg(el.dataset.pkg).service}/${el.dataset.pkg}/1`); }
  if (act === "chip") { S.form.values[el.dataset.f] = el.dataset.v; delete S.form.errors[el.dataset.f]; saveDraft(); return render(true); }
  if (act === "opt") { S.form.values.package = el.dataset.v; delete S.form.errors.package; saveDraft(); history.replaceState(null, "", `#/book/${S.form.svc}/${el.dataset.v}/${curStep()}`); return render(true); }
  if (act === "prev") return gotoStep(curStep() - 1);
  if (act === "next") {
    const errs = validateFields(S.cfg.forms[S.form.svc].steps[curStep() - 1]);
    if (Object.keys(errs).length) return showErrors(errs);
    S.form.errors = {}; return gotoStep(curStep() + 1);
  }
  if (act === "submit") return submit();
  if (act === "copy") { try { await navigator.clipboard.writeText(el.dataset.v); } catch { /* clipboard blocked */ } el.textContent = t("copied"); return setTimeout(() => (el.textContent = t("copy")), 1600); }
  if (act === "catalog") { try { await api.sendCatalog(); toast(t("catsent")); } catch { toast(t("failed"), true); } return; }
  if (act === "check") { await loadConfig(true); return render(true); }
  if (act === "reload") return location.reload();
});

document.addEventListener("input", (e) => {
  const id = e.target.dataset?.f; if (!id || !S.form || e.target.tagName === "BUTTON") return;
  S.form.values[id] = e.target.value; e.target.closest(".field")?.classList.remove("bad"); delete S.form.errors[id]; saveDraft();
});
document.addEventListener("change", async (e) => {
  const part = e.target.dataset?.d;
  if (part && S.form) {
    const d = (S.form.values.date ||= {});
    d[part] = e.target.value === "" ? undefined : part === "period" ? e.target.value : +e.target.value;
    delete S.form.errors.date; $('[data-field="date"]')?.classList.remove("bad"); saveDraft(); return hydrateDate();
  }
  if (e.target.id === "shot" && e.target.files[0]) {
    try {
      S.form.file = await compress(e.target.files[0]);
      if (S.form.previewUrl) URL.revokeObjectURL(S.form.previewUrl);
      S.form.previewUrl = URL.createObjectURL(S.form.file); delete S.form.errors.screenshot; render(true);
    } catch { toast(t("failed"), true); }
  }
});
document.addEventListener("focusout", (e) => {
  const id = e.target.dataset?.f;
  if (S.form && ["phone", "alt_phone"].includes(id)) {
    const m = e.target.value.replace(/[\s\-().]/g, "").match(PHONE_ET);
    if (m) { e.target.value = "+251" + m[1]; S.form.values[id] = e.target.value; saveDraft(); }
  }
});
try {
  tg?.BackButton?.onClick(() => {
    const r = route();
    if (r.view === "book" && curStep() > 1) gotoStep(curStep() - 1);
    else if (history.length > 1) history.back(); else nav("");
  });
} catch { /* old client */ }
window.addEventListener("hashchange", () => render());
render();
