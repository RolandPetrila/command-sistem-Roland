# GHID TESTARE — Roland Command Center

**Ultima actualizare:** 2026-03-18
**Scop:** Instrucțiuni de testare pas-cu-pas pentru fiecare funcționalitate implementată.
**Web:** `http://localhost:8000` | **Android:** `https://desktop-cjuecmn.tail7bc485.ts.net:8000`

---

## Legendă Status
- ✅ Testat OK — funcționează confirmat
- 🧪 Netestat — implementat, necesită testare
- ❌ Bug cunoscut — nu funcționează, necesită fix
- 🔧 Bug fixat, re-test — a fost un bug, rezolvat, necesită re-verificare

---

## Wave 0 — Fundație

### Module Auto-Discovery
| | Detalii |
|---|---|
| **Funcția** | Backend descoperă automat module din `backend/modules/` |
| **Test Web** | 1. Deschide `http://localhost:8000/docs` → verifică că vezi endpoint-uri `/api/calc/`, `/api/converter/`, `/api/fm/`, `/api/vault/` |
| **Test Telefon** | 1. Deschide `https://desktop-cjuecmn.tail7bc485.ts.net:8000/docs` → aceleași endpoint-uri vizibile |
| **Rezultat așteptat** | Toate modulele apar în Swagger fără restart manual |
| **Status** | ✅ Testat local OK |

### Sidebar Dinamic cu Categorii
| | Detalii |
|---|---|
| **Funcția** | Sidebar-ul afișează categorii colapsibile (Traduceri, Instrumente, Sistem) |
| **Test Web** | 1. Deschide app → sidebar stânga → click pe categorii → se deschid/închid |
| **Test Telefon** | 1. Deschide app → hamburger menu (☰) → sidebar apare → categorii funcționează |
| **Rezultat așteptat** | Categorii se colapsează/expandează; toate paginile sunt accesibile |
| **Status** | ✅ Testat local OK |

### URL-uri Dinamice (fix hardcoded)
| | Detalii |
|---|---|
| **Funcția** | API-ul folosește `window.location.origin` în loc de `localhost:8000` |
| **Test Web** | 1. Deschide orice pagină → verifică în DevTools Network că request-urile merg la URL-ul corect |
| **Test Telefon** | 1. Deschide de pe Android → navighez prin app → toate paginile încarcă date |
| **Rezultat așteptat** | Funcționează identic pe localhost și pe Tailscale |
| **Status** | ✅ Testat local OK |

### DB Migrations
| | Detalii |
|---|---|
| **Funcția** | SQLite schema se actualizează automat la pornirea backend-ului |
| **Test Web** | 1. Pornește backend → în terminal vezi `[DB] Migrated to version X` (fără erori) |
| **Test Telefon** | N/A — este un proces backend |
| **Rezultat așteptat** | Backend pornește fără erori de DB |
| **Status** | ✅ Testat local OK |

### Activity Log SQLite
| | Detalii |
|---|---|
| **Funcția** | Toate acțiunile sunt loguite în SQLite (nu JSON) |
| **Test Web** | 1. Deschide Panou Principal → secțiunea "Activitate Recentă" arată ultimele acțiuni |
| **Test Telefon** | 1. Aceeași verificare de pe telefon |
| **Rezultat așteptat** | Acțiunile recente apar cu timestamp, tip, și detalii |
| **Status** | ✅ Testat local OK |

---

## Wave 1 — Deploy + Acces

### Tailscale + HTTPS
| | Detalii |
|---|---|
| **Funcția** | App accesibilă de pe orice device din rețeaua Tailscale via HTTPS |
| **Test Web** | 1. Accesează `https://desktop-cjuecmn.tail7bc485.ts.net:8000` din browser PC |
| **Test Telefon** | 1. Conectează-te la Tailscale pe Android → deschide URL-ul de mai sus în Chrome |
| **Rezultat așteptat** | Pagina se încarcă cu certificat TLS valid (lacăt verde) |
| **Status** | ✅ Testat Android OK |

### PWA (Progressive Web App)
| | Detalii |
|---|---|
| **Funcția** | App se poate instala ca aplicație pe Android |
| **Test Web** | 1. Deschide în Chrome → apare banner "Add to Home Screen" sau din menu "Install app" |
| **Test Telefon** | 1. Deschide în Chrome Android → menu (⋮) → "Add to Home screen" → confirmă → icon apare pe home |
| **Rezultat așteptat** | App se deschide ca aplicație standalone (fără bara Chrome) |
| **Status** | ✅ Testat Android OK |

### API Key Vault
| | Detalii |
|---|---|
| **Funcția** | Stocarea securizată a cheilor API cu master password |
| **Test Web** | 1. Sidebar → Sistem → API Key Vault → setează master password → adaugă o cheie test → verifică că apare criptat |
| **Test Telefon** | 1. Aceeași procedură de pe telefon |
| **Rezultat așteptat** | Cheia se salvează, se afișează mascat (****), se poate dezvălui cu master password |
| **Status** | 🧪 Netestat Android |

---

## Wave 2 (parțial) — Quick Tools

### Command Palette (Ctrl+K)
| | Detalii |
|---|---|
| **Funcția** | Navigare rapidă prin toate paginile cu fuzzy search |
| **Test Web** | 1. Apasă `Ctrl+K` → scrie "conv" → apare "Convertor Fișiere" → Enter → navighează |
| **Test Telefon** | 1. Pe telefon nu e Ctrl+K; accesează prin sidebar |
| **Rezultat așteptat** | Dialog apare, căutarea găsește pagini, selectarea navighează |
| **Status** | ✅ Testat local OK |

### QR Generator
| | Detalii |
|---|---|
| **Funcția** | Generează cod QR din text/URL |
| **Test Web** | 1. Sidebar → Instrumente → QR Generator → scrie un text → QR apare live → click "Descarcă PNG" |
| **Test Telefon** | 1. Aceeași procedură → descarcă PNG → verifică în galerie |
| **Rezultat așteptat** | QR se generează instant, descărcarea funcționează |
| **Status** | 🧪 Netestat Android |

### Notepad
| | Detalii |
|---|---|
| **Funcția** | Note rapide cu salvare automată |
| **Test Web** | 1. Sidebar → Instrumente → Notepad → creează notă nouă → scrie text → aștepți 1s → reîncarcă pagina → nota e salvată |
| **Test Telefon** | 1. Aceeași procedură de pe telefon |
| **Rezultat așteptat** | Nota se salvează automat (debounce 800ms), persistă între sesiuni |
| **Status** | 🧪 Netestat Android |

---

## Faza 12 — Convertor Fișiere (10 funcții)

### 12.1 PDF → DOCX
| | Detalii |
|---|---|
| **Funcția** | Convertește un fișier PDF în format DOCX editabil |
| **Test Web** | 1. Sidebar → Convertor Fișiere → selectează "PDF → DOCX" → încarcă un PDF → click "Convertește" → se descarcă .docx |
| **Test Telefon** | 1. Aceeași procedură → selectează PDF din telefon → descarcă DOCX |
| **Rezultat așteptat** | Fișierul DOCX se descarcă, conține textul din PDF |
| **Status** | 🧪 Netestat Android |

### 12.2 DOCX → PDF
| | Detalii |
|---|---|
| **Funcția** | Convertește DOCX în PDF (folosește Microsoft Word pe Windows) |
| **Test Web** | 1. Convertor → "DOCX → PDF" → încarcă .docx → convertește → se descarcă .pdf |
| **Test Telefon** | 1. Selectează DOCX din Google Drive pe telefon → convertește → descarcă PDF |
| **Rezultat așteptat** | PDF-ul se descarcă cu formatarea păstrată |
| **Status** | 🔧 Bug fixat (Android octet-stream), re-test necesar |

### 12.3 Imagine → Text (OCR)
| | Detalii |
|---|---|
| **Funcția** | Extrage text din imagini (necesită Tesseract instalat) |
| **Test Web** | 1. Convertor → "Extrage Text" → încarcă o imagine cu text → rezultat text apare / se descarcă |
| **Test Telefon** | 1. Fotografiază un document → încarcă poza → extrage text |
| **Rezultat așteptat** | Textul din imagine este extras (calitate depinde de imagine) |
| **Status** | 🧪 Netestat Android |

### 12.4 CSV/Excel → JSON
| | Detalii |
|---|---|
| **Funcția** | Convertește fișiere CSV sau Excel în format JSON |
| **Test Web** | 1. Convertor → "CSV/Excel → JSON" → încarcă .csv sau .xlsx → descarcă JSON |
| **Test Telefon** | 1. Aceeași procedură de pe telefon |
| **Rezultat așteptat** | JSON valid cu datele din tabel |
| **Status** | ✅ Testat local OK |

### 12.5 Compresie ZIP
| | Detalii |
|---|---|
| **Funcția** | Comprimă mai multe fișiere într-un singur ZIP |
| **Test Web** | 1. Convertor → "ZIP" → selectează 2-3 fișiere → click "Comprimă" → descarcă .zip |
| **Test Telefon** | 1. Selectează fișiere din telefon → comprimă → descarcă ZIP |
| **Rezultat așteptat** | Arhiva ZIP se descarcă, conține fișierele selectate |
| **Status** | ✅ Testat local OK |

### 12.6 Redimensionare Imagini
| | Detalii |
|---|---|
| **Funcția** | Redimensionează imagini la dimensiune specificată |
| **Test Web** | 1. Convertor → "Redimensionare" → încarcă imagine → setează dimensiune → descarcă imaginea redimensionată |
| **Test Telefon** | 1. Selectează poză din galerie → redimensionează → descarcă |
| **Rezultat așteptat** | Imaginea descărcată are dimensiunea specificată |
| **Status** | ✅ Testat Android OK |

### 12.7 Merge PDF-uri
| | Detalii |
|---|---|
| **Funcția** | Combină mai multe PDF-uri într-un singur fișier |
| **Test Web** | 1. Convertor → "Merge PDF" → selectează 2+ PDF-uri → descarcă PDF combinat |
| **Test Telefon** | 1. Selectează PDF-uri din telefon → merge → descarcă |
| **Rezultat așteptat** | Un singur PDF cu toate paginile din fișierele selectate |
| **Status** | 🧪 Netestat Android |

### 12.8 Split PDF
| | Detalii |
|---|---|
| **Funcția** | Împarte un PDF în pagini individuale (descarcă ZIP cu pagini separate) |
| **Test Web** | 1. Convertor → "Split PDF" → încarcă PDF cu 3+ pagini → descarcă ZIP cu pagini separate |
| **Test Telefon** | 1. Aceeași procedură de pe telefon |
| **Rezultat așteptat** | ZIP cu câte un PDF per pagină |
| **Status** | 🧪 Netestat Android |

### 12.9 Compresie Imagini
| | Detalii |
|---|---|
| **Funcția** | Comprimă imagini (reduce dimensiunea fișierului cu pierdere minimă de calitate) |
| **Test Web** | 1. Convertor → "Compresie Imagini" → încarcă imagine → setează calitate → descarcă compresia |
| **Test Telefon** | 1. Selectează imagine din galerie → comprimă → verifică dimensiunea |
| **Rezultat așteptat** | Imaginea compresată e mai mică decât originalul |
| **Status** | 🧪 Netestat Android |

---

## Faza 14 — Manager Fișiere Avansat (5 funcții implementate)

### 14.1 File Browser cu Preview
| | Detalii |
|---|---|
| **Funcția** | Navighează prin fișierele proiectului cu preview inline (PDF, imagini, text/cod) |
| **Test Web** | 1. Sidebar → Sistem → Browser Fișiere → vezi lista de directoare → click pe `backend/` → vezi subdirectoare și fișiere → click pe un fișier `.py` → preview apare în dreapta |
| **Test Telefon** | 1. Aceeași navigare de pe telefon → preview apare sub lista de fișiere |
| **Rezultat așteptat** | Directoarele se deschid, fișierele au icoane corecte, preview-ul arată conținutul |
| **Status** | 🧪 Netestat Android |

### 14.2 Operații CRUD Fișiere
| | Detalii |
|---|---|
| **Funcția** | Redenumire, mutare, ștergere fișiere/directoare din browser |
| **Test Web** | 1. Browser Fișiere → navighează la un fișier test → click buton "Rename" (✏️) → scrie un nume nou → confirmă → fișierul are noul nume. 2. Click buton "Delete" (🗑️) → confirmă → fișierul dispare |
| **Test Telefon** | 1. Aceeași procedură pe telefon — butoanele de acțiune sunt vizibile pe fiecare rând |
| **Rezultat așteptat** | Rename schimbă numele, Delete elimină fișierul/directorul |
| **Status** | 🧪 Netestat Android |

### 14.3 Upload Fișiere
| | Detalii |
|---|---|
| **Funcția** | Încarcă fișiere prin drag & drop sau click pe buton |
| **Test Web** | 1. Browser Fișiere → navighează la un director → click "Upload" (⬆️) → selectează fișier(e) → fișierele apar în listă. 2. Alternativ: drag & drop un fișier pe pagină |
| **Test Telefon** | 1. Click "Upload" → selectează fișier din telefon (galerie/fișiere) → fișierul apare în listă |
| **Rezultat așteptat** | Fișierele se încarcă, apar în lista de fișiere cu dimensiunea corectă |
| **Status** | 🧪 Netestat Android |

### 14.4 Download Fișiere
| | Detalii |
|---|---|
| **Funcția** | Descarcă orice fișier pe device-ul local |
| **Test Web** | 1. Browser Fișiere → navighează la un fișier → click buton "Download" (⬇️) → fișierul se descarcă |
| **Test Telefon** | 1. Click "Download" → fișierul se salvează în Downloads pe telefon |
| **Rezultat așteptat** | Fișierul se descarcă cu numele și conținutul corect |
| **Status** | 🧪 Netestat Android |

### 14.8 Duplicate Finder
| | Detalii |
|---|---|
| **Funcția** | Găsește fișiere duplicate (identice ca conținut) și calculează spațiul pierdut |
| **Test Web** | 1. Browser Fișiere → click buton "Duplicates" (🔍) → scanare pornește → rezultate arată grupuri de fișiere identice cu hash MD5 → afișează spațiu total pierdut |
| **Test Telefon** | 1. Aceeași procedură de pe telefon |
| **Rezultat așteptat** | Lista grupurilor de duplicate cu dimensiune, număr, și posibilitate de ștergere |
| **Status** | 🧪 Netestat Android |

---

## Contoare Testare

| Fază | Total funcții | Testat Local | Testat Android | Netestat |
|------|--------------|-------------|----------------|----------|
| Wave 0 | 5 | 5 | 0 | 0 |
| Wave 1 | 3 | 1 | 2 | 1 |
| Wave 2 | 3 | 1 | 0 | 2 |
| Faza 12 | 9 | 3 | 1 | 5 |
| Faza 14 | 5 | 5 | 0 | 5 |
| **TOTAL** | **25** | **15** | **3** | **13** |
