# Pełny przegląd N = 500 – werdykty (port Pythona, 1620 przebiegów, 15 powtórzeń)

`PM9_full_N500` (zamrożony kod `98a762f`): N = 500, ewolucja (Fermi), 100 000 cykli, macierze {PD, słaby PD,
snowdrift} × sieci {baseline, fragmented, connected} × prędkość {0,1; 2} × limit Dunbara {0, 5, 15} ×
mutacja {0; 0,01}; 108 kombinacji po 15 powtórzeń. Kryteria jak w `pairs_verdict_N200_r10.md`
(P3 = wzrost udziału ALLD przy limicie, 95% CI). Port ma inny generator liczb losowych niż GAMA –
wyniki do potwierdzenia w GAMA (`PM9_full_N500` jest w `PD.gaml`).

## Wnioski

1. **Mobilność dzieli wyniki na dwa reżimy, a w obrębie reżimu część zestawień jest stała:**
   - **P1+P2 (bez limitu) przy prędkości 0,1 – „tak” we wszystkich 9 kolumnach** (3 sieci × 3 macierze).
     Przy prędkości 2 zależy od macierzy: słaby PD tak, snowdrift warunkowo, PD nie (udział D > 0,95).
   - **P2+P3 przy prędkości 2 – „tak” we wszystkich 9 kolumnach, dla limitu 5 i 15.** Przy prędkości 0,1
     zależy od sieci i macierzy (limit ogranicza mniej agentów, efekt P3 słabszy).
2. **Trójka P1+P2+P3** zachodzi przy prędkości 2 dla słabego PD (wszystkie sieci, oba limity) i dla snowdriftu
   przy limicie 5; dla klasycznego PD nie zachodzi przy prędkości 2 (brak P1). Przy prędkości 0,1 zachodzi
   tylko w części kolumn (np. fragmented: PD i słaby PD przy limicie 5).
3. **Konflikt P1–P3 przez mobilność dotyczy klasycznego PD.** Przy słabym PD i N = 500 wysoka mobilność
   pozwala na współistnienie wszystkich trzech regularności.
4. **Porównanie z N = 200 (tylko PD):** przy N = 200 P2+P3 z limitem 5 była „tak” we wszystkich sieciach
   i prędkościach; przy N = 500 dla PD i prędkości 0,1 na connected jest tylko warunkowa – wynik wrażliwy
   na skalę populacji.
5. **Klasyfikacja ogólna:** wszystkie zestawienia są parametrami kontekstowymi; pierwszorzędnym czynnikiem jest
   mobilność, drugim macierz wypłat, najsłabszym wariant sieci. Kandydatami na stałe projektowe są tylko
   zestawienia w obrębie ustalonego reżimu mobilności (P1+P2 przy niskiej, P2+P3 przy wysokiej).

## P1, P2, P3 w przestrzeni (PD, ewolucja)

| układ | macierz | prędkość | limit | n (mut. 0 / 0,01) | limit działa | ALLC bez mutacji | ALLC mut. 0,01 | ALLD mut. 0,01 | udział D mut. 0,01 | P1 | P2 | P3 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline | PD_classic | 0.1 | 0 | 15 / 15 | — | 0.000 ± 0.000 | 0.043 ± 0.012 | 0.64 ± 0.03 | 0.86 ± 0.04 | tak | tak | — |
| baseline | PD_classic | 0.1 | 5 | 15 / 15 | 100% | 0.000 ± 0.000 | 0.043 ± 0.011 | 0.68 ± 0.02 | 0.89 ± 0.03 | tak | tak | tak (ΔALLD +0.041) |
| baseline | PD_classic | 0.1 | 15 | 15 / 15 | 86% | 0.000 ± 0.000 | 0.044 ± 0.010 | 0.64 ± 0.02 | 0.88 ± 0.03 | tak | tak | brak efektu (ΔALLD +0.001) |
| baseline | PD_classic | 2 | 0 | 15 / 15 | — | 0.000 ± 0.000 | 0.010 ± 0.004 | 0.87 ± 0.02 | 0.97 ± 0.00 | nie | tak | — |
| baseline | PD_classic | 2 | 5 | 15 / 15 | 100% | 0.000 ± 0.000 | 0.009 ± 0.003 | 0.93 ± 0.01 | 0.97 ± 0.01 | nie | tak | tak (ΔALLD +0.059) |
| baseline | PD_classic | 2 | 15 | 15 / 15 | 100% | 0.000 ± 0.000 | 0.008 ± 0.003 | 0.92 ± 0.01 | 0.97 ± 0.00 | nie | tak | tak (ΔALLD +0.048) |
| baseline | snowdrift | 0.1 | 0 | 15 / 15 | — | 0.000 ± 0.000 | 0.062 ± 0.016 | 0.44 ± 0.03 | 0.66 ± 0.04 | tak | tak | — |
| baseline | snowdrift | 0.1 | 5 | 15 / 15 | 100% | 0.000 ± 0.000 | 0.062 ± 0.014 | 0.46 ± 0.05 | 0.66 ± 0.09 | tak | tak | brak efektu (ΔALLD +0.027) |
| baseline | snowdrift | 0.1 | 15 | 15 / 15 | 86% | 0.000 ± 0.000 | 0.060 ± 0.016 | 0.44 ± 0.03 | 0.65 ± 0.08 | tak | tak | brak efektu (ΔALLD +0.005) |
| baseline | snowdrift | 2 | 0 | 15 / 15 | — | 0.000 ± 0.000 | 0.038 ± 0.008 | 0.55 ± 0.06 | 0.79 ± 0.04 | warunkowo | tak | — |
| baseline | snowdrift | 2 | 5 | 15 / 15 | 100% | 0.000 ± 0.000 | 0.030 ± 0.010 | 0.73 ± 0.03 | 0.84 ± 0.03 | tak | tak | tak (ΔALLD +0.175) |
| baseline | snowdrift | 2 | 15 | 15 / 15 | 100% | 0.000 ± 0.000 | 0.030 ± 0.010 | 0.67 ± 0.05 | 0.81 ± 0.04 | warunkowo | tak | tak (ΔALLD +0.114) |
| baseline | weak_PD | 0.1 | 0 | 15 / 15 | — | 0.000 ± 0.000 | 0.053 ± 0.013 | 0.47 ± 0.03 | 0.69 ± 0.05 | tak | tak | — |
| baseline | weak_PD | 0.1 | 5 | 15 / 15 | 100% | 0.000 ± 0.000 | 0.054 ± 0.011 | 0.49 ± 0.02 | 0.71 ± 0.07 | tak | tak | brak efektu (ΔALLD +0.020) |
| baseline | weak_PD | 0.1 | 15 | 15 / 15 | 86% | 0.000 ± 0.000 | 0.052 ± 0.011 | 0.46 ± 0.03 | 0.68 ± 0.07 | tak | tak | brak efektu (ΔALLD -0.010) |
| baseline | weak_PD | 2 | 0 | 15 / 15 | — | 0.000 ± 0.000 | 0.016 ± 0.006 | 0.77 ± 0.02 | 0.93 ± 0.01 | tak | tak | — |
| baseline | weak_PD | 2 | 5 | 15 / 15 | 100% | 0.000 ± 0.000 | 0.015 ± 0.005 | 0.87 ± 0.01 | 0.94 ± 0.01 | tak | tak | tak (ΔALLD +0.099) |
| baseline | weak_PD | 2 | 15 | 15 / 15 | 100% | 0.000 ± 0.000 | 0.015 ± 0.005 | 0.85 ± 0.02 | 0.94 ± 0.01 | tak | tak | tak (ΔALLD +0.077) |
| connected | PD_classic | 0.1 | 0 | 15 / 15 | — | 0.000 ± 0.000 | 0.043 ± 0.010 | 0.65 ± 0.03 | 0.86 ± 0.05 | tak | tak | — |
| connected | PD_classic | 0.1 | 5 | 15 / 15 | 100% | 0.000 ± 0.000 | 0.041 ± 0.010 | 0.68 ± 0.04 | 0.88 ± 0.04 | tak | tak | brak efektu (ΔALLD +0.025) |
| connected | PD_classic | 0.1 | 15 | 15 / 15 | 86% | 0.000 ± 0.000 | 0.043 ± 0.010 | 0.65 ± 0.02 | 0.87 ± 0.05 | tak | tak | brak efektu (ΔALLD -0.003) |
| connected | PD_classic | 2 | 0 | 15 / 15 | — | 0.000 ± 0.000 | 0.010 ± 0.005 | 0.88 ± 0.02 | 0.97 ± 0.01 | nie | tak | — |
| connected | PD_classic | 2 | 5 | 15 / 15 | 100% | 0.000 ± 0.000 | 0.009 ± 0.003 | 0.93 ± 0.01 | 0.97 ± 0.01 | nie | tak | tak (ΔALLD +0.057) |
| connected | PD_classic | 2 | 15 | 15 / 15 | 100% | 0.000 ± 0.000 | 0.008 ± 0.003 | 0.92 ± 0.01 | 0.97 ± 0.01 | nie | tak | tak (ΔALLD +0.044) |
| connected | snowdrift | 0.1 | 0 | 15 / 15 | — | 0.000 ± 0.000 | 0.064 ± 0.011 | 0.43 ± 0.04 | 0.67 ± 0.05 | tak | tak | — |
| connected | snowdrift | 0.1 | 5 | 15 / 15 | 100% | 0.000 ± 0.000 | 0.057 ± 0.012 | 0.46 ± 0.04 | 0.66 ± 0.06 | tak | tak | tak (ΔALLD +0.033) |
| connected | snowdrift | 0.1 | 15 | 15 / 15 | 86% | 0.000 ± 0.000 | 0.062 ± 0.015 | 0.43 ± 0.03 | 0.64 ± 0.06 | tak | tak | brak efektu (ΔALLD +0.003) |
| connected | snowdrift | 2 | 0 | 15 / 15 | — | 0.000 ± 0.000 | 0.036 ± 0.012 | 0.55 ± 0.06 | 0.78 ± 0.06 | warunkowo | tak | — |
| connected | snowdrift | 2 | 5 | 15 / 15 | 100% | 0.000 ± 0.000 | 0.030 ± 0.008 | 0.74 ± 0.03 | 0.85 ± 0.02 | tak | tak | tak (ΔALLD +0.189) |
| connected | snowdrift | 2 | 15 | 15 / 15 | 100% | 0.000 ± 0.000 | 0.031 ± 0.012 | 0.68 ± 0.03 | 0.82 ± 0.03 | tak | tak | tak (ΔALLD +0.136) |
| connected | weak_PD | 0.1 | 0 | 15 / 15 | — | 0.000 ± 0.000 | 0.055 ± 0.016 | 0.46 ± 0.05 | 0.68 ± 0.07 | tak | tak | — |
| connected | weak_PD | 0.1 | 5 | 15 / 15 | 100% | 0.000 ± 0.000 | 0.057 ± 0.012 | 0.47 ± 0.04 | 0.70 ± 0.06 | tak | tak | brak efektu (ΔALLD +0.010) |
| connected | weak_PD | 0.1 | 15 | 15 / 15 | 86% | 0.000 ± 0.000 | 0.058 ± 0.012 | 0.45 ± 0.03 | 0.69 ± 0.07 | tak | tak | brak efektu (ΔALLD -0.009) |
| connected | weak_PD | 2 | 0 | 15 / 15 | — | 0.000 ± 0.000 | 0.014 ± 0.005 | 0.76 ± 0.05 | 0.93 ± 0.02 | tak | tak | — |
| connected | weak_PD | 2 | 5 | 15 / 15 | 100% | 0.000 ± 0.000 | 0.013 ± 0.006 | 0.86 ± 0.02 | 0.94 ± 0.01 | tak | tak | tak (ΔALLD +0.105) |
| connected | weak_PD | 2 | 15 | 15 / 15 | 100% | 0.000 ± 0.000 | 0.012 ± 0.003 | 0.85 ± 0.02 | 0.94 ± 0.01 | tak | tak | tak (ΔALLD +0.095) |
| fragmented | PD_classic | 0.1 | 0 | 15 / 15 | — | 0.000 ± 0.000 | 0.045 ± 0.011 | 0.59 ± 0.03 | 0.82 ± 0.05 | tak | tak | — |
| fragmented | PD_classic | 0.1 | 5 | 15 / 15 | 100% | 0.000 ± 0.000 | 0.044 ± 0.009 | 0.65 ± 0.03 | 0.87 ± 0.03 | tak | tak | tak (ΔALLD +0.057) |
| fragmented | PD_classic | 0.1 | 15 | 15 / 15 | 67% | 0.000 ± 0.000 | 0.039 ± 0.012 | 0.62 ± 0.04 | 0.86 ± 0.04 | tak | tak | tak (ΔALLD +0.027) |
| fragmented | PD_classic | 2 | 0 | 15 / 15 | — | 0.000 ± 0.000 | 0.010 ± 0.003 | 0.86 ± 0.02 | 0.97 ± 0.01 | nie | tak | — |
| fragmented | PD_classic | 2 | 5 | 15 / 15 | 100% | 0.000 ± 0.000 | 0.010 ± 0.003 | 0.92 ± 0.01 | 0.97 ± 0.01 | nie | tak | tak (ΔALLD +0.062) |
| fragmented | PD_classic | 2 | 15 | 15 / 15 | 100% | 0.000 ± 0.000 | 0.009 ± 0.003 | 0.91 ± 0.01 | 0.97 ± 0.01 | nie | tak | tak (ΔALLD +0.048) |
| fragmented | snowdrift | 0.1 | 0 | 15 / 15 | — | 0.001 ± 0.005 | 0.065 ± 0.014 | 0.40 ± 0.04 | 0.60 ± 0.06 | tak | tak | — |
| fragmented | snowdrift | 0.1 | 5 | 15 / 15 | 100% | 0.000 ± 0.001 | 0.067 ± 0.014 | 0.43 ± 0.04 | 0.61 ± 0.06 | warunkowo | tak | tak (ΔALLD +0.030) |
| fragmented | snowdrift | 0.1 | 15 | 15 / 15 | 68% | 0.001 ± 0.005 | 0.065 ± 0.014 | 0.41 ± 0.04 | 0.63 ± 0.08 | warunkowo | tak | brak efektu (ΔALLD +0.010) |
| fragmented | snowdrift | 2 | 0 | 15 / 15 | — | 0.000 ± 0.000 | 0.046 ± 0.014 | 0.49 ± 0.05 | 0.72 ± 0.05 | warunkowo | tak | — |
| fragmented | snowdrift | 2 | 5 | 15 / 15 | 100% | 0.000 ± 0.000 | 0.032 ± 0.012 | 0.67 ± 0.04 | 0.81 ± 0.03 | tak | tak | tak (ΔALLD +0.183) |
| fragmented | snowdrift | 2 | 15 | 15 / 15 | 100% | 0.000 ± 0.000 | 0.037 ± 0.010 | 0.58 ± 0.07 | 0.75 ± 0.06 | warunkowo | tak | tak (ΔALLD +0.096) |
| fragmented | weak_PD | 0.1 | 0 | 15 / 15 | — | 0.000 ± 0.001 | 0.066 ± 0.016 | 0.41 ± 0.04 | 0.65 ± 0.05 | tak | tak | — |
| fragmented | weak_PD | 0.1 | 5 | 15 / 15 | 100% | 0.000 ± 0.000 | 0.053 ± 0.015 | 0.44 ± 0.03 | 0.66 ± 0.06 | tak | tak | tak (ΔALLD +0.029) |
| fragmented | weak_PD | 0.1 | 15 | 15 / 15 | 69% | 0.000 ± 0.001 | 0.066 ± 0.013 | 0.42 ± 0.03 | 0.66 ± 0.07 | tak | tak | brak efektu (ΔALLD +0.017) |
| fragmented | weak_PD | 2 | 0 | 15 / 15 | — | 0.000 ± 0.000 | 0.015 ± 0.004 | 0.74 ± 0.04 | 0.92 ± 0.02 | tak | tak | — |
| fragmented | weak_PD | 2 | 5 | 15 / 15 | 100% | 0.000 ± 0.000 | 0.014 ± 0.007 | 0.84 ± 0.02 | 0.93 ± 0.01 | tak | tak | tak (ΔALLD +0.104) |
| fragmented | weak_PD | 2 | 15 | 15 / 15 | 100% | 0.000 ± 0.000 | 0.011 ± 0.005 | 0.83 ± 0.03 | 0.94 ± 0.02 | tak | tak | tak (ΔALLD +0.089) |

### Tabela zbiorcza – pary i trójka z P1, P2, P3

Kolumny: układ × macierz × prędkość. P1+P3 osobno: `p1p3_network_verdict_N200_r10.md`.

| zestawienie | baseline / PD_classic / 0.1 | baseline / PD_classic / 2.0 | baseline / snowdrift / 0.1 | baseline / snowdrift / 2.0 | baseline / weak_PD / 0.1 | baseline / weak_PD / 2.0 | connected / PD_classic / 0.1 | connected / PD_classic / 2.0 | connected / snowdrift / 0.1 | connected / snowdrift / 2.0 | connected / weak_PD / 0.1 | connected / weak_PD / 2.0 | fragmented / PD_classic / 0.1 | fragmented / PD_classic / 2.0 | fragmented / snowdrift / 0.1 | fragmented / snowdrift / 2.0 | fragmented / weak_PD / 0.1 | fragmented / weak_PD / 2.0 | klasyfikacja |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| P1+P2 (bez limitu) | **tak** | **nie** | **tak** | **warunkowo** | **tak** | **tak** | **tak** | **nie** | **tak** | **warunkowo** | **tak** | **tak** | **tak** | **nie** | **tak** | **warunkowo** | **tak** | **tak** | parametr kontekstowy (zależy od: macierzy wypłat, mobilności (prędkość)) |
| P2+P3, limit 5 | **tak** | **tak** | **warunkowo** | **tak** | **warunkowo** | **tak** | **warunkowo** | **tak** | **tak** | **tak** | **warunkowo** | **tak** | **tak** | **tak** | **tak** | **tak** | **tak** | **tak** | parametr kontekstowy (zależy od: układu przestrzeni, macierzy wypłat, mobilności (prędkość)) |
| P2+P3, limit 15 | **warunkowo** | **tak** | **warunkowo** | **tak** | **warunkowo** | **tak** | **warunkowo** | **tak** | **warunkowo** | **tak** | **warunkowo** | **tak** | **tak** | **tak** | **warunkowo** | **tak** | **warunkowo** | **tak** | parametr kontekstowy (zależy od: układu przestrzeni, macierzy wypłat, mobilności (prędkość)) |
| P1+P2+P3, limit 5 | **tak** | **nie** | **warunkowo** | **tak** | **warunkowo** | **tak** | **warunkowo** | **nie** | **tak** | **tak** | **warunkowo** | **tak** | **tak** | **nie** | **warunkowo** | **tak** | **tak** | **tak** | parametr kontekstowy (zależy od: układu przestrzeni, macierzy wypłat, mobilności (prędkość)) |
| P1+P2+P3, limit 15 | **warunkowo** | **nie** | **warunkowo** | **warunkowo** | **warunkowo** | **tak** | **warunkowo** | **nie** | **warunkowo** | **tak** | **warunkowo** | **tak** | **tak** | **nie** | **warunkowo** | **warunkowo** | **warunkowo** | **tak** | parametr kontekstowy (zależy od: układu przestrzeni, macierzy wypłat, mobilności (prędkość)) |

