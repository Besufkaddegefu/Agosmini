const tg = window.Telegram?.WebApp;
const DEV = new URLSearchParams(location.search).get("dev") === "1";

function headers() {
  const h = { "X-Telegram-Init-Data": tg?.initData || "" };
  if (DEV) h["X-Dev-User"] = JSON.stringify({ id: 42, first_name: "Dev", username: "dev_user" });
  return h;
}

async function call(path, opts = {}) {
  let res;
  try { res = await fetch(path, { ...opts, headers: { ...headers(), ...(opts.headers || {}) } }); }
  catch { throw { status: 0, body: { error: "network" } }; }
  let body = null;
  try { body = await res.json(); } catch { /* empty body */ }
  if (!res.ok) throw { status: res.status, body: body || {} };
  return body;
}

export const getConfig = () => call("/api/config");
export const sendCatalog = () => call("/api/catalog", { method: "POST" });
export const submitBooking = (payload, file) => {
  const fd = new FormData();
  fd.set("payload", JSON.stringify(payload));
  fd.set("screenshot", file, "payment.jpg");
  return call("/api/bookings", { method: "POST", body: fd });
};
