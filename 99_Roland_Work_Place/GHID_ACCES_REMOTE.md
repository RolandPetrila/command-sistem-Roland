# Ghid Acces Remote — Roland Command Center

> **Versiune: 3.0 — Unificata si curatata din V2**
> **Data:** 2026-03-20 | **Context:** FastAPI + React 18 + SQLite + WebSocket/SSE + PWA + Windows 10
> **Tailscale URL curent:** `https://desktop-cjuecmn.tail7bc485.ts.net:8000`

---

## CUPRINS

1. [Matrice Decizie Rapida](#matrice-decizie-rapida)
2. [Metoda 0 — Tailscale VPN Mesh (CURENTA)](#0-tailscale-vpn-mesh--metoda-curenta)
3. [Metoda 1 — Tailscale Funnel](#1-tailscale-funnel)
4. [Metoda 2 — Cloudflare Tunnel + Zero Trust](#2-cloudflare-tunnel--zero-trust)
5. [Metode Alternative (sumar)](#metode-alternative--sumar)
6. [Metode Eliminate](#metode-eliminate)
7. [Clasificare Finala — Tabel Comparativ](#clasificare-finala--tabel-comparativ)
8. [Recomandarea Optima](#recomandarea-optima)
9. [Checklist Implementare Cloudflare Tunnel](#checklist-implementare-cloudflare-tunnel)
10. [Cloudflare Access (Zero Trust) — Setup Practic](#cloudflare-access-zero-trust--setup-practic)
11. [Troubleshooting Tailscale](#troubleshooting-tailscale)
12. [Monitorizare si Contingenta](#monitorizare-si-contingenta)
13. [Modificari fata de V2](#modificari-fata-de-v2)

---

## Matrice Decizie Rapida

| Scenariul tau | Metoda recomandata | Timp setup | Observatii |
|---|---|---|---|
| Acces normal PC + telefon personal | **Tailscale** (actuala) | Deja configurat | Nimic de facut |
| Acces de pe dispozitiv strain | **Cloudflare Tunnel** | ~30 min prima data | Necesita domeniu (~10$/an) |
| Demonstratie rapida unui client | **Tailscale Funnel** | ~5 min | Aplicatia devine publica temporar |
| Backup daca Tailscale e down | **Cloudflare Tunnel** | ~30 min prima data | Coexista cu Tailscale |
| Partajare cu contabil/client | **Cloudflare + Zero Trust** | ~45 min prima data | Email OTP gratuit, pana la 50 useri |
| Buget absolut zero, fara exceptii | **Tailscale** (ramane singura) | N/A | Cloudflare Quick Tunnel = alternativa (URL temporar) |

---

## 0. Tailscale VPN Mesh — Metoda Curenta

**Status: IMPLEMENTAT SI FUNCTIONAL**

### Cum functioneaza

Tailscale creeaza un VPN mesh peer-to-peer bazat pe WireGuard. Fiecare dispozitiv primeste un IP stabil (100.x.x.x) si un hostname DNS via MagicDNS (`desktop-cjuecmn.tail7bc485.ts.net`). Traficul circula **direct intre dispozitive** (P2P), fara a trece prin serverele Tailscale. Cand conexiunea directa nu e posibila (NAT strict), se folosesc servere DERP ca relay.

### Configurare

**Deja configurat** — HTTPS/TLS via `tailscale cert`, uvicorn cu SSL, CORS dinamic, PWA functional, URL dinamic in `client.js`.

### Detalii

| Aspect | Valoare |
|---|---|
| Cost | **Gratuit** — Plan Personal: 3 utilizatori, 100 dispozitive |
| Securitate | 5/5 — Numai dispozitivele din tailnet pot accesa. Criptare WireGuard E2E |
| Compatibilitate | Perfect — WebSocket/SSE nativ, PWA functional, latenta <2ms P2P |
| Risc proiect | Nul — este metoda curenta, deja stabila |

### Limitari

- Tailscale trebuie instalat pe fiecare dispozitiv client
- Daca Tailscale e oprit pe PC, aplicatia e inaccesibila de pe telefon
- Nu poate fi accesat de pe un browser fara Tailscale (ex: calculator imprumutat)

### Tailscale ACLs (Access Control Lists)

ACL-urile controleaza **ce dispozitiv poate accesa ce serviciu** din tailnet. Se configureaza din Tailscale Admin Console > Access Controls.

**Configurare practica:**
```jsonc
// Tailscale Admin Console > Access Controls > Edit
{
  "acls": [
    // Roland poate accesa totul de pe orice dispozitiv propriu
    {
      "action": "accept",
      "src": ["autogroup:member"],
      "dst": ["*:*"]
    }
  ]
  // Optional: un dispozitiv guest poate accesa DOAR portul 8000
  // {
  //   "action": "accept",
  //   "src": ["tag:guest"],
  //   "dst": ["desktop-cjuecmn:8000"]
  // }
}
```

**Pentru proiectul curent:** ACL-ul implicit (`autogroup:member` > `*:*`) este suficient pentru single-user. Modifica doar daca adaugi dispozitive de test sau partajezi tailnet-ul.

### Tailscale SSH

Permite conectare SSH directa la PC prin tailnet, **fara a deschide porturi sau a configura SSH server separat**. Util pentru: restart uvicorn, verificare loguri, kill procese zombie — de pe telefon via Termius/JuiceSSH.

```bash
# Pe Windows (PowerShell ca Administrator):
tailscale set --ssh

# De pe telefon (cu Tailscale instalat):
ssh roland@desktop-cjuecmn
# sau prin IP:
ssh roland@100.x.x.x
```

**Nota:** Pe Windows, necesita OpenSSH Server instalat (Settings > Apps > Optional Features > OpenSSH Server).

### Tailnet Lock

Functie de securitate care **impiedica adaugarea de dispozitive noi** in tailnet fara aprobarea explicita a unui dispozitiv deja autorizat. Previne scenariul in care cineva obtine acces la contul tau Tailscale si adauga un dispozitiv strain.

```bash
# Pe un dispozitiv deja autorizat:
tailscale lock init

# Cand adaugi dispozitiv nou:
tailscale lock sign <node-key-nou>
```

**Recomandat?** Da. Dezavantaj: daca pierzi toate dispozitivele cu cheia de semnare, trebuie sa contactezi Tailscale support.

---

## 1. Tailscale Funnel

**Status: DISPONIBIL (Beta) — doar pentru demonstratii scurte**

### Cum functioneaza

Extensie a Tailscale care expune un serviciu local pe **internet public** printr-un URL HTTPS permanent, fara ca vizitatorul sa aiba nevoie de Tailscale. Traficul trece prin serverele de ingress Tailscale.

### Configurare

```bash
# Activare Funnel din Tailscale Admin Console > permisiunea "Funnel" pentru nodul tau

# Mapare port (recomandata — expune portul 8000 pe HTTPS/443):
tailscale serve --bg https+insecure://localhost:8000
tailscale funnel --bg 443

# Verificare status:
tailscale serve status
tailscale funnel status

# Dezactivare (dupa demonstratie):
tailscale funnel off
tailscale serve reset
```

**Nota:** Porturile 443/8443/10000 sunt porturile **externe** — portul local poate fi oricare via `tailscale serve`.

### Detalii

| Aspect | Valoare |
|---|---|
| Cost | **Gratuit** — inclus in planul Personal |
| Securitate | 4/5 — TLS automat, dar aplicatia e publica (oricine cu URL-ul acceseaza) |
| Compatibilitate | Compatibil, dar bug cunoscut: Funnel poate stripui query parameters din WebSocket upgrade (Issue #18651) |
| Risc proiect | Mic — nu modifica codul. **Opreste-l mereu dupa utilizare** |
| Dificultate | 1/5 — cateva comenzi CLI |

### Limitari

- Aplicatia devine **publica** — fara autentificare nativa
- Bug WebSocket query params (partial afecteaza SSE)
- **Recomandat doar pentru demonstratii scurte**

---

## 2. Cloudflare Tunnel + Zero Trust

**Status: NEIMPLEMENTAT — recomandat ca backup**

### Cum functioneaza

Daemonul `cloudflared` pe Windows creeaza o **conexiune outbound-only** criptata catre reteaua edge Cloudflare. Nu se deschide niciun port pe router. Cloudflare Zero Trust adauga autentificare (email OTP, Google SSO) inainte de a permite accesul.

### Configurare rapida

```
1. Cont Cloudflare gratuit (cloudflare.com)
2. Adauga domeniu pe Cloudflare (~10$/an pentru .com)
3. Zero Trust dashboard > Networks > Tunnels > Create tunnel
4. Descarca cloudflared-windows-amd64.exe
5. Ruleaza: cloudflared.exe tunnel run <token>
6. Configureaza hostname: app.yourdomain.com > http://localhost:8000
7. Instaleaza ca serviciu Windows: cloudflared.exe service install <token>
8. (Optional) Zero Trust > Access > protejeaza cu email OTP
```

**Pentru pasi detaliati, vezi sectiunea [Checklist Implementare Cloudflare Tunnel](#checklist-implementare-cloudflare-tunnel).**

### Detalii

| Aspect | Valoare |
|---|---|
| Cost | **Gratuit** (tunel) + ~10$/an (domeniu). Zero Trust: gratuit pana la 50 useri |
| Securitate | 5/5 — TLS automat, protectie DDoS, Zero Trust autentificare, WAF gratuit |
| Compatibilitate | Perfect — WebSocket nativ, SSE ca HTTP standard. Adauga domeniu in CORS |
| Risc proiect | Minim — singura modificare: adauga domeniu in `CORS_ORIGINS` |
| Dificultate | 2/5 — setup 20-30 minute, apoi ruleaza automat |

### Limitari

- Necesita domeniu (sau URL random temporar cu Quick Tunnel)
- `cloudflared` pe Windows nu se auto-actualizeaza
- Traficul trece prin serverele Cloudflare (vs. P2P in Tailscale)

---

## Metode Alternative — Sumar

Urmatoarele metode sunt **tehnic functionale** dar inferioare combinatiei Tailscale + Cloudflare Tunnel pentru acest proiect. Pastrate aici ca referinta.

### ngrok

Tunel HTTPS cu URL public. **Probleme:** 1 GB bandwidth/luna (insuficient cu AI streaming), pagina interstitial injectata in HTML distruge PWA, 20.000 requests/luna. Gratuit dar inutilizabil practic. Setup: 5 minute. **Verdict: nu pentru utilizare regulata.**

### ZeroTier

Retea virtuala Layer 2, similar Tailscale. **Probleme:** nu ofera MagicDNS, nu ofera certificate HTTPS automate (PWA necesita HTTPS manual — mult mai complex), nu are echivalent Funnel. Free tier: 10 dispozitive. **Verdict: inferior Tailscale in toate dimensiunile relevante.**

### Port Forwarding + DuckDNS

Router port forward + DNS dinamic gratuit + Let's Encrypt. **Probleme:** expune IP-ul de acasa direct pe internet (securitate 2/5), CGNAT la operatorii romani (RCS/RDS, Vodafone) poate bloca complet, cert expira la 90 zile. **Verdict: risc de securitate nejustificat.**

### Reverse SSH Tunnel via VPS

Tunel SSH outbound de pe Windows catre VPS cu IP public + Nginx + Let's Encrypt. **Probleme:** necesita VPS (~3.49 EUR/luna Hetzner), cunostinte Linux, mentenanta continua. Oracle Cloud Free Tier e gratuit dar signup-ul reuseste la sub 30% din incercari. **Verdict: complex si nu zero-budget.**

### frp (Fast Reverse Proxy)

Open-source, client-server: `frps` pe VPS, `frpc` pe Windows. WebSocket suportat. **Probleme:** necesita VPS, mai complex decat Cloudflare Tunnel fara avantaje clare, mentenanta duala. **Verdict: Cloudflare Tunnel e superior in orice scenariu.**

### VPS Propriu (Hetzner + Nginx)

VPS Linux (~3.49 EUR/luna) ca reverse proxy. **Probleme:** nu e zero-budget, necesita administrare Linux continua, risc major daca muti aplicatia pe VPS fara SQLite sync strategy. **Verdict: overkill pentru single-user.**

---

## Metode Eliminate

Urmatoarele metode au fost evaluate si sunt **toate nepotrivite** pentru Roland Command Center:

**WireGuard Direct, OpenVPN, Serveo.net, localhost.run, Bore, Playit.gg, Vercel/Railway/Render** — eliminate din motive variate: WireGuard Direct si OpenVPN sunt versiuni manuale ale ceea ce Tailscale face automat, fara avantaje. Serveo.net are outage-uri de saptamani intregi (complet nefiabil). localhost.run are URL-uri instabile incompatibile cu PWA. Bore si Playit.gg nu ofera HTTPS (obligatoriu pentru PWA). Vercel/Railway/Render sunt incompatibile fundamental cu SQLite local + buget zero (Railway a eliminat free tier din 2024, Render pierde datele la spin-down, Vercel nu suporta WebSocket pe Functions).

---

## Clasificare Finala — Tabel Comparativ

| # | Metoda | Cost | WS/SSE | PWA | Securitate | Dificultate | Scor |
|---|--------|------|:---:|:---:|:---:|:---:|:---:|
| **0** | **Tailscale** (curenta) | Gratuit | Da | Da Auto | 5/5 | N/A | **9.5** |
| **2** | **Cloudflare Tunnel + ZT** | Gratuit+domeniu | Da | Da Auto | 5/5 | 2/5 | **9.0** |
| **1** | **Tailscale Funnel** | Gratuit | Bug minor | Da Auto | 4/5 | 1/5 | **8.0** |
| **6** | ZeroTier | Gratuit | Da | Manual | 4/5 | 4/5 | 6.5 |
| **10** | Reverse SSH + VPS | 0-3.49 EUR/luna | Da | Manual | 4/5 | 3/5 | 6.5 |
| **9** | Port Forward + DuckDNS | Gratuit | Da | Manual | 2/5 | 3/5 | 5.0 |
| **3** | ngrok | Gratuit (1GB/luna) | Da | Interstitial | 3/5 | 1/5 | 4.0 |

---

## Recomandarea Optima

### Strategia: Tailscale (primar) + Cloudflare Tunnel (secundar)

**Tailscale ramane metoda primara** pentru toate scenariile normale — acces de pe telefonul personal, laptopul personal, din masina cu telefon conectat. Deja configurat, testat, functional.

**Cloudflare Tunnel + Zero Trust devine metoda secundara** pentru:
- Acces de pe un dispozitiv imprumutat (laptop coleg, calculator service)
- Acces de urgenta fara aplicatia Tailscale instalata
- Partajare temporara cu un client sau contabil (link + cod OTP)

**Alternativa pentru notificari:** In loc sa tii Tailscale activ permanent pe telefon, poti configura **Web Push Notifications** din PWA — aplicatia trimite notificari direct in browser cand apar alerte (ITP expirare, facturi, task-uri). Astfel, Tailscale ramane oprit pe telefon si il pornesti doar cand ai nevoie de acces complet.

### Avertizare

Nu dezactiva sau inlocui Tailscale. Cele doua metode coexista fara conflict — Tailscale pentru acces privat P2P, Cloudflare Tunnel pentru acces public controlat.

---

## Checklist Implementare Cloudflare Tunnel

### Cerinte prealabile

- [ ] Cont Cloudflare gratuit creat (cloudflare.com)
- [ ] Domeniu inregistrat si adaugat pe Cloudflare (~10$/an) **SAU** decizie de a folosi Quick Tunnel (URL temporar)
- [ ] Nameservers actualizati la Cloudflare (daca domeniu propriu)
- [ ] Windows 10 cu acces Administrator
- [ ] Proiectul pornit si functional pe `localhost:8000`

### Pasul 1 — Descarca cloudflared

```powershell
# Varianta 1: Download manual
# https://github.com/cloudflare/cloudflared/releases/latest
# Fisierul: cloudflared-windows-amd64.exe
# Pune-l in: C:\Program Files\cloudflared\cloudflared.exe

# Varianta 2: Cu winget
winget install Cloudflare.cloudflared
```

### Pasul 2 — Creeaza tunelul din dashboard

```
1. Deschide: https://one.dash.cloudflare.com/
2. Zero Trust > Networks > Tunnels > Create a tunnel
3. Tip: Cloudflared
4. Nume tunel: "roland-command-center"
5. Copiaza token-ul generat (incepe cu eyJ...)
```

### Pasul 3 — Ruleaza tunelul pe Windows

```powershell
# Test manual (prima data):
cloudflared.exe tunnel run --token eyJ...TOKEN_COMPLET...

# Daca functioneaza, instaleaza ca serviciu Windows (auto-start):
cloudflared.exe service install eyJ...TOKEN_COMPLET...

# Verificare serviciu:
sc query cloudflared
# Trebuie sa arate: STATE = RUNNING
```

### Pasul 4 — Configureaza hostname-ul

```
1. In dashboard Zero Trust > Tunnels > "roland-command-center"
2. Tab "Public Hostname" > Add a public hostname
3. Subdomain: "app" (sau "cc", "panel")
4. Domain: yourdomain.com
5. Service Type: HTTP
6. URL: localhost:8000
7. Save
```

**Rezultat:** `https://app.yourdomain.com` trimite traficul la `localhost:8000` pe PC.

### Pasul 5 — Modificare CORS (OBLIGATORIU)

**Fisier:** `C:\Proiecte\NOU_Calculator_Pret_Traduceri\backend\app\main.py`

Cauta sectiunea `CORSMiddleware` / `allow_origins` si adauga:
```python
"https://app.yourdomain.com",
```

**Fara aceasta modificare:** Browser-ul blocheaza TOATE request-urile cu eroare CORS.

### Pasul 6 — Testare

```
1. Deschide https://app.yourdomain.com in browser (incognito)
2. Verifica: pagina se incarca complet
3. Verifica: un request API functioneaza (dashboard, health check)
4. Verifica: SSE/streaming AI functioneaza (AI chat, trimite mesaj)
5. Verifica: WebSocket fara erori in Console (F12 > Console)
6. Testeaza de pe telefon (fara Tailscale activ)
```

### Pasul 7 — Dezactivare sigura

```powershell
# Oprire serviciu (temporar):
sc stop cloudflared

# Dezinstalare serviciu (permanent):
cloudflared.exe service uninstall
```

### Quick Tunnel (alternativa fara domeniu)

```powershell
cloudflared tunnel --url http://localhost:8000
# Genereaza URL temporar: https://random-words.trycloudflare.com
# URL-ul se schimba la fiecare restart
# NU necesita cont Cloudflare, NU necesita modificare CORS
# Util DOAR pentru test rapid, nu pentru utilizare regulata
```

---

## Cloudflare Access (Zero Trust) — Setup Practic

Adauga un **layer de autentificare** inainte ca vizitatorul sa ajunga la aplicatie. Gratuit pana la 50 utilizatori. Fara Access, oricine cu URL-ul acceseaza direct aplicatia.

### Setup Email OTP

**Pasul 1 — Metoda de autentificare:**
```
1. Cloudflare Zero Trust Dashboard (one.dash.cloudflare.com)
2. Settings > Authentication > Login methods
3. Add new > "One-time PIN"
4. Save
```

**Pasul 2 — Politica de acces:**
```
1. Zero Trust > Access > Applications > Add an application
2. Tip: "Self-hosted"
3. Application name: "Roland Command Center"
4. Session duration: 24 hours (sau 7 days)
5. Application domain: app.yourdomain.com
6. Path: gol (protejeaza tot)
```

**Pasul 3 — Cine are acces:**
```
1. Policies > Add a policy
2. Policy name: "Roland Only"
3. Action: "Allow"
4. Selector: "Emails"
5. Value: roland@email-ul-tau.com
6. Save
```

**Pasul 4 — Mai multi utilizatori (optional):**
```
- Adauga email-uri: contabil@firma.ro, client@email.com
- Sau "Email domain" pentru toti de pe @cipinspection.ro
```

### Experienta utilizatorului

1. Deschide `https://app.yourdomain.com`
2. Vede pagina Cloudflare cu camp de email
3. Introduce email-ul (trebuie sa fie in lista)
4. Primeste cod de 6 cifre pe email
5. Introduce codul > redirectionat la aplicatie
6. Ramane logat pentru durata configurata

**Nota:** Acest flow se aplica DOAR accesului prin Cloudflare Tunnel. Accesul prin Tailscale ramane neschimbat.

### Bypass pentru API-uri

```
1. Access > Applications > "Roland Command Center" > Policies
2. Add policy > Action: "Bypass"
3. Selector: "URI Path" > Value: "/api/health"
4. Save
```

---

## Troubleshooting Tailscale

### Connection Refused

**Simptome:** Tailscale e conectat, ping merge, dar aplicatia da "Connection refused".

**Fix-uri:**

1. **uvicorn nu ruleaza:**
   ```powershell
   tasklist | findstr python
   # Daca nu apare:
   cd C:\Proiecte\NOU_Calculator_Pret_Traduceri
   START_Production.bat
   ```

2. **uvicorn asculta doar pe 127.0.0.1:**
   ```
   # Verifica in START_Production.bat ca host-ul e 0.0.0.0, NU 127.0.0.1
   # 0.0.0.0 = accepta conexiuni de pe orice interfata (inclusiv Tailscale)
   ```

3. **Windows Firewall blocheaza:**
   ```powershell
   netsh advfirewall firewall add rule name="Python uvicorn" dir=in action=allow program="C:\Python313\python.exe" enable=yes
   ```

### Conexiune prin DERP relay (lenta)

**Simptome:** Latenta >50ms in loc de <5ms.

```powershell
tailscale status
# "relay" langa dispozitiv = trafic prin DERP
tailscale ping desktop-cjuecmn
```

**Fix-uri:** Restart Tailscale pe ambele dispozitive. Verifica firewall router (UDP outbound). Asteapta 1-2 minute (NAT traversal).

### MagicDNS nu rezolva hostname-ul

**Simptome:** Hostname-ul nu se rezolva, dar IP-ul 100.x.x.x functioneaza.

1. Verifica MagicDNS: Tailscale Admin Console > DNS > MagicDNS > ON
2. Flush DNS: `ipconfig /flushdns`
3. Workaround: `https://100.x.x.x:8000` (poate da avertizare certificat)

### Certificatul TLS a expirat

**Simptome:** "Certificate expired" sau "NET::ERR_CERT_DATE_INVALID".

```powershell
tailscale cert desktop-cjuecmn.tail7bc485.ts.net
# Copiaza certificatele noi, reporneste uvicorn
```

**Certificatele Tailscale sunt valide 90 de zile.** Adauga `tailscale cert` la inceputul START_Production.bat pentru reinnoire automata.

### Tailscale nu porneste / ramane in "Connecting"

1. **Verifica serviciul:**
   ```powershell
   sc query Tailscale
   sc start Tailscale
   ```
2. **Logout + Login:**
   ```powershell
   tailscale logout
   tailscale login
   ```
3. **Reinstalare (ultima solutie):** Dezinstaleaza din Settings > Apps, descarca de pe tailscale.com/download, reinstaleaza.

---

## Monitorizare si Contingenta

### Verificare status de pe Android

**Metoda 1 — Aplicatia Tailscale:** Verifica ca PC-ul (desktop-cjuecmn) apare ca "Online".

**Metoda 2 — Browser:** Deschide `https://desktop-cjuecmn.tail7bc485.ts.net:8000/api/health`. Raspuns JSON = totul OK. Timeout = PC oprit sau Tailscale deconectat.

**Metoda 3 — Terminal (Termux/SSH):**
```bash
curl -k -s -o /dev/null -w "%{http_code}" https://desktop-cjuecmn.tail7bc485.ts.net:8000/api/health
# 200 = OK | 000 = timeout
```

### Verificare Cloudflare Tunnel (daca implementat)

```bash
curl -s -o /dev/null -w "%{http_code}" https://app.yourdomain.com/api/health
# 200 = OK | 502 = tunel activ dar aplicatia nu ruleaza | 000 = tunelul e down
```

### Plan de contingenta: Tailscale complet down

1. **Verifica statusul:** `https://status.tailscale.com/` — Tailscale a avut uptime >99.9% in 2024-2025, outage-urile globale sunt sub 30 minute
2. **Daca ai Cloudflare Tunnel:** Acceseaza `https://app.yourdomain.com` — functioneaza independent
3. **Daca NU ai Cloudflare Tunnel si ai acces fizic la PC:**
   ```powershell
   cloudflared tunnel --url http://localhost:8000
   # Copiaza URL-ul generat si acceseaza-l de pe telefon
   ```
4. **Daca nu ai acces fizic la PC:** Nu exista solutie fara configurare prealabila. **Aceasta este motivul principal pentru Cloudflare Tunnel ca backup.**

### Monitorizare automata (optional)

- **UptimeRobot** (gratuit, 5 min interval): Monitor HTTP catre `https://app.yourdomain.com/api/health` (doar cu Cloudflare Tunnel activ)
- **Modulul Automations din proiect:** Faza 16 include Uptime Monitor — extensibil cu notificari
- **Web Push Notifications din PWA:** Alternativa la Tailscale permanent activ — primesti alerte direct in browser fara conexiune VPN activa

---

## Modificari fata de V2

### Ce s-a schimbat in V3 (aceasta versiune)

| Modificare | Detalii |
|---|---|
| **Eliminat detalii excesive** pe metode nerecomandate | WireGuard Direct, OpenVPN, Serveo, localhost.run, Bore, Playit.gg, Vercel/Railway/Render — condensate intr-un singur paragraf |
| **Condensat metode alternative** | ngrok, ZeroTier, Port Forward, Reverse SSH, frp, VPS — reduse la 2-3 linii fiecare |
| **Pastrat integral** | Tailscale (detaliat cu ACLs, SSH, Tailnet Lock), Cloudflare Tunnel (detaliat cu checklist si Zero Trust), Troubleshooting, Monitorizare |
| **Adaugat referinta Web Push** | Alternativa la Tailscale permanent activ pe telefon |
| **Simplificat tabelul comparativ** | Eliminat coloanele redundante, pastrat doar metodele relevante |
| **Redus volumul** | De la ~700 linii (V2) la ~480 linii (V3) — fara pierdere de informatii utile |
| **Eliminat sectiunea "Modificari V1 > V2"** | Inlocuita cu aceasta sectiune V2 > V3 |

---

*Document V3 generat: 2026-03-20*
*Bazat pe V2: 2026-03-20, V1: 2026-03-19*
*Stack: FastAPI Python 3.13 + React 18 + SQLite + WebSocket/SSE + PWA + Windows 10 + Tailscale*
