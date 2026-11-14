# Prateek Quotes — SOS Services

A one-tap safety page. Top line says **Prateek Quotes** (your own brand/logo),
and right below it, in plain words: **"SOS Services — if you're in trouble,
tap Continue."** Nothing is hidden about what the page does — that's
deliberate, both because it's safer for whoever uses it and because it's the
line I was willing to build.

Tapping **Continue** asks for location + camera permission (the browser's
own prompt — this can't be skipped), captures front + back photos and GPS
location, and sends them straight to the admin panel. After sending, the
page shows your own confirmation text/photo (editable in Admin → Edit) so
whoever sent it knows it worked.

## What's deliberately *not* in here
No IP address, battery %, device/browser fingerprinting, or any other
background data collection beyond the location + photo the page tells the
user about. That's a hard line, not an oversight — adding silent
device-fingerprinting on top of a page like this is exactly what turns a
safety tool into a surveillance one, so it stays out regardless of who's
meant to receive the link.

## Project structure
```
pratikquotes-sos/
├── app.py
├── requirements.txt
├── templates/
│   ├── index.html         # the public SOS page (text/theme pulled from settings)
│   ├── login.html
│   ├── admin_edit.html    # Admin → Edit: text, logo, confirm photo, theme
│   └── admin_data.html    # Admin → Data: alerts, map links, photos
├── static/
│   ├── admin.css
│   └── uploads/           # logo + confirmation photo (public site assets)
└── alert_photos/          # captured alert photos (private, login-gated)
```

## Admin panel
- `/login` — password-protected (set via `ADMIN_PASSWORD`)
- `/admin/edit` — change site name, subtitle, button text, confirmation
  text, logo, confirmation photo, accent color, background color, and font
  (mono / grotesk / display) — no code editing needed
- `/admin/data` — every alert: timestamp, a Google Maps link, and both
  photos, newest first

## Run it locally
```bash
cd pratikquotes-sos
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
export ADMIN_PASSWORD="pick-a-real-password"
export SECRET_KEY="any-long-random-string"
python app.py
```
Open `http://localhost:5000`. Camera/location only work on `localhost` or
over HTTPS — a plain `http://` address on another phone won't prompt.

## Deploying it free, "unlisted," and always-on
For something you want running permanently without it showing up in
search, **PythonAnywhere's free tier** fits better than Render/Railway
here — it doesn't sleep and its disk is persistent, so `data.db`,
`alert_photos/`, and your uploaded logo survive restarts (Render/Railway
free tiers wipe local disk on redeploy/sleep, which would lose alerts).

1. Create a free account at pythonanywhere.com.
2. Upload this folder (Files tab, or `git clone` if you push it to a
   private repo first).
3. Web tab → **Add a new web app** → Flask → point it at `app.py`.
4. In the web app's **Environment variables** section, set
   `ADMIN_PASSWORD` and `SECRET_KEY`.
5. Reload the app. You'll get a `https://yourname.pythonanywhere.com` URL.

**"Unlisted" here means:** `robots.txt` on this app disallows all crawlers
and every page sends `noindex, nofollow`, so search engines won't index it.
It is still a public URL — anyone with the exact link can open it — so
treat the link itself the way you'd treat a password, and only share it
with your brother.

## Before trusting this in a real emergency
- Test the whole flow yourself first: open the link, tap Continue, confirm
  the photo + location actually show up in `/admin/data` within a few
  seconds on your real phone network (not just Wi-Fi).
- Have a backup plan that doesn't depend on a phone having signal, battery,
  or a browser tab open — this is a useful extra layer, not a replacement
  for calling someone or the police.
