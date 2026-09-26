# Para P1+P3 na wariantach sieci (port Pythona, N = 200, 10 powtórzeń)

`PM7_P1P3_network`: ewolucja (Fermi, mutacja 0,01), klasyczny PD, rdzeń zgodności, 100 000 cykli,
limit Dunbara ∈ {0, 5, 15, 50, 150} × sieć {baseline, fragmented, connected} × prędkość {0,1; 2}.
Para się utrzymuje, gdy przy tym samym limicie zachodzą P1 i P3. P3 mierzone trzema miarami: spadek kooperacji
(udział D, główna), udział oszustów (udział ALLD, miara selekcji z etapu 2) i zysk oszustów (wypłata ALLD na grę).
Port ma inny generator liczb losowych niż GAMA; wyniki do potwierdzenia w GAMA.

## Wnioski

1. **Przy niskiej mobilności (0,1) para P1+P3 zachodzi przy małych limitach.** Na baseline i fragmented P1 = tak,
   a limit 5 podnosi udział ALLD o +0,07 i +0,06 (95% CI > 0); na baseline także limit 15 (+0,03). Na connected
   P1 jest warunkowe (stabilizacja 70%). Przy ewolucji w 100 000 cyklach agent ma więcej różnych partnerów niż
   w P3 z 20 000 cykli, więc limity 5 i 15 działają także przy prędkości 0,1; limity 50 i 150 nie działają.
2. **Przy wysokiej mobilności (2) P1 nie zachodzi.** Udział ALLD 0,79–0,81 bez limitu, ale udział ruchów D
   0,96 (> 0,95, kryterium P1) i stabilizacja 60–70%. Limit silnie wzmacnia oszustów: udział ALLD +0,10 do +0,13
   przy limitach 5–50 na wszystkich trzech sieciach (limit 150 bez efektu). P3 działa, ale populacja jest
   prawie w pełni zdradzająca, więc para się rozjeżdża.
3. **Zysk oszustów na grę przy ewolucji nie rośnie** (przy prędkości 2 nawet spada, np. fragmented −0,03):
   gdy limit zwiększa udział ALLD, ALLD mają mniej naiwnych partnerów do wykorzystania. W warunkach ewolucji
   tę miarę zastępuje udział oszustów.
4. **Czynnikiem rozstrzygającym jest mobilność, nie wariant sieci.** Wariant sieci zmienia werdykt tylko przy
   prędkości 0,1 (connected: P1 warunkowo; limit 15 działa tylko na baseline). Wniosek z planu minimalnego
   (konflikt P1–P3 przez mobilność) potwierdza się w parze: P1 wymaga niskiej mobilności, a efekt limitu jest
   najsilniejszy przy wysokiej.

## Zestawienia parami – P1+P3 (ewolucja + limit Dunbara)

| układ | macierz | prędkość | mutacja | limit | n | limit działa | ALLD | udział D | Δ udziału D (95% CI) | Δ ALLD (95% CI) | Δ wypłaty ALLD (95% CI) | ALLC | stabilizacja | P1 | P2 (część) | P3 kooperacja | P3 udział oszustów | P3 zysk oszustów |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline | PD_classic | 0.1 | 0.01 | 0 | 10 | — | 0.63 ± 0.03 | 0.83 ± 0.04 | — | — | — | 0.046 ± 0.022 | 90% | tak | utrzymuje się: tak | — | — | — |
| baseline | PD_classic | 0.1 | 0.01 | 5 | 10 | 100% | 0.69 ± 0.06 | 0.86 ± 0.11 | +0.037 [-0.033, +0.108] | +0.067 [+0.028, +0.106] | -0.044 [-0.115, +0.028] | 0.040 ± 0.022 | 100% | tak | utrzymuje się: tak | brak efektu | tak | brak efektu |
| baseline | PD_classic | 0.1 | 0.01 | 15 | 10 | 80% | 0.65 ± 0.03 | 0.89 ± 0.03 | +0.068 [+0.039, +0.097] | +0.026 [+0.001, +0.051] | -0.018 [-0.090, +0.054] | 0.041 ± 0.012 | 90% | tak | utrzymuje się: tak | tak | tak | brak efektu |
| baseline | PD_classic | 0.1 | 0.01 | 50 | 10 | 0% | 0.63 ± 0.03 | 0.83 ± 0.04 | +0.000 [-0.032, +0.032] | +0.000 [-0.027, +0.027] | +0.000 [-0.083, +0.083] | 0.046 ± 0.022 | 90% | tak | utrzymuje się: tak | brak efektu | brak efektu | brak efektu |
| baseline | PD_classic | 0.1 | 0.01 | 150 | 10 | 0% | 0.63 ± 0.03 | 0.83 ± 0.04 | +0.000 [-0.032, +0.032] | +0.000 [-0.027, +0.027] | +0.000 [-0.083, +0.083] | 0.046 ± 0.022 | 90% | tak | utrzymuje się: tak | brak efektu | brak efektu | brak efektu |
| baseline | PD_classic | 2 | 0.01 | 0 | 10 | — | 0.79 ± 0.03 | 0.96 ± 0.02 | — | — | — | 0.012 ± 0.008 | 60% | nie | utrzymuje się: tak | — | — | — |
| baseline | PD_classic | 2 | 0.01 | 5 | 10 | 100% | 0.92 ± 0.02 | 0.97 ± 0.01 | +0.007 [-0.005, +0.019] | +0.132 [+0.108, +0.156] | -0.011 [-0.025, +0.003] | 0.010 ± 0.004 | 100% | nie | utrzymuje się: tak | brak efektu | tak | brak efektu |
| baseline | PD_classic | 2 | 0.01 | 15 | 10 | 100% | 0.92 ± 0.02 | 0.97 ± 0.01 | +0.012 [+0.001, +0.022] | +0.127 [+0.104, +0.151] | -0.012 [-0.028, +0.004] | 0.008 ± 0.003 | 100% | nie | utrzymuje się: tak | tak | tak | brak efektu |
| baseline | PD_classic | 2 | 0.01 | 50 | 10 | 100% | 0.90 ± 0.03 | 0.97 ± 0.01 | +0.008 [-0.003, +0.018] | +0.107 [+0.081, +0.133] | -0.013 [-0.026, +0.001] | 0.011 ± 0.003 | 100% | nie | utrzymuje się: tak | brak efektu | tak | brak efektu |
| baseline | PD_classic | 2 | 0.01 | 150 | 10 | 91% | 0.82 ± 0.05 | 0.96 ± 0.02 | +0.000 [-0.015, +0.015] | +0.026 [-0.009, +0.061] | -0.007 [-0.023, +0.009] | 0.010 ± 0.004 | 90% | nie | utrzymuje się: tak | brak efektu | brak efektu | brak efektu |
| connected | PD_classic | 0.1 | 0.01 | 0 | 10 | — | 0.62 ± 0.04 | 0.85 ± 0.05 | — | — | — | 0.045 ± 0.020 | 70% | warunkowo | utrzymuje się: tak | — | — | — |
| connected | PD_classic | 0.1 | 0.01 | 5 | 10 | 100% | 0.69 ± 0.05 | 0.91 ± 0.05 | +0.056 [+0.010, +0.102] | +0.070 [+0.030, +0.110] | +0.024 [-0.037, +0.085] | 0.046 ± 0.012 | 70% | warunkowo | utrzymuje się: tak | tak | tak | brak efektu |
| connected | PD_classic | 0.1 | 0.01 | 15 | 10 | 81% | 0.62 ± 0.07 | 0.87 ± 0.08 | +0.015 [-0.045, +0.074] | +0.007 [-0.041, +0.054] | -0.001 [-0.048, +0.046] | 0.041 ± 0.014 | 80% | warunkowo | utrzymuje się: tak | brak efektu | brak efektu | brak efektu |
| connected | PD_classic | 0.1 | 0.01 | 50 | 10 | 0% | 0.62 ± 0.04 | 0.85 ± 0.05 | +0.000 [-0.047, +0.047] | +0.000 [-0.035, +0.035] | +0.000 [-0.050, +0.050] | 0.045 ± 0.020 | 70% | warunkowo | utrzymuje się: tak | brak efektu | brak efektu | brak efektu |
| connected | PD_classic | 0.1 | 0.01 | 150 | 10 | 0% | 0.62 ± 0.04 | 0.85 ± 0.05 | +0.000 [-0.047, +0.047] | +0.000 [-0.035, +0.035] | +0.000 [-0.050, +0.050] | 0.045 ± 0.020 | 70% | warunkowo | utrzymuje się: tak | brak efektu | brak efektu | brak efektu |
| connected | PD_classic | 2 | 0.01 | 0 | 10 | — | 0.79 ± 0.06 | 0.96 ± 0.01 | — | — | — | 0.010 ± 0.005 | 70% | nie | utrzymuje się: tak | — | — | — |
| connected | PD_classic | 2 | 0.01 | 5 | 10 | 100% | 0.93 ± 0.02 | 0.97 ± 0.01 | +0.007 [-0.004, +0.017] | +0.131 [+0.091, +0.171] | -0.014 [-0.026, -0.003] | 0.009 ± 0.006 | 100% | nie | utrzymuje się: tak | brak efektu | tak | nie |
| connected | PD_classic | 2 | 0.01 | 15 | 10 | 100% | 0.91 ± 0.02 | 0.97 ± 0.01 | +0.004 [-0.007, +0.014] | +0.117 [+0.077, +0.157] | -0.012 [-0.025, +0.002] | 0.011 ± 0.006 | 100% | nie | utrzymuje się: tak | brak efektu | tak | brak efektu |
| connected | PD_classic | 2 | 0.01 | 50 | 10 | 100% | 0.90 ± 0.02 | 0.97 ± 0.01 | +0.003 [-0.008, +0.013] | +0.104 [+0.064, +0.145] | -0.010 [-0.022, +0.001] | 0.011 ± 0.006 | 100% | nie | utrzymuje się: tak | brak efektu | tak | brak efektu |
| connected | PD_classic | 2 | 0.01 | 150 | 10 | 91% | 0.82 ± 0.04 | 0.96 ± 0.01 | -0.003 [-0.014, +0.007] | +0.020 [-0.024, +0.065] | +0.002 [-0.012, +0.016] | 0.013 ± 0.008 | 90% | nie | utrzymuje się: tak | brak efektu | brak efektu | brak efektu |
| fragmented | PD_classic | 0.1 | 0.01 | 0 | 10 | — | 0.57 ± 0.06 | 0.78 ± 0.09 | — | — | — | 0.050 ± 0.014 | 90% | tak | utrzymuje się: tak | — | — | — |
| fragmented | PD_classic | 0.1 | 0.01 | 5 | 10 | 99% | 0.63 ± 0.05 | 0.86 ± 0.06 | +0.081 [+0.016, +0.146] | +0.061 [+0.012, +0.110] | -0.044 [-0.112, +0.024] | 0.040 ± 0.008 | 100% | tak | utrzymuje się: tak | tak | tak | brak efektu |
| fragmented | PD_classic | 0.1 | 0.01 | 15 | 10 | 63% | 0.57 ± 0.06 | 0.82 ± 0.07 | +0.032 [-0.038, +0.103] | +0.008 [-0.043, +0.059] | +0.007 [-0.069, +0.082] | 0.050 ± 0.013 | 80% | tak | utrzymuje się: tak | brak efektu | brak efektu | brak efektu |
| fragmented | PD_classic | 0.1 | 0.01 | 50 | 10 | 0% | 0.57 ± 0.06 | 0.78 ± 0.09 | +0.000 [-0.076, +0.076] | +0.000 [-0.053, +0.053] | +0.000 [-0.073, +0.073] | 0.050 ± 0.014 | 90% | tak | utrzymuje się: tak | brak efektu | brak efektu | brak efektu |
| fragmented | PD_classic | 0.1 | 0.01 | 150 | 10 | 0% | 0.57 ± 0.06 | 0.78 ± 0.09 | +0.000 [-0.076, +0.076] | +0.000 [-0.053, +0.053] | +0.000 [-0.073, +0.073] | 0.050 ± 0.014 | 90% | tak | utrzymuje się: tak | brak efektu | brak efektu | brak efektu |
| fragmented | PD_classic | 2 | 0.01 | 0 | 10 | — | 0.81 ± 0.04 | 0.96 ± 0.01 | — | — | — | 0.011 ± 0.005 | 70% | nie | utrzymuje się: tak | — | — | — |
| fragmented | PD_classic | 2 | 0.01 | 5 | 10 | 100% | 0.92 ± 0.01 | 0.98 ± 0.01 | +0.012 [+0.003, +0.020] | +0.110 [+0.083, +0.137] | -0.027 [-0.041, -0.014] | 0.010 ± 0.005 | 100% | nie | utrzymuje się: tak | tak | tak | nie |
| fragmented | PD_classic | 2 | 0.01 | 15 | 10 | 100% | 0.91 ± 0.02 | 0.97 ± 0.01 | +0.007 [-0.003, +0.016] | +0.100 [+0.072, +0.129] | -0.023 [-0.039, -0.007] | 0.010 ± 0.007 | 100% | nie | utrzymuje się: tak | brak efektu | tak | nie |
| fragmented | PD_classic | 2 | 0.01 | 50 | 10 | 100% | 0.88 ± 0.03 | 0.97 ± 0.01 | +0.010 [+0.001, +0.019] | +0.071 [+0.040, +0.102] | -0.019 [-0.032, -0.005] | 0.010 ± 0.009 | 100% | nie | utrzymuje się: tak | tak | tak | nie |
| fragmented | PD_classic | 2 | 0.01 | 150 | 10 | 34% | 0.81 ± 0.05 | 0.97 ± 0.01 | +0.003 [-0.006, +0.013] | -0.002 [-0.043, +0.040] | -0.003 [-0.019, +0.014] | 0.009 ± 0.006 | 90% | nie | utrzymuje się: tak | brak efektu | brak efektu | brak efektu |

**Zgodność par** (P1 i P3 utrzymane przy tym samym limicie; „brak efektu” P3 → para warunkowo):

- baseline, PD_classic, prędkość 0.1, mutacja 0.01, limit 5 (limit działa: 100%): P1 tak; P3 kooperacja brak efektu; P3 udział oszustów tak; P3 zysk oszustów brak efektu
- baseline, PD_classic, prędkość 0.1, mutacja 0.01, limit 15 (limit działa: 80%): P1 tak; P3 kooperacja tak; P3 udział oszustów tak; P3 zysk oszustów brak efektu
- baseline, PD_classic, prędkość 0.1, mutacja 0.01, limit 50 (limit działa: 0%): P1 tak; P3 kooperacja brak efektu; P3 udział oszustów brak efektu; P3 zysk oszustów brak efektu
- baseline, PD_classic, prędkość 0.1, mutacja 0.01, limit 150 (limit działa: 0%): P1 tak; P3 kooperacja brak efektu; P3 udział oszustów brak efektu; P3 zysk oszustów brak efektu
- baseline, PD_classic, prędkość 2, mutacja 0.01, limit 5 (limit działa: 100%): P1 nie; P3 kooperacja brak efektu; P3 udział oszustów tak; P3 zysk oszustów brak efektu
- baseline, PD_classic, prędkość 2, mutacja 0.01, limit 15 (limit działa: 100%): P1 nie; P3 kooperacja tak; P3 udział oszustów tak; P3 zysk oszustów brak efektu
- baseline, PD_classic, prędkość 2, mutacja 0.01, limit 50 (limit działa: 100%): P1 nie; P3 kooperacja brak efektu; P3 udział oszustów tak; P3 zysk oszustów brak efektu
- baseline, PD_classic, prędkość 2, mutacja 0.01, limit 150 (limit działa: 91%): P1 nie; P3 kooperacja brak efektu; P3 udział oszustów brak efektu; P3 zysk oszustów brak efektu
- connected, PD_classic, prędkość 0.1, mutacja 0.01, limit 5 (limit działa: 100%): P1 warunkowo; P3 kooperacja tak; P3 udział oszustów tak; P3 zysk oszustów brak efektu
- connected, PD_classic, prędkość 0.1, mutacja 0.01, limit 15 (limit działa: 81%): P1 warunkowo; P3 kooperacja brak efektu; P3 udział oszustów brak efektu; P3 zysk oszustów brak efektu
- connected, PD_classic, prędkość 0.1, mutacja 0.01, limit 50 (limit działa: 0%): P1 warunkowo; P3 kooperacja brak efektu; P3 udział oszustów brak efektu; P3 zysk oszustów brak efektu
- connected, PD_classic, prędkość 0.1, mutacja 0.01, limit 150 (limit działa: 0%): P1 warunkowo; P3 kooperacja brak efektu; P3 udział oszustów brak efektu; P3 zysk oszustów brak efektu
- connected, PD_classic, prędkość 2, mutacja 0.01, limit 5 (limit działa: 100%): P1 nie; P3 kooperacja brak efektu; P3 udział oszustów tak; P3 zysk oszustów nie
- connected, PD_classic, prędkość 2, mutacja 0.01, limit 15 (limit działa: 100%): P1 nie; P3 kooperacja brak efektu; P3 udział oszustów tak; P3 zysk oszustów brak efektu
- connected, PD_classic, prędkość 2, mutacja 0.01, limit 50 (limit działa: 100%): P1 nie; P3 kooperacja brak efektu; P3 udział oszustów tak; P3 zysk oszustów brak efektu
- connected, PD_classic, prędkość 2, mutacja 0.01, limit 150 (limit działa: 91%): P1 nie; P3 kooperacja brak efektu; P3 udział oszustów brak efektu; P3 zysk oszustów brak efektu
- fragmented, PD_classic, prędkość 0.1, mutacja 0.01, limit 5 (limit działa: 99%): P1 tak; P3 kooperacja tak; P3 udział oszustów tak; P3 zysk oszustów brak efektu
- fragmented, PD_classic, prędkość 0.1, mutacja 0.01, limit 15 (limit działa: 63%): P1 tak; P3 kooperacja brak efektu; P3 udział oszustów brak efektu; P3 zysk oszustów brak efektu
- fragmented, PD_classic, prędkość 0.1, mutacja 0.01, limit 50 (limit działa: 0%): P1 tak; P3 kooperacja brak efektu; P3 udział oszustów brak efektu; P3 zysk oszustów brak efektu
- fragmented, PD_classic, prędkość 0.1, mutacja 0.01, limit 150 (limit działa: 0%): P1 tak; P3 kooperacja brak efektu; P3 udział oszustów brak efektu; P3 zysk oszustów brak efektu
- fragmented, PD_classic, prędkość 2, mutacja 0.01, limit 5 (limit działa: 100%): P1 nie; P3 kooperacja tak; P3 udział oszustów tak; P3 zysk oszustów nie
- fragmented, PD_classic, prędkość 2, mutacja 0.01, limit 15 (limit działa: 100%): P1 nie; P3 kooperacja brak efektu; P3 udział oszustów tak; P3 zysk oszustów nie
- fragmented, PD_classic, prędkość 2, mutacja 0.01, limit 50 (limit działa: 100%): P1 nie; P3 kooperacja tak; P3 udział oszustów tak; P3 zysk oszustów nie
- fragmented, PD_classic, prędkość 2, mutacja 0.01, limit 150 (limit działa: 34%): P1 nie; P3 kooperacja brak efektu; P3 udział oszustów brak efektu; P3 zysk oszustów brak efektu

### Tabela zbiorcza par

| para | baseline / PD_classic / 0.1 | baseline / PD_classic / 2.0 | connected / PD_classic / 0.1 | connected / PD_classic / 2.0 | fragmented / PD_classic / 0.1 | fragmented / PD_classic / 2.0 | klasyfikacja |
|---|---|---|---|---|---|---|---|
| P1+P3 kooperacja, limit 5 | **warunkowo** | **nie** | **warunkowo** | **nie** | **tak** | **nie** | parametr kontekstowy (zależy od: układu przestrzeni, mobilności (prędkość)) |
| P1+P3 kooperacja, limit 15 | **tak** | **nie** | **warunkowo** | **nie** | **warunkowo** | **nie** | parametr kontekstowy (zależy od: układu przestrzeni, mobilności (prędkość)) |
| P1+P3 kooperacja, limit 50 | **n/d (limit nie działa)** | **nie** | **n/d (limit nie działa)** | **nie** | **n/d (limit nie działa)** | **nie** | nie odtworzono |
| P1+P3 kooperacja, limit 150 | **n/d (limit nie działa)** | **nie** | **n/d (limit nie działa)** | **nie** | **n/d (limit nie działa)** | **nie** | nie odtworzono |
| P1+P3 udział oszustów, limit 5 | **tak** | **nie** | **warunkowo** | **nie** | **tak** | **nie** | parametr kontekstowy (zależy od: układu przestrzeni, mobilności (prędkość)) |
| P1+P3 udział oszustów, limit 15 | **tak** | **nie** | **warunkowo** | **nie** | **warunkowo** | **nie** | parametr kontekstowy (zależy od: układu przestrzeni, mobilności (prędkość)) |
| P1+P3 udział oszustów, limit 50 | **n/d (limit nie działa)** | **nie** | **n/d (limit nie działa)** | **nie** | **n/d (limit nie działa)** | **nie** | nie odtworzono |
| P1+P3 udział oszustów, limit 150 | **n/d (limit nie działa)** | **nie** | **n/d (limit nie działa)** | **nie** | **n/d (limit nie działa)** | **nie** | nie odtworzono |
| P1+P3 zysk oszustów, limit 5 | **warunkowo** | **nie** | **warunkowo** | **nie** | **warunkowo** | **nie** | parametr kontekstowy (zależy od: mobilności (prędkość)) |
| P1+P3 zysk oszustów, limit 15 | **warunkowo** | **nie** | **warunkowo** | **nie** | **warunkowo** | **nie** | parametr kontekstowy (zależy od: mobilności (prędkość)) |
| P1+P3 zysk oszustów, limit 50 | **n/d (limit nie działa)** | **nie** | **n/d (limit nie działa)** | **nie** | **n/d (limit nie działa)** | **nie** | nie odtworzono |
| P1+P3 zysk oszustów, limit 150 | **n/d (limit nie działa)** | **nie** | **n/d (limit nie działa)** | **nie** | **n/d (limit nie działa)** | **nie** | nie odtworzono |

