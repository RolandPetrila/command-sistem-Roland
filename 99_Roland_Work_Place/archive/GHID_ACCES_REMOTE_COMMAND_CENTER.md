# Ghid Exhaustiv: Metode de Acces Remote la Roland Command Center

> **Generat:** 2026-03-19  
> **Context proiect:** FastAPI (Python 3.13) + React 18 + SQLite local + WebSocket/SSE + PWA + Windows 10  
> **Tailscale URL curent:** `https://desktop-cjuecmn.tail7bc485.ts.net:8000`  
> **Instrucțiuni pentru Claude Code:** Analizează fiecare metodă din perspectiva stack-ului existent. Marchează ca [IMPLEMENTABIL FĂRĂ RISC], [IMPLEMENTABIL CU PRECAUȚIE] sau [NERECOMANDABIL]. Specifică dacă implementarea poate afecta configurația Tailscale existentă, uvicorn SSL, CORS, sau PWA. Menționează dacă sunt necesare modificări în `app/main.py`, `client.js`, sau `START_Production.bat`.

---

## CUPRINS

1. [Metoda 0 — Tailscale VPN Mesh (CURENTĂ)](#0-tailscale-vpn-mesh--metoda-curentă)
2. [Metoda 1 — Tailscale Funnel](#1-tailscale-funnel)
3. [Metoda 2 — Cloudflare Tunnel + Zero Trust](#2-cloudflare-tunnel--zero-trust)
4. [Metoda 3 — ngrok](#3-ngrok)
5. [Metoda 4 — Serveo.net](#4-serveont)
6. [Metoda 5 — localhost.run](#5-localhostrun)
7. [Metoda 6 — ZeroTier](#6-zerotier)
8. [Metoda 7 — WireGuard Direct](#7-wireguard-direct)
9. [Metoda 8 — OpenVPN](#8-openvpn)
10. [Metoda 9 — Port Forwarding + DuckDNS](#9-port-forwarding--duckdns)
11. [Metoda 10 — Reverse SSH Tunnel via VPS](#10-reverse-ssh-tunnel-via-vps)
12. [Metoda 11 — frp (Fast Reverse Proxy)](#11-frp-fast-reverse-proxy)
13. [Metoda 12 — Bore](#12-bore)
14. [Metoda 13 — Playit.gg](#13-playitgg)
15. [Metoda 14 — Vercel / Railway / Render](#14-vercel--railway--render-cloud-hosting)
16. [Metoda 15 — VPS Propriu (Hetzner + Nginx)](#15-vps-propriu-hetzner--nginx)
17. [Clasificare Finală & Tabel Comparativ](#clasificare-finală--tabel-comparativ)
18. [Recomandarea Optimă](#recomandarea-optimă)

---

## 0. Tailscale VPN Mesh — Metoda Curentă

### Cum funcționează
Tailscale creează un VPN mesh peer-to-peer bazat pe WireGuard. Fiecare dispozitiv primește un IP stabil (100.x.x.x) și un hostname DNS via MagicDNS (`desktop-cjuecmn.tail7bc485.ts.net`). Traficul circulă **direct între dispozitive** (P2P), fără a trece prin serverele Tailscale. Coordonarea (schimb de chei) se face prin serverul central, dar datele merg P2P cu criptare ChaCha20-Poly1305. Când conexiunea directă nu e posibilă (NAT strict), se folosesc servere DERP ca relay.

### Pași de configurare
✅ **Deja configurat și funcțional** — HTTPS/TLS via `tailscale cert`, uvicorn cu SSL, CORS dinamic, PWA funcțional, URL dinamic în `client.js`.

### Conturi necesare
- Cont Tailscale gratuit (ai deja)

### Cost real
**Gratuit** — Plan Personal: 3 utilizatori, 100 dispozitive

### Securitate
⭐⭐⭐⭐⭐ — Maxim. Numai dispozitivele din tailnet pot accesa. Nimeni din exterior nu vede aplicația. Criptare WireGuard end-to-end.

### Compatibilitate cu proiectul
✅ **Perfect compatibil** — implementat și testat. WebSocket/SSE nativ, PWA funcțional, latență <2ms P2P.

### Limitări
- Tailscale trebuie instalat pe fiecare dispozitiv client
- Dacă Tailscale e oprit pe PC → aplicația e inaccesibilă de pe telefon
- Nu poate fi accesat de pe un browser fără Tailscale (ex: calculator împrumutat)

### ⚠️ Poate strica proiectul?
**NU** — este metoda curentă, deja stabilă.

### Grad dificultate implementare
**N/A** — deja implementat.

---

## 1. Tailscale Funnel

### Cum funcționează
Extensie a Tailscale care expune un serviciu local pe **internet public** printr-un URL HTTPS permanent (`desktop-cjuecmn.tail7bc485.ts.net`), fără ca vizitatorul să aibă nevoie de Tailscale instalat. Traficul trece prin serverele de ingress Tailscale, dar TLS termination se face local.

### Pași de configurare
```bash
# Activează Funnel din Tailscale Admin Console (tailscale.com/admin)
# Activează permisiunea "Funnel" pentru nodul tău
tailscale funnel --bg 8000
# Aplicația devine accesibilă la: https://desktop-cjuecmn.tail7bc485.ts.net
```

### Conturi necesare
- Cont Tailscale existent (ai deja)

### Cost real
**Gratuit** — inclus în planul Personal

### Securitate
⭐⭐⭐⭐ — Bun. TLS automat. Dar aplicația e publică (oricine cu URL-ul poate accesa) — fără autentificare nativă pentru vizitatori externi.

### Compatibilitate cu proiectul
✅ **Compatibil** — suportă portul 8000, HTTPS automat. **Bug cunoscut (Issue #18651):** Tailscale Funnel Serve strippuiește query parameters din WebSocket upgrade requests. Poate afecta streaming SSE în anumite scenarii. Statut: **Beta**, activ în 2026.

### Limitări
- Doar porturile 443, 8443, 10000 — portul 8000 trebuie mapcat la 443
- Bug WebSocket query params (parțial afectează SSE)
- Aplicația devine **publică** — oricine cu URL-ul accesează fără autentificare

### ⚠️ Poate strica proiectul?
**Risc mic** — necesită modificarea comenzii de start uvicorn (mapare port 443→8000). Nu modifică codul aplicației. Dacă Funnel e activat greșit, aplicația poate deveni publică fără autentificare.

### Grad dificultate implementare
**1/5** — câteva comenzi CLI.

---

## 2. Cloudflare Tunnel + Zero Trust

### Cum funcționează
Instalezi daemonul `cloudflared` pe Windows 10, care creează o **conexiune outbound-only** criptată către rețeaua edge Cloudflare. Nu se deschide niciun port pe router. Când cineva accesează `app.yourdomain.com`, cererea ajunge la edge Cloudflare → traversează tunelul → este forwardată la `localhost:8000`. Cloudflare Zero Trust (Access) adaugă autentificare (email OTP, Google SSO, GitHub SSO) înainte de a permite accesul.

### Pași de configurare
```
1. Creează cont Cloudflare gratuit (cloudflare.com)
2. Adaugă domeniu pe Cloudflare (~10$/an pentru .com)
3. Zero Trust dashboard → Networks → Tunnels → Create tunnel
4. Descarcă cloudflared-windows-amd64.exe
5. Rulează comanda din dashboard: cloudflared.exe tunnel run <token>
6. Configurează hostname: app.yourdomain.com → http://localhost:8000
7. Instalează ca serviciu Windows: cloudflared.exe service install <token>
8. (Opțional) Zero Trust → Access → Applications → protejează cu email OTP
```

### Conturi necesare
- Cont Cloudflare gratuit
- Domeniu (opțional dar recomandat — ~10$/an)
- Fără domeniu: Quick Tunnels generate URL-uri temporare random

### Cost real
**Gratuit** (tunel) + ~10$/an (domeniu). Zero Trust Access: gratuit pentru până la 50 utilizatori.

### Securitate
⭐⭐⭐⭐⭐ — Excelent. TLS automat, protecție DDoS inclusă, Zero Trust autentificare, WAF gratuit. Fără expunere IP.

### Compatibilitate cu proiectul
✅ **Perfect compatibil** — WebSocket suportat nativ pe Cloudflare, SSE funcționează ca HTTP standard. Nu necesită modificări în codul aplicației. CORS-ul existent funcționează dacă adaugi domeniul Cloudflare în lista CORS din `app/main.py`.

### Limitări
- Necesită domeniu (sau URL random temporar)
- `cloudflared` pe Windows nu se auto-actualizează (actualizare manuală periodică)
- Traficul trece prin serverele Cloudflare (vs. P2P în Tailscale)

### ⚠️ Poate strica proiectul?
**Risc minim** — nu modifică nimic din proiect. Singura modificare necesară: adaugă domeniul Cloudflare în lista `CORS_ORIGINS` din `app/config.py` sau `app/main.py`. Fără această modificare, browser-ul va bloca request-urile (CORS error).

### Grad dificultate implementare
**2/5** — setup inițial 20-30 minute, apoi funcționează automat.

---

## 3. ngrok

### Cum funcționează
Client local care deschide un tunel TCP/HTTPS către serverele ngrok. Generează un URL public (ex: `your-name.ngrok-free.app`) care forwardează traficul la `localhost:8000`.

### Pași de configurare
```bash
# 1. Descarcă ngrok.exe de pe ngrok.com
# 2. Creează cont gratuit, obține authtoken
ngrok config add-authtoken <token>
ngrok http 8000
# URL apare în terminal: https://xxxx.ngrok-free.app
```

### Conturi necesare
- Cont ngrok gratuit (ngrok.com)

### Cost real
**Gratuit cu limitări severe:**
- 1 GB bandwidth/lună
- 20.000 HTTP requests/lună
- Pagină interstitial de avertizare injectată în tot HTML-ul din browser
- 1 agent simultan

### Securitate
⭐⭐⭐ — Mediu. TLS automat. Dar pagina interstitial înseamnă că ngrok vede tot traficul HTML.

### Compatibilitate cu proiectul
⚠️ **Parțial compatibil** — WebSocket și SSE funcționează. **Probleme critice:**
- **Pagina interstitial** injectată în HTML **distruge PWA** — service worker și manifest fetch sunt afectate
- **1 GB/lună** se epuizează rapid cu streaming AI (SSE = date continue)
- URL-ul se schimbă la fiecare restart (pe free tier)

### Limitări
- 1 GB bandwidth/lună — insuficient pentru utilizare curentă cu AI streaming
- Pagina interstitial incompatibilă cu PWA
- URL aleator (nu personalizabil pe free tier)
- 20.000 requests/lună — depășit rapid

### ⚠️ Poate strica proiectul?
**Risc mic pentru proiect** — nu modifică codul. Dar experiența utilizatorului este degradată major de pagina interstitial. **Nu recomandat pentru utilizare regulată.**

### Grad dificultate implementare
**1/5** — setup în 5 minute.

---

## 4. Serveo.net

### Cum funcționează
SSH reverse port forwarding fără cont, fără instalare suplimentară. Deschizi un tunel SSH de pe PC către serverele Serveo, care forwardează traficul.

### Pași de configurare
```bash
# Pe Windows, din PowerShell (necesită SSH instalat):
ssh -R 80:localhost:8000 serveo.net
# sau cu subdomain fix:
ssh -R myapp:80:localhost:8000 serveo.net
# URL: https://myapp.serveo.net
```

### Conturi necesare
- **Niciun cont** — funcționează direct via SSH

### Cost real
**Gratuit** (cu pagină interstitial). Pro: 6$/lună (elimină interstitial, subdomenii permanente).

### Securitate
⭐⭐ — Slab. Pagina interstitial înseamnă că Serveo vede traficul. Fără autentificare pentru vizitatori.

### Compatibilitate cu proiectul
⚠️ **Probleme de fiabilitate** — outage-uri de 2-4 zile raportate în 2025. Pagina interstitial afectează PWA. A adăugat recent WireGuard și extensie Chrome, dar stabilitatea rămâne incertă.

### Limitări
- Fiabilitate scăzută (serviciu menținut de o singură persoană)
- Pagina interstitial incompatibilă cu PWA
- Nu există SLA sau garanție uptime

### ⚠️ Poate strica proiectul?
**NU** — nu modifică proiectul. Dar dacă Serveo e down, accesul e pierdut complet.

### Grad dificultate implementare
**1/5** — o singură comandă SSH.

---

## 5. localhost.run

### Cum funcționează
Similar Serveo — SSH reverse tunnel fără instalare.

### Pași de configurare
```bash
ssh -R 80:localhost:8000 localhost.run
# URL aleator: https://xxxx-xxx.lhr.life
```

### Conturi necesare
- **Niciun cont** pe free tier
- Cont plătit (4$/lună) pentru URL permanent

### Cost real
**Gratuit** cu limitări: URL-uri aleatorii care se rotesc, speed throttling pe free tier.

### Securitate
⭐⭐ — Slab. Fără autentificare, URL-uri temporare.

### Compatibilitate cu proiectul
❌ **Probleme majore** — URL-urile se rotesc (PWA nu poate fi instalat cu URL instabil), speed throttling afectează streaming AI.

### ⚠️ Poate strica proiectul?
**NU** — nu modifică proiectul. Inutilizabil pentru acces persistent.

### Grad dificultate implementare
**1/5** — o comandă.

---

## 6. ZeroTier

### Cum funcționează
Rețea virtuală Layer 2 (Ethernet) — dispozitivele se comportă ca pe același switch fizic. Protocol custom (Curve25519 + Salsa20/Poly1305). Mai flexibil decât Tailscale la Layer 2, dar mai complex de configurat.

### Pași de configurare
```
1. Cont gratuit pe zerotier.com
2. Creează o rețea → obții Network ID (16 cifre)
3. Instalează ZeroTier One pe PC: zerotier.com/download
4. Instalează ZeroTier One pe Android (Play Store)
5. Pe PC: zerotier-cli join <NetworkID>
6. Aprobă dispozitivele în dashboard zerotier.com
7. Accesezi aplicația via IP ZeroTier (ex: 10.147.17.x:8000)
8. Configurează manual TLS sau accesează via HTTP pe rețeaua privată
```

### Conturi necesare
- Cont ZeroTier gratuit (zerotier.com)
- Free tier 2025: **10 dispozitive, 1 rețea** (redus de la 25)

### Cost real
**Gratuit** (10 dispozitive). Essential: ~5$/lună pentru mai multe.

### Securitate
⭐⭐⭐⭐ — Bun. Rețea privată Layer 2. Fără expunere internet.

### Compatibilitate cu proiectul
✅ **Compatibil tehnic** — WebSocket/SSE funcționează transparent la Layer 2. **Dezavantaje față de Tailscale:**
- Nu oferă MagicDNS (trebuie IP-uri sau DNS manual)
- Nu oferă certificate HTTPS automate (Tailscale cert nu există în ZeroTier)
- **PWA necesită HTTPS** — trebuie configurat manual TLS (mult mai complex)
- Nu are echivalent Funnel (nu poate expune public)

### Limitări
- Inferior Tailscale în toate dimensiunile relevante pentru acest proiect
- TLS manual necesar pentru PWA
- DNS manual sau IP-uri hardcodate

### ⚠️ Poate strica proiectul?
**Risc mic** dacă e instalat în paralel cu Tailscale. Dar dacă înlocuiești Tailscale cu ZeroTier, pierzi HTTPS automat și PWA se strică fără reconfigurare.

### Grad dificultate implementare
**2/5** pentru rețea, **4/5** pentru TLS + PWA.

---

## 7. WireGuard Direct

### Cum funcționează
Protocolul VPN pe care Tailscale îl folosește intern, dar configurat manual fără layer de management. Necesită generare manuală de chei, configurare fișiere .conf, și **obligatoriu port forwarding pe router sau VPS cu IP public**.

### Pași de configurare
```
1. Instalează WireGuard Windows: wireguard.com/install/
2. Generează perechi de chei (public/private) pentru PC și telefon
3. Creează fișiere .conf pe PC și telefon
4. Deschide portul UDP 51820 pe router (sau imposibil cu CGNAT)
5. Configurează IP-uri și routing manual
6. Testează conectivitate
```

### Conturi necesare
- **Niciunul** — open source

### Cost real
**Gratuit** (software). Dacă ISP folosește CGNAT: necesită VPS (~3-5€/lună).

### Securitate
⭐⭐⭐⭐⭐ — Maxim din punct de vedere criptografic (~4000 linii cod, auditabil).

### Compatibilitate cu proiectul
✅ **Compatibil tehnic** — dar Tailscale este literalmente WireGuard cu tot ce e dificil automatizat. Nu are avantaje față de Tailscale pentru acest caz.

### Limitări
- **Nu are NAT traversal automat** — necesită port forwarding sau VPS
- **CGNAT**: dacă ISP-ul tău folosește CGNAT (comun la operatorii români), port forwarding e imposibil
- Configurare manuală complexă pentru fiecare dispozitiv nou
- Fără DNS automat, fără cert HTTPS automat

### ⚠️ Poate strica proiectul?
**Risc mediu** — dacă configurezi greșit routingul, poți pierde conectivitate la internet temporar. Nu afectează codul aplicației.

### Grad dificultate implementare
**4/5** — complex fără beneficii față de Tailscale.

---

## 8. OpenVPN

### Cum funcționează
VPN clasic, anterior standard industrial. Necesită PKI complet (Certificate Authority, certificate server/client). Access Server (GUI) rulează doar pe Linux, nu pe Windows ca server.

### Pași de configurare
```
1. Instalează OpenVPN Community pe PC
2. Generează PKI (easy-rsa sau openssl)
3. Configurează server.conf + client.conf
4. Port forwarding UDP 1194 pe router (aceleași probleme CGNAT)
5. Instalează OpenVPN pe Android
6. Importă configurație client
```

### Cost real
**Gratuit** (Community). Access Server: ~18$/lună.

### Securitate
⭐⭐⭐⭐ — Bun, dar criptografia e mai veche decât WireGuard.

### Compatibilitate cu proiectul
✅ **Compatibil tehnic** — dar performanță de 2-3x mai slabă decât WireGuard/Tailscale.

### ⚠️ Poate strica proiectul?
**NU** — nu afectează codul. Dar dacă înlocuiești Tailscale, pierzi HTTPS automat și PWA se strică.

### Grad dificultate implementare
**5/5** — cel mai complex setup din listă, fără avantaje față de Tailscale.

---

## 9. Port Forwarding + DuckDNS

### Cum funcționează
Configurezi routerul să forwardeze portul 443 extern → portul 8000 intern. Folosești DuckDNS (DDNS gratuit, 5 subdomenii) pentru DNS dinamic. Obții certificate Let's Encrypt cu `win-acme` pentru HTTPS.

### Pași de configurare
```
1. Verifică dacă ISP-ul tău folosește CGNAT (ping IP public din router)
2. Creează cont DuckDNS (duckdns.org) → obții subdomain.duckdns.org
3. Instalează clientul DuckDNS pe PC (actualizare IP dinamică)
4. Instalează win-acme (letsencrypt pentru Windows)
5. Obține cert: wacs.exe --target manual --host subdomain.duckdns.org
6. Configurează router: Port Forward 443 → PC_IP:8000
7. Modifică START_Production.bat: adaugă certfile/keyfile pentru subdomain
8. Adaugă subdomain.duckdns.org în CORS_ORIGINS
```

### Conturi necesare
- Cont DuckDNS gratuit (duckdns.org)
- Acces admin router

### Cost real
**Gratuit** — DuckDNS gratuit, Let's Encrypt gratuit.

### Securitate
⭐⭐ — **Cel mai slab din listă.** IP-ul de acasă este expus direct pe internet. Suprafață de atac: DDoS, port scanning, brute-force. **Fără autentificare** înainte de a ajunge la aplicație.

### Compatibilitate cu proiectul
✅ **Compatibil tehnic** — WebSocket/SSE nativ. Necesită modificare `START_Production.bat` și `CORS_ORIGINS`.

### Limitări
- **CGNAT**: dacă ISP-ul tău (RCS/RDS, Vodafone România) folosește CGNAT → **imposibil** fără IP fix plătit
- Expune IP-ul fizic de acasă pe internet
- Cert Let's Encrypt expiră la 90 zile (reînnoire automată cu win-acme, dar un punct de eșec)
- Dacă IP-ul se schimbă și DuckDNS nu se actualizează → aplicație inaccesibilă

### ⚠️ Poate strica proiectul?
**Risc mediu** — modificarea START_Production.bat cu certfile/keyfile greșite poate opri uvicorn. **Recomand backup** înainte. Nu afectează codul aplicației.

### Grad dificultate implementare
**3/5** — complex și cu risc de securitate.

---

## 10. Reverse SSH Tunnel via VPS

### Cum funcționează
Închiriezi un VPS cu IP public. Stabilești o conexiune SSH outbound de pe Windows 10 cu reverse port forwarding. VPS-ul forwardează traficul public → tunelul SSH → localhost:8000. Nginx + Let's Encrypt pe VPS oferă HTTPS cu domeniu personalizat.

### Pași de configurare
```
# Pe VPS (Linux):
apt install nginx certbot
certbot --nginx -d app.yourdomain.com
# nginx.conf: proxy_pass http://localhost:8080;

# Pe Windows 10 (PowerShell / WSL / Cygwin + autossh):
autossh -M 0 -f -N -R 0.0.0.0:8080:localhost:8000 user@VPS_IP

# Sau cu Task Scheduler pentru auto-start la login
```

### Conturi necesare
- VPS cu IP public — **Oracle Cloud Free Tier** (4 cores ARM, 24GB RAM — dacă reușești signup, notoriu dificil) sau **Hetzner** (~3.49€/lună)
- Domeniu (~10$/an, opțional)

### Cost real
**Gratuit** cu Oracle Cloud (dacă obții cont) sau **~3.49€/lună** Hetzner. Domeniu opțional.

### Securitate
⭐⭐⭐⭐ — Bun. Traficul e criptat SSH. IP-ul de acasă nu e expus. Poți adăuga autentificare pe nginx.

### Compatibilitate cu proiectul
✅ **Compatibil** — WebSocket/SSE funcționează prin tunel SSH. Necesită adăugarea domeniului VPS în `CORS_ORIGINS`.

### Limitări
- Necesită mentenanță VPS (actualizări, monitorizare)
- Conexiunea SSH se poate deconecta (autossh rezolvă parțial)
- Oracle Cloud: signup extrem de dificil (carduri respinse frecvent)
- Latență adăugată față de Tailscale P2P (trafic trece prin VPS)

### ⚠️ Poate strica proiectul?
**Risc mic** — nu modifică codul aplicației. Risc: dacă tunelul SSH e configurat greșit, aplicația e inaccesibilă dar nu stricată.

### Grad dificultate implementare
**3/5** — necesită cunoștințe Linux și SSH.

---

## 11. frp (Fast Reverse Proxy)

### Cum funcționează
Open-source (Apache 2.0, 89k+ stars GitHub). Arhitectură client-server: `frps` rulează pe VPS, `frpc` rulează pe Windows 10. Suportă explicit HTTP, HTTPS, WebSocket, TCP, UDP cu compresie și criptare TLS între client-server.

### Pași de configurare
```toml
# frps.toml (pe VPS):
bindPort = 7000
[webServer]
port = 7500
dashboard = true

# frpc.toml (pe Windows):
serverAddr = "VPS_IP"
serverPort = 7000
[[proxies]]
name = "command-center"
type = "https"
localPort = 8000
customDomains = ["app.yourdomain.com"]
```

### Conturi necesare
- VPS cu IP public (Oracle Free sau Hetzner ~3.49€/lună)
- Domeniu (~10$/an)

### Cost real
**Gratuit** (software open-source) + cost VPS.

### Securitate
⭐⭐⭐ — Mediu-bun. Criptare TLS între frpc și frps. Fără autentificare nativă pentru vizitatori (trebuie adăugată manual).

### Compatibilitate cu proiectul
✅ **Compatibil** — WebSocket suportat explicit în frp. CORS_ORIGINS trebuie actualizat.

### Limitări
- Necesită VPS (nu zero-budget pur)
- Mai complex decât Cloudflare Tunnel fără avantaje clare
- Mentenanță duală (frps pe VPS + frpc pe Windows)

### ⚠️ Poate strica proiectul?
**Risc mic** — nu modifică codul. Necesită adăugarea domeniului în CORS.

### Grad dificultate implementare
**4/5** — configurare fișiere TOML + VPS setup.

---

## 12. Bore

### Cum funcționează
Tunel TCP minimalist (~400 linii Rust). Server public gratuit la `bore.pub`. Comanda: `bore local 8000 --to bore.pub`. URL: `http://bore.pub:PORT` (port aleator >10000).

### Pași de configurare
```bash
# Instalează bore (necesită Rust sau descarcă binary)
cargo install bore-cli
bore local 8000 --to bore.pub
# URL: http://bore.pub:54321 (port aleator)
```

### Cost real
**Gratuit** — server public.

### Securitate
⭐ — Minim. Fără autentificare, fără HTTPS, tunel TCP raw.

### Compatibilitate cu proiectul
❌ **Incompatibil pentru PWA** — **nu oferă HTTPS**. PWA necesită HTTPS obligatoriu. URL-ul include port non-standard.

### ⚠️ Poate strica proiectul?
**NU** — nu modifică nimic. Inutilizabil pentru scopul proiectului.

### Grad dificultate implementare
**1/5** — setup, dar inutilizabil.

---

## 13. Playit.gg

### Cum funcționează
Orientat gaming (Minecraft, Terraria) dar suportă tuneluri TCP generice. Free tier: 4 tuneluri TCP + 4 UDP, Global Anycast routing.

### Pași de configurare
```
1. Cont gratuit playit.gg
2. Descarcă agent Windows
3. Configurează tunel TCP pentru portul 8000
4. URL: XX.ip.gl.ply.gg:PORT (port non-standard)
```

### Cost real
**Gratuit** (cu limitări). Plus: 3$/lună.

### Securitate
⭐⭐ — Slab. URL-uri cu porturi non-standard, unii ISP blochează domeniile Playit.

### Compatibilitate cu proiectul
❌ **Incompatibil** — URL-urile includ porturi non-standard, fără HTTPS nativ, unii ISP blochează domeniile. **PWA incompatibil.**

### ⚠️ Poate strica proiectul?
**NU** — nu modifică nimic. Inutilizabil.

### Grad dificultate implementare
**2/5** — setup, dar nerecomandat.

---

## 14. Vercel / Railway / Render (Cloud Hosting)

### De ce sunt incompatibile (scurt)

**Vercel** — Serverless stateless, **SQLite nu poate persista date**, **WebSocket nu este suportat** nativ pe Functions. Util **doar** pentru hosting frontend React static (deja folosit pentru alte proiecte).

**Railway** — A eliminat free tier permanent. Trial: credit $5 expirat în 30 zile. Hobby: 5$/lună. Suportă SQLite cu volume + WebSocket, dar **nu zero-budget**.

**Render** — Free tier: auto-sleep la 15 minute inactivitate (cold start ~1 min), **filesystem efemer** (datele SQLite se pierd la spin-down). Disk persistent: 7$/lună+.

**Fly.io** — Nu mai are free tier din octombrie 2024. Trial: 2 ore sau 7 zile. Cost: ~3-5$/lună.

### Concluzie cloud
Nicio platformă cloud nu satisface simultan: **buget zero + SQLite persistent + WebSocket + PWA**. Aplicația trebuie să rămână self-hosted.

### ⚠️ Poate strica proiectul?
**DA — risc major** dacă încerci să muți backend-ul pe cloud fără migrarea SQLite. Datele s-ar pierde. **Nu recomand** fără o strategie completă de migrare DB (Litestream, PlanetScale, etc.).

### Grad dificultate implementare
**N/A** — nefezabil în condițiile actuale.

---

## 15. VPS Propriu (Hetzner + Nginx)

### Cum funcționează
Închiriezi un VPS Linux (Hetzner CX11 ~3.49€/lună — cel mai ieftin opțional recomandat). Muți aplicația pe VPS sau îl folosești ca **reverse proxy** pentru aplicația de pe Windows 10 (via tunel SSH sau frp). Nginx + Let's Encrypt pe VPS.

### Cost real
**~3.49€/lună** (Hetzner CX11: 2 vCPU, 2GB RAM, 40GB SSD, 20TB traffic). Nu este zero-budget.

### Securitate
⭐⭐⭐⭐ — Bun. IP fix, domeniu propriu, TLS automat.

### Compatibilitate cu proiectul
✅ **Compatibil ca reverse proxy** — aplicația rămâne pe Windows 10, VPS-ul forwardează traficul. WebSocket/SSE funcționează. SQLite rămâne local.

### ⚠️ Poate strica proiectul?
**Risc mic** dacă folosit ca proxy. **Risc major** dacă muți aplicația pe VPS fără SQLite sync strategy.

### Grad dificultate implementare
**4/5** — necesită administrare Linux continuă.

---

## Clasificare Finală — Tabel Comparativ

| # | Metodă | Cost real | WebSocket/SSE | PWA (HTTPS) | SQLite local OK | Securitate | Dificultate | ⚠️ Risc proiect | Scor |
|---|--------|-----------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **0** | **Tailscale** (curentă) | Gratuit | ✅ | ✅ Auto | ✅ | ⭐⭐⭐⭐⭐ | N/A | 🟢 Nul | **9.5** |
| **2** | **Cloudflare Tunnel + ZT** | Gratuit+domeniu | ✅ | ✅ Auto | ✅ | ⭐⭐⭐⭐⭐ | 2/5 | 🟢 Minim | **9.0** |
| **1** | **Tailscale Funnel** | Gratuit | ⚠️ Bug minor | ✅ Auto | ✅ | ⭐⭐⭐⭐ | 1/5 | 🟡 Mic | **8.0** |
| **6** | **ZeroTier** | Gratuit | ✅ | ❌ Manual | ✅ | ⭐⭐⭐⭐ | 4/5 | 🟡 Mediu | **6.5** |
| **10** | **Reverse SSH + VPS** | 0-3.49€/lună | ✅ | ✅ Manual | ✅ | ⭐⭐⭐⭐ | 3/5 | 🟢 Mic | **6.5** |
| **9** | **Port Forward + DuckDNS** | Gratuit | ✅ | ✅ Manual | ✅ | ⭐⭐ | 3/5 | 🟡 Mediu | **5.0** |
| **7** | **WireGuard Direct** | Gratuit+VPS | ✅ | ❌ Manual | ✅ | ⭐⭐⭐⭐⭐ | 4/5 | 🟡 Mediu | **5.0** |
| **11** | **frp** | +VPS | ✅ | ✅ Manual | ✅ | ⭐⭐⭐ | 4/5 | 🟢 Mic | **5.0** |
| **3** | **ngrok** | Gratuit (1GB/lună) | ✅ | ⚠️ Interstitial | ✅ | ⭐⭐⭐ | 1/5 | 🟢 Nul | **4.0** |
| **15** | **VPS Hetzner+Nginx** | ~3.49€/lună | ✅ | ✅ Auto | ✅ cu sync | ⭐⭐⭐⭐ | 4/5 | 🔴 Mare | **4.0** |
| **4** | **Serveo.net** | Gratuit | ✅ | ⚠️ Interstitial | ✅ | ⭐⭐ | 1/5 | 🟢 Nul | **3.5** |
| **8** | **OpenVPN** | Gratuit+VPS | ✅ | ❌ Manual | ✅ | ⭐⭐⭐⭐ | 5/5 | 🟡 Mediu | **3.0** |
| **5** | **localhost.run** | Gratuit | ⚠️ | ⚠️ URL instabil | ✅ | ⭐⭐ | 1/5 | 🟢 Nul | **2.5** |
| **13** | **Playit.gg** | Gratuit | ✅ TCP | ❌ | ✅ | ⭐⭐ | 2/5 | 🟢 Nul | **2.0** |
| **12** | **Bore** | Gratuit | ✅ TCP | ❌ | ✅ | ⭐ | 1/5 | 🟢 Nul | **1.5** |
| **14** | **Vercel/Railway/Render** | 0-5$/lună | ❌/✅/✅ | ✅ | ❌ Efemer | ⭐⭐⭐ | 2/5 | 🔴 **MAJOR** | **1.0** |

---

## Recomandarea Optimă

### Strategia Ideală: Tailscale (primar) + Cloudflare Tunnel (secundar)

**Tailscale rămâne metoda primară** pentru toate scenariile normale — acces de pe telefonul personal, de pe laptopul personal, din mașină cu telefon conectat. Este deja configurat, testat, și funcționează perfect cu întregul stack.

**Cloudflare Tunnel + Zero Trust devine metoda secundară** pentru scenariile unde Tailscale nu este disponibil:
- Acces de pe un dispozitiv împrumutat (laptop coleg, calculator service)
- Acces de urgență fără aplicația Tailscale instalată
- Partajare temporară cu un client sau contabil (trimiti link + cod OTP)

### De ce nu alte metode?

| Metodă | Motivul eliminării |
|--------|-------------------|
| Tailscale Funnel | Beta, bug WebSocket, aplicația devine publică fără autentificare nativă |
| ZeroTier | Inferior Tailscale în toate dimensiunile, TLS manual complex |
| WireGuard Direct | Tailscale este WireGuard cu tot ce e dificil deja rezolvat |
| OpenVPN | Cel mai complex, performanță slabă, fără avantaje |
| Port Forward | Expune IP-ul de acasă, CGNAT posibil, risc securitate |
| ngrok | 1GB/lună insuficient, interstitial distruge PWA |
| Cloud hosting | SQLite incompatibil, risc major de pierdere date |
| Bore/Playit | Fără HTTPS, incompatibil cu PWA |

### Pași concreți pentru Cloudflare Tunnel (implementare secundară)

```
1. Cont Cloudflare gratuit: cloudflare.com (5 min)
2. Adaugă sau transferă un domeniu pe Cloudflare
3. Zero Trust dashboard → Networks → Tunnels → Create tunnel (GUI)
4. Descarcă cloudflared-windows-amd64.exe
5. Rulează token din dashboard → testează că app e accesibilă
6. Instalează ca serviciu Windows (auto-start):
   cloudflared.exe service install <TOKEN>
7. MODIFICARE COD NECESARĂ — în app/main.py sau app/config.py:
   Adaugă "https://app.yourdomain.com" în CORS_ORIGINS
8. Opțional: Zero Trust → Access → adaugă autentificare email OTP
```

**Timp total setup: ~30 minute. Zero impact pe codul aplicației (cu excepția CORS).**

### Avertizare importantă
Nu dezactiva sau înlocui Tailscale. Cele două metode coexistă fără conflict — Tailscale pentru acces privat P2P, Cloudflare Tunnel pentru acces public controlat.

---

*Document generat: 2026-03-19*  
*Surse: tailscale.com/pricing, tailscale.com/kb/1223/funnel, developers.cloudflare.com/tunnel, ngrok.com/docs/pricing-limits, zerotier.com/pricing, serveo.net, localhost.run/docs, github.com/fatedier/frp, github.com/ekzhang/bore*  
*Vers. 1.0 — Pentru revizuire Claude Code în contextul proiectului Roland Command Center*  
*Stack confirmat: FastAPI Python 3.13 + React 18 + SQLite + WebSocket/SSE + PWA + Windows 10 + Tailscale `desktop-cjuecmn.tail7bc485.ts.net:8000`*
