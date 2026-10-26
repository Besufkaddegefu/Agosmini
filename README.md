# AGOS Mini App

Telegram Mini App and webhook service for AGOS postpartum care bookings.

## Local verification

From PowerShell:

```powershell
cd "C:\Users\Bese\Desktop\agos-miniapp"
py -3.14 -m pip install -r requirements-dev.txt
py -3.14 -m pytest -q
```

The current backend functionality suite should report 28 passing tests.

## Local Mini App

Development mode does not contact Telegram:

```powershell
$env:DEV_MODE="1"
$env:BOT_TOKEN="TEST:TOKEN"
$env:ADMIN_ID_1="111"
$env:ADMIN_ID_2="222"
$env:OFFLINE_START_HOUR="23"
$env:OFFLINE_END_HOUR="23"
uvicorn app.main:app --host 127.0.0.1 --port 8765
```

Open <http://127.0.0.1:8765/app/?dev=1>.

Generated development booking files are written to the system temporary
directory under `agos_dev_out`.

## Deploy on Render

1. Push this project to a private GitHub repository.
2. In Render, choose **New +** → **Blueprint**.
3. Select the repository. Render reads [render.yaml](./render.yaml).
4. Set the secret environment variables:
   - `BOT_TOKEN`
   - `ADMIN_ID_1`, `ADMIN_ID_2`, `ADMIN_ID_3`
   - `WEBHOOK_SECRET_TOKEN`
   - `BANK_ACCOUNT_NUMBER`
5. After the first deploy, copy the Render HTTPS URL and set
   `PUBLIC_BASE_URL` to that exact URL without a trailing slash.
6. Redeploy and verify `https://your-service.onrender.com/health` returns
   `{"ok":true}`.
7. Confirm `/app/` loads over HTTPS before configuring Telegram.

Use one worker. Rate limiting, duplicate protection, and the admin decision
registry are intentionally in memory in this version.

## Telegram configuration

### 1. Rotate the token if it was ever exposed

In BotFather:

1. Open `@BotFather`.
2. Use `/mybots` and select the bot.
3. Open **API Token** and revoke/regenerate the token if the old token was
   printed or shared.
4. Put the new token in Render as `BOT_TOKEN`.

### 2. Find admin Telegram IDs

Each admin can open `@userinfobot` in Telegram and send `/start`, or use
another trusted Telegram ID lookup method. Put the numeric IDs in
`ADMIN_ID_1`, `ADMIN_ID_2`, and `ADMIN_ID_3`.

### 3. Configure the Mini App

No polling is used. On startup the service:

- registers `POST /agos-bot` as the Telegram webhook;
- checks `X-Telegram-Bot-Api-Secret-Token`;
- configures the bot menu button to open `/app/`.

The webhook URL is:

```text
https://your-service.onrender.com/agos-bot
```

The app URL is:

```text
https://your-service.onrender.com/app/
```

Telegram Mini Apps require HTTPS in real use.

### 4. Test the bot

1. Open the bot in Telegram.
2. Send `/start`.
3. Confirm the **Book / ያዝዙ** menu button appears.
4. Open the Mini App.
5. Submit a test booking outside the offline window.
6. Confirm all configured admins receive the screenshot, summary, PDF,
   and decision buttons.
7. Press **Confirm payment** as an admin and verify the customer notification.
8. Repeat with **Reject**.
9. Test during `08:00–20:00` Addis Ababa time. Booking must be blocked with
   the bilingual explanation and call option.

## Important production notes

- Do not set `DEV_MODE=1` on Render.
- Do not commit `.env` or real bank/token values.
- Use a new bot token if the original code ever logged the token.
- Keep exactly one worker.
- The catalog source of truth is [Agos_Surprise_Packages.pdf](./Agos_Surprise_Packages.pdf).
- The deployed catalog PDF is [webapp/assets/services_catalog.pdf](./webapp/assets/services_catalog.pdf).

## Package photos and videos

Package media is optional and does not affect booking validation or payment
submission. Add media to the matching package record in
[app/data/catalog_pdf.json](./app/data/catalog_pdf.json), using the existing
package ID:

```json
"media": {
  "images": [
    {
      "src": "/app/assets/media/decor_basic/01.webp",
      "alt": {
        "en": "Home decoration example",
        "am": "የቤት ዲኮር ምሳሌ"
      }
    }
  ],
  "videos": [
    {
      "url": "https://www.youtube.com/watch?v=VIDEO_ID",
      "poster": "/app/assets/media/decor_basic/video-poster.webp",
      "title": {
        "en": "Previous home decoration service",
        "am": "ቀደም ሲል የተሰራ የቤት ዲኮር አገልግሎት"
      }
    }
  ]
}
```

Images must use `/app/assets/...` paths or HTTPS URLs. Videos must use HTTPS
URLs. YouTube, Vimeo, and full TikTok video links such as
`https://www.tiktok.com/@account/video/123456789` are embedded with a
preview/player. TikTok shortened links such as `https://vm.tiktok.com/...`
cannot be converted to an embedded player without first resolving their
redirect; they are shown with an `Open video` link instead. Use the full
TikTok video URL when inline playback is required. Direct HTTPS video files
use the browser's inline player. Keep media optimized for mobile,
and publish only photos/videos for which AGOS has permission. The ready-made
package folders and their complete mapping are documented in
[webapp/assets/media/README.md](./webapp/assets/media/README.md).
