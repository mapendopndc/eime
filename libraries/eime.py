from __future__ import annotations
from IPython.display import Latex, HTML, Markdown
import math
from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import wraps, update_wrapper
from inspect import signature
import numpy as np
import pandas as pd
from enum import IntEnum
from typing import List, Dict, Protocol
from abc import ABC
# Engineering Intelligence Management Engine (EIME)

# displayable protocol -> check, util, engineeringfunctions -> engineeringformula, engineeringswitch

class EngineeringFunction(ABC):

    def __init__(self, name:str, checks:List[EngineeringCheck], desc):
        self.name = name
        self.desc = desc
        self.checks:List[EngineeringCheck] = checks
        self.result = None

    def runChecks(self) -> EngineeringFunction:
        # add error check here first
        self.checks.append(InvalidResult(STATUS.ERROR, 0, "Invalid Result (not a number)"))
        self.checks = [check.setFormula(self) for check in self.checks]
        return self

    @abstractmethod
    def solve(self) -> EngineeringFunction:
        pass

    @abstractmethod
    def generateFunctionLatex(self, index) -> str:
        pass

    @abstractmethod
    def generateParamLatex(self, index) -> str:
        pass

    @abstractmethod
    def generateChecksLatex(self, index) -> str:
        pass

    @abstractmethod
    def generateLatex(self, index) -> str:
        pass

    def _getSingleResult(a, index) -> float:
        if isinstance(a, float) or isinstance(a, int): return float(a)
        if isinstance(a, pd.Series): return float(a.iloc[[index]].values[0])
        if isinstance(a, np.ndarray): return float(a[index])

    def formatResult(self, a, index) -> str:
        solution = round(self._getSingleResult(a, index), 2)
        unit_latex = "" # add logic to extract unit if its a formula or something
        return "{value}\\:{unit}".format(value=solution, unit=unit_latex)

    @abstractmethod
    def display(self,index) -> Latex:
        pass


    #Add common methods likes testing, utilities, etc
    
    def check(self) -> List[EngineeringCheck]:
        return [check.run() for check in self.checks]

    def addInputs(self, **kw) -> EngineeringFunction:
        self.inputs = kw
        return self
    
    def test(self, expected_value):
        test_bool = abs(expected_value - self.result) < (expected_value * 0.001)
        test_result = "Test Passed" if test_bool else "Test Failed"
        print(test_result)
        return test_bool
    
    def showIn(self, unit:str):
        self.resultUnits = unit
        return self

    def formula():
        return Latex("static")


class EngineeringFormula(EngineeringFunction):
    def __init__(self, name, params, logic, latex_template, source, checks, desc, comments) -> None:
        super().__init__(name, checks, desc)
        self.params: List[Param] = params
        self.logic = logic
        self.source = source
        self.latexString = latex_template
        self.inputs = None
        self.substitutions: List[EngineeringFunction] = []
        self.resultUnits = None

    def generateFunctionLatex(self, index) -> str:

        #subLatex: str = "" # this has to be a list of the latex output of all the substitutions
        #for subs in self.substitutions:
            #subLatex += str(subs.generateLatex(index)) + " \\\\ "
        # paramsLatex: str = "where,\\\\"
        # for param in self.params:
        #     paramsLatex += self.params[param].latex + "&=\\text{" + self.params[param].desc + "} \\\\ "
        #sourceTag = "\\tag{"+self.source+"}" if self.source != "" else ""
        #return subLatex + self.name + "&=" + formula + "=" + substitution + "=" + unitFormatResults(self.result) + sourceTag

        latexymbols = [self.params[x].latex for x in self.inputs.keys()]
        formula = ''.join(self.latexString(*latexymbols))

        substitutions = [x if isinstance(x, str) else self.formatResult(x, index) for x in self.inputs.values()]
        subtituted_formula_latex = ''.join(self.latexString(*substitutions))

        return self.name + "&=" + formula + "\\\\&=" + subtituted_formula_latex + "\\\\&=" + self.formatResult(self, index)
    
    def generateParamLatex(self) -> str:
        #subLatex: str = "" # this has to be a list of the latex output of all the substitutions
        #for subs in self.substitutions:
            #subLatex += str(subs.generateParams())
        paramsLatex: str = ""
        for param in self.params:
            paramsLatex += " \\\\ " + self.params[param].latex+ "&=\\text{" + self.params[param].desc + "}"
        return paramsLatex
    
    def generateLatex(self, index) -> str:
        return "\\begin{align*}" + self.generateFunctionLatex(index) + self.generateParamLatex() + "\\end{align*}"

    def solve(self):
        for i in self.inputs:
            if isinstance(self.inputs[i],EngineeringFunction):
                self.substitutions.append(self.inputs[i])
                self.inputs[i] = self.inputs[i].result
        self.result = self.logic(**self.inputs)
        return self
    
class EngineeringSwitch(EngineeringFunction):
    def __init__(self, name, params, bounds, outputs, source, checks, desc, comments) -> None:
        super().__init__(name, checks, desc)
        self.params = params
        self.bounds = bounds
        self.source = source
        self.outputs = outputs
        self.selected_output = None
        self.inputs = None
        self.substitutions: List[EngineeringFunction] = []
        self.resultUnits = None

    def _getRangeAtIndex(self, ranges, index) -> list:
        for i, range in enumerate(ranges):
            if isinstance(range, pd.Series): range[i] = range.iloc[[index]].values[0]
            if isinstance(range, np.ndarray): range[i] = range[index]

    def _getRangeLatexAtIndex(self, ranges, index, fn) -> list:
        for i, range in enumerate(ranges):
            if isinstance(range, pd.Series): ranges[i] = range.iloc[[index]].values[0]
            if isinstance(ranges[i], EngineeringFunction): ranges[i] = fn(ranges[i])
            else: ranges[i] = str(ranges[i])


    def generateFunctionLatex(self, index:int) -> str:
        current_solved_bounds = self._getRangeAtIndex(self.solved_bounds.copy(), index)
        current_outputs_raw = self._getRangeAtIndex(self.outputs.copy(), index)
        
        current_input = None
        if (isinstance(self.solved_inputs[0], pd.Series)):
            current_input = self.solved_inputs[0].iloc[[index]].values[0]
        elif(isinstance(self.solved_inputs[0], np.ndarray)):
            current_input = self.solved_inputs[0][index]
        else:
            current_input = self.solved_inputs[0]

        selected_formula_idx = 0
        if (current_input > current_solved_bounds[-1]):selected_formula_idx = -1
        
        string_bounds = self._getRangeLatexAtIndex(self.bounds.copy(), index, lambda x:x.name)
        string_outputs = self._getRangeLatexAtIndex(self.outputs.copy(), index, lambda x:x.generateLatex(index))

        #TODO: eventually compute selected option for every element during solve
        for i, bound in enumerate(current_solved_bounds):
            if (i + 1) == len(current_solved_bounds): continue
            if current_input > float(bound) and current_input <= float(current_solved_bounds[i+1]): selected_formula_idx = i+1

        latex_string = ""
        if selected_formula_idx == 0: latex_string += f"{list(self.params.values())[0].latex} < {string_bounds[0]}:"
        elif selected_formula_idx == -1: latex_string += f"{list(self.params.values())[0].latex} > {string_bounds[-1]}:"
        else: latex_string += f" {string_bounds[selected_formula_idx-1]} < {list(self.params.values())[0].latex} < {string_bounds[selected_formula_idx]}:"
        return latex_string + "\\\\ " + self.name + ("&" if isinstance(current_outputs_raw[selected_formula_idx], EngineeringSwitch) else "") + "=" + ((current_outputs_raw[selected_formula_idx].name + " \\\\ \\\\ ") if isinstance(current_outputs_raw[selected_formula_idx], EngineeringSwitch) else "") + string_outputs[selected_formula_idx]
    
    def generateParamLatex(self) -> str:
        #subLatex: str = "" # this has to be a list of the latex output of all the substitutions
        #for subs in self.substitutions:
            #subLatex += str(subs.generateParams())

        paramsLatex: str = ""
        for param in self.params:
            paramsLatex += self.params[param].latex + "&=\\text{" + self.params[param].desc + "} \\\\ "
        return paramsLatex
    
    def generateLatex(self,index:int) -> Latex:
        return "\\begin{align*}" + self.generateFunctionLatex(index) + "\\\\\\text{where,}\\\\" + self.generateParamLatex() + "\\end{align*}"

    def solve(self) -> EngineeringFunction:
        self.solved_inputs = list(self.inputs.values())
        for idx, i in enumerate(self.inputs):
            if isinstance(self.inputs[i],EngineeringFunction):
                #self.substitutions.append(self.inputs[i])
                self.solved_inputs[idx] = self.inputs[i].result
        
        self.solved_outputs = self.outputs.copy()
        for i, output in enumerate(self.outputs):
            if isinstance(output,EngineeringFunction):
                #self.substitutions.append(output)
                self.solved_outputs[i] = output.result

        self.solved_bounds = self.bounds.copy()
        for i, bound in enumerate(self.bounds):
            if isinstance(bound,EngineeringFunction):
                #self.substitutions.append(output)
                self.solved_bounds[i] = bound.result

        filtered_mask = self.solved_outputs[0]
        for i, bound in enumerate(self.solved_bounds):
            self.solved_inputs[0] = np.array(self.solved_inputs[0]).astype(float) ####### Fix this
            filtered_mask = np.where(self.solved_inputs[0] > bound, self.solved_outputs[i+1], filtered_mask)
        self.result = filtered_mask
        return self
    

class Depr_EngineeringChecks:
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
    
class Depr_EngineeringCheck(ABC):
    def __init__(self, name) -> None:
        self.name = name

    @abstractmethod
    def displayHTML(self) -> HTML:
        raise NotImplementedError("Must override displayHTML")
    
class SimpleCheck(Depr_EngineeringCheck):
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
        argsk = list(signature(self._func).parameters.keys())
        kww = tupleToDict(args, argsk)
        return self._func(*args, **kw).addInputs(**kww).solve().runChecks()
    def __repr__(self):
        print("Latex representation here") # here we could display latex of the formula
        return str(self._func)
    
def formula():
    def _wrap(func):
        return wraps(func)(formulawrapper(func))
    return _wrap

def switch():
    def _wrap(func):
        return wraps(func)(formulawrapper(func))
    return _wrap

def tupleToDict(vals, tup) -> dict:
    newdict = {}
    for idx, par in enumerate(tup):
        newdict[tup[idx]] = vals[idx]
    return newdict


# Just a wrapper to make it easier to read in the client code
def CreateFormula(name: str, params: dict[str,Param], logic:function, latex_template:function, source:str=None, checks:List[EngineeringCheck] = None,  desc:str=None, comments=None) -> EngineeringFormula:
    """Creates an engineering formula object

    ### Args:
        name (str): Formula's Latex form 
        params (dict[str,Param]): Dictionary with your parameters
        logic (function): Core logic
        latexTemplate (function): Latex template

    ### Returns:
        EngineeringFormula: An engineering formula object
    """
    
    checks = [] if checks is None else checks
    
    return EngineeringFormula(name, params, logic, latex_template, source, checks, desc, comments)


# Just a wrapper to make it easier to read in the client code
def CreateSwitch(name: str, params: dict[str,Param], bounds, outputs, source:str=None, checks:List[EngineeringCheck] = None, desc:str=None, comments=None) -> EngineeringSwitch:
    """Creates an engineering formula object from a switch statement

    ### Args:
        name (str): Formula's Latex form 
        params (dict[str,Param]): Dictionary with your parameters
        logic (function): Core logic
        latexTemplate (function): Latex template

    ### Returns:
        EngineeringFormula: An engineering formula object
    """

    checks = [] if checks is None else checks

    return EngineeringSwitch(name, params, bounds, outputs, source, checks, desc, comments)


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

class STATUS(IntEnum):
        PASS = 0,
        WARNING = 1,
        FAIL = 2,
        ERROR = 3

status_desc = ["Pass", "Pass with warnings", "Fail", "Error"]

#dataclass
class CheckCode:
    def __init__(self, ID, message, status):
        self.ID = ID
        self.msg = message
        self.status = status

#Use this to display various elements in engineering procedure
class Displayable(Protocol):
    def generateLatex(self, index:int) -> str:
        ...

class DisplayText:
    def __init__(self, text:str, header=False):
        self.text = text

    def generateLatex(self, index:int) -> str:
        return "\\text{" + self.text + "}"
    
    def generateMarkdown(self, index:int) -> str:
        return "### " + self.text

#Used to make design calculators
class EngineeringDesign(ABC):
    pass

class EngineeringProcedure:
    # Holds the logic of a complete design check

    def __init__(self, name):
        self.name = name
        self.procedure:List[Displayable] = []
        self.checks: Dict[int, EngineeringCheck] = {}
        self.results: pd.DataFrame = pd.DataFrame()
        self.status_log: pd.DataFrame = pd.DataFrame()
        self.check_log: pd.DataFrame = pd.DataFrame()
        self.utilizations: pd.DataFrame = pd.DataFrame()

    def AddComputation(self, formula: EngineeringFunction, supress_check=False, show_util=True):
        #Add the formula
        self.procedure.append(formula)
        self.results[formula.name] = formula.result

        #Add checks
        if (formula.checks == None): return #No checks performed for this computation
        for check in formula.checks:
            self.procedure.append(check)
            self.checks[check.check_id] = check
            self.check_log[formula.name + "_code:" + str(check.check_id)] = check.applied_check_ids
            self.status_log[formula.name + "_code:" + str(check.check_id)] = check.applied_status_codes
            if check.check_id and show_util:
                self.utilizations[formula.name + "_code:" + str(check.check_id)] = check.util
            pass

    def AddTitle(self, text):
        self.procedure.append(DisplayText(text))

    def displayLatex(self, index) -> Latex:
        latex_output = " \\begin{align*} "
        for displayObject in self.procedure:
            latex_output += displayObject.generateLatex(index) + "\\\\"
        return Latex(latex_output + " \\end{align*} ")
    
    def displayObjects(self, index):
        dispObjs = []
        for displayObject in self.procedure:
            if (isinstance(displayObject, EngineeringFunction)):
                dispObjs.append(Latex(" \\begin{align*} " + displayObject.generateLatex(index) + " \\end{align*} "))
            elif (isinstance(displayObject, DisplayText)):
                dispObjs.append(Markdown(displayObject.generateMarkdown(index)))
        return dispObjs

    #Future Features:
    def computeUtil(self): #return worst util for each element in list and its governing step
        pass

    def computeGoverning(self): #return governing step
        pass

    def computeStatus(self): #return worst status for each element in list
        pass

    def getErrorBreakdown(self): #returns number of errors of each type
        pass



class EngineeringCheck(ABC):

    @abstractmethod
    def __init__(self, status_code:int, check_id:int, message:str):
        self.check_id: int = check_id
        self.status_code: int = status_code
        self.message: str = message
        self.applied_check_ids: np.ndarray = None
        self.applied_status_codes: np.ndarray = None
        self.applied_messages: np.ndarray = None
        self.result: np.ndarray = None
        self.util: np.ndarray = None
        self.formula = None

    def setFormula(self, formula:EngineeringFunction) -> EngineeringCheck:
        self.formula = formula
        self.check()
        return self

    @abstractmethod
    def check() -> EngineeringCheck:
        pass

    @abstractmethod
    def generateLatex(self, index:int) -> str:
        pass

class Lowerbound(EngineeringCheck):
    def __init__(self, lowerbound, status_code:int, check_id:int, message:str, inclusive=False):
        super().__init__(status_code, check_id, message)
        self.lowerbound = lowerbound
        self.inclusive = inclusive
        
    def check(self) -> EngineeringCheck:
        self.formula.result = np.array(self.formula.result).astype(float)#fixthis

        lowerbound_result = self.lowerbound if not isinstance(self.lowerbound, EngineeringFunction) else self.lowerbound.result

        if (self.inclusive):
            self.applied_check_ids = np.where(self.formula.result <= lowerbound_result, self.check_id, None)
            self.applied_status_codes = np.where(self.formula.result <= lowerbound_result, self.status_code, STATUS.PASS)
            self.applied_messages = np.where(self.formula.result <= lowerbound_result, self.message, None)
        else:
            self.applied_check_ids = np.where(self.formula.result < lowerbound_result, self.check_id, None)
            self.applied_status_codes = np.where(self.formula.result < lowerbound_result, self.status_code, STATUS.PASS)
            self.applied_messages = np.where(self.formula.result < lowerbound_result, self.message, None)

        self.util = lowerbound_result / self.formula.result

    def generateLatex(self, index:int) -> str:
        selected_result = None
        if (isinstance(self.formula.result, pd.Series)):
            selected_result = self.formula.result.iloc[[index]].values[0]
        elif(isinstance(self.formula.result, np.ndarray)):
            selected_result = self.formula.result[index]
        else:
            selected_result = self.formula.result

        lowerbound_results = self.lowerbound if not isinstance(self.lowerbound, EngineeringFunction) else self.lowerbound.result
        selected_lowerbound = None
        if (isinstance(lowerbound_results, pd.Series)):
            selected_lowerbound = lowerbound_results.iloc[[index]].values[0]
        elif(isinstance(lowerbound_results, np.ndarray)):
            selected_lowerbound = lowerbound_results[index]
        else:
            selected_lowerbound = lowerbound_results

        error_message = status_desc[self.status_code] + "; " + self.message
        bound_string = str(selected_lowerbound) if not isinstance(self.lowerbound, EngineeringFunction) else self.lowerbound.name

        if (self.inclusive):
            status_message = status_desc[STATUS.PASS] if selected_result >= selected_lowerbound else error_message
            upper_text = self.formula.name + " \\geq " + bound_string + "&=" + str(round(selected_result,2)) + " \\geq " + str(selected_lowerbound) + " \\\\"
        else:
            status_message = status_desc[STATUS.PASS] if selected_result > selected_lowerbound else error_message
            upper_text = self.formula.name + " > " + bound_string + "&=" + str(round(selected_result,2)) + " > " + str(selected_lowerbound) + " \\\\"

        


        
        return upper_text + "\\text{Check}&=\\text{" + status_message + "}"

class Upperbound(EngineeringCheck):
    def __init__(self, upperbound, status_code:int, check_id:int, message:str, inclusive=False):
        super().__init__(status_code, check_id, message)
        self.upperbound = upperbound
        self.inclusive = inclusive

    def check(self) -> EngineeringCheck:
        self.formula.result = np.array(self.formula.result).astype(float)#fixthis

        upperbound_result = self.upperbound if not isinstance(self.upperbound, EngineeringFunction) else self.upperbound.result

        if (self.inclusive):
            self.applied_check_ids = np.where(self.formula.result >= upperbound_result, self.check_id, None)
            self.applied_status_codes = np.where(self.formula.result >= upperbound_result, self.status_code, STATUS.PASS)
            self.applied_messages = np.where(self.formula.result >= upperbound_result, self.message, None)
        else:
            self.applied_check_ids = np.where(self.formula.result > upperbound_result, self.check_id, None)
            self.applied_status_codes = np.where(self.formula.result > upperbound_result, self.status_code, STATUS.PASS)
            self.applied_messages = np.where(self.formula.result > upperbound_result, self.message, None)

        self.util = self.formula.result / upperbound_result


    def generateLatex(self, index:int) -> str:
        selected_result = None
        if (isinstance(self.formula.result, pd.Series)):
            selected_result = self.formula.result.iloc[[index]].values[0]
        elif(isinstance(self.formula.result, np.ndarray)):
            selected_result = self.formula.result[index]
        else:
            selected_result = self.formula.result

        upperbound_results = self.upperbound if not isinstance(self.upperbound, EngineeringFunction) else self.upperbound.result
        selected_upperbound = None
        if (isinstance(upperbound_results, pd.Series)):
            selected_upperbound = upperbound_results.iloc[[index]].values[0]
        elif(isinstance(upperbound_results, np.ndarray)):
            selected_upperbound = upperbound_results[index]
        else:
            selected_upperbound = upperbound_results

        error_message = status_desc[self.status_code] + "; " + self.message

        bound_string = str(selected_upperbound) if not isinstance(self.upperbound, EngineeringFunction) else self.upperbound.name

        if (self.inclusive):
            status_message = status_desc[STATUS.PASS] if selected_result < selected_upperbound else error_message
            upper_text = self.formula.name + " \\leq " + bound_string + "&=" + str(round(selected_result,2)) + " \\leq " + str(selected_upperbound) + " \\\\"
        else:
            status_message = status_desc[STATUS.PASS] if selected_result < selected_upperbound else error_message
            upper_text = self.formula.name + " < " + bound_string + "&=" + str(round(selected_result,2)) + " < " + str(selected_upperbound) + " \\\\"
        
        return upper_text + "\\text{Check}&=\\text{" + status_message + "}"


#in progress
class Equality(EngineeringCheck):
    def __init__(self, value, status_code:int, check_id:int, message:str, tolerance:float=0.001):
        super().__init__(status_code, check_id, message)
        self.value = value
        self.tolerance = tolerance 

    def check(self) -> EngineeringCheck:
        pass

    def generateLatex(self, index:int) -> str:
        return "latex representation not built for this check"

class InvalidResult(EngineeringCheck):
    def __init__(self, status_code:STATUS, check_id:int, message:str):
        super().__init__(status_code, check_id, message)

    def check(self) -> EngineeringCheck:
        # self.formula.result = np.array(self.formula.result).astype(float)#fixthis
        self.applied_check_ids = np.where(np.isnan(self.formula.result), self.check_id, None)
        self.applied_status_codes = np.where(np.isnan(self.formula.result), self.status_code, STATUS.PASS)
        self.applied_messages = np.where(np.isnan(self.formula.result), self.message, None)

    def generateLatex(self, index:int) -> str:
        current_status = 0 if not np.any(self.applied_status_codes) else self.applied_status_codes[index]
        current_message = "" if not np.any(self.applied_messages) else self.applied_messages[index]
        error_message = "\\text{Error} &= \\text{" + current_message + "}" if current_status > 0 else ""
        return error_message


class Check: #collects all the engineering check classes. could make this a module but i dont want to break this file
    @staticmethod
    def Upperbound(upperbound, status_code, check_id, message, inclusive=False) -> EngineeringCheck:
        return Upperbound(upperbound, status_code, check_id, message, inclusive)

    @staticmethod
    def Lowerbound(lowerbound, status_code, check_id, message, inclusive=False) -> EngineeringCheck:
        return Lowerbound(lowerbound, status_code, check_id, message, inclusive)
