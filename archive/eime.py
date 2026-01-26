from __future__ import annotations
from IPython.display import Latex, HTML
import math
from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import wraps, update_wrapper
import inspect
# Engineering Intelligence Management Engine (EIME)

class EngineeringFormula:
    def __init__(self, name, params, logic, latex_template, source) -> None:
        self.name = name
        self.params = params
        self.logic = logic
        self.source = source
        self.latexString = latex_template
        self.inputs = None
        self.substitutions: list[EngineeringFormula] = []
        self.result = None
        self.resultUnits = None

    def generateLatex(self) -> str:
        # Display proper latex equation
        subLatex: str = "" # this has to be a list of the latex output of all the substitutions
        for subs in self.substitutions:
            subLatex += str(subs.generateLatex()) + " \\\\ "

        paramsLatex: str = "where,\\\\"
        for param in self.params:
            paramsLatex += self.params[param].latex + "&=\\text{" + self.params[param].desc + "} \\\\ "

        latexymbols = [self.params[x].latex for x in self.inputs.keys()]
        formula = ''.join(self.latexString(*latexymbols))
        def unitFormat(a):
            if isinstance(a, float): return str(round(a,2)) #better check required
            return "{value}\\:{unit}".format(value=round(a.value, 2), unit=a.unit.latex) #better rounding
        
        def unitFormatResults(a):
            if isinstance(a, float): return str(round(a,2)) #better check required
            resultquant = a
            if self.resultUnits != None: resultquant = resultquant.to(self.resultUnits) #!!only works with PhysicalQuantities modules!!
            return "{value}\\:{unit}".format(value=round(resultquant.value, 2), unit=resultquant.unit.latex) #better rounding

        newlist = [x if isinstance(x, str) else unitFormat(x) for x in self.inputs.values()]
        substitution = ''.join(self.latexString(*newlist))
        sourceTag = "\\tag{"+self.source+"}" if self.source != "" else ""
        return subLatex + self.name + "&=" + formula + "=" + substitution + "=" + unitFormatResults(self.result) + sourceTag
    
    def generateParams(self) -> str:
        subLatex: str = "" # this has to be a list of the latex output of all the substitutions
        for subs in self.substitutions:
            subLatex += str(subs.generateParams())

        paramsLatex: str = ""
        for param in self.params:
            paramsLatex += self.params[param].latex + "&=\\text{" + self.params[param].desc + "} \\\\ "
        return subLatex + paramsLatex
    
    def showIn(self, unit:str):
        self.resultUnits = unit
        return self

    def display(self) -> Latex:
        return Latex("\\begin{align*}" + self.generateLatex() + "\\\\\\text{where,}\\\\" + self.generateParams() + "\\end{align*}")

    def formula():
        return Latex("static")

    def solve(self):
        for i in self.inputs:
            if isinstance(self.inputs[i],EngineeringFormula):
                self.substitutions.append(self.inputs[i])
                self.inputs[i] = self.inputs[i].result
        self.result = self.logic(**self.inputs)
        return self

    def addInputs(self, **kw):
        self.inputs = kw
        return self
    
    def test(self, expected_value):
        test_bool = abs(expected_value - self.result) < (expected_value * 0.001)
        test_result = "Test Passed" if test_bool else "Test Failed"
        print(test_result)
        return test_bool

class EngineeringChecks:
    def __init__(self) -> None:
        self.checks: list[EngineeringCheck] = []

    def addCheck(self, check: EngineeringCheck):
        self.checks.append(check)

    def displayUtilizationTable(self) -> HTML:
        htmlheader = '''
            <link rel="stylesheet" type="text/css" href="https://www.w3schools.com/w3css/4/w3.css">
            <style>
                td, th {text-align: left !important;}
                tr {background-color: transparent !important;}
            </style>
        '''
        tablecontent = ""
        for check in self.checks:
            tablecontent += f'''<tr>
                    <td>{check.name}</td>
                    <td>{check.displayHTML().data}</td>
                </tr>'''
        return HTML(f'{htmlheader}<table><tr><th>Check</th><th>Utilization</th></tr>{tablecontent}</table>')
    
class EngineeringCheck(ABC):
    def __init__(self, name) -> None:
        self.name = name

    @abstractmethod
    def displayHTML(self) -> HTML:
        raise NotImplementedError("Must override displayHTML")
    
class SimpleCheck(EngineeringCheck):
    def __init__(self, name, numerator, denominator) -> None:
        self.value1 = numerator
        self.value2 = denominator
        self.util = numerator / denominator
        super().__init__(name)

    def displayHTML(self) -> HTML:
        gradient = ["green","green","green","yellow","orange","red"]
        color_level = gradient[math.floor((self.util-0.01)*6)]
        return HTML(f'''
            <div class="w3-light-grey" style="width:300px">
                <div class="w3-container w3-{color_level} w3-center" style="width:{round(self.util*100)}%">{round(self.util*100)}%</div>
            </div>
        ''')
    
# the point of these wrappers is just to extract the parameters
class formulawrapper(object):
    def __init__(self, func):
        self._func = func
        update_wrapper(self, func)
    def __call__(self, *args, **kw):
        argsk = list(inspect.signature(self._func).parameters.keys())
        kww = tupleToDict(args, argsk)
        return self._func(*args, **kw).addInputs(**kww).solve()
    def __repr__(self):
        print("Latex representation here") # here we could display latex of the formula
        return str(self._func)
    
def formula():
    def _wrap(func):
        return wraps(func)(formulawrapper(func))
    return _wrap

def tupleToDict(vals, tup) -> dict:
    newdict = {}
    for idx, par in enumerate(tup):
        newdict[tup[idx]] = vals[idx]
    return newdict


# Just a wrapper to make it easier to read in the client code
def CreateFormula(name: str, params: dict[str,Param], logic:function, latex_template:function, source:str="") -> EngineeringFormula:
    """Creates an engineering formula object

    ### Args:
        name (str): Formula's Latex form 
        params (dict[str,Param]): Dictionary with your parameters
        logic (function): Core logic
        latexTemplate (function): Latex template

    ### Returns:
        EngineeringFormula: An engineering formula object
    """
    return EngineeringFormula(name, params, logic, latex_template, source)

@dataclass
class Param:
    latex: str
    val:object = None
    desc: str = ""
    src: str = ""

class InputGroup:
    def printParams(self) -> Latex:
        latexString = "\\begin{align}"
        attributes =  [a for a in dir(self) if not a.startswith('__') and not callable(getattr(self, a))]
        for att in attributes:
            latexString += "\\text{"+getattr(self, att).desc+"},\\ " +  getattr(self, att).latex + "&=" + str(getattr(self, att).val) +"\\tag{"+getattr(self, att).src+"}\\\\"
        latexString += "\\end{align}"
        return Latex(latexString)