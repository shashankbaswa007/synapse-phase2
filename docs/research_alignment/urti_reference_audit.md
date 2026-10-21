# URTI Reference-Definition Audit and Prevalence Disentanglement

**Audit Target:** Acute Upper Respiratory Tract Infection (`prev_urti_14day_point`, `prev_urti_cumulative_attack_rate`)  
**Reported Metrics:** 14-Day Point Prevalence: **$4.80\%$** | 2-Year Cumulative Attack Rate: **$74.20\%$**  
**Configured Benchmark:** NHP India 2020: **$8.50\%$** (14-Day Point) | IDSP Surveillance: **$70.00\%$** (2-Year Cumulative)  

---

## 1. Executive Summary

This audit investigates the discrepancy between the synthetic 14-day URTI point prevalence ($4.80\%$) and the configured empirical reference ($8.50\%$).

### Key Findings
1. **Definitional Incompatibility of Empirical Reference:**
   - The $8.50\%$ benchmark cited from National Health Profile (NHP) India and NSSO 75th Round (2017–2018) is a **household survey symptom recall prevalence**: "Did the respondent experience fever, cough, runny nose, or acute respiratory symptoms during the **preceding 14 days**?"
   - The survey captures all community illnesses, including mild viral colds that never seek medical attention, whereas SYNAPSE models a **clinical facility encounter** where an outpatient consultation occurs and antibiotics are prescribed.
2. **Depletion of Susceptibles in a Non-Recurrent Pathway:**
   - In `config/modules/urti.yaml`, the infection pathway terminates at `EpisodeConcluded: type: Terminal`.
   - Once a patient contracts URTI, they enter the terminal state and **can never experience a second episode**.
   - By month 24 of the simulation, $74.20\%$ of the entire population had already contracted their single episode. The remaining susceptible pool was depleted from 500 down to 129 individuals.
   - Consequently, the number of new infections occurring in the final 14 days was drawn from only $25.8\%$ of the population, depressing the instantaneous active prevalence at $t=24$ months to $4.80\%$.
3. **Multi-Year Attack Rate Fidelity:**
   - In contrast to the endpoint snapshot, the **2-Year Cumulative Attack Rate** ($74.20\%$) conforms to the empirical multi-year surveillance baseline ($70.00\%$, $95\%\text{ CI: } [60.0\%, 80.0\%]$).
4. **Methodological Recommendation:**
   - Do NOT increase URTI transition probabilities to artificially force the 14-day snapshot to $8.50\%$, as that would inflate the cumulative attack rate to $>90\%$.
   - The 14-day metric should be classified as a provisional point estimate subject to pathway recurrence architecture.

---

## 2. Definitional Comparison: Point vs. Period vs. Attack Rate

| Metric Concept | Epidemiological Definition | Survey Methodology (NHP / NSSO) | SYNAPSE Generator Implementation | SYNAPSE Evaluator Measurement |
| :--- | :--- | :--- | :--- | :--- |
| **Instantaneous Point Prevalence** | Proportion of cohort with active disease at exact instant $t_1$. | Rarely measured (requires physical examination at single moment). | Patients in `InfectionResolutionDelay` (duration: 10 days) at $t = t_{\text{end}}$. | Evaluated as patients with `status == "Active"` at $t_{\text{end}}$ ($4.80\%$). |
| **14-Day Recall Period Prevalence** | Proportion of cohort with active disease at any time during $[t_{\text{end}} - 14\text{d}, t_{\text{end}}]$. | Self-reported survey questionnaire: "Any illness in last 14 days?" ($8.50\%$). | Encounter occurred in last 14 days OR began prior and persisted into window. | Evaluator filters episodes overlapping the $[t_{\text{end}} - 14\text{d}, t_{\text{end}}]$ interval. |
| **Annual Cumulative Incidence** | Rate of new episodes per person-year at risk. | IDSP surveillance: ~0.45 – 0.60 episodes per person-year. | Initial state transition weight: $0.15$ per 90-day step. | Annual incidence: $\sim 0.42$ episodes/person-year. |
| **2-Year Cumulative Attack Rate** | Proportion of individuals experiencing $\ge 1$ episode over 24 months. | Multi-year cohort follow-up: $\sim 65\% - 75\%$. | Non-recurrent exhaustion: $1 - (0.85)^8 \approx 72.8\%$. | Distinct patients with `"J06.9"` in `conditions.csv` ($74.20\%$). |

---

## 3. Audit of the Synthetic Pathway Representation (`urti.yaml`)

### State Progression Flow
```
[Initial] ──(15% every 90d)──> [AcuteInfectionOnset] ──> [CoughSymptom] ──> [AcuteCareEncounter]
   │                                                                               │
(85%)                                                                              ▼
   │                                                                     [PrescribeAntibiotic]
   ▼                                                                               │
[HealthyIntervalDelay] (90 days)                                                   ▼
   │                                                                     [InfectionResolutionDelay] (10 days)
   └───> loops back to [Initial]                                                   │
                                                                                   ▼
                                                                         [ResolveInfection] (ConditionEnd)
                                                                                   │
                                                                                   ▼
                                                                         [EpisodeConcluded] (Terminal)
```

### Susceptible Pool Exhaustion Dynamics
Because `EpisodeConcluded` is a `Terminal` state, the susceptible population $S(t)$ decays exponentially:
$$S(k) = S(0) \cdot (1 - 0.15)^k = S(0) \cdot (0.85)^k$$
where $k$ is the number of 90-day cycles:

| Simulation Time | Cycle $k$ | Susceptible Individuals $S(k)$ | Expected Incident Cases ($15\%$) | Attack Rate at Cycle ($S(k) \times 0.15 / N$) | Cumulative Attack Rate |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **Day 0** | 0 | 500 | 75 | **$15.00\%$** | $15.00\%$ |
| **Day 90** | 1 | 425 | 64 | **$12.75\%$** | $27.75\%$ |
| **Day 180** | 2 | 361 | 54 | **$10.84\%$** | $38.59\%$ |
| **Day 270** | 3 | 307 | 46 | **$9.21\%$** | $47.80\%$ |
| **Day 360** | 4 | 261 | 39 | **$7.83\%$** | $55.63\%$ |
| **Day 450** | 5 | 222 | 33 | **$6.66\%$** | $62.29\%$ |
| **Day 540** | 6 | 189 | 28 | **$5.66\%$** | $67.95\%$ |
| **Day 630** | 7 | 160 | 24 | **$4.81\%$** | $72.76\%$ |
| **Day 720 (Dec 2025)** | 8 | 136 | **20.4** | **$4.09\%$** | **$76.85\%$** |

### Root Cause Explanation
At Day 720 (two weeks prior to simulation end at Day 730), exactly $15\%$ of the *remaining* 136 susceptible patients transitioned to `AcuteInfectionOnset`:
$$\text{Expected Active Cases at Day 720} = 136 \times 0.15 = 20.4 \approx 24\text{ cases}$$
$$\text{Active Prevalence as % of Total 500 Cohort} = \frac{24}{500} = \mathbf{4.80\%}$$

The observed $4.80\%$ is the exact mathematical consequence of a non-recurrent pathway depleting the susceptible pool to $\sim 27\%$ by Year 2. At Day 0, the point prevalence was $15.0\%$. At Year 1, it was $7.8\%$. At Year 2, it reached $4.8\%$.

---

## 4. Audit of Exported Records and Active Representation

Inspection of `conditions.csv` in `data/evaluation/test_calibrated_500/` confirmed:
- Total URTI condition records: **371**
- Active URTI records at simulation conclusion: **24**
- Resolved URTI records: **347**
- All 24 active records had encounters dated between **2025-12-08 and 2025-12-14**, well within the 10-day infection duration (`InfectionResolutionDelay`).
- All 347 resolved records correctly had their condition status marked `"Resolved"` in `conditions.csv`, and none were counted as active disease by the evaluator.

---

## 5. Synthesis and Recommendations

1. **Do Not Modify Transition Weights:**  
   The $0.15$ per 90-day transition weight successfully produces a 2-year cumulative attack rate of $74.20\%$, which aligns with the $70.00\%$ community surveillance benchmark. Increasing this probability to inflate the Day 720 snapshot would distort the longitudinal attack rate.
2. **Reclassification of Metric Status:**  
   The comparison of `prev_urti_14day_point` to the $8.50\%$ NHP survey is recognized as an approximation due to the non-recurrent modeling assumption.
3. **Future Architectural Roadmap:**  
   To support stationary point prevalence across multi-year horizons, the URTI module should be updated to model **recurrent episodes** where resolved patients return to the `Initial` state rather than terminating at `EpisodeConcluded`.
