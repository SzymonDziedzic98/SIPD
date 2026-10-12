# SIPD-D: spotkania w parkach (Urban Forestry & Urban Greening)

Dane do artykułu „When do park paths shape who meets again? Simulated repeat encounters in five urban parks”.

## Zawartość
- `networks/`: sieci ścieżek sześciu obszarów w pięciu parkach Wrocławia (OSM, przycięte do granic, wejścia na granicy, ścieżka wokół obszaru); `parki.csv` z listą obszarów; `przygotuj.py` buduje sieci z OSM. © OpenStreetMap contributors, ODbL.
- `SIPD-D_results_v4.tar.gz` (ok. 21 MB):
  - `python/dane_v4/`: wyniki przebiegów portu Pythona (`web/sipd.py`) dla wszystkich eksperymentów artykułu i suplementu; `wyniki_v4.md` = tabele artykułu; `epizody/` = Suplement S4;
  - `python/skrypty/`: skrypty uruchomień, analiz, rycin i tabel (`v4/tabele_v4.py`, `v4/epizody.py`, `build_docx.py` itd.);
  - `gama/`: te same przebiegi powtórzone w GAMA z tymi samymi seedami (`pliki_gama/`), porównanie z portem (`porownanie.md`) i analiza epizodów na plikach GAMA (`epizody_analiza.txt`) = Suplement S5.

## Odtworzenie
Skrypty czytają zmienne środowiskowe: `SIPD_WEB` (katalog `web/` tego repozytorium), `PARKI` (katalog `networks/`), `NET_SRC=podzial`, `THROUGH_SHARE=0.25`, `END=20000`, `REPS=3`. Kolejność uruchomień: `python/dane_v4/kolejka.sh`, `kolejka_bank.sh`, `analiza.sh`, `analiza2.sh`, `epizody/kolejka_epizody.sh`; ścieżki bezwzględne w tych plikach trzeba dopasować do własnego katalogu.
