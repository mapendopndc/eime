# Timber Beam Design Calculation
## Batch Calculator Approach - CSA O86:24 with NBCC Load Combinations
*Calculation Date: January 27, 2026*

---
## 1. Design Parameters
### Geometry
- Span: $L = 6.0$ m
- Beam spacing: $s = 400.0$ mm
- Section: $130 \times 456$ mm

### Material Properties
- Species: Douglas Fir-Larch
- Grade: 20f-E
- Service condition: Dry-service conditions
- Treatment: Untreated
*Material properties loaded automatically from CSA O86:24 Table 7.2*

### Nominal Loading
**Distributed Loads:**
- D: $1.5$ kPa
- L: $1.9$ kPa
- S: $1.2$ kPa

**Axial Loads (Compression):**
- D: $5.0$ kN
- L: $10.0$ kN
- S: $8.0$ kN

## 2. NBCC 2020 ULS Load Combinations
Generated **4** load combinations:

| Combination | Factored Load (kPa) |
|-------------|---------------------|
| 1.25D+1.5L | 4.725 |
| 1.25D+1.5S | 3.675 |
| 1.25D+1.5L+0.5S | 5.325 |
| 1.25D+1.5S+0.5L | 4.625 |

## 3. Applied Forces (Governing Combination)
Governing combination: **1.25D+1.5L+0.5S**

For a simply supported beam with axial compression:
$$
\begin{align}
M_f &= \frac{w_f L^2}{8} = 9.58 \text{ kNm} \\
V_f &= \frac{w_f L}{2} = 6.39 \text{ kN} \\
P_f &= 25.25 \text{ kN}
\end{align}
$$

## 4. Resistance Calculations

Showing calculations for the first load combination.

### Bending Resistance


**Long Duration Factor**

$$
\begin{align*}
K_D &= 1.0 - 0.50 \log_{10}(P_L/P_S) \ge 0.65 \\ &= 1.0 - 0.50 \log_{10}(44.12/55.88) \ge 0.65 \\ &= 1.05 \tag{CSA O86:24 cl.5.3.2.2} \\ \text{where,} \\
P_L &= \text{specified long-term load}  \\
P_S &= \text{specified standard-term load}
\end{align*}
$$


**Modified Bending Strength**

$$
\begin{align*}
F_b &= f_b \cdot K_D \cdot K_H \cdot K_{Sb} \cdot K_T \\ &= 25.60 \, \text{MPa} \cdot 1.05 \cdot 1.00 \cdot 1.00 \cdot 1.00 \\ &= 26.91 \, \text{MPa} \tag{CSA O86:24 7.5.6.6.1} \\ \text{where,} \\
f_b &= \text{specified bending strength}  \\
K_D &= \text{load-duration factor}  \\
K_H &= \text{system factor}  \\
K_{Sb} &= \text{service condition factor}  \\
K_T &= \text{treatment factor}
\end{align*}
$$


**Slenderness Ratio**

$$
\begin{align*}
\lambda &= \sqrt{\frac{L_u \cdot d}{b^2}} \\ &= \sqrt{\frac{6.00 \, \text{m} \cdot 456.00 \, \text{mm}}{130.00 \, \text{mm}^2}} \\ &= 0.40 \, m^{0}.5 / mm^{0}.5 \tag{CSA O86:24 7.5.6.5.2} \\ \text{where,} \\
L_u &= \text{unbraced segment length}  \\
d &= \text{depth}  \\
b &= \text{width}
\end{align*}
$$


**Slenderness Ratio Limit**

$$
\begin{align*}
\lambda_e &= \sqrt{\frac{0.97 \cdot E \cdot K_{SE} \cdot K_T}{F_b}} \\ &= \sqrt{\frac{0.97 \cdot 12400.00 \, \text{MPa} \cdot 1.00 \cdot 1.00}{26.91 \, \text{MPa}}} \\ &= 21.14 \tag{CSA O86:24 7.5.6.5.2 b)} \\ \text{where,} \\
E &= \text{specified modulus of elasticity}  \\
K_{SE} &= \text{service condition factor}  \\
K_T &= \text{treatment factor}  \\
F_b &= \text{modified bending strength}
\end{align*}
$$


**Lateral Stability Factor for Unbraced Members**

$$
\begin{align*}
\text{Condition:} & \quad \lambda \leq 10 \\ K_L &= \begin{aligned}[t]
K_L &= 1.0 \\ &= 1.0 \\ &= 1.00 \tag{CSA O86:24 7.5.6.5.2 a)}
\end{aligned} \\ \text{where,} \\
\lambda &= \text{slenderness ratio}  \\
\lambda_e &= \text{slenderness ratio limit}  \\
K_L &= \text{lateral stability factor output a)}  \\
K_L &= \text{lateral stability factor output b)}  \\
K_L &= \text{lateral stability factor output c)}  \\
K_L &= \text{lateral stability factor output d)}  \\ \\ K_L \leq 1.01&= 0.96 \leq 1.01 \\ \text{Check} &= \text{Pass}
\end{align*}
$$


**Bending Size Factor**

$$
\begin{align*}
K_{Zbg} &= \left(\frac{130}{b}\right)^{0.1} \left(\frac{610}{d}\right)^{0.1} \left(\frac{9100}{L}\right)^{0.1} \\ &= \left(\frac{130}{130.00 \, \text{mm}}\right)^{0.1} \left(\frac{610}{456.00 \, \text{mm}}\right)^{0.1} \left(\frac{9100}{6.00 \, \text{m}}\right)^{0.1} \\ &= 1.07 \tag{CSA O86:24 7.5.6.6.1} \\ \text{where,} \\
b &= \text{width}  \\
d &= \text{depth}  \\
L &= \text{length}  \\ \\ K_{Zbg} \leq 1.3&= 1.07 \leq 1.30 \\ \text{Check} &= \text{Pass}
\end{align*}
$$


**Section Modulus**

$$
\begin{align*}
S &= \frac{b \cdot d^{2}}{6} \\ &= \frac{130.00 \, \text{mm} \cdot 456.00 \, \text{mm}^{2}}{6} \\ &= 4505280.00 \, \text{mm}^{3}  \\ \text{where,} \\
b &= \text{width}  \\
d &= \text{depth}
\end{align*}
$$


**Moment Resistance**

$$
\begin{align*}
\text{Condition:} & \quad K_L \leq 0.9999 \\ M_r &= \begin{aligned}[t]
M_{r,b} &= \min(M_{{r1}}, M_{{r2}}) \\ &= \min(117130316.40 \, \text{mm} \cdot \text{N}, 104356229.35 \, \text{mm} \cdot \text{N}) \\ &= 104356229.35 \, \text{mm} \cdot \text{N} \tag{CSA O86:24 7.5.6.6.1 b)}
\end{aligned} \\ \text{where,} \\
K_L &= \text{lateral stability factor}  \\
M_r &= \text{resistance A (braced)}  \\
M_r &= \text{resistance B (unbraced)}  \\ \\ M_r > 8504999.999999998&= 104356229.35 \, \text{mm} \cdot \text{N} > 8505000.00 \, \text{mm} \cdot \text{N} \\ \text{Check} &= \text{Pass}
\end{align*}
$$

### Shear Resistance


**Long Duration Factor**

$$
\begin{align*}
K_D &= 1.0 - 0.50 \log_{10}(P_L/P_S) \ge 0.65 \\ &= 1.0 - 0.50 \log_{10}(44.12/55.88) \ge 0.65 \\ &= 1.05 \tag{CSA O86:24 cl.5.3.2.2} \\ \text{where,} \\
P_L &= \text{specified long-term load}  \\
P_S &= \text{specified standard-term load}
\end{align*}
$$


**Shear-Load Coefficient**

$$
\begin{align*}
C_V &= 1.825 \cdot W_f \left( \frac{L}{\sum G} \right)^{0.2} \\ &= 1.825 \cdot 11340.00 \, \text{N} \left( \frac{6000.00 \, \text{mm}}{70322862513128401272832.00 \, \text{mm} \cdot \text{N}^{5}} \right)^{0.2} \\ &= 3.18 \tag{CSA O86:24 7.5.7.6 d) i)} \\ \text{where,} \\
W_f &= \text{total factored loads on beam}  \\
L &= \text{length of beam}  \\
\sum G &= \text{sum of G factors}
\end{align*}
$$


**Modified Shear Strength**

$$
\begin{align*}
F_v &= f_v \cdot K_D \cdot K_H \cdot K_{Sv} \cdot K_T \\ &= 2.00 \, \text{MPa} \cdot 1.05 \cdot 1.00 \cdot 1.00 \cdot 1.00 \\ &= 2.10 \, \text{MPa} \tag{CSA O86:24 7.5.7.3 b)} \\ \text{where,} \\
f_v &= \text{specified shear strength}  \\
K_D &= \text{load-duration factor}  \\
K_H &= \text{system factor}  \\
K_{Sv} &= \text{service condition factor}  \\
K_T &= \text{treatment factor}
\end{align*}
$$


**Total Shear Resistance**

$$
\begin{align*}
W_r &= \phi \cdot F_v \cdot 0.48 \cdot A_g \cdot C_V \cdot \left(Z\right)^{-0.18} \\ &= 0.90 \cdot 2.10 \, \text{MPa} \cdot 0.48 \cdot 59280.00 \, \text{mm}^{2} \cdot 3.18 \cdot \left(355680000.00 \, \text{mm}^{3}\right)^{-0.18} \\ &= 4943.76 \, \text{MPa} \cdot mm^{1}.46 \tag{CSA O86:24 7.5.7.3 a)} \\ \text{where,} \\
\phi &= \text{shear resistance modification factor}  \\
F_v &= \text{factored strength in shear}  \\
A_g &= \text{gross cross-sectional area, mm²}  \\
C_V &= \text{shear load coefficient}  \\
Z &= \text{beam volume, mm³}
\end{align*}
$$


**Shear Resistance**

$$
\begin{align*}
V_r &= \phi \cdot F_v \cdot \frac{2 \cdot A_g}{3} \\ &= 0.90 \cdot 2.10 \, \text{MPa} \cdot \frac{2 \cdot 59280.00 \, \text{mm}^{2}}{3} \\ &= 74787.49 \, \text{N} \tag{CSA O86:24 7.5.7.3 b)} \\ \text{where,} \\
\phi &= \text{shear resistance modification factor}  \\
F_v &= \text{factored strength in shear}  \\
A_g &= \text{gross cross-sectional area, mm²}  \\
V_f &= \text{factored shear force}  \\ \\ V_r > 5670.0&= 74787.49 \, \text{N} > 5670.00 \, \text{N} \\ \text{Check} &= \text{Pass}
\end{align*}
$$

### Compression Resistance


**Long Duration Factor**

$$
\begin{align*}
K_D &= 1.0 - 0.50 \log_{10}(P_L/P_S) \ge 0.65 \\ &= 1.0 - 0.50 \log_{10}(44.12/55.88) \ge 0.65 \\ &= 1.05 \tag{CSA O86:24 cl.5.3.2.2} \\ \text{where,} \\
P_L &= \text{specified long-term load}  \\
P_S &= \text{specified standard-term load}
\end{align*}
$$


**Modified Compression Strength**

$$
\begin{align*}
F_c &= f_c \cdot K_D \cdot K_H \cdot K_{Sc} \cdot K_T \\ &= 30.20 \, \text{MPa} \cdot 1.05 \cdot 1.00 \cdot 1.00 \cdot 1.00 \\ &= 31.75 \, \text{MPa} \tag{CSA O86:24 7.5.8.5} \\ \text{where,} \\
f_c &= \text{specified compression strength}  \\
K_D &= \text{load-duration factor}  \\
K_H &= \text{system factor}  \\
K_{Sc} &= \text{service condition factor}  \\
K_T &= \text{treatment factor}
\end{align*}
$$


**Compression Size Factor**

$$
\begin{align*}
K_{Zcg} &= 0.68 \cdot \left(Z\right)^{-0.13} \\ &= 0.68 \cdot \left(355680.00 \, \text{m} \cdot \text{mm}^{2}\right)^{-0.13} \\ &= 0.78 \tag{CSA O86:24 7.5.8.5} \\ \text{where,} \\
Z &= \text{member volume, m³}  \\ \\ K_{Zcg} \leq 1.0&= 0.78 \leq 1.00 \\ \text{Check} &= \text{Pass}
\end{align*}
$$


**Compression Slenderness Ratio**

$$
\begin{align*}
C_C &= \frac{L_e}{w} \\ &= \frac{6.00 \, \text{m}}{130.00 \, \text{mm}} \\ &= 46.15 \tag{CSA O86:24 7.5.8.2} \\ \text{where,} \\
L_e &= \text{effective length associated with width}  \\
w &= \text{width}
\end{align*}
$$


**Slenderness Factor**

$$
\begin{align*}
K_c &= \left[ 1.0 + \frac{F_c \cdot K_{Zcg} \cdot C_C^3}{35 \cdot E_{05} \cdot K_{SE} \cdot K_T} \right]^{-1} \\ &= \left[ 1.0 + \frac{31.75 \, \text{MPa} \cdot 0.78 \cdot 46.15^3}{35 \cdot 10788.00 \, \text{MPa} \cdot 1.00 \cdot 1.00} \right]^{-1} \\ &= 0.13 \tag{CSA O86:24 7.5.8.6} \\ \text{where,} \\
F_c &= \text{factored strength in compression}  \\
K_{Zcg} &= \text{compression size factor}  \\
C_C &= \text{compression slenderness ratio}  \\
E_{05} &= \text{fifth percentile modulus of elasticity}  \\
K_{SE} &= \text{service condition factor}  \\
K_T &= \text{treatment factor}
\end{align*}
$$


**Compression Resistance**

$$
\begin{align*}
P_r &= \phi \cdot F_c \cdot A \cdot K_{Zcg} \cdot K_C \\ &= 0.80 \cdot 31.75 \, \text{MPa} \cdot 59280.00 \, \text{mm}^{2} \cdot 0.78 \cdot 0.13 \\ &= 157618.98 \, \text{N} \tag{CSA O86:24 7.5.8.5} \\ \text{where,} \\
\phi &= \text{compression resistance modification factor}  \\
F_c &= \text{factored strength in compression}  \\
A &= \text{cross-sectional area, mm²}  \\
K_{Zcg} &= \text{compression size factor}  \\
K_C &= \text{compression slenderness factor}  \\
P_f &= \text{factored compressive force}  \\ \\ P_r > 21250.0&= 157618.98 \, \text{N} > 21250.00 \, \text{N} \\ \text{Check} &= \text{Pass}
\end{align*}
$$

## 5. Batch Results Summary

Complete results for all load combinations:

*Note: Units are stripped in this table for display. M_r values are in N·mm, V_r in N.*

| Combination | beam_id | Bending_Util | Shear_Util | Compression_Util | worst_util |
|---|---|---|---|---|---|
| 1.25D+1.5L | 1.25D+1.5L | 0.0815 | 0.0758 | 0.1348 | 0.1348 |
| 1.25D+1.5S | 1.25D+1.5S | 0.0695 | 0.0652 | 0.1174 | 0.1174 |
| 1.25D+1.5L+0.5S | 1.25D+1.5L+0.5S | 0.0842 | 0.0776 | 0.1582 | 0.1582 |
| 1.25D+1.5S+0.5L | 1.25D+1.5S+0.5L | 0.0732 | 0.0674 | 0.1457 | 0.1457 |


## 6. Design Checks (Governing Case)
### Bending Check
$$
\frac{M_f}{M_r} = 0.084 \le 1.0 \quad \checkmark
$$

### Shear Check
$$
\frac{V_f}{V_r} = 0.078 \le 1.0 \quad \checkmark
$$

### Compression Check
$$
\frac{P_f}{P_r} = 0.158 \le 1.0 \quad \checkmark
$$

## 7. Summary
- **Load Combinations Analyzed:** 4
- **Governing Combination:** 1.25D+1.5L+0.5S
- **Maximum Bending Utilization:** 8.4%
- **Maximum Shear Utilization:** 7.8%
- **Maximum Compression Utilization:** 15.8%
- **Maximum Utilization:** 15.8%
- **Design Status:** **PASS**

The $130 \times 456$ mm 20f-E Douglas Fir-Larch glulam beam is adequate for all 4 NBCC load combinations including axial compression.

---
*Calculation performed using EIME TimberMemberDesign with NBCC 2020 load combinations*
