# Timber Beam Design Calculation
## Calculator Approach - CSA O86:24
*Calculation Date: January 26, 2026*

---
## 1. Design Parameters
### Geometry
- Span: $L = 6.0$ m
- Beam spacing: $s = 400.0$ mm
- Section: $130 \times 456$ mm

### Material Properties
- Species: Douglas Fir-Larch
- Grade: 20f-E
- Specified bending strength: $f_b = 25.6$ MPa
- Specified shear strength: $f_v = 2.0$ MPa
- Modulus of elasticity: $E = 12400$ MPa
- Service condition: Dry-service conditions
- Treatment: Untreated

### Loading
- Dead load: $D = 1.5$ kPa
- Live load: $L = 1.9$ kPa
- Factored UDL: $w_f = 1.890$ kN/m

## 2. Applied Forces
For a simply supported beam:
$$
\begin{align}
M_f &= \frac{w_f L^2}{8} = 8.51 \text{ kNm} \\
V_f &= \frac{w_f L}{2} = 5.67 \text{ kN}
\end{align}
$$

## 3. Resistance Calculations


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
F_b &= f_b \cdot K_D \cdot K_H \cdot K_{{Sb}} \cdot K_T \\ &= 25.60 \, \text{MPa} \cdot 1.05 \cdot 1.00 \cdot 1.00 \cdot 1.00 \\ &= 26.91 \, \text{MPa} \tag{CSA O86:24 7.5.6.6.1} \\ \text{where,} \\
f_b &= \text{specified bending strength}  \\
K_D &= \text{load-duration factor}  \\
K_H &= \text{system factor}  \\
K_{{Sb}} &= \text{service condition factor}  \\
K_T &= \text{treatment factor}
\end{align*}
$$


**Bending Size Factor**

$$
\begin{align*}
K_{Zbg} &= \left(\frac{130}{b}\right)^{0.1} \left(\frac{610}{d}\right)^{0.1} \left(\frac{9100}{L}\right)^{0.1} \\ &= \left(\frac{130}{130.00 \, \text{mm}}\right)^{0.1} \left(\frac{610}{456.00 \, \text{mm}}\right)^{0.1} \left(\frac{9100}{6000.00 \, \text{mm}}\right)^{0.1} \\ &= 1.07 \tag{CSA O86:24 7.5.6.6.1} \\ \text{where,} \\
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


**Moment Resistance a)**

$$
\begin{align*}
M_{r,a} &= \phi \cdot F_b \cdot S \cdot K_x \cdot K_{{Zbg}} \\ &= 0.90 \cdot 26.91 \, \text{MPa} \cdot 4505280.00 \, \text{mm}^{3} \cdot 1.00 \cdot 1.07 \\ &= 117.13 \, \text{kN} \cdot \text{m} \tag{CSA O86:24 7.5.6.6.1 a)} \\ \text{where,} \\
\phi &= \text{resistance factor}  \\
F_b &= \text{modified bending strength}  \\
S &= \text{section modulus}  \\
K_x &= \text{curvature factor}  \\
K_{{Zbg}} &= \text{size factor}
\end{align*}
$$


### Shear Resistance


**Modified Shear Strength**

$$
\begin{align*}
F_v &= f_v \cdot K_D \cdot K_H \cdot K_{{Sv}} \cdot K_T \\ &= 2.00 \, \text{MPa} \cdot 1.05 \cdot 1.00 \cdot 1.00 \cdot 1.00 \\ &= 2.10 \, \text{MPa} \tag{CSA O86:24 7.5.7.3 b)} \\ \text{where,} \\
f_v &= \text{specified shear strength}  \\
K_D &= \text{load-duration factor}  \\
K_H &= \text{system factor}  \\
K_{{Sv}} &= \text{service condition factor}  \\
K_T &= \text{treatment factor}
\end{align*}
$$


**Shear Resistance**

$$
\begin{align*}
V_r &= \phi \cdot F_v \cdot \frac{2 \cdot A_g}{3} \\ &= 0.90 \cdot 2.10 \, \text{MPa} \cdot \frac{2 \cdot 59280.00 \, \text{mm}^{2}}{3} \\ &= 74787.49 \, \text{N} \tag{CSA O86:24 7.5.7.3 b)} \\ \text{where,} \\
\phi &= \text{shear resistance modification factor}  \\
F_v &= \text{factored strength in shear}  \\
A_g &= \text{gross cross-sectional area, mm²}
\end{align*}
$$

## 4. Design Checks
### Bending Check
$$
\frac{M_f}{M_r} = \frac{8.51}{117.13} = 0.073 \le 1.0 \quad \checkmark
$$

### Shear Check
$$
\frac{V_f}{V_r} = \frac{5.67}{74.79} = 0.076 \le 1.0 \quad \checkmark
$$

## 5. Summary
- **Maximum Utilization:** 7.6%
- **Design Status:** **PASS**

The $130 \times 456$ mm 20f-E Douglas Fir-Larch glulam beam is adequate for the applied loading.

---
*Calculation performed using EIME TimberBeamCalculator*
