# /rebuild — Rebuild frontend productie + verificare

Rebuild rapid al frontend-ului pentru productie (dist/ servit de FastAPI).

1. `cd frontend && npm run build` — build Vite + PWA
2. Verifica dimensiunea `dist/` si numarul de fisiere
3. Verifica ca PWA `sw.js` s-a generat
4. Raporteaza: "Build OK: X fisiere, Y KB, PWA: DA/NU"
5. Daca build esueaza — afiseaza eroarea si propune fix
