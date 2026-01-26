from enum import Enum
from libraries.eime import Param, Check, formula, switch, CreateFormula, CreateSwitch, STATUS
import numpy as np # library of vectorized math operations

@formula()
def LongDurationFactor(P_L: float, P_S:float):
    """Except as specified in Clause 5.3.2.3, when the specified long-term load, PL, is greater than the specified standard-term load, Ps, a load-duration factor of 0.65 may be used, or KD may be calculated using this formula
    
    ### Parameters
        P_L (float): specified long-term load
        P_S (float): specified standard-term load based on Snow (S) and Live (L) loads acting alone or in combination
        = S, L, S + 0.5L, or 0.5S + L, determined using importance factors equal to 1.0

    ### Checks
    P_L and P_S must be non-zero
    """

    name = "K_D"

    description = "Long Duration Factor"

    params = {
        "P_L": Param("P_L", desc="specified long-term load"),
        "P_S": Param("P_S", desc="specified standard-term load"),
    }

    source = "CSA O86:24 cl.5.3.2.2"

    outputUnit = ""

    def logic(P_L, P_S):
        return np.maximum(1.0 - 0.50 * np.log10(abs(P_L/P_S)), 0.65)

    def latex_template(P_L, P_S):
        return "1.0 - 0.50 \\log_{10}(",P_L,"/",P_S,")\\ge 0.65"

    return CreateFormula(name,params,logic,latex_template,source,desc=description)

@formula()
def StiffnessModulusOfElasticity(E: float, K_SE:float, K_T:float):
    """Modulus of Elasticity for Stiffness calculations
    
    ### Parameters
        E (float): specified modulus of elasticity
        K_SE (float): service-condition factor
        K_T (float): treatment factor
    """

    name = "E_S"

    description = "Stiffness Modulus of Elasticity"

    params = {
        "E": Param("E", desc="specified modulus of elasticity"),
        "K_SE": Param("K_SE", desc="service-condition factor"),
        "K_T": Param("K_T", desc="treatment factor"),
    }

    source = "CSA O86:24 cl.5.4.1"

    outputUnit = "MPa"

    def logic(E, K_SE, K_T):
        return E*K_SE*K_T

    def latex_template(E, K_SE, K_T):
        return E,"(",K_SE,"\\cdot ",K_T,")"

    return CreateFormula(name,params,logic,latex_template,source,desc=description)

@formula()
def MomentOfIntertia(b: float, d:float):
    """Computes the moment of interia of a rectangular shape
    
    ### Parameters
        b (float): width
        d (float): depth
    """

    name = "I"

    description = "Moment of Inertia"

    params = {
        "b": Param("b", desc="width"),
        "d": Param("d", desc="depth")
    }

    source = ""

    outputUnit = "mm^4"

    def logic(b,d):
        return b*pow(d,3)/12

    def latex_template(b,d):
        return "\\frac{",b,"\\cdot ",d,"^3}{12}"

    return CreateFormula(name,params,logic,latex_template,source,desc=description)

@formula()
def SectionModulus(b: float, d:float):
    """Computes the section modulus of a rectangular shape
    
    ### Parameters
        b (float): width
        d (float): depth
    """

    name = "S"

    description = "Section Modulus"

    params = {
        "b": Param("b", desc="width"),
        "d": Param("d", desc="depth")
    }

    source = ""

    outputUnit = "mm^3"

    def logic(b,d):
        return b*pow(d,2)/6

    def latex_template(b,d):
        return "\\frac{",b,"\\cdot ",d,"^2}{6}"

    return CreateFormula(name,params,logic,latex_template,source,desc=description)

@formula()
def ModifiedBendingStrength(f_b: float, K_D: float, K_H: float, K_Sb: float, K_T: float):
    """Modified strength in bending
    
    ### Parameters
        f_b (float): specified strength in bending
        K_D (float): load-duration factor
        K_H (float): system factor
        K_Sb (float): service condition factor
        K_T (float): treatment factor
    """

    name = "F_b"

    description = "Modified Bending Strength"

    params = {
        "f_b": Param("f_b", desc="specified bending strength"),
        "K_D": Param("K_D", desc="load-duration factor"),
        "K_H": Param("K_H", desc="system factor"),
        "K_Sb": Param("K_{Sb}", desc="service condition factor"),
        "K_T": Param("K_T", desc="treatment factor")
    }

    source = "CSA O86:24 7.5.6.6.1"

    outputUnit = "MPa"

    def logic(f_b, K_D, K_H, K_Sb, K_T):
        return f_b*K_D*K_H*K_Sb*K_T

    def latex_template(f_b, K_D, K_H, K_Sb, K_T):
        return f_b,"(",K_D,"\\cdot ",K_H,"\\cdot ",K_Sb,"\\cdot ",K_T,")"

    return CreateFormula(name,params,logic,latex_template,source,desc=description)

@formula()
def BendingSizeFactor(b: float, d: float, L: float):
    """Size factor for bending for glued-laminated timber.
    **UNITS MUST BE MM**

    ### Parameters
        b (float): specified strength in bending
        d (float): load-duration factor
        L (float): system factor

    ### Checks
        upperbound: 1.5
    """

    name = "K_{Zbg}"

    description = "Bending Size Factor"

    params = {
        "b": Param("b", desc="width"),
        "d": Param("d", desc="depth"),
        "L": Param("L", desc="length")
    }

    source = "CSA O86:24 7.5.6.6.1"

    outputUnit = ""

    def logic(b,d,L):
        return pow((130/b),0.1)*pow((610/d),0.1)*pow((9100/L),0.1)

    def latex_template(b,d,L):
        return "\\left(\\frac{130}{",b,"}\\right)^{\\frac{1}{10}}\\left(\\frac{610}{",d,"}\\right)^{\\frac{1}{10}}\\left(\\frac{9100}{",L,"}\\right)^{\\frac{1}{10}}"

    checks = [
        Check.Upperbound(1.3, STATUS.FAIL, 564, "Size factor must be <= 1.3", inclusive=True)
    ]

    return CreateFormula(name,params,logic,latex_template,source, checks,desc=description)

@formula()
def SlendernessRatio(L_u: float, d: float, b: float):
    """Unbraced segment slendernes ratio. **Simplied - NOT TO CODE**
    
    ### Parameters
        L_u (float): unbraced segment length
        d (float): depth
        b (float): width
    """

    name = "\\lambda"

    description = "Slenderness Ratio"

    params = {
        "L_u": Param("L_u", desc="unbraced segment length"),
        "d": Param("d", desc="depth"),
        "b": Param("b", desc="width")
    }

    source = "CSA O86:24 7.5.6.5.2"

    outputUnit = ""

    def logic(L_u,d,b):
        return pow(L_u*d/pow(b,2),0.5)

    def latex_template(L_u,d,b):
        return "\\sqrt{\\frac{",L_u,"\\cdot ",d,"}{",b,"^2}}"

    return CreateFormula(name,params,logic,latex_template,source,desc=description)

@formula()
def SlendernessRatioLimit(E: float, K_SE: float, K_T: float, F_b: float):
    """Slenderness ratio limit for elastic lateral-torsional buckling. **Simplied - NOT TO CODE**
    
    ### Parameters
        E (float): specified modulus of elasticity
        K_SE (float): service condition factor
        K_T (float): treatment factor
        F_b (float): modified bending strength
    """

    name = "\\lambda_e"

    description = "Slenderness Ratio Limit"

    params = {
        "E": Param("E", desc="specified modulus of elasticity"),
        "K_SE": Param("K_{SE}", desc="service condition factor"),
        "K_T": Param("K_T", desc="treatment factor"),
        "F_b": Param("F_b", desc="modified bending strength")
    }

    source = "CSA O86:24 7.5.6.5.2 b)"

    outputUnit = ""

    def logic(E, K_SE, K_T, F_b):
        return pow(0.97*E*K_SE*K_T/F_b,0.5)

    def latex_template(E, K_SE, K_T, F_b):
        return "\\sqrt{\\frac{0.97\\cdot ",E,"\\cdot ",K_SE,"\\cdot ",K_T,"}{",F_b,"}}"

    return CreateFormula(name,params,logic,latex_template,source,desc=description)

@formula()
def LateralStabilityFactorA():
    """Lateral stability factor.
    
    ### Parameters
        None

    ### Source
        CSA O86:24 7.5.6.5.2 a)
    """

    name = "K_L"

    params = {}

    description = "Lateral Stability Factor a)"

    source = "CSA O86:24 7.5.6.5.2 a)"

    outputUnit = ""

    def logic():
        return 1

    def latex_template():
        return "1.0"

    return CreateFormula(name,params,logic,latex_template,source,desc=description)

@formula()
def LateralStabilityFactorB(lambda_1: float, lambda_e: float):
    """Lateral stability factor.
    
    ### Parameters
        lambda (float): slenderness ratio
        lambda_e (float): slenderness ratio limit

    ### Source
        CSA O86:24 7.5.6.5.2 b)
    """

    name = "K_L"

    description="Lateral Stability Factor b)"

    params = {
        "lambda_1": Param("\\lambda", desc="slenderness ratio"),
        "lambda_e": Param("\\lambda_e", desc="slenderness ratio limit"),
    }

    source = "CSA O86:24 7.5.6.5.2 b)"

    outputUnit = ""

    def logic(lambda_1,lambda_e):
        return 1-1/3*pow(lambda_1/lambda_e,4)

    def latex_template(lambda_1,lambda_e):
        return "1-\\frac{1}{3}\\left(\\frac{",lambda_1,"}{",lambda_e,"}\\right)^4"

    return CreateFormula(name,params,logic,latex_template,source,desc=description)

@switch()
def LateralStabilityFactor(lambda1: float, lambda_e:float, KL_a:float, KL_b:float, KL_c:float, KL_d:float):
    """Lateral stability factor for unbraced member.

    ### Parameters
        lambda1 (float): Slenderness Ratio
        lambda_e (float): Slenderness Ratio Limit
        KL_a (float): Lateral Stability Factor - Output A
        KL_b (float): Lateral Stability Factor - Output B
        KL_c (float): Lateral Stability Factor - Output C
        KL_d (float): Lateral Stability Factor - Output D

    ### Source
        CSA O86:24 7.5.6.5.2
    """

    name = "K_L"

    description = "Lateral Stability Factor for Unbraced Members"

    params = {
        "lambda1": Param("\\lambda", desc="slenderness ratio"),
        "lambda_e": Param("\\lambda_e", desc="slenderness ratio limit"),
        "KL_a": Param("K_L", desc="lateral stability factor output a)"),
        "KL_b": Param("K_L", desc="lateral stability factor output b)"),
        "KL_c": Param("K_L", desc="lateral stability factor output c)"),
        "KL_d": Param("K_L", desc="lateral stability factor output d)"),
    }

    source = "CSA O86:24 7.5.6.5.2"

    outputUnit = ""

    bounds = [10,lambda_e, 50]

    outputs = [KL_a, KL_b, KL_c, KL_d]

    checks = [
        Check.Upperbound(1.01, STATUS.FAIL, 453, message="KL must be <= 1.0", inclusive=True) #fix with tolerance
    ]

    return CreateSwitch(name, params, bounds, outputs, source, checks,desc=description)

@formula()
def MomentResistanceA(phi: float, F_b: float, S: float, K_x: float, K_Zbg: float):
    """Factored bending moment resistance.
    
    ### Parameters
        phi (float): resistance factor
        F_b (float): modified bending strength
        S (float): section modulus
        K_x (float): curvature factor
        K_Zbg (float): size factor
    """

    name = "M_{r,a}"

    description = "Moment Resistance a)"

    params = {
        "phi": Param("\\phi", desc="resistance factor"),
        "F_b": Param("F_b", desc="modified bending strength"),
        "S": Param("S", desc="section modulus"),
        "K_x": Param("K_x", desc="curvature factor"),
        "K_Zbg": Param("K_{Zbg}", desc="size factor"),
    }

    source = "CSA O86:24 7.5.6.6.1 a)"

    outputUnit = "MPa"

    def logic(phi, F_b, S, K_x, K_Zbg):
        return phi*F_b*S*K_x*K_Zbg

    def latex_template(phi, F_b, S, K_x, K_Zbg):
        return phi,"\\cdot ",F_b,"\\cdot ",S,"\\cdot ",K_x,"\\cdot ",K_Zbg

    return CreateFormula(name,params,logic,latex_template,source,desc=description)

@formula()
def MomentResistanceB1(phi: float, F_b: float, S: float, K_x: float, K_Zbg: float):
    """Factored bending moment resistance.
    
    ### Parameters
        phi (float): resistance factor
        F_b (float): modified bending strength
        S (float): section modulus
        K_x (float): curvature factor
        K_Zbg (float): size factor
    """

    name = "M_{r1}"

    description = "Moment Resistance b) i)"

    params = {
        "phi": Param("\\phi", desc="resistance factor"),
        "F_b": Param("F_b", desc="modified bending strength"),
        "S": Param("S", desc="section modulus"),
        "K_x": Param("K_x", desc="curvature factor"),
        "K_Zbg": Param("K_{Zbg}", desc="size factor"),
    }

    source = "CSA O86:24 7.5.6.6.1 b)"

    outputUnit = "MPa"

    def logic(phi, F_b, S, K_x, K_Zbg):
        return phi*F_b*S*K_x*K_Zbg

    def latex_template(phi, F_b, S, K_x, K_Zbg):
        return phi,"\\cdot ",F_b,"\\cdot ",S,"\\cdot ",K_x,"\\cdot ",K_Zbg

    return CreateFormula(name,params,logic,latex_template,source,desc=description)

@formula()
def MomentResistanceB2(phi: float, F_b: float, S: float, K_x: float, K_L: float):
    """Factored bending moment resistance.
    
    ### Parameters
        phi (float): resistance factor
        F_b (float): modified bending strength
        S (float): section modulus
        K_x (float): curvature factor
        K_L (float): lateral-stability factor
    """

    name = "M_{r2}"

    description = "Moment Resistance b) 2)"

    params = {
        "phi": Param("\\phi", desc="resistance factor"),
        "F_b": Param("F_b", desc="modified bending strength"),
        "S": Param("S", desc="section modulus"),
        "K_x": Param("K_x", desc="curvature factor"),
        "K_L": Param("K_L", desc="size factor"),
    }

    source = "CSA O86:24 7.5.6.6.1 b)"

    outputUnit = "MPa"

    def logic(phi, F_b, S, K_x, K_L):
        return phi*F_b*S*K_x*K_L

    def latex_template(phi, F_b, S, K_x, K_L):
        return phi,"\\cdot ",F_b,"\\cdot ",S,"\\cdot ",K_x,"\\cdot ",K_L

    return CreateFormula(name,params,logic,latex_template,source,desc=description)

@switch()
def MomentResistanceB(M_r1: float, M_r2: float):
    """Factored bending moment resistance.
    
    ### Parameters
        M_r1 (float): based on K_Zbg
        M_r2 (float): based on K_L
    """

    name = "M_{r,b}"

    description = "Moment Resistance b)"

    params = {
        "M_r1": Param("M_{r1}", desc="resistance based on K_Zbg"),
        "M_r2": Param("M_{r2}", desc="resistance based on K_L")
    }

    source = "CSA O86:24 7.5.6.6.1 b)"

    outputUnit = "MPa"

    bounds = [M_r2]

    outputs = [M_r1, M_r2]

    return CreateSwitch(name,params,bounds,outputs,source,desc=description)

@switch()
def MomentResistance(K_L:float, M_rA: float, M_rB: float, M_f:float=None):
    """Factored bending moment resistance.
    
    ### Parameters
        K_L (float): size factor
        M_rA (float): based on K_Zbg
        M_rB (float): based on K_L
        [For checks] M_f (float): Factored moment
    """

    name = "M_r"

    description = "Moment Resistance"

    params = {
        "K_L": Param("K_L", desc="size factor"),
        "M_rA": Param("M_{r}", desc="resistance A"),
        "M_rB": Param("M_{r}", desc="resistance B")
    }

    source = "CSA O86:24 7.5.6.6.1"

    outputUnit = "MPa"

    bounds = [1.0]

    outputs = [M_rB, M_rA]

    checks = [
        Check.Lowerbound(M_f, STATUS.FAIL, 132, "Factored force exceeds resistance.")
    ]

    return CreateSwitch(name,params,bounds,outputs,source,checks,desc=description)

@formula() #make this a placeholder type instead??
def AppliedMoment(M_f:float):
    """Factored applied moment.
    
    ### Parameters
        M_f (float): Factored applied moment
    """

    name = "M_f"

    description = "Factored Applied Moment"

    params = {
        "M_f": Param("M_f", desc="factored applied moment")
    }

    source = ""

    outputUnit = "KNm"

    def logic(M_f):
        return M_f

    def latex_template(M_f):
        return M_f

    return CreateFormula(name,params,logic,latex_template,source,desc=description)

@formula() #make this a placeholder type instead??
def AppliedShear(V_f:float):
    """Factored applied shear.
    
    ### Parameters
        V_f (float): Factored applied shear
    """

    name = "V_f"

    description = "Factored Applied Shear"

    params = {
        "V_f": Param("V_f", desc="factored applied shear")
    }

    source = ""

    outputUnit = "KN"

    def logic(V_f):
        return V_f

    def latex_template(V_f):
        return V_f

    return CreateFormula(name,params,logic,latex_template,source,desc=description)

@formula() #make this a placeholder type instead??
def AppliedCompression(P_f:float):
    """Factored applied compression.
    
    ### Parameters
        P_f (float): Factored applied compression
    """

    name = "P_f"

    description = "Factored Applied Compression"

    params = {
        "P_f": Param("P_f", desc="factored applied compression")
    }

    source = ""

    outputUnit = "KN"

    def logic(P_f):
        return P_f

    def latex_template(P_f):
        return P_f

    return CreateFormula(name,params,logic,latex_template,source,desc=description)

@formula()
def GFactor(l_a: float, V_A: float, V_B: float, V_C: float):
    """G factor used to compute the shear-load coefficient, Cv
    
    ### Parameters
        l_a (float): segment length
        V_A (float): absolute value of factored shear force at beginning of segment
        V_B (float): absolute value of factored shear force at end of segment
        V_C (float): absolute value of factored shear force at centre of segment
    """

    name = "G"

    description = "Shear Factor G"

    params = {
        "l_a": Param("l_a", desc="segment length"),
        "V_A": Param("V_A", desc="value of factored shear force at beginning of segment"),
        "V_B": Param("V_B", desc="value of factored shear force at end of segment"),
        "V_C": Param("V_C", desc="value of factored shear force at centre of segment")
    }

    source = "CSA O86:24 7.5.7.6 c)"

    outputUnit = ""

    def logic(l_a, V_A, V_B, V_C):
        return abs(l_a * (pow(V_A,5) + pow(V_B,5) + pow(4*V_C,5)))

    def latex_template(l_a, V_A, V_B, V_C):
        return l_a, "\\left[ ", V_A, "^5+", V_B, "^5+4\\cdot ",V_C, "^5]"

    return CreateFormula(name,params,logic,latex_template,source,desc=description)

@formula()
def ShearLoadCoefficient(W_f: float, L: float, Sum_G: float):
    """Shear-load coefficient, Cv
    
    ### Parameters
        W_f (float): the total of all factored loads applied to the beam
        L (float): length of beam
        Sum_G (float): sum of G factors
    """

    name = "C_V"

    description = "Shear-Load Coefficient"

    params = {
        "W_f": Param("W_f", desc="the total of all factored loads applied to the beam"),
        "L": Param("L", desc="length of beam"),
        "Sum_G": Param("\\sum G", desc="sum of G factors")
    }

    source = "CSA O86:24 7.5.7.6 d) i)"

    outputUnit = ""

    def logic(W_f, L, Sum_G):
        return 1.825*W_f*pow((L/Sum_G), 0.2)

    def latex_template(W_f, L, Sum_G):
        return "1.825\\cdot ", W_f, "\\left( \\frac{", L, "}{", Sum_G, "} \\right)^{0.2}"

    return CreateFormula(name,params,logic,latex_template,source,desc=description)

@formula()
def ModifiedShearStrength(f_v: float, K_D: float, K_H: float, K_Sv: float, K_T: float):
    """Modified strength in shear
    
    ### Parameters
        f_v (float): specified strength in shear
        K_D (float): load-duration factor
        K_H (float): system factor
        K_Sv (float): service condition factor
        K_T (float): treatment factor
    """

    name = "F_v"

    description = "Modified Shear Strength"

    params = {
        "f_v": Param("f_v", desc="specified shear strength"),
        "K_D": Param("K_D", desc="load-duration factor"),
        "K_H": Param("K_H", desc="system factor"),
        "K_Sv": Param("K_{Sv}", desc="service condition factor"),
        "K_T": Param("K_T", desc="treatment factor")
    }

    source = "CSA O86:24 7.5.7.3 b)"

    outputUnit = "MPa"

    def logic(f_v, K_D, K_H, K_Sv, K_T):
        return f_v*K_D*K_H*K_Sv*K_T

    def latex_template(f_v, K_D, K_H, K_Sv, K_T):
        return f_v,"(",K_D,"\\cdot ",K_H,"\\cdot ",K_Sv,"\\cdot ",K_T,")"

    return CreateFormula(name,params,logic,latex_template,source,desc=description)

@formula()
def TotalShearResistance(phi: float, F_v: float, A_g: float, C_V: float, Z: float):
    """Total factored shear resistance, Wr
    
    ### Parameters
        phi (float): shear resistance modification factor
        F_v (float): factored strength in shear
        A_g (float): gross cross-sectional area, mm2
        C_V (float): shear load coefficient
        Z (float): beam volume, m3
    """

    name = "W_r"

    description = "Total Shear Resistance"

    params = {
        "phi": Param("\\phi", desc="shear resistance modification factor"),
        "F_v": Param("F_v", desc="factored strength in shear"),
        "A_g": Param("A_g", desc="gross cross-sectional area, mm2"),
        "C_V": Param("C_V", desc="shear load coefficient"),
        "Z": Param("Z", desc="beam volume, m3")
    }

    source = "CSA O86:24 7.5.7.3 a)"

    outputUnit = "MPa"

    def logic(phi, F_v, A_g, C_V, Z):
        return phi*F_v*0.48*A_g*C_V*pow(Z,-0.18)

    def latex_template(phi, F_v, A_g, C_V, Z):
        return phi, "\\cdot ", F_v, "\\cdot 0.48\\cdot ",A_g, "\\cdot ",C_V, "\\cdot ", Z, "^{-0.18}"

    return CreateFormula(name,params,logic,latex_template,source,desc=description)

@formula()
def ShearResistance(phi: float, F_v: float, A_g: float, V_f:float=None):
    """Factored shear resistance, Vr
    
    ### Parameters
        phi (float): shear resistance modification factor
        F_v (float): factored strength in shear
        A_g (float): gross cross-sectional area, mm2,
        [for checks] V_f (float): factored shear resistanace
    """

    name = "V_r"

    description = "Shear Resistance"

    params = {
        "phi": Param("\\phi", desc="shear resistance modification factor"),
        "F_v": Param("F_v", desc="factored strength in shear"),
        "A_g": Param("A_g", desc="gross cross-sectional area, mm2"),
        "V_f": Param("V_f", desc="factored shear resistance")
    }

    source = "CSA O86:24 7.5.7.3 b)"

    outputUnit = "MPa"

    def logic(phi, F_v, A_g, V_f):
        return phi*F_v*2*A_g/3

    def latex_template(phi, F_v, A_g, V_f):
        return phi, "\\cdot ", F_v, "\\frac{2\\cdot ",A_g, "}{3}"
    
    checks = [
        Check.Lowerbound(V_f, STATUS.FAIL, 136, "Factored force exceeds resistance.")
    ]

    return CreateFormula(name,params,logic,latex_template,source,checks,desc=description)

@formula()
def ModifiedCompressionStrength(f_c: float, K_D: float, K_H: float, K_Sc: float, K_T: float):
    """Modified strength in compression parallel to grain
    
    ### Parameters
        f_c (float): specified strength in compression parallel to grain
        K_D (float): load-duration factor
        K_H (float): system factor
        K_Sc (float): service condition factor
        K_T (float): treatment factor
    """

    name = "F_c"

    description="Modified Compression Strength"

    params = {
        "f_c": Param("f_c", desc="specified compression strength"),
        "K_D": Param("K_D", desc="load-duration factor"),
        "K_H": Param("K_H", desc="system factor"),
        "K_Sc": Param("K_{Sc}", desc="service condition factor"),
        "K_T": Param("K_T", desc="treatment factor")
    }

    source = "CSA O86:24 7.5.8.5"

    outputUnit = "MPa"

    def logic(f_c, K_D, K_H, K_Sc, K_T):
        return f_c*K_D*K_H*K_Sc*K_T

    def latex_template(f_c, K_D, K_H, K_Sc, K_T):
        return f_c,"(",K_D,"\\cdot ",K_H,"\\cdot ",K_Sc,"\\cdot ",K_T,")"

    return CreateFormula(name,params,logic,latex_template,source,desc=description)

@formula()
def CompressionSizeFactor(Z: float):
    """Size factor for compression members, K_Zcg <= 1.0
    
    ### Parameters
        Z (float): member volume, m3
    """

    name = "K_{Zcg}"

    description="Compression Size Factor"

    params = {
        "Z": Param("Z", desc="member volume, m3"),
    }

    source = "CSA O86:24 7.5.8.5"

    outputUnit = ""

    def logic(Z):
        return 0.68*pow(Z,-0.13)

    def latex_template(Z):
        return "0.68(", Z, ")^{-0.13}"
    
    checks = [
        Check.Upperbound(1.0, STATUS.FAIL, 874, "Compression size factor over 1.0", inclusive=True)
    ]

    return CreateFormula(name,params,logic,latex_template,source, checks,desc=description)

@formula()
def CompressionSlendernessRatio(L_e: float, w: float):
    """Slenderness ratio, C_C. w is either depth or width
    
    ### Parameters
        L_e (float): effective length associate with width
        w (float): width
    """

    name = "C_C"

    description="Compression Slenderness Ratio"

    params = {
        "L_e": Param("L_e", desc="effective length associated with width"),
        "w": Param("w", desc="width")
    }

    source = "CSA O86:24 7.5.8.2"

    outputUnit = ""

    def logic(L_e, w):
        return L_e/w

    def latex_template(L_e, w):
        return "\\frac{",L_e,"}{",w,"}"

    return CreateFormula(name,params,logic,latex_template,source,desc=description)

@formula()
def SlendernessFactor(F_c:float, K_Zcg:float, C_C:float, E_05: float, K_SE: float, K_T: float):
    """Slenderness factor, Kc
    
    ### Parameters
        F_c (float): factored strength in compression parallel to grain
        K_Zcg (float): compression size factor
        C_C (float): compression slenderness ratio
        E_05 (float): fifth percentile of specified modulus of elasticity, MPa
        K_SE (float): service condition factor
        K_T (float): treatment factor
    """

    name = "K_c"

    description="Slenderness Factor"

    params = {
        "F_c": Param("F_c", desc="factored strength in compression parallel to grain"),
        "K_Zcg": Param("K_{Zcg}", desc="compression size factor"),
        "C_C": Param("C_C", desc="compression slenderness ratio"),
        "E_05": Param("E_{05}", desc="fifth percentile of specified modulus of elasticity, MPa"),
        "K_SE": Param("K_{SE}", desc="service condition factor"),
        "K_T": Param("K_T", desc="treatment factor")
    }

    source = "CSA O86:24 7.5.8.6"

    outputUnit = ""

    def logic(F_c, K_Zcg, C_C, E_05, K_SE, K_T):
        return 1 / (1 + F_c*K_Zcg*pow(C_C,3)/35/E_05/K_SE/K_T)

    def latex_template(F_c, K_Zcg, C_C, E_05, K_SE, K_T):
        return "\\left[ 1.0 + \\frac{", F_c, "\\cdot ", K_Zcg, "\\cdot ", C_C,"^3}{35\\cdot ", E_05, "\\cdot ", K_SE, "\\cdot ", K_T, "}\\right]^{-1}"

    return CreateFormula(name,params,logic,latex_template,source,desc=description)

@formula()
def CompressionResistance(phi: float, F_c: float, A: float, K_Zcg: float, K_C: float, P_f:float=None):
    """Factored compressive resistance parallel to grain, P_r
    
    ### Parameters
        phi (float): compression resistance modification factor
        F_c (float): factored strength in compression parallel to grain, MPa
        A (float): cross-sectional area, mm2
        K_Zcg (float): compression size factor
        K_C (float): compression slenderness factor
        [for checks] P_f (float): factored compressive force
    """

    name = "P_r"

    description="Compression Resistance"

    params = {
        "phi": Param("\\phi", desc="compression resistance modification factor"),
        "F_c": Param("F_c", desc="factored strength in compression parallel to grain"),
        "A": Param("A", desc="cross-sectional area, mm2"),
        "K_Zcg": Param("K_{Zcg}", desc="compression size factor"),
        "K_C": Param("K_C", desc="compression slenderness factor"),
        "P_f": Param("P_f", desc="factored compressive force")
    }

    source = "CSA O86:24 7.5.8.5"

    outputUnit = "MPa"

    def logic(phi, F_c, A, K_Zcg, K_C, P_f):
        return phi*F_c*A*K_Zcg*K_C

    def latex_template(phi, F_c, A, K_Zcg, K_C, P_f):
        return phi, "\\cdot ", F_c, "\\cdot ", A, "\\cdot ", K_Zcg, "\\cdot ", K_C
    
    checks = [
        Check.Lowerbound(P_f, STATUS.FAIL, 136, "Factored force exceeds resistance.")
    ]

    return CreateFormula(name,params,logic,latex_template,source,checks,desc=description)
