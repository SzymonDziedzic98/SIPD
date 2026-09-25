# Etap 1 – werdykty (port Pythona)

Źródło: `compat_results_P12_N200_r5_100k.csv`, 120 przebiegów. Wartości: średnia ± odchylenie standardowe między powtórzeniami.

## P1 – oszuści stabilni w (0, 1), P2 – altruiści

| układ | macierz | N | prędkość | mutacja | n | gier/partnera | ALLD | udział D | ALLC | trend ALLD /10k | stabilizacja | P1 | P2 (część) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| przestrzeń | PD_classic | 200 | 0.1 | 0 | 5 | 96.5 ± 3.1 | 1.00 ± 0.00 | 1.00 ± 0.00 | 0.000 ± 0.000 | 0.001 ± 0.001 | 100% | nie | wymiera: tak |
| przestrzeń | PD_classic | 200 | 0.1 | 0.01 | 5 | 96.8 ± 4.5 | 0.62 ± 0.04 | 0.82 ± 0.03 | 0.037 ± 0.019 | -0.008 ± 0.008 | 100% | tak | utrzymuje się: tak |
| przestrzeń | PD_classic | 200 | 0.5 | 0 | 5 | 27.7 ± 0.5 | 1.00 ± 0.00 | 1.00 ± 0.00 | 0.000 ± 0.000 | 0.000 ± 0.000 | 100% | nie | wymiera: tak |
| przestrzeń | PD_classic | 200 | 0.5 | 0.01 | 5 | 27.8 ± 0.2 | 0.85 ± 0.04 | 0.97 ± 0.01 | 0.012 ± 0.009 | -0.003 ± 0.005 | 100% | nie | utrzymuje się: tak |
| przestrzeń | PD_classic | 200 | 2 | 0 | 5 | 14.1 ± 0.1 | 1.00 ± 0.00 | 1.00 ± 0.00 | 0.000 ± 0.000 | 0.000 ± 0.000 | 100% | nie | wymiera: tak |
| przestrzeń | PD_classic | 200 | 2 | 0.01 | 5 | 14.1 ± 0.1 | 0.79 ± 0.02 | 0.96 ± 0.01 | 0.011 ± 0.003 | -0.017 ± 0.012 | 60% | nie | utrzymuje się: tak |
| przestrzeń | snowdrift | 200 | 0.1 | 0 | 5 | 96.3 ± 1.6 | 0.99 ± 0.02 | 1.00 ± 0.00 | 0.000 ± 0.000 | 0.027 ± 0.016 | 60% | nie | wymiera: tak |
| przestrzeń | snowdrift | 200 | 0.1 | 0.01 | 5 | 95.5 ± 3.3 | 0.37 ± 0.07 | 0.58 ± 0.12 | 0.050 ± 0.011 | -0.023 ± 0.012 | 60% | warunkowo | utrzymuje się: tak |
| przestrzeń | snowdrift | 200 | 0.5 | 0 | 5 | 27.8 ± 0.8 | 1.00 ± 0.00 | 1.00 ± 0.00 | 0.000 ± 0.000 | 0.000 ± 0.000 | 100% | nie | wymiera: tak |
| przestrzeń | snowdrift | 200 | 0.5 | 0.01 | 5 | 27.8 ± 0.8 | 0.67 ± 0.06 | 0.84 ± 0.06 | 0.021 ± 0.006 | 0.004 ± 0.016 | 80% | tak | utrzymuje się: tak |
| przestrzeń | snowdrift | 200 | 2 | 0 | 5 | 14.1 ± 0.1 | 1.00 ± 0.00 | 1.00 ± 0.00 | 0.000 ± 0.000 | 0.002 ± 0.003 | 100% | nie | wymiera: tak |
| przestrzeń | snowdrift | 200 | 2 | 0.01 | 5 | 14.1 ± 0.1 | 0.48 ± 0.08 | 0.77 ± 0.06 | 0.050 ± 0.007 | -0.022 ± 0.044 | 40% | warunkowo | utrzymuje się: tak |
| przestrzeń | weak_PD | 200 | 0.1 | 0 | 5 | 95.3 ± 1.7 | 1.00 ± 0.00 | 1.00 ± 0.00 | 0.000 ± 0.000 | 0.013 ± 0.006 | 80% | nie | wymiera: tak |
| przestrzeń | weak_PD | 200 | 0.1 | 0.01 | 5 | 97.1 ± 3.5 | 0.43 ± 0.04 | 0.64 ± 0.09 | 0.070 ± 0.014 | -0.003 ± 0.019 | 80% | tak | utrzymuje się: tak |
| przestrzeń | weak_PD | 200 | 0.5 | 0 | 5 | 28.0 ± 0.5 | 1.00 ± 0.00 | 1.00 ± 0.00 | 0.000 ± 0.000 | 0.000 ± 0.000 | 100% | nie | wymiera: tak |
| przestrzeń | weak_PD | 200 | 0.5 | 0.01 | 5 | 27.5 ± 0.5 | 0.71 ± 0.05 | 0.91 ± 0.03 | 0.020 ± 0.009 | -0.011 ± 0.021 | 40% | warunkowo | utrzymuje się: tak |
| przestrzeń | weak_PD | 200 | 2 | 0 | 5 | 14.1 ± 0.1 | 1.00 ± 0.00 | 1.00 ± 0.00 | 0.000 ± 0.000 | 0.000 ± 0.000 | 100% | nie | wymiera: tak |
| przestrzeń | weak_PD | 200 | 2 | 0.01 | 5 | 14.1 ± 0.1 | 0.64 ± 0.08 | 0.90 ± 0.05 | 0.013 ± 0.004 | -0.023 ± 0.030 | 80% | warunkowo | utrzymuje się: tak |
| well_mixed | PD_classic | 200 | 2 | 0 | 5 | 919.5 ± 0.1 | 0.40 ± 0.55 | 0.40 ± 0.55 | 0.000 ± 0.000 | 0.000 ± 0.000 | 100% | nie | wymiera: tak |
| well_mixed | PD_classic | 200 | 2 | 0.01 | 5 | 919.6 ± 0.1 | 0.66 ± 0.38 | 0.79 ± 0.43 | 0.008 ± 0.013 | -0.032 ± 0.027 | 20% | nie | utrzymuje się: tak |
| well_mixed | snowdrift | 200 | 2 | 0 | 5 | 919.5 ± 0.0 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.511 ± 0.501 | 0.000 ± 0.000 | 100% | nie | wymiera: warunkowo |
| well_mixed | snowdrift | 200 | 2 | 0.01 | 5 | 919.6 ± 0.1 | 0.33 ± 0.01 | 0.34 ± 0.01 | 0.642 ± 0.009 | 0.000 ± 0.002 | 100% | tak | utrzymuje się: warunkowo |
| well_mixed | weak_PD | 200 | 2 | 0 | 5 | 919.5 ± 0.0 | 0.20 ± 0.45 | 0.39 ± 0.53 | 0.000 ± 0.000 | 0.000 ± 0.000 | 100% | nie | wymiera: tak |
| well_mixed | weak_PD | 200 | 2 | 0.01 | 5 | 919.6 ± 0.0 | 0.37 ± 0.25 | 0.57 ± 0.25 | 0.024 ± 0.013 | -0.041 ± 0.051 | 0% | nie | utrzymuje się: tak |

**P2 łącznie** (obie części muszą się utrzymać):

- przestrzeń, PD_classic, N=200, prędkość 0.1: **tak**
- przestrzeń, PD_classic, N=200, prędkość 0.5: **tak**
- przestrzeń, PD_classic, N=200, prędkość 2: **tak**
- przestrzeń, snowdrift, N=200, prędkość 0.1: **tak**
- przestrzeń, snowdrift, N=200, prędkość 0.5: **tak**
- przestrzeń, snowdrift, N=200, prędkość 2: **tak**
- przestrzeń, weak_PD, N=200, prędkość 0.1: **tak**
- przestrzeń, weak_PD, N=200, prędkość 0.5: **tak**
- przestrzeń, weak_PD, N=200, prędkość 2: **tak**
- well_mixed, PD_classic, N=200, prędkość 2: **tak**
- well_mixed, snowdrift, N=200, prędkość 2: **warunkowo**
- well_mixed, weak_PD, N=200, prędkość 2: **tak**

## Interpretacja

- **Bez mutacji** każda populacja w przestrzeni kończy fiksacją ALLD (w `well_mixed` fiksacją ALLD albo
  jej brakiem). W skończonej populacji bez mutacji fiksacja jest stanem pochłaniającym, więc P1 ma sens
  tylko przy `mutation_rate` > 0.
- **Z mutacją 0,01** P1 zależy od mobilności (liczby gier na partnera):
  - prędkość 0,1 (ok. 96 gier/partnera): PD **tak** (ALLD 0,62), słaby PD **tak** (0,43),
    snowdrift **warunkowo** (0,37; 60% przebiegów bez trendu);
  - prędkość 0,5 (ok. 28): PD **nie** (udział D 0,97), słaby PD warunkowo, snowdrift **tak** (0,67);
  - prędkość 2 (ok. 14): PD **nie** (udział D 0,96), słaby PD i snowdrift warunkowo;
  - `well_mixed`: snowdrift **tak** (0,33), PD i słaby PD **nie** (wynik dwubiegunowy).
- **P2** utrzymuje się we wszystkich układach przestrzennych; w `well_mixed` przy snowdrifcie ALLC
  dominuje (0,64) zamiast wymierać – zgodne z teorią gry snowdrift (współistnienie C i D).

Warunki: port Pythona, N = 200, 5 powtórzeń, 100 000 cykli, park syntetyczny skalowany z N.
