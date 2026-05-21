# Cloudflare Tunnel — Setup pentru Roland CC

> Permite acces public HTTPS la aplicația ta locală, fără port forwarding, gratuit.
> URL stabil + PWA instalabilă pe telefon + HMR live.

## Două variante

### A. Quick Tunnel (zero setup, URL random la fiecare pornire)

**Avantaj:** funcționează imediat, nu necesită cont Cloudflare.
**Dezavantaj:** URL-ul se schimbă la fiecare repornire (ex: `random-name-xxx.trycloudflare.com`).

```powershell
# Instalare cloudflared (o singură dată)
winget install --id Cloudflare.cloudflared

# Pornire sistem + tunnel
python start.py tunnel
```

URL-ul random apare în fereastra cloudflared. Lipește-l în browser de pe telefon → instalează PWA.

---

### B. Named Tunnel (setup unic, URL stabil pentru totdeauna) — **RECOMANDAT**

**Avantaj:** URL fix, persistent. Instalezi PWA o dată, funcționează săptămâni.
**Dezavantaj:** 5 minute setup unic.

#### Pas 1 — Instalare cloudflared

```powershell
winget install --id Cloudflare.cloudflared
```

#### Pas 2 — Autentificare Cloudflare

```powershell
cloudflared tunnel login
```

Se deschide browser → login cu contul tău Cloudflare (gratuit) → autorizezi domeniul.

#### Pas 3 — Creare tunel persistent

```powershell
cloudflared tunnel create roland-cc
```

Va afișa un UUID — copiază-l, îl folosești la pas 4.

#### Pas 4 — Creare config local

Creează fișierul `cloudflared/config.yml` în rădăcina proiectului:

```yaml
tunnel: <UUID-ul-de-la-pas-3>
credentials-file: C:\Users\ALIENWARE\.cloudflared\<UUID>.json

ingress:
  - hostname: roland-cc.<domeniul-tau>.com
    service: http://localhost:5173
  - service: http_status:404
```

> **Fără domeniu propriu?** Folosește un subdomeniu `*.trycloudflare.com` (gratuit, persistent dacă e named tunnel) sau cumpără un domeniu cheap (~10 RON/an pe .xyz / .top).

#### Pas 5 — Route DNS (doar dacă ai domeniu)

```powershell
cloudflared tunnel route dns roland-cc roland-cc.<domeniul-tau>.com
```

#### Pas 6 — Pornire

```powershell
python start.py tunnel
```

Script-ul detectează automat `cloudflared/config.yml` și folosește named tunnel.

---

## Cum se actualizează aplicația în URL?

Cu setup-ul de mai sus (Vite HMR + uvicorn `--reload` + Cloudflare Tunnel):

| Modifici                           | Ce se întâmplă                                                       |
| ---------------------------------- | -------------------------------------------------------------------- |
| `.jsx` / `.css` în `frontend/src/` | **Pagina se actualizează în <1 sec** fără reload (HMR)               |
| `.py` în `backend/`                | Backend se restartează automat, request-urile noi merg pe cod nou    |
| `vite.config.js`                   | Restart manual: `python start.py stop` apoi `python start.py tunnel` |

URL-ul rămâne stabil. PWA-ul instalat pe telefon vede actualizările instant prin auto-update SW (vezi `vite.config.js` → `registerType: 'autoUpdate'` + `skipWaiting: true`).

---

## Instalare PWA pe Android

1. Deschide URL-ul public în Chrome
2. Meniu (⋮) → "Adaugă pe ecranul principal" / "Instalează aplicație"
3. Pictograma apare ca app nativă

Updates: la fiecare deschidere a PWA, Service Worker verifică automat versiunea nouă. Cu `skipWaiting: true`, update-urile se aplică imediat fără reinstalare.

---

## Troubleshooting

**Tunnel pornește dar URL-ul dă 502:**

- Verifică că Vite rulează: `curl http://127.0.0.1:5173/`
- Verifică `vite.config.js` are `server.host: true`

**HMR nu funcționează prin tunnel:**

- Verifică în consolă browser: WebSocket connection to `wss://...:443/`
- Adaugă în `vite.config.js` → `server.hmr: { clientPort: 443, protocol: 'wss' }`

**PWA nu cere instalare:**

- PWA cere HTTPS — verifică că URL-ul începe cu `https://`
- Verifică în DevTools → Application → Manifest

**cloudflared.exe nu pornește ca service:**

```powershell
cloudflared service install
```

---

**Vezi și:** `vite.config.js` (PWA + server config), `start.py` (launcher Python — `dev`/`prod`/`tunnel`/`stop`).
