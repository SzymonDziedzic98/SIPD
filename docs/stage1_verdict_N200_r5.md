# Etap 1 – werdykty (port Pythona)

Źródło: `compat_results_N200_r5.csv`, 180 przebiegów. Wartości: średnia ± odchylenie standardowe między powtórzeniami.

## P1 – oszuści stabilni w (0, 1), P2 – altruiści

| układ | macierz | N | mutacja | n | ALLD | udział D | ALLC | stabilizacja | P1 | P2 (część) |
|---|---|---|---|---|---|---|---|---|---|---|
| przestrzeń | PD_classic | 200 | 0 | 5 | 1.00 ± 0.00 | 1.00 ± 0.00 | 0.000 ± 0.000 | 100% | nie | wymiera: tak |
| przestrzeń | PD_classic | 200 | 0.01 | 5 | 0.91 ± 0.02 | 0.97 ± 0.01 | 0.011 ± 0.005 | 0% | nie | utrzymuje się: tak |
| przestrzeń | snowdrift | 200 | 0 | 5 | 0.92 ± 0.03 | 0.97 ± 0.01 | 0.000 ± 0.000 | 0% | nie | wymiera: tak |
| przestrzeń | snowdrift | 200 | 0.01 | 5 | 0.60 ± 0.09 | 0.78 ± 0.08 | 0.034 ± 0.015 | 0% | nie | utrzymuje się: tak |
| przestrzeń | weak_PD | 200 | 0 | 5 | 1.00 ± 0.01 | 1.00 ± 0.00 | 0.000 ± 0.000 | 80% | nie | wymiera: tak |
| przestrzeń | weak_PD | 200 | 0.01 | 5 | 0.79 ± 0.03 | 0.93 ± 0.02 | 0.015 ± 0.005 | 0% | nie | utrzymuje się: tak |
| well_mixed | PD_classic | 200 | 0 | 5 | 0.39 ± 0.54 | 0.41 ± 0.54 | 0.000 ± 0.000 | 20% | nie | wymiera: tak |
| well_mixed | PD_classic | 200 | 0.01 | 5 | 0.67 ± 0.27 | 0.88 ± 0.20 | 0.016 ± 0.031 | 0% | nie | utrzymuje się: tak |
| well_mixed | snowdrift | 200 | 0 | 5 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.263 ± 0.327 | 0% | nie | wymiera: warunkowo |
| well_mixed | snowdrift | 200 | 0.01 | 5 | 0.19 ± 0.17 | 0.20 ± 0.18 | 0.458 ± 0.263 | 0% | nie | utrzymuje się: warunkowo |
| well_mixed | weak_PD | 200 | 0 | 5 | 0.35 ± 0.48 | 0.38 ± 0.52 | 0.067 ± 0.149 | 20% | nie | wymiera: tak |
| well_mixed | weak_PD | 200 | 0.01 | 5 | 0.48 ± 0.28 | 0.60 ± 0.32 | 0.046 ± 0.059 | 0% | nie | utrzymuje się: tak |

**P2 łącznie** (obie części muszą się utrzymać):

- przestrzeń, PD_classic, N=200: **tak**
- przestrzeń, snowdrift, N=200: **tak**
- przestrzeń, weak_PD, N=200: **tak**
- well_mixed, PD_classic, N=200: **tak**
- well_mixed, snowdrift, N=200: **warunkowo**
- well_mixed, weak_PD, N=200: **tak**

## P3 – limit Dunbara: zysk oszustów

| układ | macierz | N | limit | n | różnych partnerów | limit działa | ALLD / grę | zysk vs brak limitu (95% CI) | TFT / grę | udział D |
|---|---|---|---|---|---|---|---|---|---|---|
| przestrzeń | PD_classic | 200 | 0 | 5 | 59.5 ± 0.8 | — | 1.844 ± 0.012 | — | 4.181 ± 0.036 | 0.328 ± 0.016 |
| przestrzeń | PD_classic | 200 | 5 | 5 | 59.5 ± 0.8 | 100% | 2.258 ± 0.013 | +0.414 [+0.398, +0.429] | 4.168 ± 0.036 | 0.314 ± 0.016 |
| przestrzeń | PD_classic | 200 | 15 | 5 | 59.5 ± 0.8 | 100% | 2.015 ± 0.014 | +0.170 [+0.154, +0.186] | 4.176 ± 0.036 | 0.320 ± 0.016 |
| przestrzeń | PD_classic | 200 | 50 | 5 | 59.5 ± 0.8 | 82% | 1.854 ± 0.014 | +0.009 [-0.007, +0.026] | 4.181 ± 0.036 | 0.327 ± 0.016 |
| przestrzeń | snowdrift | 200 | 0 | 5 | 59.5 ± 0.8 | — | 0.422 ± 0.006 | — | 2.458 ± 0.024 | 0.328 ± 0.016 |
| przestrzeń | snowdrift | 200 | 5 | 5 | 59.5 ± 0.8 | 100% | 0.629 ± 0.006 | +0.207 [+0.199, +0.214] | 2.484 ± 0.024 | 0.314 ± 0.016 |
| przestrzeń | snowdrift | 200 | 15 | 5 | 59.5 ± 0.8 | 100% | 0.507 ± 0.007 | +0.085 [+0.077, +0.093] | 2.469 ± 0.024 | 0.320 ± 0.016 |
| przestrzeń | snowdrift | 200 | 50 | 5 | 59.5 ± 0.8 | 82% | 0.427 ± 0.007 | +0.005 [-0.003, +0.013] | 2.459 ± 0.024 | 0.327 ± 0.016 |
| przestrzeń | weak_PD | 200 | 0 | 5 | 59.5 ± 0.8 | — | 0.169 ± 0.002 | — | 0.802 ± 0.009 | 0.328 ± 0.016 |
| przestrzeń | weak_PD | 200 | 5 | 5 | 59.5 ± 0.8 | 100% | 0.252 ± 0.003 | +0.083 [+0.080, +0.086] | 0.802 ± 0.009 | 0.314 ± 0.016 |
| przestrzeń | weak_PD | 200 | 15 | 5 | 59.5 ± 0.8 | 100% | 0.203 ± 0.003 | +0.034 [+0.031, +0.037] | 0.802 ± 0.009 | 0.320 ± 0.016 |
| przestrzeń | weak_PD | 200 | 50 | 5 | 59.5 ± 0.8 | 82% | 0.171 ± 0.003 | +0.002 [-0.001, +0.005] | 0.802 ± 0.009 | 0.327 ± 0.016 |
| well_mixed | PD_classic | 200 | 0 | 5 | 199.0 ± 0.0 | — | 1.035 ± 0.000 | — | 4.195 ± 0.000 | 0.361 ± 0.001 |
| well_mixed | PD_classic | 200 | 5 | 5 | 199.0 ± 0.0 | 100% | 7.433 ± 0.003 | +6.398 [+6.395, +6.400] | 3.995 ± 0.001 | 0.200 ± 0.001 |
| well_mixed | PD_classic | 200 | 15 | 5 | 199.0 ± 0.0 | 100% | 7.420 ± 0.003 | +6.385 [+6.382, +6.388] | 3.995 ± 0.001 | 0.200 ± 0.001 |
| well_mixed | PD_classic | 200 | 50 | 5 | 199.0 ± 0.0 | 100% | 6.272 ± 0.002 | +5.237 [+5.235, +5.239] | 4.031 ± 0.001 | 0.229 ± 0.001 |
| well_mixed | snowdrift | 200 | 0 | 5 | 199.0 ± 0.0 | — | 0.017 ± 0.000 | — | 2.399 ± 0.000 | 0.361 ± 0.001 |
| well_mixed | snowdrift | 200 | 5 | 5 | 199.0 ± 0.0 | 100% | 3.216 ± 0.001 | +3.199 [+3.198, +3.200] | 2.799 ± 0.000 | 0.200 ± 0.001 |
| well_mixed | snowdrift | 200 | 15 | 5 | 199.0 ± 0.0 | 100% | 3.210 ± 0.002 | +3.193 [+3.191, +3.194] | 2.798 ± 0.000 | 0.200 ± 0.001 |
| well_mixed | snowdrift | 200 | 50 | 5 | 199.0 ± 0.0 | 100% | 2.636 ± 0.001 | +2.619 [+2.617, +2.620] | 2.726 ± 0.000 | 0.229 ± 0.001 |
| well_mixed | weak_PD | 200 | 0 | 5 | 199.0 ± 0.0 | — | 0.007 ± 0.000 | — | 0.799 ± 0.000 | 0.361 ± 0.001 |
| well_mixed | weak_PD | 200 | 5 | 5 | 199.0 ± 0.0 | 100% | 1.287 ± 0.001 | +1.280 [+1.279, +1.280] | 0.799 ± 0.000 | 0.200 ± 0.001 |
| well_mixed | weak_PD | 200 | 15 | 5 | 199.0 ± 0.0 | 100% | 1.284 ± 0.001 | +1.277 [+1.276, +1.278] | 0.799 ± 0.000 | 0.200 ± 0.001 |
| well_mixed | weak_PD | 200 | 50 | 5 | 199.0 ± 0.0 | 100% | 1.054 ± 0.000 | +1.047 [+1.047, +1.048] | 0.799 ± 0.000 | 0.229 ± 0.001 |

**P3 łącznie:**

- przestrzeń, PD_classic, N=200: **tak** (próg: limit ≤ 15)
- przestrzeń, snowdrift, N=200: **tak** (próg: limit ≤ 15)
- przestrzeń, weak_PD, N=200: **tak** (próg: limit ≤ 15)
- well_mixed, PD_classic, N=200: **tak** (próg: limit ≤ 50)
- well_mixed, snowdrift, N=200: **tak** (próg: limit ≤ 50)
- well_mixed, weak_PD, N=200: **tak** (próg: limit ≤ 50)

## Warunki i zastrzeżenia

- Port Pythona (`web/stage1.py`), N = 200, 5 powtórzeń (seedy stałe, jak w `S1_*` w PD.gaml),
  20 000 cykli, wygrzewanie 5000, okno 1000, ε = 0,01, K = 5, `vision_radius` 30, park syntetyczny
  skalowany z N (siatka 32 × 32). Pełny plan (N = 500, 15 powtórzeń) i przebiegi w GAMA – do zrobienia.
- W P3 bez ewolucji ruchy nie zależą od macierzy wypłat (te same seedy → ten sam udział D), więc trzy
  macierze różnią się tylko skalą wypłat; nie są niezależnymi potwierdzeniami.
