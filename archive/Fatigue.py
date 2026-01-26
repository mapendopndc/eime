from eime import Param, formula, CreateFormula
import math

@formula()
def StressInLongitudinalSteel(m_a: float, a_s:float, d:float, y_b:float):
    """Computes stress in longitudinal steel for RC fatigue calculations

    ### Parameters
        m_a (float): factored moment
        a_s (float): area of steel in longitudinal direction
        d (float): depth of rebar in cross-section
        y_b (float): neutral axis
    """

    name = "f_s"

    params = {
        "m_a": Param("M_a", desc="factored moment"),
        "a_s": Param("A_s", desc="area of steel in longitudinal direction"),
        "d": Param("d", desc="depth of rebar in cross-section"),
        "y_b": Param("\\bar{y} ", desc="neutral axis")
    }

    outputUnit = "MPa" # not implemented yet

    def logic(m_a, a_s, d, y_b):
        return m_a/a_s/(d-y_b/3)

    def latex_template(m_a, a_s, d, y_b):
        return "\\frac{",m_a,"}{",a_s,"\\left (",d,"-\\dfrac{",y_b,"}{3} \\right )}"

    return CreateFormula(name,params,logic,latex_template)

@formula()  
def StressInTransverseSteel(v_s:float, a_s:float, n:float):
    """Stress in tranverse steel.

    ### Parameters
        v_s (float): Shear force
        a_s (float): Area of steel
        n (float): number of bars across shear plane
    """
    
    name = "f_s"

    params = {
        "v_s": Param("V_s", desc="factored shear force"),
        "a_s": Param("A_s", desc="area of steel of stirrup"),
        "n": Param("n", desc="number of bars crossing shear plane")
    }

    def logic(v_s, a_s,n):
        return v_s/n/a_s
    
    def latex_template(v_s, a_s,n):
        return "\\frac{",v_s,"}{",n,"\\cdot ",a_s,"}"
    
    return CreateFormula(name,params,logic,latex_template)

@formula()
def NumTransverseBars(d_v:float, theta:float, s:float):
    """Number of transverse bars

    ### Parameters
        d_v (float): Depth of shear plane
        theta (float): Shear angle
        s (float): transverse bar spacing
    """
    name = "n"

    params = {
        "d_v": Param("d_v", desc="depth of shear plane"),
        "theta": Param("\\theta ", desc="angle of shear plane"),
        "s": Param("s", desc="spacing of transverse bars")
    }

    source = "AISC.2.3"

    def logic(d_v, theta, s):
        return d_v / (math.tan(theta) * s)
    
    def latex_template(d_v, theta, s):
        return "\\frac{",d_v,"}{\\tan(",theta," )\\cdot ",s,"}"
    
    return CreateFormula(name,params,logic,latex_template,source)

if __name__ == "__main__":
    # Test your functions here
    pass