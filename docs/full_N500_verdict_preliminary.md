# Pełny przegląd N = 500 – werdykty WSTĘPNE (1144 z 1620 przebiegów)

`PM9_full_N500` (port Pythona, zamrożony kod `98a762f`): N = 500, macierze {PD, słaby PD, snowdrift},
sieci {baseline, fragmented, connected} × prędkość {0,1; 2} × limit Dunbara {0, 5, 15} × mutacja {0; 0,01}.
Stan: 1144 przebiegi, 8–14 powtórzeń na kombinację (docelowo 15). Pozostałe liczone w 4 porcjach
(`results/full_N500_r15_shard*.csv`); po zakończeniu werdykty zostaną policzone ponownie.

## Pierwsze obserwacje (do potwierdzenia na pełnych danych)

- **P2+P3 przy limicie 15 zależy wyłącznie od mobilności:** „tak” przy prędkości 2 we wszystkich 9 kolumnach
  (3 sieci × 3 macierze), „warunkowo” przy 0,1. Przy N = 500 limit 15 ogranicza agentów także przy wysokiej mobilności.
- **P2+P3 przy limicie 5:** „tak” przy prędkości 2 wszędzie; przy 0,1 zależne od macierzy (PD tak, słaby PD
  i część snowdrift warunkowo). Przy N = 200 (tylko PD) ta para była stałą kandydacką – przy trzech macierzach
  już nie.
- **P1 przy N = 500 i prędkości 2 zachodzi dla słabego PD** (i częściowo snowdriftu), a nie zachodzi dla PD –
  więc konflikt P1–P3 przez mobilność dotyczy głównie klasycznego PD.

## P1, P2, P3 w przestrzeni (PD, ewolucja)

| układ | macierz | prędkość | limit | n (mut. 0 / 0,01) | limit działa | ALLC bez mutacji | ALLC mut. 0,01 | ALLD mut. 0,01 | udział D mut. 0,01 | P1 | P2 | P3 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline | PD_classic | 0.1 | 0 | 14 / 11 | — | 0.000 ± 0.000 | 0.042 ± 0.012 | 0.64 ± 0.03 | 0.86 ± 0.04 | tak | tak | — |
| baseline | PD_classic | 0.1 | 5 | 14 / 11 | 100% | 0.000 ± 0.000 | 0.040 ± 0.011 | 0.68 ± 0.02 | 0.89 ± 0.03 | tak | tak | tak (ΔALLD +0.044) |
| baseline | PD_classic | 0.1 | 15 | 13 / 11 | 86% | 0.000 ± 0.000 | 0.044 ± 0.010 | 0.64 ± 0.02 | 0.87 ± 0.03 | tak | tak | brak efektu (ΔALLD +0.001) |
| baseline | PD_classic | 2 | 0 | 14 / 11 | — | 0.000 ± 0.000 | 0.011 ± 0.004 | 0.87 ± 0.02 | 0.97 ± 0.00 | nie | tak | — |
| baseline | PD_classic | 2 | 5 | 14 / 11 | 100% | 0.000 ± 0.000 | 0.009 ± 0.003 | 0.93 ± 0.01 | 0.97 ± 0.01 | nie | tak | tak (ΔALLD +0.060) |
| baseline | PD_classic | 2 | 15 | 11 / 11 | 100% | 0.000 ± 0.000 | 0.008 ± 0.004 | 0.92 ± 0.01 | 0.97 ± 0.01 | nie | tak | tak (ΔALLD +0.049) |
| baseline | snowdrift | 0.1 | 0 | 11 / 8 | — | 0.000 ± 0.000 | 0.061 ± 0.011 | 0.44 ± 0.03 | 0.68 ± 0.04 | tak | tak | — |
| baseline | snowdrift | 0.1 | 5 | 10 / 8 | 100% | 0.000 ± 0.000 | 0.059 ± 0.016 | 0.46 ± 0.06 | 0.66 ± 0.11 | tak | tak | brak efektu (ΔALLD +0.019) |
| baseline | snowdrift | 0.1 | 15 | 9 / 8 | 85% | 0.000 ± 0.000 | 0.062 ± 0.015 | 0.44 ± 0.04 | 0.64 ± 0.10 | tak | tak | brak efektu (ΔALLD +0.002) |
| baseline | snowdrift | 2 | 0 | 11 / 8 | — | 0.000 ± 0.000 | 0.036 ± 0.008 | 0.56 ± 0.05 | 0.80 ± 0.03 | warunkowo | tak | — |
| baseline | snowdrift | 2 | 5 | 9 / 8 | 100% | 0.000 ± 0.000 | 0.032 ± 0.010 | 0.71 ± 0.02 | 0.83 ± 0.03 | tak | tak | tak (ΔALLD +0.153) |
| baseline | snowdrift | 2 | 15 | 9 / 8 | 100% | 0.000 ± 0.000 | 0.028 ± 0.009 | 0.68 ± 0.05 | 0.82 ± 0.04 | warunkowo | tak | tak (ΔALLD +0.125) |
| baseline | weak_PD | 0.1 | 0 | 11 / 11 | — | 0.000 ± 0.000 | 0.054 ± 0.015 | 0.47 ± 0.04 | 0.70 ± 0.05 | tak | tak | — |
| baseline | weak_PD | 0.1 | 5 | 11 / 11 | 100% | 0.000 ± 0.000 | 0.055 ± 0.012 | 0.49 ± 0.02 | 0.72 ± 0.06 | tak | tak | brak efektu (ΔALLD +0.017) |
| baseline | weak_PD | 0.1 | 15 | 11 / 11 | 86% | 0.000 ± 0.000 | 0.050 ± 0.011 | 0.46 ± 0.03 | 0.68 ± 0.07 | tak | tak | brak efektu (ΔALLD -0.014) |
| baseline | weak_PD | 2 | 0 | 11 / 11 | — | 0.000 ± 0.000 | 0.016 ± 0.006 | 0.77 ± 0.03 | 0.93 ± 0.01 | tak | tak | — |
| baseline | weak_PD | 2 | 5 | 11 / 11 | 100% | 0.000 ± 0.000 | 0.016 ± 0.005 | 0.87 ± 0.01 | 0.94 ± 0.01 | tak | tak | tak (ΔALLD +0.100) |
| baseline | weak_PD | 2 | 15 | 11 / 11 | 100% | 0.000 ± 0.000 | 0.014 ± 0.005 | 0.84 ± 0.03 | 0.94 ± 0.01 | tak | tak | tak (ΔALLD +0.076) |
| connected | PD_classic | 0.1 | 0 | 14 / 11 | — | 0.000 ± 0.000 | 0.042 ± 0.010 | 0.65 ± 0.03 | 0.85 ± 0.06 | tak | tak | — |
| connected | PD_classic | 0.1 | 5 | 14 / 11 | 100% | 0.000 ± 0.000 | 0.039 ± 0.009 | 0.69 ± 0.03 | 0.89 ± 0.04 | tak | tak | tak (ΔALLD +0.039) |
| connected | PD_classic | 0.1 | 15 | 11 / 11 | 86% | 0.000 ± 0.000 | 0.041 ± 0.009 | 0.65 ± 0.02 | 0.87 ± 0.05 | tak | tak | brak efektu (ΔALLD +0.006) |
| connected | PD_classic | 2 | 0 | 14 / 11 | — | 0.000 ± 0.000 | 0.011 ± 0.005 | 0.88 ± 0.02 | 0.97 ± 0.01 | nie | tak | — |
| connected | PD_classic | 2 | 5 | 13 / 11 | 100% | 0.000 ± 0.000 | 0.009 ± 0.003 | 0.93 ± 0.01 | 0.97 ± 0.00 | nie | tak | tak (ΔALLD +0.054) |
| connected | PD_classic | 2 | 15 | 11 / 11 | 100% | 0.000 ± 0.000 | 0.008 ± 0.003 | 0.93 ± 0.01 | 0.97 ± 0.00 | nie | tak | tak (ΔALLD +0.047) |
| connected | snowdrift | 0.1 | 0 | 10 / 8 | — | 0.000 ± 0.000 | 0.065 ± 0.014 | 0.42 ± 0.04 | 0.65 ± 0.04 | tak | tak | — |
| connected | snowdrift | 0.1 | 5 | 9 / 8 | 100% | 0.000 ± 0.000 | 0.052 ± 0.008 | 0.46 ± 0.02 | 0.64 ± 0.05 | tak | tak | tak (ΔALLD +0.044) |
| connected | snowdrift | 0.1 | 15 | 9 / 8 | 86% | 0.000 ± 0.000 | 0.059 ± 0.011 | 0.43 ± 0.03 | 0.64 ± 0.07 | warunkowo | tak | brak efektu (ΔALLD +0.014) |
| connected | snowdrift | 2 | 0 | 10 / 8 | — | 0.000 ± 0.000 | 0.039 ± 0.014 | 0.54 ± 0.08 | 0.77 ± 0.06 | warunkowo | tak | — |
| connected | snowdrift | 2 | 5 | 9 / 8 | 100% | 0.000 ± 0.000 | 0.031 ± 0.007 | 0.74 ± 0.03 | 0.85 ± 0.02 | tak | tak | tak (ΔALLD +0.194) |
| connected | snowdrift | 2 | 15 | 8 / 8 | 100% | 0.000 ± 0.000 | 0.036 ± 0.014 | 0.67 ± 0.02 | 0.81 ± 0.02 | warunkowo | tak | tak (ΔALLD +0.126) |
| connected | weak_PD | 0.1 | 0 | 11 / 11 | — | 0.000 ± 0.000 | 0.050 ± 0.013 | 0.48 ± 0.05 | 0.70 ± 0.05 | tak | tak | — |
| connected | weak_PD | 0.1 | 5 | 11 / 11 | 100% | 0.000 ± 0.000 | 0.060 ± 0.010 | 0.47 ± 0.05 | 0.71 ± 0.06 | warunkowo | tak | brak efektu (ΔALLD -0.003) |
| connected | weak_PD | 0.1 | 15 | 11 / 11 | 86% | 0.000 ± 0.000 | 0.053 ± 0.009 | 0.46 ± 0.02 | 0.71 ± 0.05 | tak | tak | brak efektu (ΔALLD -0.013) |
| connected | weak_PD | 2 | 0 | 11 / 11 | — | 0.000 ± 0.000 | 0.014 ± 0.004 | 0.78 ± 0.04 | 0.93 ± 0.01 | tak | tak | — |
| connected | weak_PD | 2 | 5 | 11 / 11 | 100% | 0.000 ± 0.000 | 0.013 ± 0.007 | 0.86 ± 0.02 | 0.94 ± 0.01 | tak | tak | tak (ΔALLD +0.085) |
| connected | weak_PD | 2 | 15 | 11 / 11 | 100% | 0.000 ± 0.000 | 0.013 ± 0.004 | 0.85 ± 0.02 | 0.94 ± 0.01 | tak | tak | tak (ΔALLD +0.078) |
| fragmented | PD_classic | 0.1 | 0 | 14 / 11 | — | 0.000 ± 0.000 | 0.044 ± 0.010 | 0.59 ± 0.04 | 0.83 ± 0.06 | tak | tak | — |
| fragmented | PD_classic | 0.1 | 5 | 14 / 11 | 100% | 0.000 ± 0.000 | 0.044 ± 0.007 | 0.64 ± 0.03 | 0.86 ± 0.03 | tak | tak | tak (ΔALLD +0.054) |
| fragmented | PD_classic | 0.1 | 15 | 11 / 11 | 67% | 0.000 ± 0.000 | 0.038 ± 0.012 | 0.61 ± 0.04 | 0.87 ± 0.04 | tak | tak | brak efektu (ΔALLD +0.024) |
| fragmented | PD_classic | 2 | 0 | 14 / 11 | — | 0.000 ± 0.000 | 0.010 ± 0.003 | 0.86 ± 0.02 | 0.97 ± 0.01 | nie | tak | — |
| fragmented | PD_classic | 2 | 5 | 13 / 11 | 100% | 0.000 ± 0.000 | 0.010 ± 0.003 | 0.92 ± 0.01 | 0.97 ± 0.01 | nie | tak | tak (ΔALLD +0.062) |
| fragmented | PD_classic | 2 | 15 | 11 / 11 | 100% | 0.000 ± 0.000 | 0.010 ± 0.003 | 0.91 ± 0.01 | 0.97 ± 0.00 | nie | tak | tak (ΔALLD +0.053) |
| fragmented | snowdrift | 0.1 | 0 | 11 / 8 | — | 0.002 ± 0.005 | 0.070 ± 0.013 | 0.39 ± 0.05 | 0.61 ± 0.06 | warunkowo | tak | — |
| fragmented | snowdrift | 0.1 | 5 | 10 / 8 | 100% | 0.000 ± 0.001 | 0.064 ± 0.014 | 0.43 ± 0.04 | 0.61 ± 0.08 | warunkowo | tak | brak efektu (ΔALLD +0.041) |
| fragmented | snowdrift | 0.1 | 15 | 9 / 8 | 70% | 0.002 ± 0.006 | 0.063 ± 0.015 | 0.39 ± 0.03 | 0.62 ± 0.09 | warunkowo | tak | brak efektu (ΔALLD +0.000) |
| fragmented | snowdrift | 2 | 0 | 10 / 8 | — | 0.000 ± 0.000 | 0.040 ± 0.014 | 0.48 ± 0.05 | 0.72 ± 0.06 | warunkowo | tak | — |
| fragmented | snowdrift | 2 | 5 | 9 / 8 | 100% | 0.000 ± 0.000 | 0.031 ± 0.012 | 0.68 ± 0.05 | 0.81 ± 0.03 | tak | tak | tak (ΔALLD +0.193) |
| fragmented | snowdrift | 2 | 15 | 9 / 8 | 100% | 0.000 ± 0.000 | 0.038 ± 0.011 | 0.56 ± 0.05 | 0.73 ± 0.05 | warunkowo | tak | tak (ΔALLD +0.080) |
| fragmented | weak_PD | 0.1 | 0 | 11 / 11 | — | 0.000 ± 0.001 | 0.064 ± 0.018 | 0.42 ± 0.03 | 0.67 ± 0.03 | tak | tak | — |
| fragmented | weak_PD | 0.1 | 5 | 11 / 11 | 100% | 0.000 ± 0.000 | 0.054 ± 0.017 | 0.43 ± 0.03 | 0.66 ± 0.06 | tak | tak | brak efektu (ΔALLD +0.012) |
| fragmented | weak_PD | 0.1 | 15 | 11 / 11 | 69% | 0.000 ± 0.001 | 0.068 ± 0.012 | 0.43 ± 0.03 | 0.67 ± 0.07 | tak | tak | brak efektu (ΔALLD +0.010) |
| fragmented | weak_PD | 2 | 0 | 11 / 11 | — | 0.000 ± 0.000 | 0.016 ± 0.004 | 0.73 ± 0.03 | 0.92 ± 0.02 | tak | tak | — |
| fragmented | weak_PD | 2 | 5 | 11 / 11 | 100% | 0.000 ± 0.000 | 0.016 ± 0.007 | 0.85 ± 0.02 | 0.93 ± 0.02 | tak | tak | tak (ΔALLD +0.115) |
| fragmented | weak_PD | 2 | 15 | 11 / 11 | 100% | 0.000 ± 0.000 | 0.010 ± 0.005 | 0.84 ± 0.03 | 0.94 ± 0.02 | tak | tak | tak (ΔALLD +0.106) |

### Tabela zbiorcza – pary i trójka z P1, P2, P3

Kolumny: układ × macierz × prędkość. P1+P3 osobno: `p1p3_network_verdict_N200_r10.md`.

| zestawienie | baseline / PD_classic / 0.1 | baseline / PD_classic / 2.0 | baseline / snowdrift / 0.1 | baseline / snowdrift / 2.0 | baseline / weak_PD / 0.1 | baseline / weak_PD / 2.0 | connected / PD_classic / 0.1 | connected / PD_classic / 2.0 | connected / snowdrift / 0.1 | connected / snowdrift / 2.0 | connected / weak_PD / 0.1 | connected / weak_PD / 2.0 | fragmented / PD_classic / 0.1 | fragmented / PD_classic / 2.0 | fragmented / snowdrift / 0.1 | fragmented / snowdrift / 2.0 | fragmented / weak_PD / 0.1 | fragmented / weak_PD / 2.0 | klasyfikacja |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| P1+P2 (bez limitu) | **tak** | **nie** | **tak** | **warunkowo** | **tak** | **tak** | **tak** | **nie** | **tak** | **warunkowo** | **tak** | **tak** | **tak** | **nie** | **warunkowo** | **warunkowo** | **tak** | **tak** | parametr kontekstowy (zależy od: układu przestrzeni, macierzy wypłat, mobilności (prędkość)) |
| P2+P3, limit 5 | **tak** | **tak** | **warunkowo** | **tak** | **warunkowo** | **tak** | **tak** | **tak** | **tak** | **tak** | **warunkowo** | **tak** | **tak** | **tak** | **warunkowo** | **tak** | **warunkowo** | **tak** | parametr kontekstowy (zależy od: układu przestrzeni, macierzy wypłat, mobilności (prędkość)) |
| P2+P3, limit 15 | **warunkowo** | **tak** | **warunkowo** | **tak** | **warunkowo** | **tak** | **warunkowo** | **tak** | **warunkowo** | **tak** | **warunkowo** | **tak** | **warunkowo** | **tak** | **warunkowo** | **tak** | **warunkowo** | **tak** | parametr kontekstowy (zależy od: mobilności (prędkość)) |
| P1+P2+P3, limit 5 | **tak** | **nie** | **warunkowo** | **tak** | **warunkowo** | **tak** | **tak** | **nie** | **tak** | **tak** | **warunkowo** | **tak** | **tak** | **nie** | **warunkowo** | **tak** | **warunkowo** | **tak** | parametr kontekstowy (zależy od: układu przestrzeni, macierzy wypłat, mobilności (prędkość)) |
| P1+P2+P3, limit 15 | **warunkowo** | **nie** | **warunkowo** | **warunkowo** | **warunkowo** | **tak** | **warunkowo** | **nie** | **warunkowo** | **warunkowo** | **warunkowo** | **tak** | **warunkowo** | **nie** | **warunkowo** | **warunkowo** | **warunkowo** | **tak** | parametr kontekstowy (zależy od: macierzy wypłat, mobilności (prędkość)) |

