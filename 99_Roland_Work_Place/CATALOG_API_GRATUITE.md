# Catalog API Gratuite — Roland Command Center

> **Actualizat:** 2026-03-20
> **Conditie:** Toate API-urile din acest catalog sunt utilizabile GRATUIT (free tier permanent sau self-hosted)
> **Strategie:** Rotatie legitima intre platforme diferite (nu conturi multiple pe aceeasi platforma)
> **Compatibilitate:** Python 3.13 + FastAPI + Windows 10 + Tailscale mesh

---

## Sumar Executiv

| Categorie | Provider Primar | Limita Lunara Gratuita | Fallback Chain |
|---|---|---|---|
| AI Text Generation | Gemini Flash | 250 RPD, 250K TPM | Gemini -> Cerebras -> Groq -> Mistral -> SambaNova |
| Traduceri | DeepL Free | 500K chars/luna | DeepL -> Azure -> Google Direct -> MyMemory -> LibreTranslate |
| Text-to-Speech | edge-tts | Nelimitat | edge-tts -> Web Speech API -> Azure TTS F0 |
| OCR | Tesseract + EasyOCR | Nelimitat local | Tesseract/EasyOCR local -> OCR.space -> Azure Vision |
| Notificari Push | Web Push VAPID | Nelimitat | Web Push -> Telegram Bot -> ntfy.sh -> Email |
| Email | Gmail SMTP | 500/zi | Gmail -> Brevo -> Resend -> Mailgun |
| Stocare Cloud | Google Drive | 15 GB | Google Drive -> OneDrive -> Dropbox |
| Calendar | Google Calendar | ~1M queries/zi | Google Calendar -> Notion |
| Business RO | BNR XML | Nelimitat | BNR + ANAF — fara alternative necesare |
| Embeddings | Gemini Embeddings | Inclus in Gemini free | Gemini -> all-MiniLM-L6-v2 local -> Cohere -> Jina |
| Image Generation | Pollinations.ai | Nelimitat | Pollinations.ai (unic gratuit fara cheie) |
| PDF Generation | WeasyPrint | Nelimitat local | WeasyPrint (self-hosted) |
| Developer Tools | GitHub API | 5.000 req/ora | GitHub + Discord + Slack webhooks |

**Totaluri combinate zilnice/lunare:**
- **AI Text Generation:** ~2,2M tokeni/zi (~66M/luna)
- **Traduceri:** ~4,5M caractere/luna + nelimitat self-hosted
- **OCR:** Nelimitat local + ~20.000 req/luna cloud
- **Email:** ~900/zi (~27.000/luna)
- **TTS:** Nelimitat (edge-tts local)

---

## 1. AI Text Generation

**Priority chain:** Gemini Flash -> Cerebras -> Groq -> Mistral -> SambaNova
**Total combinat:** ~2,2M tokeni/zi

### Providers Recomandate

| Provider | Free Tier | Limita | Card | Calitate | API |
|---|---|---|---|---|---|
| Google Gemini | Permanent | 250-1000 RPD, 250K TPM | Nu | ★★★★★ | REST + OpenAI-compat |
| Cerebras | Permanent | 1M tokeni/zi | Nu | ★★★★☆ | OpenAI-compat |
| Groq | Permanent | ~30 RPM, ~14.4K RPD | Nu | ★★★★☆ | OpenAI-compat |
| Mistral AI | Permanent | ~1B tokeni/luna, 2 RPM | Nu | ★★★★☆ | OpenAI-compat |
| SambaNova | Permanent | 200K tokeni/zi, 20 RPD/model | Nu | ★★★☆☆ | OpenAI-compat |
| Cohere | Permanent | 1.000 calls/luna | Nu | ★★★☆☆ | REST Bearer |
| Hugging Face | Permanent | Credite lunare modeste | Nu | ★★★☆☆ | REST Bearer |

### Provider Details

**Google Gemini API** [GRATUIT FARA CARD]
- Modele: Gemini 2.5 Flash (250 RPD), Flash-Lite (1.000 RPD), Pro (50-100 RPD)
- Context: pana la 1M tokeni (Flash)
- Signup: aistudio.google.com/apikey
- Nota: restrictie EU/EEA in ToS, dar functional practic

```python
import httpx
r = httpx.post(f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}",
               json={"contents": [{"parts": [{"text": "Salut!"}]}]})
```

**Cerebras API** [GRATUIT FARA CARD]
- Modele: Llama 4 Scout, Qwen3, Llama 3.1 8B/70B
- Viteza: ~1.800 tokeni/sec (Llama 3.1 8B) — cea mai rapida inferenta
- Context: 64K tokeni
- Signup: cloud.cerebras.ai

```python
import httpx
r = httpx.post("https://api.cerebras.ai/v1/chat/completions",
               headers={"Authorization": f"Bearer {KEY}"},
               json={"model": "llama-3.1-8b", "messages": [{"role": "user", "content": "Salut!"}]})
```

**Groq** [GRATUIT FARA CARD]
- Modele: Llama 3.3 70B, Mixtral, Gemma 2
- Viteza: 300+ tokeni/sec (LPU hardware)
- Limita: ~30 RPM, ~14.400 RPD distribuite intre modele
- Signup: console.groq.com

```python
import httpx
r = httpx.post("https://api.groq.com/openai/v1/chat/completions",
               headers={"Authorization": f"Bearer {KEY}"},
               json={"model": "llama-3.3-70b-versatile", "messages": [{"role": "user", "content": "Salut!"}]})
```

**Mistral AI** [GRATUIT FARA CARD]
- Modele: Mistral Small, Large, Codestral, Mixtral, Pixtral
- Limita: ~1B tokeni/luna DAR doar 2 RPM (throughput mic)
- Caveat: datele din plan Experiment pot fi folosite pentru antrenare
- Signup: console.mistral.ai

```python
import httpx
r = httpx.post("https://api.mistral.ai/v1/chat/completions",
               headers={"Authorization": f"Bearer {KEY}"},
               json={"model": "mistral-small-latest", "messages": [{"role": "user", "content": "Salut!"}]})
```

**SambaNova** [GRATUIT FARA CARD]
- Modele: DeepSeek-R1, Llama 3.3 70B
- Limita: 200K tokeni/zi, 20 RPD per model — mai restrictiv
- Signup: cloud.sambanova.ai

```python
import httpx
r = httpx.post("https://api.sambanova.ai/v1/chat/completions",
               headers={"Authorization": f"Bearer {KEY}"},
               json={"model": "Meta-Llama-3.3-70B-Instruct", "messages": [{"role": "user", "content": "Salut!"}]})
```

### Providers cu Credite Limitate (nu in rotatie principala)

| Provider | Tip | Detalii | Status |
|---|---|---|---|
| AI21 Labs | $10 credit / 3 luni | 200 RPM, fara card | [CREDIT LIMITAT] |
| NVIDIA NIM | 1000-5000 credite one-time | ~40 RPM, necesita telefon | [CREDIT LIMITAT] |
| Fireworks AI | $1 credit la signup | 10 RPM, fara card | [CREDIT LIMITAT] |

### Providers Nerecomandate

| Provider | Motiv | Status |
|---|---|---|
| OpenAI | Free tier nefunctional — erori "quota exceeded" imediat, minimum $5 necesar | [FREE TIER NEFUNCTIONAL] |
| Anthropic Claude API | API exclusiv platit, doar claude.ai web are free tier limitat | [EXCLUSIV PLATIT] |
| Together AI | Free trial eliminat din iulie 2025, minimum $5 | [FREE TIER ELIMINAT] |
| Perplexity | Exclusiv pay-as-you-go, $5 credit/luna doar cu abonament Pro $20 | [EXCLUSIV PLATIT] |
| DeepSeek | Entitate chineza, restrictii securitate in multiple tari, date 30 zile | [CU PRECAUTIE] |

---

## 2. Traduceri Automate

**Priority chain:** DeepL -> Azure -> Google Direct HTTP -> MyMemory -> LibreTranslate
**Total combinat:** ~4,5M caractere/luna + nelimitat self-hosted

### Providers Recomandate

| Provider | Free Tier | Limita | Card | Calitate | Tip |
|---|---|---|---|---|---|
| DeepL Free | Permanent | 500K chars/luna | Nu | ★★★★★ | REST API |
| Azure Translator F0 | Permanent | 2M chars/luna | Da (F0 gratis) | ★★★★☆ | REST API |
| Google Direct HTTP | Permanent | Nelimitat* | Nu | ★★★★☆ | HTTP scraping |
| MyMemory | Permanent | 50K chars/zi cu email | Nu | ★★★☆☆ | REST GET |
| LibreTranslate | Self-hosted | Nelimitat | Nu | ★★★☆☆ | REST local |
| Argos Translate | Self-hosted | Nelimitat | Nu | ★★★☆☆ | Python lib |

*Google Direct HTTP: foloseste endpoint-ul direct fara API key, rate limiting nedocumentat

### Provider Details

**DeepL API Free** [GRATUIT FARA CARD]
- Calitate excelenta pentru limbile europene (EN<->RO foarte bun)
- Endpoint: api-free.deepl.com (diferit de cel platit)
- Max 2 chei active simultan
- Caveat: textul poate fi stocat pentru antrenare pe free tier
- Signup: deepl.com/pro/change-plan#developer

```python
import httpx
r = httpx.post("https://api-free.deepl.com/v2/translate",
               data={"auth_key": KEY, "text": "Hello world", "target_lang": "RO"})
```

**Azure Translator F0** [NECESITA CARD LA SIGNUP]
- 2.000.000 caractere/luna — cel mai mare volum din categorie
- Throttling automat la limita (nu suprataxare)
- Rate limit: 2M chars/ora
- Conturile noi: +$200 credit suplimentar 30 zile
- Signup: portal.azure.com -> Translator -> tier F0

```python
import httpx
r = httpx.post("https://api.cognitive.microsofttranslator.com/translate?api-version=3.0&to=ro",
               headers={"Ocp-Apim-Subscription-Key": KEY, "Content-Type": "application/json"},
               json=[{"Text": "Hello world"}])
```

**Google Translate Direct HTTP** [GRATUIT FARA CARD]
- Fara cheie API, fara signup — request HTTP direct
- Calitate Google Translate standard
- Rate limiting nedocumentat — nu abuza
- Deja implementat in backend/modules/translator/

```python
import httpx
r = httpx.get("https://translate.googleapis.com/translate_a/single",
              params={"client": "gtx", "sl": "en", "tl": "ro", "dt": "t", "q": "Hello world"})
```

**MyMemory** [GRATUIT FARA CARD]
- 5.000 chars/zi anonim, 50.000 chars/zi cu parametru email
- Fara signup necesar — cel mai simplu de integrat
- Calitate variabila (translation memory + ModernMT)

```python
import httpx
r = httpx.get("https://api.mymemory.translated.net/get",
              params={"q": "Hello world", "langpair": "en|ro", "de": "email@example.com"})
```

**LibreTranslate** [GRATUIT FARA CARD] — Self-hosted
- Bazat pe Argos Translate, AGPL-3.0
- `pip install libretranslate` sau Docker
- Nelimitat, offline dupa download modele
- ~30+ limbi suportate
- Pe Windows: Docker recomandat

```python
import httpx
r = httpx.post("http://localhost:5000/translate",
               json={"q": "Hello world", "source": "en", "target": "ro"})
```

---

## 3. Text-to-Speech (TTS) — NOU

**Priority chain:** edge-tts -> Web Speech API -> Azure TTS F0
**Total combinat:** Nelimitat (edge-tts local)

### Providers Recomandate

| Provider | Free Tier | Limita | Card | Calitate | Tip |
|---|---|---|---|---|---|
| edge-tts | Permanent | Nelimitat | Nu | ★★★★★ | Python lib |
| Web Speech API | Browser built-in | Nelimitat | Nu | ★★★☆☆ | JavaScript API |
| Azure TTS F0 | Permanent | 500K chars/luna | Da | ★★★★★ | REST API |

### Provider Details

**edge-tts** [GRATUIT FARA CARD] — RECOMANDAT
- Microsoft Neural TTS voices prin Edge — calitate identica cu Azure Neural
- Voci romanesti: `ro-RO-AlinaNeural` (feminin), `ro-RO-EmilNeural` (masculin)
- Nelimitat, fara cheie API, fara signup, fara limita de requests
- Output: MP3 direct, integrare simpla cu FastAPI
- Install: `pip install edge-tts`

```python
import edge_tts, asyncio
async def tts(text, voice="ro-RO-AlinaNeural", output="output.mp3"):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output)
asyncio.run(tts("Buna ziua! Aceasta este o demonstratie."))
```

Integrare FastAPI (endpoint streaming):
```python
from fastapi.responses import StreamingResponse
import edge_tts

@router.post("/api/tts")
async def text_to_speech(text: str, voice: str = "ro-RO-AlinaNeural"):
    communicate = edge_tts.Communicate(text, voice)
    async def generate():
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                yield chunk["data"]
    return StreamingResponse(generate(), media_type="audio/mpeg")
```

**Web Speech API** [GRATUIT FARA CARD] — Browser-only
- Built-in in Chrome/Edge/Firefox
- Calitate variabila per browser si OS
- Fara backend necesar — ruleaza in frontend
- Limitat la browser, nu poate fi folosit server-side

```javascript
const utterance = new SpeechSynthesisUtterance("Buna ziua!");
utterance.lang = "ro-RO";
window.speechSynthesis.speak(utterance);
```

**Azure TTS F0** [NECESITA CARD LA SIGNUP]
- 500.000 caractere/luna gratuit pe tier F0
- Neural voices de calitate suprema, 400+ voci, 140+ limbi
- Voci romanesti premium incluse
- Signup: portal.azure.com -> Speech service -> F0

```python
import httpx
r = httpx.post(f"https://{REGION}.tts.speech.microsoft.com/cognitiveservices/v1",
               headers={"Ocp-Apim-Subscription-Key": KEY, "Content-Type": "application/ssml+xml"},
               content=f'<speak version="1.0" xml:lang="ro-RO"><voice name="ro-RO-AlinaNeural">{text}</voice></speak>')
```

---

## 4. OCR (Recunoastere Text)

**Priority chain:** Tesseract + EasyOCR local -> OCR.space -> Azure Vision
**Total combinat:** Nelimitat local + ~20.000 req/luna cloud

### Providers Recomandate

| Provider | Free Tier | Limita | Card | Calitate | Tip |
|---|---|---|---|---|---|
| Tesseract OCR | Open-source | Nelimitat | Nu | ★★★★☆ | Local binary |
| EasyOCR | Open-source | Nelimitat | Nu | ★★★★☆ | Python lib |
| Surya OCR | Open-source | Nelimitat | Nu | ★★★★★ | Python lib |
| OCR.space | Permanent | 500 req/zi (~15K/luna) | Nu | ★★★★☆ | REST API |
| Azure Vision F0 | Permanent | 5.000 trx/luna | Da | ★★★★★ | REST API |
| Google Vision | Permanent | 1.000 unitati/luna | Da | ★★★★★ | REST API |

### Provider Details

**Tesseract OCR** [GRATUIT FARA CARD] — Self-hosted
- Apache 2.0, 100+ limbi, inclusiv romana
- Windows: instalare de la github.com/UB-Mannheim/tesseract
- `pip install pytesseract Pillow`
- Cel mai testat si stabil OCR open-source

```python
import pytesseract
from PIL import Image
text = pytesseract.image_to_string(Image.open("document.png"), lang="ron")
```

**EasyOCR** [GRATUIT FARA CARD] — NOU, Self-hosted
- Suport limba romana nativ (`ro` in lista de limbi)
- Deep learning-based — mai bun pe text handwritten si distorsionat
- `pip install easyocr`
- Apache 2.0 license
- Primul run descarca modele (~100MB)

```python
import easyocr
reader = easyocr.Reader(["ro", "en"])
result = reader.readtext("document.png", detail=0)  # lista de stringuri
```

**Surya OCR** [GRATUIT FARA CARD] — NOU, Self-hosted
- Layout analysis + table recognition — ideal pentru facturi si documente structurate
- Suporta 90+ limbi
- GPL-3.0 license (atentie la implicatii comerciale)
- `pip install surya-ocr`
- Mai greu ca EasyOCR (~1GB modele), dar calitate superioara pe documente complexe

```python
from surya.ocr import run_ocr
from surya.model.detection.model import load_model as load_det_model
from surya.model.recognition.model import load_model as load_rec_model
# Necesita mai mult setup — vezi documentatia surya pentru pipeline complet
```

**OCR.space** [GRATUIT FARA CARD]
- 500 requests/zi, 200+ limbi, file limit 1MB
- API REST simplu, fara signup complex

```python
import httpx
r = httpx.post("https://api.ocr.space/parse/image",
               data={"apikey": KEY, "language": "ron"},
               files={"file": open("doc.png", "rb")})
```

---

## 5. Notificari Push

**Priority chain:** Web Push VAPID -> Telegram Bot -> ntfy.sh -> Email
**Total combinat:** Practic nelimitat

### Providers Recomandate

| Provider | Free Tier | Limita | Card | Calitate | Tip |
|---|---|---|---|---|---|
| Web Push VAPID | Standard web | Nelimitat | Nu | ★★★★★ | Python lib |
| Telegram Bot | Permanent | 30 msg/sec broadcast | Nu | ★★★★★ | REST API |
| ntfy.sh | Permanent/Self-host | 250 msg/zi hosted | Nu | ★★★★☆ | REST POST |
| Discord Webhooks | Permanent | 5 req/2 sec | Nu | ★★★☆☆ | REST POST |
| Slack Webhooks | Permanent | 1 msg/sec | Nu | ★★★☆☆ | REST POST |

### Provider Details

**Web Push VAPID** [GRATUIT FARA CARD] — NOU, RECOMANDAT
- Standard web nativ — fara serviciu extern
- Nelimitat, push direct la browser/Android
- Necesita VAPID keys (generate o singura data)
- `pip install pywebpush`
- Ideal pentru PWA (Roland Command Center deja e PWA)

```python
from pywebpush import webpush
webpush(subscription_info={"endpoint": url, "keys": {"p256dh": key, "auth": auth}},
        data="Notificare noua!", vapid_private_key=PRIVATE_KEY,
        vapid_claims={"sub": "mailto:roland@example.com"})
```

**Telegram Bot API** [GRATUIT FARA CARD]
- Complet gratuit, fara tier-uri
- 30 msg/sec broadcast, 1 msg/sec per chat
- Creare bot instant prin @BotFather
- Suporta text, imagini, documente, butoane inline

```python
import httpx
httpx.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
           json={"chat_id": CHAT_ID, "text": "Alerta: backup complet!", "parse_mode": "HTML"})
```

**ntfy.sh** [GRATUIT FARA CARD] — NOU
- Hosted: 250 msg/zi gratuit pe ntfy.sh
- Self-hosted: nelimitat (`docker run -p 8080:80 binwiederhier/ntfy serve`)
- Cel mai simplu push notification posibil — un singur POST/PUT
- Suporta Android native, iOS, web
- Fara cont, fara signup, fara cheie — doar un topic name

```python
import httpx
httpx.post("https://ntfy.sh/roland-alerts", content=b"Backup finalizat cu succes!")
# Cu prioritate si emoji:
httpx.post("https://ntfy.sh/roland-alerts",
           headers={"Priority": "high", "Tags": "warning"}, content=b"Disk 90% full!")
```

**Discord Webhooks** [GRATUIT FARA CARD]
- 5 req/2 sec per webhook
- Configurat o data in Discord server settings

```python
import httpx
httpx.post(WEBHOOK_URL, json={"content": "Alerta: eroare backend!"})
```

---

## 6. Email

**Priority chain:** Gmail SMTP -> Brevo -> Resend -> Mailgun
**Total combinat:** ~900 emailuri/zi (~27.000/luna)

### Providers Recomandate

| Provider | Free Tier | Limita | Card | Calitate | Tip |
|---|---|---|---|---|---|
| Gmail SMTP | Permanent | 500/zi | Nu | ★★★★★ | SMTP |
| Brevo (Sendinblue) | Permanent | 300/zi (~9K/luna) | Nu | ★★★★☆ | REST API |
| Resend.com | Permanent | 100/zi (3K/luna) | Nu | ★★★★☆ | REST API |
| Mailgun | Permanent | 100/zi | Nu* | ★★★☆☆ | REST API |

*Mailgun fara card: doar 5 destinatari verificati

### Provider Details

**Gmail SMTP** [GRATUIT FARA CARD]
- 500 emailuri/zi prin App Password
- Necesita 2FA activat pe cont Google
- `smtplib` — built-in Python, fara pip install
- Cel mai fiabil pentru email-uri personale

```python
import smtplib
from email.mime.text import MIMEText
msg = MIMEText("Factura atasata")
msg["Subject"], msg["From"], msg["To"] = "Factura", "roland@gmail.com", "client@x.com"
with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
    s.login("roland@gmail.com", APP_PASSWORD)
    s.send_message(msg)
```

**Brevo** [GRATUIT FARA CARD]
- 300 emailuri/zi, 100.000 contacte, REST API complet
- Include branding Brevo pe free tier
- Signup: brevo.com

```python
import httpx
httpx.post("https://api.brevo.com/v3/smtp/email",
           headers={"api-key": KEY},
           json={"sender": {"email": "r@x.com"}, "to": [{"email": "c@x.com"}],
                 "subject": "Factura", "htmlContent": "<p>Buna ziua</p>"})
```

**Resend.com** [GRATUIT FARA CARD]
- 3.000 emailuri/luna (100/zi), REST API + SMTP
- Modern, developer-friendly

```python
import httpx
httpx.post("https://api.resend.com/emails",
           headers={"Authorization": f"Bearer {KEY}"},
           json={"from": "r@resend.dev", "to": "c@x.com", "subject": "Test", "text": "Buna!"})
```

---

## 7. Stocare Cloud

**Priority chain:** Google Drive -> OneDrive -> Dropbox

| Provider | Stocare | Rate Limit | Card | Calitate |
|---|---|---|---|---|
| Google Drive | 15 GB | 12K req/60s proiect | Nu | ★★★★★ |
| OneDrive | 5 GB | 130K req/10s global | Nu | ★★★★☆ |
| Dropbox | 2 GB (16 GB cu referrals) | Generoase | Nu | ★★★☆☆ |

**Google Drive** [GRATUIT FARA CARD]
- Deja integrat in Roland Command Center (modul integrations)
- 15 GB shared cu Gmail si Google Photos
- Upload limit: 750 GB/zi

```python
import httpx
# Upload cu Google Drive API v3 (necesita OAuth2 token)
httpx.post("https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart",
           headers={"Authorization": f"Bearer {TOKEN}"}, files={"file": open("backup.zip", "rb")})
```

---

## 8. Calendar & Contacts

**Priority chain:** Google Calendar -> Notion

| Provider | Free Tier | Limita | Card | Calitate |
|---|---|---|---|---|
| Google Calendar | Permanent | ~1M queries/zi | Nu | ★★★★★ |
| Notion API | Permanent | 3 req/sec | Nu | ★★★★☆ |

**Google Calendar** [GRATUIT FARA CARD]
- Deja integrat in Roland Command Center
- Practic nelimitat pentru uz personal

```python
import httpx
r = httpx.get("https://www.googleapis.com/calendar/v3/calendars/primary/events",
              headers={"Authorization": f"Bearer {TOKEN}"}, params={"maxResults": 10})
```

**Notion API** [GRATUIT FARA CARD]
- 3 req/sec per integrare
- Pagini nelimitate pe plan gratuit individual
- Bun ca CRM simplu sau knowledge base

```python
import httpx
r = httpx.post("https://api.notion.com/v1/pages",
               headers={"Authorization": f"Bearer {KEY}", "Notion-Version": "2022-06-28"},
               json={"parent": {"database_id": DB_ID}, "properties": {"Name": {"title": [{"text": {"content": "Nota"}}]}}})
```

---

## 9. Business APIs Romania

Toate gratuite, fara card, fara signup, fara limite practice.

| Provider | Scop | Limita | Tip |
|---|---|---|---|
| BNR XML Feed | Curs valutar oficial | Nelimitat | XML GET |
| ANAF Verificare CUI | Verificare platitor TVA | Nelimitat | REST POST |
| data.gov.ro | Date publice Romania | Nelimitat | Various |

### Provider Details

**BNR Curs Valutar** [GRATUIT FARA CARD] — NOU
- Feed XML oficial al Bancii Nationale a Romaniei
- Curs de referinta zilnic pentru EUR, USD, GBP, CHF, etc.
- Fara autentificare, fara cheie API, fara limita
- Actualizat zilnic la ~13:00

```python
import httpx
from xml.etree import ElementTree
r = httpx.get("https://www.bnr.ro/nbrfxrates.xml")
root = ElementTree.fromstring(r.text)
ns = {"bnr": "http://www.bnr.ro/xsd"}
for rate in root.findall(".//bnr:Rate", ns):
    print(f"{rate.get('currency')}: {rate.text} RON")
# Exemplu output: EUR: 4.9770 RON
```

**ANAF Verificare CUI** [GRATUIT FARA CARD] — NOU
- Verificare platitor TVA, date firma, adresa, stare
- POST JSON, maxim 500 CUI-uri per request
- API v8 (ultima versiune)
- Fara autentificare

```python
import httpx
from datetime import date
r = httpx.post("https://webservicesp.anaf.ro/PlatitorTvaRest/api/v8/ws/tva",
               json=[{"cui": 43978110, "data": date.today().isoformat()}])
# Returneaza: denumire, adresa, platitor TVA, stare, etc.
```

**data.gov.ro** [GRATUIT FARA CARD]
- Portal national de date deschise
- Seturi de date diverse: demografie, transport, educatie, etc.
- Format: CSV, JSON, XML

---

## 10. Embeddings / Semantic Search — NOU

**Priority chain:** Gemini Embeddings -> all-MiniLM-L6-v2 local -> Cohere -> Jina
**Utilitate:** Cautare semantica in documente, clasificare, similarity matching

### Providers Recomandate

| Provider | Free Tier | Dimensiuni | Card | Calitate | Tip |
|---|---|---|---|---|---|
| Gemini Embeddings | Inclus in Gemini free | 768-3072 | Nu | ★★★★★ | REST API |
| all-MiniLM-L6-v2 | Open-source | 384 | Nu | ★★★★☆ | Python local |
| Cohere Embed | 1.000 calls/luna | 1024 | Nu | ★★★★☆ | REST API |
| Jina Embeddings | 10M tokeni/cheie noua | 1024 | Nu | ★★★★☆ | REST API |

### Provider Details

**Gemini Embeddings** [GRATUIT FARA CARD] — NOU, RECOMANDAT
- Inclus in Gemini API free tier (aceeasi cheie)
- Model: text-embedding-004
- Dimensiuni: 768 (default), configurabil pana la 3072
- Multilingual — suporta romana nativ
- Ideal pentru document search in Roland Command Center

```python
import httpx
r = httpx.post(f"https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent?key={API_KEY}",
               json={"content": {"parts": [{"text": "Traducere document tehnic"}]}})
embedding = r.json()["embedding"]["values"]  # lista de 768 float-uri
```

**all-MiniLM-L6-v2** [GRATUIT FARA CARD] — NOU, Self-hosted
- Model local, nelimitat, offline dupa download initial (~80MB)
- 384 dimensiuni — compact, rapid
- `pip install sentence-transformers`
- Bun pentru similarity search in volume mici-medii

```python
from sentence_transformers import SentenceTransformer
model = SentenceTransformer("all-MiniLM-L6-v2")
embeddings = model.encode(["Traducere tehnica", "Technical translation", "Factura proforma"])
# Cosine similarity intre embeddings pentru search
```

**Cohere Embed** [GRATUIT FARA CARD]
- 1.000 calls/luna pe free tier
- Model embed-multilingual-v3.0 — bun pentru romana
- 1024 dimensiuni

```python
import httpx
r = httpx.post("https://api.cohere.ai/v1/embed",
               headers={"Authorization": f"Bearer {KEY}"},
               json={"texts": ["Traducere document"], "model": "embed-multilingual-v3.0",
                     "input_type": "search_document"})
```

**Jina Embeddings** [GRATUIT FARA CARD] — NOU
- 10M tokeni gratuit per cheie API noua
- Model jina-embeddings-v3
- 1024 dimensiuni
- Multilingual bun
- Signup: jina.ai

```python
import httpx
r = httpx.post("https://api.jina.ai/v1/embeddings",
               headers={"Authorization": f"Bearer {KEY}"},
               json={"model": "jina-embeddings-v3", "input": ["Traducere document tehnic"]})
```

---

## 11. Image Generation — NOU

**Provider unic gratuit fara cheie:**

**Pollinations.ai** [GRATUIT FARA CARD] — NOU
- Zero signup, zero cheie API, zero limita declarata
- GET request returneaza imagine direct
- Modele: Flux (default), alte modele open-source
- Calitate buna pentru thumbnails, diagrame, ilustratii
- Nu necesita cont — cel mai simplu API din tot catalogul

```python
import httpx
# Varianta GET — URL direct (poate fi folosit si in <img src="">)
url = "https://image.pollinations.ai/prompt/modern%20office%20dashboard%20dark%20theme?width=800&height=600"
r = httpx.get(url, follow_redirects=True)
with open("generated.png", "wb") as f:
    f.write(r.content)
```

Integrare HTML directa (fara backend):
```html
<img src="https://image.pollinations.ai/prompt/professional%20invoice%20template?width=400&height=300" />
```

---

## 12. PDF Generation — NOU

**WeasyPrint** [GRATUIT FARA CARD] — NOU, Self-hosted
- HTML/CSS to PDF — ideal pentru facturi, rapoarte
- `pip install weasyprint`
- BSD license
- Suporta CSS Paged Media (headers, footers, page numbers)
- Compatibil Windows 10 (necesita GTK+ runtime sau instalare prin MSYS2)

```python
from weasyprint import HTML
HTML(string="<h1>Factura #001</h1><p>Total: 500 RON</p>").write_pdf("factura.pdf")
# Sau din URL:
HTML(url="http://localhost:5173/invoice/preview/1").write_pdf("factura.pdf")
```

Integrare FastAPI:
```python
from fastapi.responses import Response
from weasyprint import HTML

@router.get("/api/invoice/{id}/pdf")
async def generate_pdf(id: int):
    html_content = f"<h1>Factura #{id}</h1><p>...</p>"
    pdf_bytes = HTML(string=html_content).write_pdf()
    return Response(content=pdf_bytes, media_type="application/pdf",
                    headers={"Content-Disposition": f"attachment; filename=factura_{id}.pdf"})
```

---

## 13. Developer Tools

| Provider | Free Tier | Limita | Card | Tip |
|---|---|---|---|---|
| GitHub API | Permanent | 5.000 req/ora auth | Nu | REST + GraphQL |
| Airtable | Permanent | 1.000 calls/luna, 1K records | Nu | REST API |
| Discord Webhooks | Permanent | 5 req/2 sec | Nu | REST POST |
| Slack Webhooks | Permanent | 1 msg/sec | Nu | REST POST |

**GitHub API** [GRATUIT FARA CARD]
- 5.000 req/ora autentificat, 60 req/ora anonim
- REST v3 + GraphQL v4
- Deja integrat in Roland Command Center (modul integrations)

```python
import httpx
r = httpx.get("https://api.github.com/repos/user/repo/commits",
              headers={"Authorization": f"token {TOKEN}"})
```

### Platforme No-Code (nu API-uri directe)

| Provider | Free Tier | Limita | Nota |
|---|---|---|---|
| Zapier | 100 tasks/luna | Doar 2-step Zaps, fara webhooks pe free | Nu se integreaza cu Python |
| Make | 1.000 operatiuni/luna | 2 scenarii active | Nu se integreaza cu Python |

---

## Key Rotation Strategy

### Principiu

Rotatie intre **platforme diferite** (complet legala) — NU conturi multiple pe aceeasi platforma (contra ToS).

### Implementare in FastAPI

```python
# Exemplu: AI provider rotation cu fallback automat
PROVIDERS = [
    {"name": "gemini", "base_url": "https://generativelanguage.googleapis.com/v1beta/", "key": GEMINI_KEY},
    {"name": "cerebras", "base_url": "https://api.cerebras.ai/v1/", "key": CEREBRAS_KEY},
    {"name": "groq", "base_url": "https://api.groq.com/openai/v1/", "key": GROQ_KEY},
    {"name": "mistral", "base_url": "https://api.mistral.ai/v1/", "key": MISTRAL_KEY},
]

async def ai_request(messages: list, provider_index: int = 0):
    """Incearca provider-ul curent; la 429/500, trece la urmatorul."""
    if provider_index >= len(PROVIDERS):
        raise Exception("Toate provider-urile epuizate")
    provider = PROVIDERS[provider_index]
    try:
        r = await httpx.AsyncClient().post(f"{provider['base_url']}chat/completions",
            headers={"Authorization": f"Bearer {provider['key']}"},
            json={"model": "auto", "messages": messages}, timeout=30)
        if r.status_code == 429:  # Rate limited
            return await ai_request(messages, provider_index + 1)
        return r.json()
    except Exception:
        return await ai_request(messages, provider_index + 1)
```

### Rate Limiting Local

```python
import asyncio
from collections import defaultdict

class RateLimiter:
    """Token bucket per provider — previne 429 inainte sa apara."""
    def __init__(self):
        self.semaphores = defaultdict(lambda: asyncio.Semaphore(5))  # max 5 concurrent
        self.last_call = defaultdict(float)

    async def acquire(self, provider: str, min_interval: float = 0.5):
        async with self.semaphores[provider]:
            now = asyncio.get_event_loop().time()
            wait = max(0, min_interval - (now - self.last_call[provider]))
            if wait > 0:
                await asyncio.sleep(wait)
            self.last_call[provider] = asyncio.get_event_loop().time()
```

### Strategia pe Categorii

**AI Text Generation** — Round-robin cu health check:
1. Gemini Flash (primary — cel mai bun calitate/volum)
2. Cerebras (1M tokeni/zi — viteza maxima)
3. Groq (rapid, bun pentru summarization)
4. Mistral (volum mare dar 2 RPM — folosit ca buffer)
5. SambaNova (backup final)

**Traduceri** — Cascada pe volum:
1. DeepL Free (500K chars — calitate maxima EN<->RO)
2. Azure F0 (2M chars — volum mare)
3. Google Direct HTTP (nelimitat — fallback)
4. MyMemory (50K/zi — alternative rapide)
5. LibreTranslate local (overflow nelimitat)

**OCR** — Local-first:
1. Tesseract/EasyOCR (tot ce se poate offline)
2. OCR.space (cand local esueaza)
3. Azure Vision (documente complexe)

---

## Tabel Comparativ Final

### AI Text Generation

| Provider | Limita Free | Card | API | Calitate | Status |
|---|---|---|---|---|---|
| Google Gemini | 250-1000 RPD | Nu | REST/OpenAI | ★★★★★ | [GRATUIT FARA CARD] |
| Cerebras | 1M tokeni/zi | Nu | OpenAI | ★★★★☆ | [GRATUIT FARA CARD] |
| Groq | ~14.4K RPD | Nu | OpenAI | ★★★★☆ | [GRATUIT FARA CARD] |
| Mistral AI | ~1B tok/luna, 2RPM | Nu | OpenAI | ★★★★☆ | [GRATUIT FARA CARD] |
| SambaNova | 200K tok/zi | Nu | OpenAI | ★★★☆☆ | [GRATUIT FARA CARD] |
| Cohere | 1K calls/luna | Nu | REST | ★★★☆☆ | [GRATUIT FARA CARD] |
| Hugging Face | Credite modeste | Nu | REST | ★★★☆☆ | [GRATUIT FARA CARD] |
| AI21 Labs | $10/3 luni | Nu | REST | ★★★☆☆ | [CREDIT LIMITAT] |
| NVIDIA NIM | 1-5K credite | Nu* | REST | ★★★★☆ | [CREDIT LIMITAT] |
| Fireworks AI | $1 credit | Nu | OpenAI | ★★★☆☆ | [CREDIT LIMITAT] |
| OpenAI | Nefunctional | Da | REST | ★★★★★ | [FREE TIER NEFUNCTIONAL] |
| Anthropic | Inexistent | Da | REST | ★★★★★ | [EXCLUSIV PLATIT] |
| Together AI | Eliminat | Nu | OpenAI | ★★★★☆ | [FREE TIER ELIMINAT] |
| Perplexity | Inexistent | Da | REST | ★★★★☆ | [EXCLUSIV PLATIT] |
| DeepSeek | 5M tok/30 zile | Nu | OpenAI | ★★★★☆ | [CU PRECAUTIE] |

### Traduceri

| Provider | Limita Free | Card | Calitate | Status |
|---|---|---|---|---|
| DeepL Free | 500K chars/luna | Nu | ★★★★★ | [GRATUIT FARA CARD] |
| Azure Translator F0 | 2M chars/luna | Da | ★★★★☆ | [NECESITA CARD LA SIGNUP] |
| Google Direct HTTP | Nelimitat* | Nu | ★★★★☆ | [GRATUIT FARA CARD] |
| MyMemory | 50K chars/zi | Nu | ★★★☆☆ | [GRATUIT FARA CARD] |
| LibreTranslate | Nelimitat | Nu | ★★★☆☆ | [GRATUIT FARA CARD] |
| Argos Translate | Nelimitat | Nu | ★★★☆☆ | [GRATUIT FARA CARD] |

### TTS, OCR, Notificari, Email

| Provider | Categorie | Limita Free | Card | Calitate | Status |
|---|---|---|---|---|---|
| edge-tts | TTS | Nelimitat | Nu | ★★★★★ | [GRATUIT FARA CARD] |
| Web Speech API | TTS | Nelimitat | Nu | ★★★☆☆ | [GRATUIT FARA CARD] |
| Azure TTS F0 | TTS | 500K chars/luna | Da | ★★★★★ | [NECESITA CARD LA SIGNUP] |
| Tesseract | OCR | Nelimitat | Nu | ★★★★☆ | [GRATUIT FARA CARD] |
| EasyOCR | OCR | Nelimitat | Nu | ★★★★☆ | [GRATUIT FARA CARD] |
| Surya OCR | OCR | Nelimitat | Nu | ★★★★★ | [GRATUIT FARA CARD] |
| OCR.space | OCR | 500 req/zi | Nu | ★★★★☆ | [GRATUIT FARA CARD] |
| Azure Vision F0 | OCR | 5K trx/luna | Da | ★★★★★ | [NECESITA CARD LA SIGNUP] |
| Google Vision | OCR | 1K unitati/luna | Da | ★★★★★ | [NECESITA CARD LA SIGNUP] |
| Web Push VAPID | Notificari | Nelimitat | Nu | ★★★★★ | [GRATUIT FARA CARD] |
| Telegram Bot | Notificari | 30 msg/sec | Nu | ★★★★★ | [GRATUIT FARA CARD] |
| ntfy.sh | Notificari | 250 msg/zi | Nu | ★★★★☆ | [GRATUIT FARA CARD] |
| Discord Webhooks | Notificari | 5 req/2s | Nu | ★★★☆☆ | [GRATUIT FARA CARD] |
| Gmail SMTP | Email | 500/zi | Nu | ★★★★★ | [GRATUIT FARA CARD] |
| Brevo | Email | 300/zi | Nu | ★★★★☆ | [GRATUIT FARA CARD] |
| Resend | Email | 100/zi | Nu | ★★★★☆ | [GRATUIT FARA CARD] |
| Mailgun | Email | 100/zi | Nu* | ★★★☆☆ | [GRATUIT FARA CARD] |

### Stocare, Calendar, Business, Developer

| Provider | Categorie | Limita Free | Card | Calitate | Status |
|---|---|---|---|---|---|
| Google Drive | Stocare | 15 GB | Nu | ★★★★★ | [GRATUIT FARA CARD] |
| OneDrive | Stocare | 5 GB | Nu | ★★★★☆ | [GRATUIT FARA CARD] |
| Dropbox | Stocare | 2 GB | Nu | ★★★☆☆ | [GRATUIT FARA CARD] |
| Google Calendar | Calendar | ~1M queries/zi | Nu | ★★★★★ | [GRATUIT FARA CARD] |
| Notion API | Calendar/DB | 3 req/sec | Nu | ★★★★☆ | [GRATUIT FARA CARD] |
| BNR XML | Business RO | Nelimitat | Nu | ★★★★★ | [GRATUIT FARA CARD] |
| ANAF CUI | Business RO | Nelimitat | Nu | ★★★★★ | [GRATUIT FARA CARD] |
| data.gov.ro | Business RO | Nelimitat | Nu | ★★★☆☆ | [GRATUIT FARA CARD] |
| GitHub API | Dev | 5K req/ora | Nu | ★★★★★ | [GRATUIT FARA CARD] |
| Airtable | Dev | 1K calls/luna | Nu | ★★★☆☆ | [GRATUIT FARA CARD] |
| Gemini Embeddings | Embeddings | Inclus in Gemini | Nu | ★★★★★ | [GRATUIT FARA CARD] |
| all-MiniLM-L6-v2 | Embeddings | Nelimitat | Nu | ★★★★☆ | [GRATUIT FARA CARD] |
| Cohere Embed | Embeddings | 1K calls/luna | Nu | ★★★★☆ | [GRATUIT FARA CARD] |
| Jina Embeddings | Embeddings | 10M tokeni/cheie | Nu | ★★★★☆ | [GRATUIT FARA CARD] |
| Pollinations.ai | Image Gen | Nelimitat | Nu | ★★★★☆ | [GRATUIT FARA CARD] |
| WeasyPrint | PDF Gen | Nelimitat | Nu | ★★★★☆ | [GRATUIT FARA CARD] |

---

## Statistici Finale

- **Total provideri catalogati:** 50
- **Gratuit fara card:** 38
- **Necesita card la signup (dar free tier real):** 5 (Azure Translator, Azure TTS, Azure Vision, Google Vision, Google Cloud Translation)
- **Credit limitat / trial:** 3 (AI21, NVIDIA NIM, Fireworks)
- **Nerecomandate / platite:** 4 (OpenAI, Anthropic, Together AI, Perplexity)
- **Cu precautie:** 1 (DeepSeek)

**Deja integrate in Roland Command Center:**
- AI: Gemini Flash, OpenAI (backup), Groq (fallback)
- Traduceri: DeepL, Azure, Google Direct, MyMemory, LibreTranslate
- Stocare: Google Drive
- Calendar: Google Calendar
- Dev: GitHub
- OCR: Tesseract (via backend)

**Candidate prioritare pentru integrare:**
1. **edge-tts** — TTS romanesc de calitate, zero cost, zero configurare
2. **Web Push VAPID** — notificari native PWA, fara serviciu extern
3. **BNR + ANAF** — API-uri business Romania esentiale
4. **Gemini Embeddings** — search semantic in documente (aceeasi cheie existenta)
5. **ntfy.sh** — notificari push Android ultra-simple
6. **EasyOCR** — OCR imbunatatit pentru romana
7. **Pollinations.ai** — generare imagini fara cheie
8. **WeasyPrint** — export PDF facturi
9. **Cerebras** — 1M tokeni/zi AI gratuit suplimentar

---

> **Nota:** Limitele free tier se pot schimba oricand. Verificati periodic paginile oficiale ale providerilor.
> **Ultima verificare:** Martie 2026
