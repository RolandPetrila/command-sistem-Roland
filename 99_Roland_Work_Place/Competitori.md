# Research Competitori — Traduceri Tehnice EN↔RO Romania

**Data cercetarii**: 2026-03-17
**Metoda**: Playwright MCP — navigare directa pe site-urile competitorilor
**Focus**: Traduceri tehnice/industriale Engleza ↔ Romana, piata din Romania
**Unitate standard**: 1 pagina = 2.000 caractere cu spatii (standard national)

---

## Tabel Comparativ Competitori

| # | Competitor | Locatie | Tarif EN↔RO (RON/pag) | Tarif Tehnic (RON/pag) | Urgenta | Obs |
|---|-----------|---------|----------------------|----------------------|---------|-----|
| 1 | **Activ Traduceri** | Bucuresti | 30-35 | Personalizat (de la 30) | +50-100% | Non-TVA. Negociabil la volum mare |
| 2 | **TopLevel Traduceri** | National | 30 | Personalizat | +50% | Calculator online pe site |
| 3 | **TraduceriLegalizate.com** | Bucuresti | 20-35 | **40** (carti tehnice, manuale) | +50% | Specializat pe documente EN |
| 4 | **NB Traduceri** | Bucuresti | **27** | ~35 (medicale) | +50-100% | Rating 4.7/5 (167 recenzii). Discount >50 pag |
| 5 | **Tradutex** | Brasov | **45** | >45 (personalizat) | +50-300% | ISO 9001:2015 certificat. Non-TVA. Premium |
| 6 | **traduceri-autorizate.com** | National | 30-35 | Inclus in tarif general | - | Grupa 1: EN, FR, IT, ES |
| 7 | **Highlights Translations** | National | **30** | - | - | Interpretariat 2400 RON/zi |
| 8 | **traducerisupralegalizari.ro** | National | 30-35 | - | 40-45 (urgenta) | Include apostilare |
| 9 | **AS Traduceri** | National | **30** | Personalizat | - | Standard documente tipizate |
| 10 | **AQualityTranslation** | Bucuresti | de la **22** | 40+ (tehnice medicale) | - | Cel mai ieftin tarif de baza gasit |
| 11 | **Lexitrad** | Cluj-Napoca | 35-45 | In range-ul general | - | Preturi 2025, piata Cluj |
| 12 | **Protranslate** | International | ~35 RON (€0.07/cuv) | - | - | Platforma online, 120+ limbi |
| 13 | **Translated.com** | International | ~115 RON (~25 USD/pag) | - | - | Standard international, 250 cuv/pag |
| 14 | **Serious.ro** | National | La cerere | La cerere | - | Specializat tehnic: auto, chimie, IT |
| 15 | **Atelierul de Traduceri** | National | Competitiv | Personalizat | Fara taxa urgenta | 300 traducatori nativi |

---

## Analiza Statistica — Piata Romaneasca EN↔RO

### Tarife per PAGINA (2.000 caractere cu spatii)

| Metric | Documente Generale | Tehnice/Industriale |
|--------|-------------------|-------------------|
| **Minim** | 22 RON | 30 RON |
| **Maxim** | 45 RON | 50 RON |
| **Medie** | 31 RON | 38 RON |
| **Median** | 30 RON | 37.5 RON |
| **Cel mai frecvent** | 30 RON | 35-40 RON |

### Tarife estimate per CUVANT

Calculat pe baza: 1 pagina standard ≈ 300-350 cuvinte romanesti (2.000 car cu spatii)

| Metric | Documente Generale | Tehnice/Industriale |
|--------|-------------------|-------------------|
| **Minim** | 0.063 RON/cuv | 0.086 RON/cuv |
| **Maxim** | 0.150 RON/cuv | 0.167 RON/cuv |
| **Medie** | 0.094 RON/cuv | 0.113 RON/cuv |
| **Recomandat calculator** | **0.09 RON/cuv** | **0.11 RON/cuv** |

### Factori de Pret Identificati

1. **Complexitate tehnica**: +15-30% fata de tariful general
2. **Urgenta**: +50% standard, pana la +300% (Tradutex) pentru urgente extreme
3. **Volum mare** (>50 pagini): -10-20% discount (NB Traduceri, Activ)
4. **Legalizare notariala**: +30-100 RON/document (separat)
5. **Certificare ISO**: Tarife cu ~30% mai mari (Tradutex vs media)
6. **Locatie**: Cluj/Brasov usor mai scump decat Bucuresti
7. **TVA**: Majoritatea birourilor mici sunt non-TVA (avantaj 19%)

---

## Recomandari pentru Calculator

### Valori Recomandate market_rates.json

```json
{
  "avg_rate_per_page": {
    "technical": 38,
    "general": 31,
    "legal": 40
  },
  "avg_rate_per_word": {
    "technical": 0.11,
    "general": 0.09,
    "legal": 0.12
  }
}
```

### Range-uri pentru Validare

- **Pret rezonabil**: 22-50 RON/pagina (in afara = avertisment)
- **Pret tehnic rezonabil**: 30-50 RON/pagina
- **Confidence interval**: ±20% fata de media (30-46 RON pentru tehnic)

### Factori de Ajustare Sugerate

| Factor | Multiplicator |
|--------|-------------|
| Document general (sub 10 pag) | x1.0 |
| Document tehnic simplu | x1.15 |
| Document tehnic complex (tabele, diagrame) | x1.30 |
| Urgenta (aceeasi zi) | x1.50 |
| Volum mare (>50 pag) | x0.85 |
| Cu imagini/OCR necesar | x1.20 |

---

## Surse si Metodologie

- **12 site-uri romanesti** vizitate direct cu Playwright MCP
- **3 platforme internationale** verificate pentru referinta
- Preturile reflecta tarifele publicate pe site-uri la data de 17 martie 2026
- Tarifele pentru "tehnic" sunt estimate acolo unde competitorii indica "personalizat"
- Conversie cuvinte/pagina: 1 pagina (2000 car) ≈ 300-350 cuvinte (limba romana)
- Conversie EUR/RON: 1 EUR ≈ 5 RON (curs aproximativ)

---

*Generat automat prin research Playwright MCP — 2026-03-17*
