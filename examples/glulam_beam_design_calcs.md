# Glulam Beam Design Calculations

## Beam Information
- Section: 175 x 456 mm
- Material: 20f-E Douglas Fir-Larch
- Span: 8.0 m

## Load Combination: 1.25D+1.5L+1.0S

---


**Load Duration Factor**

$$
\begin{align*}
\text{Condition:} & \quad P_L/P_S \leq 1.0 \\ K_D &= 1.0 \\ \text{where,} \\
P_L/P_S &= \text{load ratio}  \\ \\ K_D \geq 0.65&= 1.00 \geq 0.65 \\ \text{Check} &= \text{Pass} \\ K_D < 1.15&= 1.00 < 1.15 \\ \text{Check} &= \text{Pass}
\end{align*}
$$


**Modified Bending Strength**

$$
\begin{align*}
F_b &= f_b \cdot K_D \cdot K_H \cdot K_{Sb} \cdot K_T \\ &= 25.60 \, \text{MPa} \cdot 1.00 \cdot 1.00 \cdot 1.00 \cdot 1.00 \\ &= 25.60 \, \text{MPa} \tag{CSA O86:24 7.5.6.6.1} \\ \text{where,} \\
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
\lambda &= \sqrt{\frac{L_u \cdot d}{b^2}} \\ &= \sqrt{\frac{8.00 \, \text{m} \cdot 456.00 \, \text{mm}}{175.00 \, \text{mm}^2}} \\ &= 0.35 \, m^{0}.5 / mm^{0}.5 \tag{CSA O86:24 7.5.6.5.2} \\ \text{where,} \\
L_u &= \text{unbraced segment length}  \\
d &= \text{depth}  \\
b &= \text{width}
\end{align*}
$$


**Slenderness Ratio Limit**

$$
\begin{align*}
\lambda_e &= \sqrt{\frac{0.97 \cdot E \cdot K_{SE} \cdot K_T}{F_b}} \\ &= \sqrt{\frac{0.97 \cdot 12400.00 \, \text{MPa} \cdot 1.00 \cdot 1.00}{25.60 \, \text{MPa}}} \\ &= 21.68 \tag{CSA O86:24 7.5.6.5.2 b)} \\ \text{where,} \\
E &= \text{specified modulus of elasticity}  \\
K_{SE} &= \text{service condition factor}  \\
K_T &= \text{treatment factor}  \\
F_b &= \text{modified bending strength}
\end{align*}
$$


**Lateral Stability Factor for Unbraced Members**

$$
\begin{align*}
\text{Condition:} & \quad \lambda \leq 10 \\ \begin{aligned}K_L &= 1.0 \\ &= 1.0 \\ &= 1.00 \tag{CSA O86:24 7.5.6.5.2 a)}\end{aligned} \\ \text{where,} \\
\lambda &= \text{slenderness ratio}  \\
\lambda_e &= \text{slenderness ratio limit}  \\
K_L &= \text{lateral stability factor output a)}  \\
K_L &= \text{lateral stability factor output b)}  \\
K_L &= \text{lateral stability factor output c)}  \\
K_L &= \text{lateral stability factor output d)}  \\ \\ K_L \leq 1.01&= 0.98 \leq 1.01 \\ \text{Check} &= \text{Pass}
\end{align*}
$$


**Bending Size Factor**

$$
\begin{align*}
K_{Zbg} &= \left(\frac{130}{b}\right)^{0.1} \left(\frac{610}{d}\right)^{0.1} \left(\frac{9100}{L}\right)^{0.1} \\ &= \left(\frac{130}{175.00 \, \text{mm}}\right)^{0.1} \left(\frac{610}{456.00 \, \text{mm}}\right)^{0.1} \left(\frac{9100}{8.00 \, \text{m}}\right)^{0.1} \\ &= 1.01 \tag{CSA O86:24 7.5.6.6.1} \\ \text{where,} \\
b &= \text{width}  \\
d &= \text{depth}  \\
L &= \text{length}  \\ \\ K_{Zbg} \leq 1.3&= 1.01 \leq 1.30 \\ \text{Check} &= \text{Pass}
\end{align*}
$$


**Section Modulus**

$$
\begin{align*}
S &= \frac{b \cdot d^{2}}{6} \\ &= \frac{175.00 \, \text{mm} \cdot 456.00 \, \text{mm}^{2}}{6} \\ &= 6064800.00 \, \text{mm}^{3}  \\ \text{where,} \\
b &= \text{width}  \\
d &= \text{depth}
\end{align*}
$$


**Moment Resistance**

$$
\begin{align*}
\text{Condition:} & \quad K_L \leq 0.9999 \\ \begin{aligned}M_{r,b} &= \min(M_{{r1}}, M_{{r2}}) \\ &= \min(141455920.29 \, \text{mm} \cdot \text{N}, 136739154.25 \, \text{mm} \cdot \text{N}) \\ &= 136739154.25 \, \text{mm} \cdot \text{N} \tag{CSA O86:24 7.5.6.6.1 b)}\end{aligned} \\ \text{where,} \\
K_L &= \text{lateral stability factor}  \\
M_r &= \text{resistance A (braced)}  \\
M_r &= \text{resistance B (unbraced)}  \\ \\ M_r > 354.96000000000004&= 136739154.25 \, \text{mm} \cdot \text{N} > 354.96 \, \text{mm} \cdot \text{N} \\ \text{Check} &= \text{Pass}
\end{align*}
$$


---


**Load Duration Factor**

$$
\begin{align*}
\text{Condition:} & \quad P_L/P_S \leq 1.0 \\ K_D &= 1.0 \\ \text{where,} \\
P_L/P_S &= \text{load ratio}  \\ \\ K_D \geq 0.65&= 1.00 \geq 0.65 \\ \text{Check} &= \text{Pass} \\ K_D < 1.15&= 1.00 < 1.15 \\ \text{Check} &= \text{Pass}
\end{align*}
$$


**Shear-Load Coefficient**

$$
\begin{align*}
C_V &= 1.825 \cdot W_f \left( \frac{L}{\sum G} \right)^{0.2} \\ &= 1.825 \cdot 354960.00 \, \text{N} \left( \frac{8000.00 \, \text{mm}}{1.00 \, \text{mm} \cdot \text{N}^{5}} \right)^{0.2} \\ &= 3908951.50 \tag{CSA O86:24 7.5.7.6 d) i)} \\ \text{where,} \\
W_f &= \text{total factored loads on beam}  \\
L &= \text{length of beam}  \\
\sum G &= \text{sum of G factors}
\end{align*}
$$


**Modified Shear Strength**

$$
\begin{align*}
F_v &= f_v \cdot K_D \cdot K_H \cdot K_{Sv} \cdot K_T \\ &= 2.00 \, \text{MPa} \cdot 1.00 \cdot 1.00 \cdot 1.00 \cdot 1.00 \\ &= 2.00 \, \text{MPa} \tag{CSA O86:24 7.5.7.3 b)} \\ \text{where,} \\
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
W_r &= \phi \cdot F_v \cdot 0.48 \cdot A_g \cdot C_V \cdot \left(Z\right)^{-0.18} \\ &= 0.90 \cdot 2.00 \, \text{MPa} \cdot 0.48 \cdot 79800.00 \, \text{mm}^{2} \cdot 3908951.50 \cdot \left(638400000.00 \, \text{mm}^{3}\right)^{-0.18} \\ &= 7009066777.00 \, \text{MPa} \cdot mm^{1}.46 \tag{CSA O86:24 7.5.7.3 a)} \\ \text{where,} \\
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
V_r &= \phi \cdot F_v \cdot \frac{2 \cdot A_g}{3} \\ &= 0.90 \cdot 2.00 \, \text{MPa} \cdot \frac{2 \cdot 79800.00 \, \text{mm}^{2}}{3} \\ &= 95760.00 \, \text{N} \tag{CSA O86:24 7.5.7.3 b)} \\ \text{where,} \\
\phi &= \text{shear resistance modification factor}  \\
F_v &= \text{factored strength in shear}  \\
A_g &= \text{gross cross-sectional area, mm²}  \\
V_f &= \text{factored shear force}  \\ \\ V_r > 177.48000000000002&= 95760.00 \, \text{N} > 177.48 \, \text{N} \\ \text{Check} &= \text{Pass}
\end{align*}
$$


---


**Load Duration Factor**

$$
\begin{align*}
\text{Condition:} & \quad P_L/P_S \leq 1.0 \\ K_D &= 1.0 \\ \text{where,} \\
P_L/P_S &= \text{load ratio}  \\ \\ K_D \geq 0.65&= 1.00 \geq 0.65 \\ \text{Check} &= \text{Pass} \\ K_D < 1.15&= 1.00 < 1.15 \\ \text{Check} &= \text{Pass}
\end{align*}
$$


**Modified Compression Strength**

$$
\begin{align*}
F_c &= f_c \cdot K_D \cdot K_H \cdot K_{Sc} \cdot K_T \\ &= 30.20 \, \text{MPa} \cdot 1.00 \cdot 1.00 \cdot 1.00 \cdot 1.00 \\ &= 30.20 \, \text{MPa} \tag{CSA O86:24 7.5.8.5} \\ \text{where,} \\
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
K_{Zcg} &= 0.68 \cdot \left(Z\right)^{-0.13} \\ &= 0.68 \cdot \left(638400.00 \, \text{m} \cdot \text{mm}^{2}\right)^{-0.13} \\ &= 0.72 \tag{CSA O86:24 7.5.8.5} \\ \text{where,} \\
Z &= \text{member volume, m³}  \\ \\ K_{Zcg} \leq 1.0&= 0.72 \leq 1.00 \\ \text{Check} &= \text{Pass}
\end{align*}
$$


**Compression Slenderness Ratio (Strong Axis)**

$$
\begin{align*}
C_{C,strong} &= \frac{L_{e,strong}}{d} \\ &= \frac{8.00 \, \text{m}}{456.00 \, \text{mm}} \\ &= 17.54 \tag{CSA O86:24 7.5.8.2} \\ \text{where,} \\
L_{e,strong} &= \text{effective length for strong axis buckling}  \\
d &= \text{depth (strong dimension)}
\end{align*}
$$


**Compression Slenderness Ratio (Weak Axis)**

$$
\begin{align*}
C_{C,weak} &= \frac{L_{e,weak}}{b} \\ &= \frac{8.00 \, \text{m}}{175.00 \, \text{mm}} \\ &= 45.71 \tag{CSA O86:24 7.5.8.2} \\ \text{where,} \\
L_{e,weak} &= \text{effective length for weak axis buckling}  \\
b &= \text{width (weak dimension)}
\end{align*}
$$


**Maximum Compression Slenderness Ratio**

$$
\begin{align*}
C_C &= \max(C_{C,strong}, C_{C,weak}) \\ &= \max(17.54, 45.71) \\ &= 45.71 \tag{CSA O86:24 7.5.8.2} \\ \text{where,} \\
C_{C,strong} &= \text{slenderness ratio for strong axis}  \\
C_{C,weak} &= \text{slenderness ratio for weak axis}
\end{align*}
$$


**Slenderness Factor**

$$
\begin{align*}
K_c &= \left[ 1.0 + \frac{F_c \cdot K_{Zcg} \cdot C_C^3}{35 \cdot E_{05} \cdot K_{SE} \cdot K_T} \right]^{-1} \\ &= \left[ 1.0 + \frac{30.20 \, \text{MPa} \cdot 0.72 \cdot 45.71^3}{35 \cdot 10788.00 \, \text{MPa} \cdot 1.00 \cdot 1.00} \right]^{-1} \\ &= 0.15 \tag{CSA O86:24 7.5.8.6} \\ \text{where,} \\
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
P_r &= \phi \cdot F_c \cdot A \cdot K_{Zcg} \cdot K_C \\ &= 0.80 \cdot 30.20 \, \text{MPa} \cdot 79800.00 \, \text{mm}^{2} \cdot 0.72 \cdot 0.15 \\ &= 213546.99 \, \text{N} \tag{CSA O86:24 7.5.8.5} \\ \text{where,} \\
\phi &= \text{compression resistance modification factor}  \\
F_c &= \text{factored strength in compression}  \\
A &= \text{cross-sectional area, mm²}  \\
K_{Zcg} &= \text{compression size factor}  \\
K_C &= \text{compression slenderness factor}  \\
P_f &= \text{factored compressive force}  \\ \\ P_r > 12.75&= 213546.99 \, \text{N} > 12.75 \, \text{N} \\ \text{Check} &= \text{Pass}
\end{align*}
$$

