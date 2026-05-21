# RECOMANDARI IMBUNATATIRI & COMPLETARI
## Roland Command Center — Analiza Exhaustiva

**Data:** 2026-03-31
**Versiune:** 1.0
**Analiza:** Inventar complet al celor 14 module, 365+ endpoint-uri, 25 pagini frontend, 64+ tabele DB
**Scop:** Identificare imbunatatiri existente + features noi + imbunatatiri tehnice

---

## SUMAR EXECUTIV

Proiectul este matur si functional, cu 32 faze implementate. Aceasta analiza identifica **38 de recomandari** organizate in 3 categorii:

| Categorie | Nr. | Impact Total |
|-----------|-----|-------------|
| **Partea I** — Imbunatatiri functii existente | 16 | Maximizare ROI pe codul existent |
| **Partea II** — Functii noi | 12 | Completare workflow-uri business |
| **Partea III** — Imbunatatiri tehnice | 10 | Stabilitate, calitate, securitate |

**Top 5 cu impact maxim:**
1. e-Factura XML ANAF (obligatoriu legal)
2. Time Tracking legat de facturare
3. Cautare Globala Cross-Module
4. Fix Migration 017 Duplicate (risc coruptie schema)
5. PWA Offline Enhanced pentru Android

---

# PARTEA I — IMBUNATATIRI FUNCTII EXISTENTE

---

### 1. Dashboard — Obiective Zilnice cu Progres

**Fisier:** `frontend/src/pages/DashboardPage.jsx`
**Problema actuala:** Sectiunea "Ziua Mea" arata salutare, alerte si quick actions, dar nu ofera o viziune de tip "ce am de facut azi" cu tracking progres. Utilizatorul nu stie cat a realizat din ce si-a propus.

**Imbunatatire propusa:**
- Widget "Obiectivele Zilei" cu checklist editabil
- Bara de progres zilnica (% din obiective indeplinite)
- Persistare in DB cu endpoint dedicat
- Reset automat la miezul noptii

**Exemplu implementare (backend):**
```python
# modules/reports/router.py — adaugare endpoint obiective zilnice
@router.get("/api/reports/dashboard/daily-goals")
async def get_daily_goals():
    async with get_db() as db:
        today = datetime.now().strftime("%Y-%m-%d")
        rows = await db.execute_fetchall(
            "SELECT id, text, completed FROM daily_goals WHERE date = ?", (today,)
        )
        return {"date": today, "goals": [dict(r) for r in rows]}

@router.post("/api/reports/dashboard/daily-goals")
async def add_daily_goal(text: str = Body(...)):
    async with get_db() as db:
        today = datetime.now().strftime("%Y-%m-%d")
        await db.execute(
            "INSERT INTO daily_goals (date, text, completed) VALUES (?, ?, 0)",
            (today, text)
        )
        await db.commit()
        return {"status": "ok"}

@router.put("/api/reports/dashboard/daily-goals/{goal_id}")
async def toggle_goal(goal_id: int, completed: bool = Body(...)):
    async with get_db() as db:
        await db.execute(
            "UPDATE daily_goals SET completed = ? WHERE id = ?",
            (1 if completed else 0, goal_id)
        )
        await db.commit()
        return {"status": "ok"}
```

**Exemplu implementare (frontend):**
```jsx
// In DashboardPage.jsx — sectiunea "Ziua Mea"
function DailyGoals() {
  const [goals, setGoals] = useState([]);
  const [newGoal, setNewGoal] = useState('');

  useEffect(() => {
    api.get('/api/reports/dashboard/daily-goals').then(r => setGoals(r.data.goals));
  }, []);

  const addGoal = async () => {
    if (!newGoal.trim()) return;
    await api.post('/api/reports/dashboard/daily-goals', newGoal, {
      headers: { 'Content-Type': 'application/json' }
    });
    setNewGoal('');
    const r = await api.get('/api/reports/dashboard/daily-goals');
    setGoals(r.data.goals);
  };

  const toggleGoal = async (id, completed) => {
    await api.put(`/api/reports/dashboard/daily-goals/${id}`, !completed);
    setGoals(goals.map(g => g.id === id ? { ...g, completed: !completed } : g));
  };

  const completedCount = goals.filter(g => g.completed).length;
  const progress = goals.length > 0 ? Math.round((completedCount / goals.length) * 100) : 0;

  return (
    <div className="bg-gray-900 rounded-2xl border border-gray-800 p-5">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-medium text-gray-300">Obiective Azi</h3>
        <span className="text-xs text-gray-500">{completedCount}/{goals.length}</span>
      </div>
      <div className="w-full bg-gray-800 rounded-full h-2 mb-3">
        <div className="bg-blue-500 h-2 rounded-full transition-all" style={{ width: `${progress}%` }} />
      </div>
      {goals.map(g => (
        <label key={g.id} className="flex items-center gap-2 py-1 cursor-pointer">
          <input type="checkbox" checked={g.completed} onChange={() => toggleGoal(g.id, g.completed)}
            className="rounded border-gray-600" />
          <span className={g.completed ? 'line-through text-gray-500' : 'text-gray-300'}>{g.text}</span>
        </label>
      ))}
      <div className="flex gap-2 mt-2">
        <input value={newGoal} onChange={e => setNewGoal(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && addGoal()}
          placeholder="Obiectiv nou..." className="input-field flex-1 text-sm" />
        <button onClick={addGoal} className="btn-primary text-sm px-3">+</button>
      </div>
    </div>
  );
}
```

**Migrare SQL necesara:**
```sql
CREATE TABLE IF NOT EXISTS daily_goals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    text TEXT NOT NULL,
    completed INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX idx_daily_goals_date ON daily_goals(date);
```

**Complexitate:** Mica | **Impact:** Mare

---

### 2. Dashboard — Grafice Comparative Saptamana Curenta vs Anterioara

**Fisier:** `frontend/src/pages/DashboardPage.jsx`
**Problema actuala:** Graficul de activitate arata ultimele 7 zile ca bare simple. Nu exista comparatie cu saptamana anterioara, deci nu se vede trendul (creste/scade activitatea?).

**Imbunatatire propusa:**
- Grafic cu doua serii: saptamana curenta (albastru) vs anterioara (gri, 50% opacity)
- Label-uri cu diferenta procentuala
- Endpoint backend care returneaza ambele saptamani

**Exemplu implementare (backend):**
```python
@router.get("/api/reports/dashboard/weekly-comparison")
async def weekly_comparison():
    async with get_db() as db:
        now = datetime.now()
        this_week_start = (now - timedelta(days=now.weekday())).strftime("%Y-%m-%d")
        last_week_start = (now - timedelta(days=now.weekday() + 7)).strftime("%Y-%m-%d")
        last_week_end = (now - timedelta(days=now.weekday() + 1)).strftime("%Y-%m-%d")

        this_week = await db.execute_fetchall(
            "SELECT DATE(timestamp) as day, COUNT(*) as count FROM activity_log "
            "WHERE DATE(timestamp) >= ? GROUP BY DATE(timestamp) ORDER BY day",
            (this_week_start,)
        )
        last_week = await db.execute_fetchall(
            "SELECT DATE(timestamp) as day, COUNT(*) as count FROM activity_log "
            "WHERE DATE(timestamp) >= ? AND DATE(timestamp) <= ? "
            "GROUP BY DATE(timestamp) ORDER BY day",
            (last_week_start, last_week_end)
        )
        return {
            "this_week": [dict(r) for r in this_week],
            "last_week": [dict(r) for r in last_week],
        }
```

**Complexitate:** Mica | **Impact:** Mediu

---

### 3. Translator — Sugestii TM in Timp Real la Tastare

**Fisier:** `frontend/src/pages/TranslatorPage.jsx`
**Problema actuala:** Translation Memory (TM) se aplica doar la submit. Utilizatorul nu vede sugestii TM in timp real pe masura ce tasteaza, ca intr-un CAT tool profesional.

**Imbunatatire propusa:**
- Debounce search TM la 500ms dupa ce utilizatorul opreste tastarea
- Afisare sugestii TM sub textarea sursa (max 3)
- Click pe sugestie = insereaza traducerea in textarea destinatie
- Nu afiseaza daca textul sursa < 5 caractere

**Exemplu implementare (frontend):**
```jsx
// In TranslatorPage.jsx — dupa textarea sursa
const [tmSuggestions, setTmSuggestions] = useState([]);

useEffect(() => {
  if (!sourceText || sourceText.length < 5 || !useTm) {
    setTmSuggestions([]);
    return;
  }
  const timer = setTimeout(async () => {
    try {
      const { data } = await api.get('/api/translator/tm/search', {
        params: { q: sourceText.substring(0, 100), source_lang: sourceLang, target_lang: targetLang, limit: 3 }
      });
      setTmSuggestions(data.results || []);
    } catch { setTmSuggestions([]); }
  }, 500);
  return () => clearTimeout(timer);
}, [sourceText, sourceLang, targetLang, useTm]);

// In JSX, dupa textarea sursa:
{tmSuggestions.length > 0 && (
  <div className="bg-gray-800/50 rounded-lg p-2 mt-1 space-y-1">
    <p className="text-xs text-gray-500">Sugestii TM:</p>
    {tmSuggestions.map((s, i) => (
      <button key={i} onClick={() => setTargetText(s.target)}
        className="block w-full text-left text-sm p-1.5 rounded hover:bg-gray-700 text-gray-300">
        <span className="text-blue-400">{s.score}%</span> {s.target}
      </button>
    ))}
  </div>
)}
```

**Complexitate:** Mica | **Impact:** Mare (economiseste timp la fiecare traducere)

---

### 4. Translator — Shortcut-uri Tastatura pentru Flux Rapid

**Fisier:** `frontend/src/pages/TranslatorPage.jsx`
**Problema actuala:** Traducerea necesita click pe buton. Un traducator profesionist prefera shortcut-uri rapide.

**Imbunatatire propusa:**
- `Ctrl+Enter` = Traduce text
- `Ctrl+Shift+S` = Swap limbi sursa/destinatie
- `Ctrl+Shift+C` = Copiaza traducerea
- `Ctrl+Shift+D` = Detecteaza limba
- Indicator vizual al shortcut-urilor pe butoane (tooltip sau label)

**Exemplu implementare:**
```jsx
// In TranslatorPage.jsx
useEffect(() => {
  const handleKey = (e) => {
    if (e.ctrlKey && e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleTranslate();
    }
    if (e.ctrlKey && e.shiftKey && e.key === 'S') {
      e.preventDefault();
      setSourceLang(targetLang);
      setTargetLang(sourceLang);
      setSourceText(targetText);
      setTargetText(sourceText);
    }
    if (e.ctrlKey && e.shiftKey && e.key === 'C') {
      e.preventDefault();
      if (targetText) navigator.clipboard.writeText(targetText);
    }
  };
  window.addEventListener('keydown', handleKey);
  return () => window.removeEventListener('keydown', handleKey);
}, [sourceText, targetText, sourceLang, targetLang]);
```

**Complexitate:** Mica | **Impact:** Mediu

---

### 5. Invoice — Generare XML e-Factura (ANAF — Obligatoriu Legal)

**Fisier:** `backend/modules/invoice/`
**Problema actuala:** Sistemul genereaza PDF-uri de facturi, dar NU genereaza fisiere XML e-Factura in format UBL 2.1 / RO_CIUS. Din ianuarie 2024 (B2B) si ianuarie 2025 (B2C), e-Factura este **obligatorie** in Romania. CIP Inspection SRL trebuie sa genereze XML-uri conforme ANAF.

**Imbunatatire propusa:**
- Endpoint care genereaza XML e-Factura din factura existenta
- Format UBL 2.1 cu profil RO_CIUS (conform ANAF)
- Validare structura XML inainte de export
- Download XML pentru incarcare manuala in SPV ANAF
- Nota: integrarea completa cu API SPV necesita certificat digital calificat (cost), dar generarea XML este gratuita

**Exemplu implementare (backend):**
```python
# modules/invoice/efactura.py
from xml.etree.ElementTree import Element, SubElement, tostring
from datetime import datetime

UBL_NS = "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
CAC_NS = "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
CBC_NS = "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"

def generate_efactura_xml(invoice: dict, client: dict, company: dict, items: list) -> str:
    """Genereaza XML e-Factura in format UBL 2.1 / RO_CIUS"""
    root = Element("Invoice", xmlns=UBL_NS)
    root.set("xmlns:cac", CAC_NS)
    root.set("xmlns:cbc", CBC_NS)

    # Header
    SubElement(root, f"{{{CBC_NS}}}CustomizationID").text = (
        "urn:cen.eu:en16931:2017#compliant#urn:efactura.mfinante.ro:CIUS-RO:1.0.1"
    )
    SubElement(root, f"{{{CBC_NS}}}ID").text = invoice["invoice_number"]
    SubElement(root, f"{{{CBC_NS}}}IssueDate").text = invoice["date"]
    SubElement(root, f"{{{CBC_NS}}}DueDate").text = invoice.get("due_date", invoice["date"])
    SubElement(root, f"{{{CBC_NS}}}InvoiceTypeCode").text = "380"
    SubElement(root, f"{{{CBC_NS}}}DocumentCurrencyCode").text = "RON"

    # Supplier (CIP Inspection SRL)
    supplier = SubElement(root, f"{{{CAC_NS}}}AccountingSupplierParty")
    sp = SubElement(supplier, f"{{{CAC_NS}}}Party")
    sp_id = SubElement(sp, f"{{{CAC_NS}}}PartyIdentification")
    SubElement(sp_id, f"{{{CBC_NS}}}ID", schemeID="CUI").text = company.get("cui", "")
    sp_name = SubElement(sp, f"{{{CAC_NS}}}PartyName")
    SubElement(sp_name, f"{{{CBC_NS}}}Name").text = company.get("name", "")

    # Customer
    customer = SubElement(root, f"{{{CAC_NS}}}AccountingCustomerParty")
    cp = SubElement(customer, f"{{{CAC_NS}}}Party")
    if client.get("cui"):
        cp_id = SubElement(cp, f"{{{CAC_NS}}}PartyIdentification")
        SubElement(cp_id, f"{{{CBC_NS}}}ID", schemeID="CUI").text = client["cui"]
    cp_name = SubElement(cp, f"{{{CAC_NS}}}PartyName")
    SubElement(cp_name, f"{{{CBC_NS}}}Name").text = client["name"]

    # Lines
    total = 0
    for i, item in enumerate(items, 1):
        line = SubElement(root, f"{{{CAC_NS}}}InvoiceLine")
        SubElement(line, f"{{{CBC_NS}}}ID").text = str(i)
        SubElement(line, f"{{{CBC_NS}}}InvoicedQuantity", unitCode="C62").text = str(item["quantity"])
        line_total = item["quantity"] * item["unit_price"]
        total += line_total
        SubElement(line, f"{{{CBC_NS}}}LineExtensionAmount", currencyID="RON").text = f"{line_total:.2f}"
        li = SubElement(line, f"{{{CAC_NS}}}Item")
        SubElement(li, f"{{{CBC_NS}}}Name").text = item["description"]
        lp = SubElement(line, f"{{{CAC_NS}}}Price")
        SubElement(lp, f"{{{CBC_NS}}}PriceAmount", currencyID="RON").text = f"{item['unit_price']:.2f}"

    # Total
    monetary = SubElement(root, f"{{{CAC_NS}}}LegalMonetaryTotal")
    SubElement(monetary, f"{{{CBC_NS}}}TaxExclusiveAmount", currencyID="RON").text = f"{total:.2f}"
    SubElement(monetary, f"{{{CBC_NS}}}PayableAmount", currencyID="RON").text = f"{total:.2f}"

    return tostring(root, encoding="unicode", xml_declaration=True)
```

**Endpoint:**
```python
@router.get("/api/invoice/{invoice_id}/efactura-xml")
async def export_efactura_xml(invoice_id: int):
    # Load invoice, client, items from DB
    # Generate XML
    xml_str = generate_efactura_xml(invoice, client, company_config, items)
    return Response(content=xml_str, media_type="application/xml",
                    headers={"Content-Disposition": f"attachment; filename=efactura_{invoice['invoice_number']}.xml"})
```

**Frontend — buton nou pe tab facturi:**
```jsx
<button onClick={() => window.open(`/api/invoice/${inv.id}/efactura-xml`)}
  className="text-green-400 hover:text-green-300" title="Download e-Factura XML">
  <FileText className="w-4 h-4" />
</button>
```

**Complexitate:** Mare | **Impact:** Maxim (obligatie legala)

---

### 6. Invoice — Preview Live Factura la Creare

**Fisier:** `frontend/src/pages/InvoicePage.jsx`
**Problema actuala:** La crearea facturii, utilizatorul completeaza un formular dar nu vede cum va arata factura finala pana cand nu genereaza PDF-ul. Feedback-ul e tardiv.

**Imbunatatire propusa:**
- Panel lateral (sau modal) cu preview live al facturii pe masura ce se completeaza formularul
- Calcul total automat (subtotal, TVA, total)
- Preview responsiv care se actualizeaza la fiecare modificare

**Exemplu implementare:**
```jsx
// InvoicePage.jsx — in tab-ul Create, adauga panel lateral
function InvoicePreview({ client, items, date, dueDate, notes, vatPercent, series }) {
  const subtotal = items.reduce((s, i) => s + i.quantity * i.unit_price, 0);
  const vat = subtotal * (vatPercent / 100);
  const total = subtotal + vat;

  return (
    <div className="bg-white text-gray-900 rounded-lg p-6 text-sm max-w-md">
      <div className="text-center border-b pb-3 mb-3">
        <h2 className="font-bold text-lg">CIP Inspection SRL</h2>
        <p className="text-xs text-gray-500">CUI: 43978110</p>
      </div>
      <div className="flex justify-between text-xs mb-4">
        <div>
          <p className="font-medium">Client:</p>
          <p>{client?.name || '—'}</p>
          <p>{client?.cui ? `CUI: ${client.cui}` : ''}</p>
        </div>
        <div className="text-right">
          <p>Data: {date || '—'}</p>
          <p>Scadenta: {dueDate || '—'}</p>
        </div>
      </div>
      <table className="w-full text-xs mb-3">
        <thead><tr className="border-b"><th className="text-left py-1">Descriere</th>
          <th className="text-right">Cant.</th><th className="text-right">Pret</th>
          <th className="text-right">Total</th></tr></thead>
        <tbody>
          {items.filter(i => i.description).map((i, idx) => (
            <tr key={idx} className="border-b border-gray-200">
              <td className="py-1">{i.description}</td>
              <td className="text-right">{i.quantity}</td>
              <td className="text-right">{i.unit_price} RON</td>
              <td className="text-right">{(i.quantity * i.unit_price).toFixed(2)} RON</td>
            </tr>
          ))}
        </tbody>
      </table>
      <div className="text-right space-y-1">
        <p>Subtotal: <span className="font-medium">{subtotal.toFixed(2)} RON</span></p>
        {vatPercent > 0 && <p>TVA ({vatPercent}%): {vat.toFixed(2)} RON</p>}
        <p className="text-base font-bold">Total: {total.toFixed(2)} RON</p>
      </div>
      {notes && <p className="mt-3 text-xs text-gray-500 italic">{notes}</p>}
    </div>
  );
}
```

**Complexitate:** Mica | **Impact:** Mediu

---

### 7. Invoice — Conversie Automata Moneda cu Curs BNR

**Fisier:** `frontend/src/pages/InvoicePage.jsx`, `backend/modules/invoice/crud.py`
**Problema actuala:** Facturile sunt doar in RON. Clientii externi platesc in EUR/USD. Utilizatorul trebuie sa calculeze manual conversia, desi exista deja endpoint BNR (`/api/quick-tools/exchange-rate`).

**Imbunatatire propusa:**
- Selector moneda pe factura (RON/EUR/USD/GBP)
- Daca moneda != RON, afiseaza automat contravaloarea in RON la curs BNR
- Cursul BNR se preia automat din endpoint-ul existent
- Mentiune pe factura: "Curs BNR din data de DD.MM.YYYY: 1 EUR = X.XXXX RON"

**Exemplu implementare (frontend):**
```jsx
const [currency, setCurrency] = useState('RON');
const [exchangeRate, setExchangeRate] = useState(null);

useEffect(() => {
  if (currency !== 'RON') {
    api.get('/api/quick-tools/exchange-rate').then(r => {
      const rates = r.data;
      const rate = rates[currency] || null;
      setExchangeRate(rate);
    });
  } else {
    setExchangeRate(null);
  }
}, [currency]);

// In formularul de creare:
<select value={currency} onChange={e => setCurrency(e.target.value)} className="input-field w-24">
  <option value="RON">RON</option>
  <option value="EUR">EUR</option>
  <option value="USD">USD</option>
  <option value="GBP">GBP</option>
</select>

{exchangeRate && (
  <p className="text-xs text-gray-400 mt-1">
    Curs BNR: 1 {currency} = {exchangeRate.toFixed(4)} RON
    (Total RON: {(total * exchangeRate).toFixed(2)})
  </p>
)}
```

**Complexitate:** Mica | **Impact:** Mare (clienti externi)

---

### 8. ITP — Notificari Expirare cu Integrare Calendar

**Fisier:** `backend/modules/itp/router.py`
**Problema actuala:** Exista endpoint `/api/itp/expiring` care returneaza inspectii care vor expira, dar nu exista notificari proactive. Utilizatorul trebuie sa verifice manual.

**Imbunatatire propusa:**
- Task cron zilnic care verifica ITP-urile ce expira in urmatoarele 7/14/30 zile
- Trimite notificare (Telegram bot, existent in .env) pentru fiecare vehicul
- Optiune de creare eveniment Google Calendar cu data expirarii
- Marcare "notificat" pentru a nu retrimite

**Exemplu implementare (backend):**
```python
# In modules/itp/router.py — adaugare cron job
async def check_itp_expiring_notifications():
    """Cron job zilnic — verifica ITP-uri care expira curand"""
    async with get_db() as db:
        rows = await db.execute_fetchall(
            "SELECT plate_number, owner_name, expiry_date FROM inspection_records "
            "WHERE DATE(expiry_date) BETWEEN DATE('now') AND DATE('now', '+14 days') "
            "AND notified_expiry IS NULL OR notified_expiry = 0"
        )
        for row in rows:
            days_left = (datetime.strptime(row["expiry_date"], "%Y-%m-%d") - datetime.now()).days
            message = f"ITP expira in {days_left} zile: {row['plate_number']} ({row['owner_name']})"

            # Notificare via Telegram (daca configurat)
            telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
            telegram_chat = os.getenv("TELEGRAM_CHAT_ID")
            if telegram_token and telegram_chat:
                async with httpx.AsyncClient() as client:
                    await client.post(
                        f"https://api.telegram.org/bot{telegram_token}/sendMessage",
                        json={"chat_id": telegram_chat, "text": message}
                    )

            # Marcheaza ca notificat
            await db.execute(
                "UPDATE inspection_records SET notified_expiry = 1 WHERE plate_number = ?",
                (row["plate_number"],)
            )
        await db.commit()
```

**Migrare SQL necesara:**
```sql
ALTER TABLE inspection_records ADD COLUMN notified_expiry INTEGER DEFAULT 0;
```

**Complexitate:** Medie | **Impact:** Mare (previne penalitati)

---

### 9. ITP — Atasare Fotografii la Inspectie

**Fisier:** `backend/modules/itp/router.py`, `frontend/src/pages/ITPPage.jsx`
**Problema actuala:** Inspectiile stocheaza doar date text. In practica, fotografii ale vehiculului/defectelor sunt esentiale pentru documentare si disputte.

**Imbunatatire propusa:**
- Endpoint upload foto legat de inspection_id
- Stocare in `backend/data/itp_photos/{inspection_id}/`
- Maxim 5 fotografii per inspectie, max 5MB/foto
- Galerie in modal la vizualizare inspectie
- Compresie automata (resize la 1920px latime)

**Exemplu implementare (backend):**
```python
@router.post("/api/itp/inspections/{inspection_id}/photos")
async def upload_inspection_photo(inspection_id: int, file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(400, "Doar imagini sunt permise")
    if file.size > 5 * 1024 * 1024:
        raise HTTPException(400, "Fisierul depaseste 5MB")

    photo_dir = Path(settings.data_dir) / "itp_photos" / str(inspection_id)
    photo_dir.mkdir(parents=True, exist_ok=True)

    existing = list(photo_dir.glob("*.jpg"))
    if len(existing) >= 5:
        raise HTTPException(400, "Maxim 5 fotografii per inspectie")

    filename = f"{len(existing) + 1}_{int(time.time())}.jpg"
    filepath = photo_dir / filename
    content = await file.read()

    # Resize daca e prea mare
    from PIL import Image
    import io
    img = Image.open(io.BytesIO(content))
    if img.width > 1920:
        ratio = 1920 / img.width
        img = img.resize((1920, int(img.height * ratio)), Image.LANCZOS)
    img.save(str(filepath), "JPEG", quality=85)

    return {"filename": filename, "path": str(filepath)}
```

**Nota:** Necesita `pip install Pillow` (gratuit, deja disponibil in ecosistem Python).

**Complexitate:** Medie | **Impact:** Mare (documentare teren)

---

### 10. File Manager — Mod Galerie pentru Imagini

**Fisier:** `frontend/src/pages/FileBrowserPage.jsx`
**Problema actuala:** File Manager-ul afiseaza fisierele ca lista (icon, nume, dimensiune). Imaginile au preview, dar nu exista un mod galerie grid care sa arate thumbnails.

**Imbunatatire propusa:**
- Toggle lista/galerie (icoane Grid/List)
- Mod galerie: grid 3-4 coloane cu thumbnails
- Click pe imagine = fullscreen preview (existent)
- Filtru automat "doar imagini" cand e activ modul galerie

**Exemplu implementare:**
```jsx
const [viewMode, setViewMode] = useState('list'); // list | gallery

// Toggle button in header
<div className="flex gap-1">
  <button onClick={() => setViewMode('list')}
    className={`p-1.5 rounded ${viewMode === 'list' ? 'bg-blue-600' : 'bg-gray-700'}`}>
    <List className="w-4 h-4" />
  </button>
  <button onClick={() => setViewMode('gallery')}
    className={`p-1.5 rounded ${viewMode === 'gallery' ? 'bg-blue-600' : 'bg-gray-700'}`}>
    <Grid className="w-4 h-4" />
  </button>
</div>

// Gallery view
{viewMode === 'gallery' ? (
  <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
    {files.filter(f => /\.(jpg|jpeg|png|gif|webp|bmp)$/i.test(f.name)).map(f => (
      <div key={f.name} onClick={() => setPreview(f)}
        className="aspect-square bg-gray-800 rounded-lg overflow-hidden cursor-pointer hover:ring-2 ring-blue-500">
        <img src={`/api/filemanager/serve?path=${encodeURIComponent(currentPath + '/' + f.name)}`}
          alt={f.name} className="w-full h-full object-cover" loading="lazy" />
        <p className="text-xs text-gray-400 p-1 truncate">{f.name}</p>
      </div>
    ))}
  </div>
) : (
  // Existing list view...
)}
```

**Complexitate:** Mica | **Impact:** Mediu

---

### 11. Calculator — Grafic Trend Preturi Istorice

**Fisier:** `frontend/src/pages/HistoryPage.jsx`
**Problema actuala:** History afiseaza lista de calcule trecute, dar nu exista o vizualizare grafica a evolutiei preturilor. Utilizatorul nu poate vedea daca preturile cresc/scad in timp.

**Imbunatatire propusa:**
- Grafic linie (Recharts, deja disponibil) deasupra tabelului de istoric
- Axa X: data, Axa Y: pret (RON)
- Tooltip cu detalii (fisier, metoda, confidence)
- Filtru pe tip fisier (PDF/DOCX) si pe perioada

**Exemplu implementare:**
```jsx
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

// In HistoryPage, deasupra tabelului
const chartData = useMemo(() =>
  entries
    .filter(e => e.market_price > 0)
    .sort((a, b) => new Date(a.created_at) - new Date(b.created_at))
    .map(e => ({
      date: new Date(e.created_at).toLocaleDateString('ro-RO', { day: '2d', month: '2d' }),
      price: e.market_price,
      filename: e.filename,
    })),
  [entries]
);

{chartData.length > 2 && (
  <div className="bg-gray-900 rounded-2xl border border-gray-800 p-4 mb-6">
    <h3 className="text-sm font-medium text-gray-300 mb-3">Evolutie Preturi</h3>
    <ResponsiveContainer width="100%" height={200}>
      <LineChart data={chartData}>
        <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#9ca3af' }} />
        <YAxis tick={{ fontSize: 10, fill: '#9ca3af' }} />
        <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151' }}
          labelStyle={{ color: '#9ca3af' }} />
        <Line type="monotone" dataKey="price" stroke="#3b82f6" strokeWidth={2} dot={{ r: 3 }} />
      </LineChart>
    </ResponsiveContainer>
  </div>
)}
```

**Complexitate:** Mica | **Impact:** Mediu

---

### 12. AI Chat — Syntax Highlighting in Raspunsuri

**Fisier:** `frontend/src/pages/AIChatPage.jsx`
**Problema actuala:** Raspunsurile AI care contin cod sunt afisate ca text simplu. Nu exista syntax highlighting, ceea ce face codul greu de citit.

**Imbunatatire propusa:**
- Parsare markdown in raspunsuri (blocuri ``` cu limbaj)
- Syntax highlighting cu `highlight.js` (zero cost, gratuit, 30+ limbaje)
- Buton "Copiaza cod" pe fiecare bloc de cod
- Alternativa zero-dependency: simpla colorare cu regex pentru cuvinte cheie

**Exemplu implementare (varianta usoara, fara dependency noua):**
```jsx
// Funcție simpla de parsare markdown -> HTML
function renderMarkdown(text) {
  if (!text) return '';
  return text
    // Code blocks
    .replace(/```(\w+)?\n([\s\S]*?)```/g, (_, lang, code) =>
      `<pre class="bg-gray-900 rounded-lg p-3 my-2 overflow-x-auto border border-gray-700">
        <div class="flex justify-between items-center mb-2">
          <span class="text-xs text-gray-500">${lang || 'code'}</span>
        </div>
        <code class="text-sm text-green-300">${code.replace(/</g, '&lt;')}</code>
      </pre>`)
    // Inline code
    .replace(/`([^`]+)`/g, '<code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-sm">$1</code>')
    // Bold
    .replace(/\*\*(.+?)\*\*/g, '<strong class="text-white">$1</strong>')
    // Italic
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    // Line breaks
    .replace(/\n/g, '<br/>');
}

// In chat message render:
<div className="prose prose-invert prose-sm max-w-none"
  dangerouslySetInnerHTML={{ __html: renderMarkdown(message.content) }} />
```

**Nota:** Pentru syntax highlighting complet, se poate adauga `npm install highlight.js` (gratuit, 1MB), dar varianta regex de mai sus acopera 80% din cazuri fara dependency noua.

**Complexitate:** Mica | **Impact:** Mediu

---

### 13. Notepad — Preview Markdown si Mod Split

**Fisier:** `frontend/src/pages/NotepadPage.jsx`
**Problema actuala:** Notepad-ul este un editor text simplu. Multe notite contin formatare markdown (liste, titluri, bold), dar nu exista preview.

**Imbunatatire propusa:**
- Buton toggle "Edit / Preview / Split"
- Mod Split: jumatate stanga editor, jumatate dreapta preview
- Refolosire functie `renderMarkdown` din AI Chat
- Preview se actualizeaza live la tastare (debounce 300ms)

**Exemplu implementare:**
```jsx
const [viewMode, setViewMode] = useState('edit'); // edit | preview | split

// Toggle buttons
<div className="flex gap-1 mb-2">
  {['edit', 'preview', 'split'].map(m => (
    <button key={m} onClick={() => setViewMode(m)}
      className={`px-3 py-1 text-xs rounded ${viewMode === m ? 'bg-blue-600' : 'bg-gray-700'}`}>
      {m === 'edit' ? 'Edit' : m === 'preview' ? 'Preview' : 'Split'}
    </button>
  ))}
</div>

// Content area
<div className={`flex gap-4 ${viewMode === 'split' ? '' : ''}`}>
  {(viewMode === 'edit' || viewMode === 'split') && (
    <textarea value={content} onChange={e => setContent(e.target.value)}
      className={`input-field ${viewMode === 'split' ? 'w-1/2' : 'w-full'} min-h-[400px] font-mono text-sm`} />
  )}
  {(viewMode === 'preview' || viewMode === 'split') && (
    <div className={`${viewMode === 'split' ? 'w-1/2' : 'w-full'} bg-gray-800 rounded-lg p-4 prose prose-invert prose-sm min-h-[400px] overflow-auto`}
      dangerouslySetInnerHTML={{ __html: renderMarkdown(content) }} />
  )}
</div>
```

**Complexitate:** Mica | **Impact:** Mediu

---

### 14. Vault — Dashboard Utilizare Chei API

**Fisier:** `frontend/src/pages/VaultPage.jsx`
**Problema actuala:** Vault-ul stocheaza si afiseaza cheile API, dar nu arata cat s-a consumat din fiecare free tier. Utilizatorul nu stie cand se apropie de limita.

**Imbunatatire propusa:**
- Sectiune "Usage Overview" cu bare de progres per provider
- Date preluate din endpoint-urile existente (translator usage, AI providers)
- Culori: verde (<50%), galben (50-80%), rosu (>80%)
- Link direct la pagina providerului pentru verificare

**Exemplu implementare:**
```jsx
function VaultUsageOverview() {
  const [usage, setUsage] = useState([]);

  useEffect(() => {
    Promise.allSettled([
      api.get('/api/translator/usage'),
      api.get('/api/ai/providers'),
    ]).then(([transRes, aiRes]) => {
      const items = [];
      if (transRes.status === 'fulfilled') {
        const u = transRes.value.data;
        if (u.deepl) items.push({
          name: 'DeepL', used: u.deepl.character_count || 0,
          limit: 500000, unit: 'chars/luna'
        });
      }
      // Similar for other providers...
      setUsage(items);
    });
  }, []);

  return (
    <div className="bg-gray-900 rounded-2xl border border-gray-800 p-5 mb-4">
      <h3 className="text-sm font-medium text-gray-300 mb-3">Utilizare Free Tier</h3>
      {usage.map(u => {
        const pct = Math.min(100, Math.round((u.used / u.limit) * 100));
        const color = pct < 50 ? 'bg-green-500' : pct < 80 ? 'bg-yellow-500' : 'bg-red-500';
        return (
          <div key={u.name} className="mb-2">
            <div className="flex justify-between text-xs text-gray-400 mb-1">
              <span>{u.name}</span>
              <span>{u.used.toLocaleString()} / {u.limit.toLocaleString()} {u.unit} ({pct}%)</span>
            </div>
            <div className="w-full bg-gray-800 rounded-full h-1.5">
              <div className={`${color} h-1.5 rounded-full transition-all`} style={{ width: `${pct}%` }} />
            </div>
          </div>
        );
      })}
    </div>
  );
}
```

**Complexitate:** Medie | **Impact:** Mare (previne depasire limite)

---

### 15. Automations — Notificari pe Esec Task

**Fisier:** `backend/modules/automations/router.py`
**Problema actuala:** Task-urile cron ruleaza in background, dar daca esueaza, eroarea se logheaza doar in activity_log. Utilizatorul nu afla daca backup-ul zilnic a esuat, de exemplu.

**Imbunatatire propusa:**
- La esec task cron, trimite notificare via Telegram (deja configurat)
- Adauga camp `notify_on_failure` pe task
- Retry automat deja exista (max_retries), dar notificarea lipseste

**Exemplu implementare:**
```python
# In _execute_task() din automations/router.py
async def _execute_task(task_id: int, task_name: str, action_type: str, config: dict):
    try:
        result = await _run_action(action_type, config)
        await _log_execution(task_id, "success", result)
    except Exception as e:
        await _log_execution(task_id, "error", str(e))

        # Notificare pe esec
        async with get_db() as db:
            task = await db.execute_fetchone(
                "SELECT notify_on_failure FROM scheduled_tasks WHERE id = ?", (task_id,)
            )
            if task and task["notify_on_failure"]:
                telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
                telegram_chat = os.getenv("TELEGRAM_CHAT_ID")
                if telegram_token and telegram_chat:
                    msg = f"Task ESUAT: {task_name}\nEroare: {str(e)[:200]}\nData: {datetime.now().strftime('%H:%M %d.%m.%Y')}"
                    async with httpx.AsyncClient() as client:
                        await client.post(
                            f"https://api.telegram.org/bot{telegram_token}/sendMessage",
                            json={"chat_id": telegram_chat, "text": msg, "parse_mode": "HTML"}
                        )
```

**Migrare SQL:**
```sql
ALTER TABLE scheduled_tasks ADD COLUMN notify_on_failure INTEGER DEFAULT 1;
```

**Complexitate:** Mica | **Impact:** Mare (awareness esecuri)

---

### 16. Reports — Export Raport Lunar Complet PDF

**Fisier:** `backend/modules/reports/system_reports.py`
**Problema actuala:** Exista endpoint `/api/reports/export/pdf` dar nu genereaza un raport lunar business complet. Raportul actual e tehnic (disk stats, system info). Nu include: facturi emise, incasari, traduceri efectuate, ITP-uri, venit per client.

**Imbunatatire propusa:**
- Endpoint `/api/reports/monthly-business-report?month=2026-03` care genereaza PDF cu:
  - Rezumat luna: venit total, nr facturi, nr traduceri, nr ITP
  - Top 5 clienti dupa venit
  - Facturi neincasate (aged receivables)
  - Grafic activitate zilnica (bar chart in PDF)
  - Lista facturi emise cu status
- Format PDF cu layout profesional

**Complexitate:** Mare | **Impact:** Mare (vizibilitate business)

---

# PARTEA II — FUNCTII NOI

---

### 17. Cautare Globala Cross-Module

**Descriere:** Bara de cautare unificata (integrata in Command Palette existent) care cauta simultan in: facturi, clienti, inspectii ITP, notite, traduceri, fisiere, sesiuni AI.

**De ce e util:** Acum utilizatorul trebuie sa navigheze la fiecare modul separat si sa caute acolo. O cautare globala economiseste timp si gaseste informatia instant indiferent unde e stocata. Fluxul natural: "stiu ca am tradus ceva pentru clientul X" — cauta si gaseste factura, traducerea, nota asociata.

**Complexitate:** Medie | **Impact:** Maxim

**Exemplu implementare (backend):**
```python
# app/api/routes_search.py
@router.get("/api/search")
async def global_search(q: str, limit: int = 10):
    if len(q) < 2:
        raise HTTPException(400, "Minim 2 caractere")

    results = []
    async with get_db() as db:
        # Facturi
        invoices = await db.execute_fetchall(
            "SELECT id, invoice_number, status FROM invoices "
            "WHERE invoice_number LIKE ? OR notes LIKE ? LIMIT ?",
            (f"%{q}%", f"%{q}%", limit)
        )
        for inv in invoices:
            results.append({"type": "invoice", "id": inv["id"],
                "title": inv["invoice_number"], "subtitle": inv["status"],
                "url": "/invoices"})

        # Clienti
        clients = await db.execute_fetchall(
            "SELECT id, name, cui FROM clients WHERE name LIKE ? OR cui LIKE ? LIMIT ?",
            (f"%{q}%", f"%{q}%", limit)
        )
        for cl in clients:
            results.append({"type": "client", "id": cl["id"],
                "title": cl["name"], "subtitle": cl.get("cui", ""),
                "url": "/invoices"})

        # ITP
        itps = await db.execute_fetchall(
            "SELECT id, plate_number, owner_name FROM inspection_records "
            "WHERE plate_number LIKE ? OR owner_name LIKE ? LIMIT ?",
            (f"%{q}%", f"%{q}%", limit)
        )
        for itp in itps:
            results.append({"type": "itp", "id": itp["id"],
                "title": itp["plate_number"], "subtitle": itp["owner_name"],
                "url": "/itp"})

        # Notite
        notes = await db.execute_fetchall(
            "SELECT id, title FROM notes WHERE title LIKE ? OR content LIKE ? LIMIT ?",
            (f"%{q}%", f"%{q}%", limit)
        )
        for n in notes:
            results.append({"type": "note", "id": n["id"],
                "title": n["title"], "url": "/notepad"})

    return {"query": q, "results": results, "total": len(results)}
```

**Frontend — integrare in CommandPalette:**
```jsx
// In CommandPalette.jsx — adauga tab "Cauta Peste Tot"
const [globalResults, setGlobalResults] = useState([]);

useEffect(() => {
  if (query.length >= 2) {
    const timer = setTimeout(async () => {
      const { data } = await api.get('/api/search', { params: { q: query } });
      setGlobalResults(data.results);
    }, 300);
    return () => clearTimeout(timer);
  }
}, [query]);
```

---

### 18. Time Tracking — Cronometru Legat de Facturare

**Descriere:** Modul de time tracking care permite cronometrarea timpului petrecut pe traduceri si inspectii, cu posibilitatea de a genera automat linii de factura din timpii inregistrati.

**De ce e util:** Roland factureaza traduceri la ora sau per document. Fara time tracking, estimeaza manual timpul. Cu time tracking, poate demonstra clientilor exact cat a durat, si poate genera facturi precise. Este un workflow critic pentru orice freelancer/firma mica.

**Complexitate:** Mare | **Impact:** Maxim

**Exemplu implementare (backend):**
```python
# modules/timetracking/router.py
from fastapi import APIRouter, HTTPException
from app.db.database import get_db
from datetime import datetime

router = APIRouter(prefix="/api/time", tags=["Time Tracking"])

@router.post("/start")
async def start_timer(project: str, description: str = "", client_id: int = None):
    async with get_db() as db:
        # Check for running timer
        running = await db.execute_fetchone(
            "SELECT id FROM time_entries WHERE end_time IS NULL"
        )
        if running:
            raise HTTPException(400, "Exista deja un cronometru activ. Opreste-l mai intai.")

        await db.execute(
            "INSERT INTO time_entries (project, description, client_id, start_time) "
            "VALUES (?, ?, ?, ?)",
            (project, description, client_id, datetime.now().isoformat())
        )
        await db.commit()
        return {"status": "started"}

@router.post("/stop")
async def stop_timer():
    async with get_db() as db:
        running = await db.execute_fetchone(
            "SELECT id, start_time FROM time_entries WHERE end_time IS NULL"
        )
        if not running:
            raise HTTPException(400, "Niciun cronometru activ")

        end_time = datetime.now()
        start_time = datetime.fromisoformat(running["start_time"])
        duration_minutes = int((end_time - start_time).total_seconds() / 60)

        await db.execute(
            "UPDATE time_entries SET end_time = ?, duration_minutes = ? WHERE id = ?",
            (end_time.isoformat(), duration_minutes, running["id"])
        )
        await db.commit()
        return {"status": "stopped", "duration_minutes": duration_minutes}

@router.get("/entries")
async def list_entries(client_id: int = None, start_date: str = None, end_date: str = None):
    async with get_db() as db:
        where = []
        params = []
        if client_id:
            where.append("client_id = ?")
            params.append(client_id)
        if start_date:
            where.append("DATE(start_time) >= ?")
            params.append(start_date)
        if end_date:
            where.append("DATE(start_time) <= ?")
            params.append(end_date)

        where_sql = "WHERE " + " AND ".join(where) if where else ""
        rows = await db.execute_fetchall(
            f"SELECT * FROM time_entries {where_sql} ORDER BY start_time DESC LIMIT 100",
            params
        )
        return {"entries": [dict(r) for r in rows]}

@router.post("/to-invoice-items")
async def convert_to_invoice_items(entry_ids: list[int], hourly_rate: float = 50.0):
    """Converteste intrari de timp in linii de factura"""
    async with get_db() as db:
        items = []
        for eid in entry_ids:
            entry = await db.execute_fetchone(
                "SELECT * FROM time_entries WHERE id = ?", (eid,)
            )
            if entry and entry["duration_minutes"]:
                hours = round(entry["duration_minutes"] / 60, 2)
                items.append({
                    "description": f"{entry['project']}: {entry['description']}",
                    "quantity": hours,
                    "unit_price": hourly_rate,
                    "unit": "ore"
                })
        return {"items": items}
```

**Migrare SQL:**
```sql
CREATE TABLE IF NOT EXISTS time_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project TEXT NOT NULL,
    description TEXT DEFAULT '',
    client_id INTEGER,
    start_time TEXT NOT NULL,
    end_time TEXT,
    duration_minutes INTEGER,
    invoiced INTEGER DEFAULT 0,
    invoice_id INTEGER,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (client_id) REFERENCES clients(id)
);
CREATE INDEX idx_time_entries_client ON time_entries(client_id);
CREATE INDEX idx_time_entries_date ON time_entries(DATE(start_time));
```

---

### 19. Floating Timer — Widget Persistent

**Descriere:** Widget floating (colt stanga-jos) care arata cronometrul activ pe orice pagina. Click = start/stop. Vizibil permanent, nu doar pe pagina time tracking.

**De ce e util:** Utilizatorul navigheaza intre module in timp ce lucreaza. Cronometrul trebuie vizibil si controlabil de oriunde, nu doar din pagina dedicata.

**Complexitate:** Mica | **Impact:** Mare

**Exemplu implementare:**
```jsx
// components/shared/FloatingTimer.jsx
function FloatingTimer() {
  const [running, setRunning] = useState(null);
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    // Check for active timer on mount
    api.get('/api/time/active').then(r => {
      if (r.data.active) setRunning(r.data);
    }).catch(() => {});
  }, []);

  useEffect(() => {
    if (!running) return;
    const interval = setInterval(() => {
      const start = new Date(running.start_time);
      setElapsed(Math.floor((Date.now() - start.getTime()) / 1000));
    }, 1000);
    return () => clearInterval(interval);
  }, [running]);

  if (!running) return null;

  const hours = Math.floor(elapsed / 3600);
  const mins = Math.floor((elapsed % 3600) / 60);
  const secs = elapsed % 60;

  return (
    <div className="fixed bottom-4 left-4 z-50 bg-blue-600 text-white rounded-full px-4 py-2 shadow-lg flex items-center gap-3 cursor-pointer hover:bg-blue-700"
      onClick={async () => {
        await api.post('/api/time/stop');
        setRunning(null);
      }}>
      <Clock className="w-4 h-4 animate-pulse" />
      <span className="font-mono text-sm">
        {String(hours).padStart(2, '0')}:{String(mins).padStart(2, '0')}:{String(secs).padStart(2, '0')}
      </span>
      <span className="text-xs opacity-75">{running.project}</span>
    </div>
  );
}
```

---

### 20. Activity Digest — Sumar Zilnic via Telegram

**Descriere:** La sfarsitul zilei (ora 20:00), trimite un mesaj Telegram cu rezumatul activitatii: facturi emise, traduceri facute, ITP-uri, timp lucrat total.

**De ce e util:** Roland primeste un rezumat automat al zilei fara sa deschida aplicatia. Util mai ales pe telefon cand nu e la PC.

**Complexitate:** Medie | **Impact:** Mare

**Exemplu implementare:**
```python
async def send_daily_digest():
    """Cron job la 20:00 — rezumat zilnic"""
    async with get_db() as db:
        today = datetime.now().strftime("%Y-%m-%d")

        invoices = await db.execute_fetchone(
            "SELECT COUNT(*) as cnt, COALESCE(SUM(total_amount), 0) as total "
            "FROM invoices WHERE DATE(created_at) = ?", (today,)
        )
        translations = await db.execute_fetchone(
            "SELECT COUNT(*) as cnt FROM activity_log "
            "WHERE action LIKE 'translator%' AND DATE(timestamp) = ?", (today,)
        )
        itps = await db.execute_fetchone(
            "SELECT COUNT(*) as cnt FROM inspection_records "
            "WHERE DATE(created_at) = ?", (today,)
        )

        msg = (
            f"Rezumat {today}:\n"
            f"- Facturi: {invoices['cnt']} ({invoices['total']:.0f} RON)\n"
            f"- Traduceri: {translations['cnt']}\n"
            f"- ITP: {itps['cnt']}\n"
        )

        telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
        telegram_chat = os.getenv("TELEGRAM_CHAT_ID")
        if telegram_token and telegram_chat:
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"https://api.telegram.org/bot{telegram_token}/sendMessage",
                    json={"chat_id": telegram_chat, "text": msg}
                )
```

---

### 21. Client Communication Log

**Descriere:** Tab nou in sectiunea Clienti din Invoice care pastreaza un jurnal de comunicare per client: note despre discutii telefonice, emailuri trimise, acorduri verbale, preferinte.

**De ce e util:** Roland lucreaza cu clienti recurenti. Memoria umana nu retine toate discutiile. Un log de comunicare legat de client ofera context instant la urmatoarea interactiune.

**Complexitate:** Medie | **Impact:** Mare

**Exemplu implementare (backend):**
```python
@router.get("/api/invoice/clients/{client_id}/comm-log")
async def get_comm_log(client_id: int):
    async with get_db() as db:
        rows = await db.execute_fetchall(
            "SELECT * FROM client_comm_log WHERE client_id = ? ORDER BY date DESC",
            (client_id,)
        )
        return {"entries": [dict(r) for r in rows]}

@router.post("/api/invoice/clients/{client_id}/comm-log")
async def add_comm_entry(client_id: int, comm_type: str, summary: str, details: str = ""):
    async with get_db() as db:
        await db.execute(
            "INSERT INTO client_comm_log (client_id, comm_type, summary, details, date) "
            "VALUES (?, ?, ?, ?, ?)",
            (client_id, comm_type, summary, details, datetime.now().isoformat())
        )
        await db.commit()
        return {"status": "ok"}
```

**Migrare SQL:**
```sql
CREATE TABLE IF NOT EXISTS client_comm_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    comm_type TEXT NOT NULL CHECK(comm_type IN ('phone', 'email', 'meeting', 'note')),
    summary TEXT NOT NULL,
    details TEXT DEFAULT '',
    date TEXT NOT NULL,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
);
CREATE INDEX idx_comm_log_client ON client_comm_log(client_id);
```

---

### 22. Document Templates Library

**Descriere:** Biblioteca de template-uri pentru documente frecvent create: scrisori de insotire traduceri, procese verbale ITP, oferte standard, contracte cadru.

**De ce e util:** Roland genereaza frecvent aceleasi tipuri de documente cu date diferite. Template-urile cu placeholdere ({{client_name}}, {{date}}, {{plate_number}}) elimina copy-paste manual.

**Complexitate:** Medie | **Impact:** Mare

**Exemplu implementare:**
```python
@router.get("/api/templates")
async def list_templates():
    async with get_db() as db:
        rows = await db.execute_fetchall("SELECT * FROM document_templates ORDER BY name")
        return {"templates": [dict(r) for r in rows]}

@router.post("/api/templates/{template_id}/render")
async def render_template(template_id: int, variables: dict):
    """Randeaza template cu variabile: {{client_name}} -> 'SC Exemplu SRL'"""
    async with get_db() as db:
        tpl = await db.execute_fetchone(
            "SELECT content FROM document_templates WHERE id = ?", (template_id,)
        )
        if not tpl:
            raise HTTPException(404, "Template negasit")

        content = tpl["content"]
        for key, value in variables.items():
            content = content.replace(f"{{{{{key}}}}}", str(value))

        return {"rendered": content}
```

---

### 23. Offline Mode Enhanced (PWA)

**Descriere:** Imbunatatire PWA pentru a functiona offline pe Android: cache local pentru ultimele facturi, inspectii ITP, notite. Sincronizare la reconectare.

**De ce e util:** Roland face inspectii ITP in teren unde conexiunea poate fi instabila. Cu offline mode, poate vizualiza/crea inspectii si sincroniza cand revine la retea.

**Complexitate:** Mare | **Impact:** Maxim (utilizare teren)

**Exemplu implementare (conceptual — vite.config.js):**
```javascript
// Upgrade workbox strategies in vite.config.js
workbox: {
  runtimeCaching: [
    {
      urlPattern: /\/api\/itp\/inspections/,
      handler: 'NetworkFirst',
      options: {
        cacheName: 'itp-cache',
        expiration: { maxEntries: 100, maxAgeSeconds: 86400 },
        networkTimeoutSeconds: 5,  // Fallback to cache after 5s
      },
    },
    {
      urlPattern: /\/api\/invoice\/(invoices|clients)/,
      handler: 'NetworkFirst',
      options: {
        cacheName: 'invoice-cache',
        expiration: { maxEntries: 200, maxAgeSeconds: 86400 },
        networkTimeoutSeconds: 5,
      },
    },
    {
      urlPattern: /\/api\/quick-tools\/notes/,
      handler: 'StaleWhileRevalidate',
      options: {
        cacheName: 'notes-cache',
        expiration: { maxEntries: 50, maxAgeSeconds: 604800 },
      },
    },
  ],
},
```

**Frontend — indicator offline:**
```jsx
// In Header.jsx
const [isOnline, setIsOnline] = useState(navigator.onLine);
useEffect(() => {
  const onOnline = () => setIsOnline(true);
  const onOffline = () => setIsOnline(false);
  window.addEventListener('online', onOnline);
  window.addEventListener('offline', onOffline);
  return () => { window.removeEventListener('online', onOnline); window.removeEventListener('offline', onOffline); };
}, []);

{!isOnline && (
  <div className="bg-yellow-600/20 text-yellow-400 text-xs px-3 py-1 rounded-full flex items-center gap-1">
    <WifiOff className="w-3 h-3" /> Offline
  </div>
)}
```

---

### 24. Pagina Keyboard Shortcuts Completa

**Descriere:** Pagina dedicata `/shortcuts` cu toate shortcut-urile disponibile, grupate pe module, cu posibilitatea de a le personaliza.

**De ce e util:** Exista shortcut-uri in useHotkeys.js, dar utilizatorul nu le cunoaste pe toate. Modalul de shortcuts (Ctrl+/) este minimal. O pagina dedicata cu cautare ajuta la descoperire.

**Complexitate:** Mica | **Impact:** Mic

---

### 25. Quick Invoice from Calculator

**Descriere:** Buton "Factureaza Direct" pe rezultatul calculatorului de pret care creeaza automat o factura cu clientul selectat si pretul calculat, fara a naviga manual la Invoice.

**De ce e util:** Fluxul natural: upload document -> calculeaza pret -> factureaza. Acum pasii 2 si 3 sunt deconectati. Integrarea directa elimina copy-paste manual al pretului.

**Complexitate:** Mica | **Impact:** Mare (flux natural)

**Exemplu implementare:**
```jsx
// In UploadPage.jsx, pe PriceCard
<button onClick={async () => {
  const { data } = await api.post('/api/create-invoice-from-calculation', {
    calculation_id: result.calculation_id,
    client_id: selectedClient || null,
  });
  navigate(`/invoices?tab=create&invoice_id=${data.invoice_id}`);
}} className="btn-primary text-sm mt-2">
  <Receipt className="w-4 h-4 mr-1" /> Factureaza Direct
</button>
```

---

### 26. Drag & Drop Reordonare Dashboard Widgets

**Descriere:** Posibilitatea de a reordona widget-urile de pe dashboard prin drag & drop, cu persistare in localStorage.

**De ce e util:** Fiecare utilizator are prioritati diferite. Roland poate vrea cursul BNR sus, altcineva preferă activitatea recenta. Personalizarea creste eficienta.

**Complexitate:** Medie | **Impact:** Mic

---

### 27. Duplicate Invoice Detection Enhancement

**Descriere:** Avertizare inteligenta la creare factura daca exista deja o factura similara (acelasi client + aceleasi servicii + data apropiata).

**De ce e util:** Previne facturarea dubla accidentala, care duce la confuzie cu clientii si probleme contabile.

**Complexitate:** Mica | **Impact:** Mare (previne erori financiare)

---

### 28. ITP — Quick Entry din Mobile

**Descriere:** Formular simplificat de creare inspectie ITP optimizat pentru telefon: doar campurile esentiale (numar inmatriculare, tip, rezultat), cu autocomplete pe baza istoricului.

**De ce e util:** In teren, Roland introduce inspectii de pe Android. Formularul actual (desktop-first) are prea multe campuri. Un formular simplificat mobile-first creste viteza de inregistrare.

**Complexitate:** Medie | **Impact:** Mare (productivitate teren)

---

# PARTEA III — IMBUNATATIRI TEHNICE

---

### 29. FIX CRITIC: Migration 017 Duplicata

**Problema:** Exista doua fisiere cu acelasi numar de migrare: `017_notes_category.sql` si `017_translation_cache.sql`. Sistemul de migrari ruleaza fisierele in ordine alfabetica/numerica. Daca ambele au numarul 017, una poate fi sarita sau poate cauza conflict in tabela `schema_version`.

**Solutie:** Renumeste `017_translation_cache.sql` in `023_translation_cache.sql` (urmatorul numar disponibil).

**Complexitate:** Mica | **Impact:** Categorie (Securitate Date) — **URGENT**

---

### 30. Frontend Tests cu Vitest

**Problema:** Zero teste frontend. Orice modificare de componenta poate introduce regresii fara sa fie detectate. 61 componente JSX fara niciun test.

**Solutie:** Configureaza Vitest + React Testing Library. Adauga teste pentru componentele critice: DashboardPage, InvoicePage, TranslatorPage, AIChatPage.

**Complexitate:** Mare | **Impact:** Categorie (Calitate)

**Configurare:**
```bash
npm install -D vitest @testing-library/react @testing-library/jest-dom jsdom
```

```javascript
// vite.config.js — adauga:
test: {
  globals: true,
  environment: 'jsdom',
  setupFiles: './src/test-setup.js',
}
```

---

### 31. Backend Tests Module Netestate

**Problema:** Module critice fara teste: AI (chat, document analysis), Translator (multi-provider), Automations (cron scheduler), Vault (encryption), File Manager.

**Solutie:** Adauga minimum 5 teste per modul pentru operatiile CRUD de baza si edge cases.

**Complexitate:** Mare | **Impact:** Categorie (Calitate)

---

### 32. Configurare Linting (Ruff + ESLint)

**Problema:** Nicio configurare de linting. Cod mort, impoturi nefolosite, inconsistente de stil nu sunt detectate automat.

**Solutie:**
- Backend: Ruff (rapid, Python, inlocuieste pylint + flake8 + isort)
- Frontend: ESLint (standard React config)

**Complexitate:** Mica | **Impact:** Categorie (Calitate)

**Configurare Ruff:**
```toml
# backend/pyproject.toml
[tool.ruff]
line-length = 120
target-version = "py313"

[tool.ruff.lint]
select = ["E", "F", "W", "I"]
ignore = ["E501"]
```

---

### 33. Database UNIQUE Constraints

**Problema:** Lipsesc constrangeri UNIQUE pe campuri business critice: `invoice_number` per serie, `cui` pe clienti, `plate_number + expiry_date` pe ITP. Duplicatele sunt prevenite doar la nivel de aplicatie, nu de baza de date.

**Solutie:** Migrare SQL care adauga UNIQUE constraints:
```sql
CREATE UNIQUE INDEX IF NOT EXISTS idx_invoices_number_series
  ON invoices(invoice_number, series_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_clients_cui
  ON clients(cui) WHERE cui IS NOT NULL AND cui != '';
```

**Complexitate:** Mica | **Impact:** Categorie (Securitate Date)

---

### 34. Bundle Size Optimization

**Problema:** Fara analiza de bundle size. Lucide-react importa toate iconele, recharts e mare (~500KB). Chunk splitting exista dar poate fi optimizat.

**Solutie:**
- Adauga `rollup-plugin-visualizer` pentru analiza
- Importa iconele individual: `import { X } from 'lucide-react'` (deja facut corect)
- Verifica tree-shaking pe recharts
- Lazy load paginile rare (Settings, Reports, Integrations)

**Complexitate:** Mica | **Impact:** Categorie (Performanta)

---

### 35. PWA Service Worker — Prompt Update Strategy

**Problema:** PWA-ul foloseste `registerType: 'autoUpdate'` implicit, ceea ce inseamna ca versiunile noi se aplica fara ca utilizatorul sa stie. [CERT] — conform best practices 2026, strategia `prompt` este recomandata pentru a preveni pierderea de date in formulare deschise.

**Solutie:** Schimba la `registerType: 'prompt'` si adauga banner "Versiune noua disponibila — Actualizeaza".

**Complexitate:** Mica | **Impact:** Categorie (Calitate)

---

### 36. API Rate Limiting Granular

**Problema:** Rate limiting actual: 60 req/min global, 10 req/min pentru AI/translator. Nu exista rate limiting per-endpoint pentru operatii costisitoare (backup, export, PDF generation).

**Solutie:** Adauga rate limiting specific pentru:
- `/api/reports/backup/*` — 2 req/min
- `/api/invoice/export-batch-pdf` — 3 req/min
- `/api/converter/*` — 5 req/min

**Complexitate:** Mica | **Impact:** Categorie (Securitate)

---

### 37. Monitorizare Dimensiune DB

**Problema:** SQLite-ul creste in timp (activity_log, chat_messages, TM entries). Nu exista avertizare daca depaseste un prag (ex: 500MB).

**Solutie:** Adauga in health check si in daily digest dimensiunea DB. Avertizare daca > 500MB.

```python
# In health check
db_size = os.path.getsize(settings.db_path)
db_size_mb = db_size / (1024 * 1024)
if db_size_mb > 500:
    warnings.append(f"DB size: {db_size_mb:.0f}MB — consider cleanup")
```

**Complexitate:** Mica | **Impact:** Categorie (Mentenanta)

---

### 38. Cleanup Automat Activity Log

**Problema:** Tabela `activity_log` creste nelimitat. Dupa luni de utilizare, poate avea zeci de mii de randuri care incetinesc query-urile si cresc dimensiunea DB.

**Solutie:** Task cron lunar care sterge intrari mai vechi de 90 zile (pastrand cele cu status "error" 180 zile).

```python
async def cleanup_old_activity_logs():
    async with get_db() as db:
        await db.execute(
            "DELETE FROM activity_log WHERE timestamp < datetime('now', '-90 days') "
            "AND status != 'error'"
        )
        await db.execute(
            "DELETE FROM activity_log WHERE timestamp < datetime('now', '-180 days')"
        )
        await db.commit()
        await db.execute("VACUUM")
```

**Complexitate:** Mica | **Impact:** Categorie (Performanta/Mentenanta)

---

# SUMAR PRIORITATI

| Prioritate | # | Nume | Complexitate | Impact | Categorie |
|---|---|---|---|---|---|
| **P0 — URGENT** | 29 | Fix Migration 017 Duplicate | Mica | Maxim | Tehnic/Securitate Date |
| **P0 — URGENT** | 5 | e-Factura XML ANAF | Mare | Maxim | Obligatie Legala |
| **P1 — IMPORTANT** | 18 | Time Tracking + Facturare | Mare | Maxim | Feature Nou |
| **P1 — IMPORTANT** | 17 | Cautare Globala Cross-Module | Medie | Maxim | Feature Nou |
| **P1 — IMPORTANT** | 3 | Sugestii TM Timp Real | Mica | Mare | Imbunatatire |
| **P1 — IMPORTANT** | 8 | ITP Notificari Expirare | Medie | Mare | Imbunatatire |
| **P1 — IMPORTANT** | 15 | Notificari Esec Task Cron | Mica | Mare | Imbunatatire |
| **P1 — IMPORTANT** | 23 | PWA Offline Enhanced | Mare | Maxim | Feature Nou |
| **P2 — VALOROS** | 1 | Dashboard Obiective Zilnice | Mica | Mare | Imbunatatire |
| **P2 — VALOROS** | 7 | Invoice Multi-Currency BNR | Mica | Mare | Imbunatatire |
| **P2 — VALOROS** | 14 | Vault Usage Dashboard | Medie | Mare | Imbunatatire |
| **P2 — VALOROS** | 19 | Floating Timer Widget | Mica | Mare | Feature Nou |
| **P2 — VALOROS** | 20 | Activity Digest Telegram | Medie | Mare | Feature Nou |
| **P2 — VALOROS** | 21 | Client Communication Log | Medie | Mare | Feature Nou |
| **P2 — VALOROS** | 25 | Quick Invoice from Calculator | Mica | Mare | Feature Nou |
| **P2 — VALOROS** | 33 | DB UNIQUE Constraints | Mica | Mare | Tehnic |
| **P3 — STRATEGIC** | 6 | Invoice Preview Live | Mica | Mediu | Imbunatatire |
| **P3 — STRATEGIC** | 9 | ITP Atasare Fotografii | Medie | Mare | Imbunatatire |
| **P3 — STRATEGIC** | 11 | Calculator Trend Preturi | Mica | Mediu | Imbunatatire |
| **P3 — STRATEGIC** | 12 | AI Chat Syntax Highlighting | Mica | Mediu | Imbunatatire |
| **P3 — STRATEGIC** | 13 | Notepad Markdown Preview | Mica | Mediu | Imbunatatire |
| **P3 — STRATEGIC** | 16 | Raport Lunar Business PDF | Mare | Mare | Imbunatatire |
| **P3 — STRATEGIC** | 22 | Document Templates Library | Medie | Mare | Feature Nou |
| **P3 — STRATEGIC** | 28 | ITP Quick Entry Mobile | Medie | Mare | Feature Nou |
| **P3 — STRATEGIC** | 30 | Frontend Tests (Vitest) | Mare | Mare | Tehnic |
| **P3 — STRATEGIC** | 31 | Backend Tests Module Noi | Mare | Mare | Tehnic |
| **P4 — NICE-TO-HAVE** | 2 | Dashboard Grafic Comparativ | Mica | Mediu | Imbunatatire |
| **P4 — NICE-TO-HAVE** | 4 | Translator Shortcuts | Mica | Mediu | Imbunatatire |
| **P4 — NICE-TO-HAVE** | 10 | File Manager Galerie | Mica | Mediu | Imbunatatire |
| **P4 — NICE-TO-HAVE** | 24 | Pagina Shortcuts Completa | Mica | Mic | Feature Nou |
| **P4 — NICE-TO-HAVE** | 26 | Dashboard Drag & Drop | Medie | Mic | Feature Nou |
| **P4 — NICE-TO-HAVE** | 27 | Invoice Duplicate Detection+ | Mica | Mare | Imbunatatire |
| **P4 — NICE-TO-HAVE** | 32 | Configurare Linting | Mica | Mediu | Tehnic |
| **P4 — NICE-TO-HAVE** | 34 | Bundle Size Optimization | Mica | Mic | Tehnic |
| **P4 — NICE-TO-HAVE** | 35 | PWA Prompt Update | Mica | Mic | Tehnic |
| **P4 — NICE-TO-HAVE** | 36 | Rate Limiting Granular | Mica | Mic | Tehnic |
| **P4 — NICE-TO-HAVE** | 37 | Monitorizare Dimensiune DB | Mica | Mic | Tehnic |
| **P4 — NICE-TO-HAVE** | 38 | Cleanup Activity Log | Mica | Mic | Tehnic |

---

## NOTE IMPLEMENTARE

1. **Constrangere buget ZERO** — Toate recomandarile folosesc exclusiv resurse gratuite (Telegram Bot API, BNR XML, Pillow, Vitest, Ruff — toate free). Nicio recomandare nu necesita abonamente noi.

2. **Constrangere single-user** — Nicio recomandare nu introduce auth multi-user. Time tracking, communication log, templates — toate sunt pentru Roland.

3. **Pattern stocare comun** — Toate noile tabele urmeaza conventia existenta: aiosqlite, migrari SQL in `migrations/`, async CRUD cu get_db(). Toate recomandarile frontend refolosesc componente existente (input-field, btn-primary, card styling).

4. **Dependinte intre recomandari:**
   - #18 (Time Tracking) depinde de schema DB noua, dar e independent de restul
   - #19 (Floating Timer) depinde de #18
   - #20 (Activity Digest) depinde de Telegram config (existent)
   - #5 (e-Factura) e independent, dar beneficiaza de #7 (multi-currency)
   - #14 (Vault Usage) depinde de endpoint-uri existente (translator/usage, ai/providers)
   - #17 (Global Search) e independent, se integreaza in CommandPalette existent

5. **Ce NU se schimba:**
   - Arhitectura modulara (modules/ auto-discovery) — ramane identica
   - Stack tehnic (FastAPI + React + SQLite) — nicio migrare
   - Sistemul de navigare (manifest.js) — doar adaugiri
   - Provider chains (AI, translator, TTS) — nicio modificare
   - Regulile .claude/rules/ — nicio modificare

6. **Ordine recomandata implementare:**
   - Sprint 1: #29 (fix migration) + #15 (notificari esec) + #3 (TM suggestions) — toate Mica complexitate
   - Sprint 2: #5 (e-Factura) + #7 (multi-currency) — legal + business
   - Sprint 3: #18 + #19 (time tracking + timer) — workflow complet
   - Sprint 4: #17 (global search) + #1 (obiective) + #20 (digest) — productivitate
   - Sprint 5: #8 (ITP notificari) + #9 (ITP foto) + #28 (ITP mobile) — teren
   - Sprint 6: #30 + #31 (teste) + #32 (linting) — calitate

---

## SURSE RESEARCH

- [e-Factura ANAF — Ghid Complet](https://up2date.ro/ghiduri/integrare-efactura-anaf-ghid-complet)
- [API e-Factura — Prezentare MFinante](https://mfinante.gov.ro/static/10/eFactura/prezentare%20api%20efactura.pdf)
- [e-Factura 2026 — Generare XML](https://factureanu.ro/blog/ghid-generare-descarcare-xml-efactura-2026)
- [Informații tehnice e-Factura](https://mfinante.gov.ro/en/web/efactura/informatii-tehnice)
- [Building Offline-First React PWA](https://dalenguyen.me/blog/2026-01-18-building-offline-first-react-app-complete-pwa-guide)
- [Vite + PWA Offline Caching 2026](https://www.enjoytoday.cn/posts/vite-pwa-guide/)
- [FastAPI SQLite Best Practices](https://medium.com/@premnathm/building-lightweight-apis-a-deep-dive-into-fastapi-and-sqlite-crud-0c9500d09ed7)
- [FastAPI Production Best Practices](https://medium.com/@kasimoluwasegun/fastapi-best-practices-for-production-apis-924676d5d134)
