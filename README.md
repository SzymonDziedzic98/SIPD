# SIPD
Spatial iterated prisoner dillema

## Wersja w Pythonie / w przeglądarce (`web/`)

- `web/sipd.py` – port `models/PD.gaml` do czystego Pythona (tylko biblioteka standardowa):
  model, eksperymenty batch (A–F, E1–E3, R0) i testy.
  - `python web/sipd.py --test`
  - `python web/sipd.py --experiment A_baseline --repeat 2 --end-cycle 2000 --geojson includes/gis/drogi.geojson`
- `web/index.html` – uruchamia `sipd.py` w przeglądarce (Pyodide): mapa, pamięć agenta, wykresy,
  batch, testy i pobieranie CSV. Otwórz przez serwer HTTP, np. `cd web && python -m http.server`,
  potem `http://localhost:8000`, albo opublikuj katalog `web/` przez GitHub Pages.

Wyniki zgadzają się z GAMA statystycznie, nie liczba w liczbę (inny generator liczb losowych).
Bez `drogi.geojson` używana jest syntetyczna sieć parkowa.
