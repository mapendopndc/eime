# Timber Column Design Calculation
## Axial Compression - CSA O86:24

*Calculation Date: January 26, 2026*

## 1. Design Parameters

### Material
- Species: Douglas Fir-Larch
- Grade: 20f-E
- Service Condition: Dry-service conditions

### Geometry
- Column Height: 4.00 m
- Section: 175 mm × 304 mm
- Effective Length (X-axis): 4.00 m
- Effective Length (Y-axis): 4.00 m

### Material Properties (CSA O86-24 Table 7.2)
- Specified compression strength, f_c = 30.2 MPa
- Modulus of elasticity, E = 12400 MPa

### Design Factors
- Service condition factor (compression), K_Sc = 1.00
- Service condition factor (modulus), K_SE = 1.00
- System factor, K_H = 1.00
- Treatment factor, K_T = 1.00
- Resistance factor (compression), φ_c = 0.80

## 2. Applied Forces

### Unfactored Loads
- Dead Load: 80.0 kN
- Live Load: 50.0 kN

### Load Factors (NBC 2020)
- Dead load factor, α_D = 1.25
- Live load factor, α_L = 1.50

### Factored Compression Load
$$
P_f = \alpha_D \cdot P_D + \alpha_L \cdot P_L = 1.25 \times 80.0 + 1.50 \times 50.0 = 175.0 \text{ kN}
$$

### Load Duration
- Long-term load (dead): 61.5 dimensionless%
- Standard-term load (live): 38.5 dimensionless%

## 3. Resistance Calculations


### Compression Resistance - X-Axis Buckling


**Long Duration Factor**

$$
\begin{align*}
K_D &= 1.0 - 0.50 \log_{10}(P_L/P_S) \ge 0.65 \\ &= 1.0 - 0.50 \log_{10}(61.54/38.46) \ge 0.65 \\ &= 0.90 \tag{CSA O86:24 cl.5.3.2.2} \\ \text{where,} \\
P_L &= \text{specified long-term load}  \\
P_S &= \text{specified standard-term load}
\end{align*}
$$


**Modified Compression Strength**

$$
\begin{align*}
F_c &= f_c \cdot K_D \cdot K_H \cdot K_{{Sc}} \cdot K_T \\ &= 30.20 \, \text{MPa} \cdot 0.90 \cdot 1.00 \cdot 1.00 \cdot 1.00 \\ &= 27.12 \, \text{MPa} \tag{CSA O86:24 7.5.8.5} \\ \text{where,} \\
f_c &= \text{specified compression strength}  \\
K_D &= \text{load-duration factor}  \\
K_H &= \text{system factor}  \\
K_{{Sc}} &= \text{service condition factor}  \\
K_T &= \text{treatment factor}
\end{align*}
$$


**Compression Size Factor**

$$
\begin{align*}
K_{Zcg} &= 0.68 \cdot \left(Z\right)^{-0.13} \\ &= 0.68 \cdot \left(0.21 \, \text{m}^{3}\right)^{-0.13} \\ &= 0.83 \tag{CSA O86:24 7.5.8.5} \\ \text{where,} \\
Z &= \text{member volume, m³}  \\ \\ K_{Zcg} \leq 1.0&= 0.83 \leq 1.00 \\ \text{Check} &= \text{Pass}
\end{align*}
$$


**Compression Slenderness Ratio**

$$
\begin{align*}
C_C &= \frac{L_e}{w} \\ &= \frac{4000.00 \, \text{mm}}{0.30 \, \text{m}} \\ &= 13.16 \tag{CSA O86:24 7.5.8.2} \\ \text{where,} \\
L_e &= \text{effective length associated with width}  \\
w &= \text{width}
\end{align*}
$$


**Slenderness Factor**

$$
\begin{align*}
K_c &= \left[ 1.0 + \frac{F_c \cdot K_{{Zcg}} \cdot C_C^3}{35 \cdot E_{{05}} \cdot K_{{SE}} \cdot K_T} \right]^{-1} \\ &= \left[ 1.0 + \frac{27.12 \, \text{MPa} \cdot 0.83 \cdot 13.16^3}{35 \cdot 10540.00 \, \text{MPa} \cdot 1.00 \cdot 1.00} \right]^{-1} \\ &= 0.88 \tag{CSA O86:24 7.5.8.6} \\ \text{where,} \\
F_c &= \text{factored strength in compression}  \\
K_{{Zcg}} &= \text{compression size factor}  \\
C_C &= \text{compression slenderness ratio}  \\
E_{{05}} &= \text{fifth percentile modulus of elasticity}  \\
K_{{SE}} &= \text{service condition factor}  \\
K_T &= \text{treatment factor}
\end{align*}
$$


**Compression Resistance**

$$
\begin{align*}
P_r &= \phi \cdot F_c \cdot A \cdot K_{{Zcg}} \cdot K_C \\ &= 0.80 \cdot 27.12 \, \text{MPa} \cdot 0.05 \, \text{m}^{2} \cdot 0.83 \cdot 0.88 \\ &= 842386.93 \, \text{N} \tag{CSA O86:24 7.5.8.5} \\ \text{where,} \\
\phi &= \text{compression resistance modification factor}  \\
F_c &= \text{factored strength in compression}  \\
A &= \text{cross-sectional area, mm²}  \\
K_{{Zcg}} &= \text{compression size factor}  \\
K_C &= \text{compression slenderness factor}
\end{align*}
$$


### Compression Resistance - Y-Axis Buckling


**Compression Slenderness Ratio**

$$
\begin{align*}
C_C &= \frac{L_e}{w} \\ &= \frac{4000.00 \, \text{mm}}{0.18 \, \text{m}} \\ &= 22.86 \tag{CSA O86:24 7.5.8.2} \\ \text{where,} \\
L_e &= \text{effective length associated with width}  \\
w &= \text{width}
\end{align*}
$$


**Slenderness Factor**

$$
\begin{align*}
K_c &= \left[ 1.0 + \frac{F_c \cdot K_{{Zcg}} \cdot C_C^3}{35 \cdot E_{{05}} \cdot K_{{SE}} \cdot K_T} \right]^{-1} \\ &= \left[ 1.0 + \frac{27.12 \, \text{MPa} \cdot 0.83 \cdot 22.86^3}{35 \cdot 10540.00 \, \text{MPa} \cdot 1.00 \cdot 1.00} \right]^{-1} \\ &= 0.58 \tag{CSA O86:24 7.5.8.6} \\ \text{where,} \\
F_c &= \text{factored strength in compression}  \\
K_{{Zcg}} &= \text{compression size factor}  \\
C_C &= \text{compression slenderness ratio}  \\
E_{{05}} &= \text{fifth percentile modulus of elasticity}  \\
K_{{SE}} &= \text{service condition factor}  \\
K_T &= \text{treatment factor}
\end{align*}
$$


**Compression Resistance**

$$
\begin{align*}
P_r &= \phi \cdot F_c \cdot A \cdot K_{{Zcg}} \cdot K_C \\ &= 0.80 \cdot 27.12 \, \text{MPa} \cdot 0.05 \, \text{m}^{2} \cdot 0.83 \cdot 0.58 \\ &= 554751.86 \, \text{N} \tag{CSA O86:24 7.5.8.5} \\ \text{where,} \\
\phi &= \text{compression resistance modification factor}  \\
F_c &= \text{factored strength in compression}  \\
A &= \text{cross-sectional area, mm²}  \\
K_{{Zcg}} &= \text{compression size factor}  \\
K_C &= \text{compression slenderness factor}
\end{align*}
$$

## 4. Design Checks

### Compression Check (X-Axis Buckling)
$$
\frac{P_f}{P_r} = \frac{175.0}{842.39} = 0.208 \le 1.0 \quad \checkmark
$$

## 5. Summary

**Material:** Douglas Fir-Larch 20f-E

**Section:** 175 mm × 304 mm

**Height:** 4.00 m

**Factored Load:** 175.0 kN

**Compression Resistance:** 842.39 kN

**Utilization:** 20.8%

**Design Status:** PASS ✓
