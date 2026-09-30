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
  Interfejs jest po polsku i po angielsku: przełącznik PL/EN w nagłówku, wybór zapamiętuje przeglądarka;
  `?lang=en` albo `?lang=pl` w adresie wymusza język. Teksty angielskie są w `web/i18n.js`.
- Parki z OpenStreetMap jak w PD: „Wczytaj gotowy” bierze park z `web/parki/` (Staszica, Szczytnicki, Południowy,
  Grabiszyński, Zachodni; OSM, ODbL, pobrane 2026-09-28, już po poprawkach sieci), „Pobierz z OSM” pyta Overpass API.
  Poprawki sieci (łączenie kawałków do 50 m, ścieżek równoległych 3 m, skrzyżowań 6 m, ślepych końców 25 m) liczy
  `web/psm.py`, kopia `src/psm.py` z repozytorium PD. Plik GeoJSON w stopniach bez znacznika `psm_processed`
  (np. surowy zapis z PD) jest poprawiany przy wczytaniu, jeśli zaznaczono „Popraw sieć z OSM”; pliki w metrach
  zostają bez zmian. W pliku z warstwami (`properties.layer`) ścieżkami są tylko `roads`. Gotowe parki dają te same
  sieci co `parki_osm/po_poprawkach` (UDI, badanie 3).

Wyniki zgadzają się z GAMA statystycznie, nie liczba w liczbę (inny generator liczb losowych).
Bez `drogi.geojson` używana jest syntetyczna sieć parkowa.
