
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
K_{Zcg} &= 0.68 \cdot \left(Z\right)^{-0.13} \\ &= 0.68 \cdot \left(172900.00 \, \text{m} \cdot \text{mm}^{2}\right)^{-0.13} \\ &= 0.85 \tag{CSA O86:24 7.5.8.5} \\ \text{where,} \\
Z &= \text{member volume, m³}  \\ \\ K_{Zcg} \leq 1.0&= 0.85 \leq 1.00 \\ \text{Check} &= \text{Pass}
\end{align*}
$$


**Compression Slenderness Ratio (Strong Axis)**

$$
\begin{align*}
C_{C,strong} &= \frac{L_{e,strong}}{d} \\ &= \frac{7.00 \, \text{m}}{190.00 \, \text{mm}} \\ &= 36.84 \tag{CSA O86:24 7.5.8.2} \\ \text{where,} \\
L_{e,strong} &= \text{effective length for strong axis buckling}  \\
d &= \text{depth (strong dimension)}
\end{align*}
$$


**Compression Slenderness Ratio (Weak Axis)**

$$
\begin{align*}
C_{C,weak} &= \frac{L_{e,weak}}{b} \\ &= \frac{5.10 \, \text{m}}{130.00 \, \text{mm}} \\ &= 39.23 \tag{CSA O86:24 7.5.8.2} \\ \text{where,} \\
L_{e,weak} &= \text{effective length for weak axis buckling}  \\
b &= \text{width (weak dimension)}
\end{align*}
$$


**Maximum Compression Slenderness Ratio**

$$
\begin{align*}
C_C &= \max(C_{C,strong}, C_{C,weak}) \\ &= \max(36.84, 39.23) \\ &= 39.23 \tag{CSA O86:24 7.5.8.2} \\ \text{where,} \\
C_{C,strong} &= \text{slenderness ratio for strong axis}  \\
C_{C,weak} &= \text{slenderness ratio for weak axis}
\end{align*}
$$


**Slenderness Factor**

$$
\begin{align*}
K_c &= \left[ 1.0 + \frac{F_c \cdot K_{Zcg} \cdot C_C^3}{35 \cdot E_{05} \cdot K_{SE} \cdot K_T} \right]^{-1} \\ &= \left[ 1.0 + \frac{30.20 \, \text{MPa} \cdot 0.85 \cdot 39.23^3}{35 \cdot 10788.00 \, \text{MPa} \cdot 1.00 \cdot 1.00} \right]^{-1} \\ &= 0.20 \tag{CSA O86:24 7.5.8.6} \\ \text{where,} \\
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
P_r &= \phi \cdot F_c \cdot A \cdot K_{Zcg} \cdot K_C \\ &= 0.80 \cdot 30.20 \, \text{MPa} \cdot 24700.00 \, \text{mm}^{2} \cdot 0.85 \cdot 0.20 \\ &= 99461.57 \, \text{N} \tag{CSA O86:24 7.5.8.5} \\ \text{where,} \\
\phi &= \text{compression resistance modification factor}  \\
F_c &= \text{factored strength in compression}  \\
A &= \text{cross-sectional area, mm²}  \\
K_{Zcg} &= \text{compression size factor}  \\
K_C &= \text{compression slenderness factor}  \\
P_f &= \text{factored compressive force}  \\ \\ P_r > 80.5&= 99461.57 \, \text{N} > 80.50 \, \text{N} \\ \text{Check} &= \text{Pass}
\end{align*}
$$
