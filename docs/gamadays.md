# SIPD – rozbudowa pod GAMA Days 2026

Gałąź `feature/gamadays-compat`. Wersja pod JASSS (`48b450c`) się nie zmienia: każdy nowy
mechanizm ma przełącznik, a przy wyłączonych przełącznikach odcisk `R0_regression` musi być
identyczny z commitem bazowym `d1ea934`.

## Decyzje

| Nr | Decyzja |
|---|---|
| 1 | Baza gałęzi: `48b450c` (z poprawkami z PR #1). |
| 2 | Eksperymenty zgodności: `unlimited_games = true`. |
| 3 | Macierze: PD (T=9, R=5, P=1, S=0), słaby PD (T=1,6, R=1, P=S=0), snowdrift (T=4, R=3, S=2, P=0). |
| 4 | Przełącznik `classic_start_cooperate`; **w eksperymentach zgodności włączony**. |
| 5 | Zapominanie (Dunbar) jednostronne; pamięć miejsc nie jest zapominana. |
| 6 | GRIM po zmianie charakteru liczy historię tylko od przejęcia. |
| 7 | Imitacja Fermiego: model = losowy sąsiad w `vision_radius`; w `well_mixed` losowy agent z populacji. |
| 8 | QLEARN/AQLEARN nie ewoluują w etapach 1–3; w etapie 4 przejście do Q = nowe tablice, z Q = tablice kasowane. |
| 9 | Przyspieszenia tylko takie, które nie zmieniają wyników (leniwe mapy, sąsiedzi raz na krok, równoległe powtórzenia). |
| 10 | Przełącznik `disorder_clamp` (disorder w [0, 1]); domyślnie wyłączony. |
| 11 | Q-learning poza rdzeniem; jego ograniczenie opisane niżej. |
| 12 | P3 mierzona zyskiem oszustów (wypłata ALLD na grę, `exploitation_rate()`), nie samym udziałem kooperacji. `dunbar_limit` ∈ {0, 5, 15, 50}; 150 tylko przy N, przy którym agenci mają > 150 różnych partnerów. |

## Diagnostyka dynamiki (port Pythona, `web/diagnostics.py`)

Warunki: 200 agentów, syntetyczny park ok. 1,9 × 1,9 km (ta sama gęstość co 20 agentów na
540 × 540 m), `vision_radius` 30, 50 000 cykli (Q-learning 200 000, Dunbar 30 000), 2 seedy.
Port ma ten sam algorytm co `PD.gaml`, ale inny generator liczb losowych; wyniki są orientacyjne
i trzeba je potwierdzić w GAMA na prawdziwej sieci (`drogi.geojson`).

**Spotkania.** Agent rozgrywa ok. 1066 gier z ok. 115 różnymi partnerami; mediana gier na parę
wynosi 7 (przy `vision_radius` 10: 349 gier, 97 partnerów, mediana 2). Gra jest w małym stopniu
„iterowana”: większa populacja nie zwiększa liczby powtórzeń z tym samym partnerem.

**Q-learning per przeciwnik praktycznie się nie uczy.** Po 200 000 cyklach udział D QLEARN wobec
ALLC 0,48, wobec ALLD 0,54 (para gra średnio 23 razy). W teście kontrolnym (jeden QLEARN,
jeden przeciwnik) udział D wobec ALLC wynosi 0,48 po 30 grach, 0,49 po 300 i 0,92 po 3000.
Przy `learning_rate` 0,1 i `discount` 0,9 wartości Q nie odchodzą od prioru, więc QLEARN/AQLEARN
grają zgodnie z `initial_cooperation_bias` i `epsilon`. Dotyczy to też interpretacji wariantów A–F.

**TFT z losowym startem.** Populacja TFT ma udział D 0,49 (wzajemny odwet po losowym pierwszym D);
z `classic_start_cooperate` udział D 0,00 i wypłata 5,00 na grę.

**Rozbita szyba.** Przy `broken_windows_sensitivity` 0,4 udział D 0,99 (pełne załamanie).
Bez ograniczenia `disorder` dochodzi do ok. 800 w najczęściej odwiedzanych punktach (ok. 100
nawet bez efektu szyby); stąd `disorder_clamp`. W populacji samych ALLC efekt się nie uruchamia.

**Tryb z limitem gier.** Bez istotnego zniekształcenia częstości gier między charakterami.

**Limit Dunbara.** W 30 000 cykli agent spotyka ok. 83 różnych partnerów, więc limity 5, 15, 50
działają, 150 nie. Mieszanka 160 TFT (start od C) + 40 ALLD:

| `dunbar_limit` | zapomnień | udział D | TFT / grę | ALLD / grę |
|---|---|---|---|---|
| 0 | 0 | 0,337 | 4,20 | 1,80 |
| 50 | 7 573 | 0,341 | 4,19 | 1,86 |
| 15 | 19 084 | 0,324 | 4,19 | 2,08 |
| 5 | 26 374 | 0,326 | 4,18 | 2,33 |

Zapominanie zwiększa zysk oszustów (do +29%), a udział kooperacji prawie się nie zmienia; brak
wyraźnego progu. Stąd decyzja 12.
