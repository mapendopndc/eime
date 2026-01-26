This codebase contains legacy code for a program called EIME - Engineering Intelligence Management Engine. The goal is to refactor this codebase completely from ground up to set it up to be a proper production ready python library, and improve the structure and organization of the cobebase to adhere to best software design practice. It is important that the overall complexity of the program stays relatively low and similar to what is currently being implemented, so developers can still follow. Backwards compatibility is not required under any circumstances, so unused code is to be discarded so that the code base stays very lean. Here are more princinples and notes on this program to guide this refactor plan:

# Purpose and Features
EIME is the next generation of engineering calculation software. Its main goal is the allow non-technical engineers to write and review engineering formulas in python (using simple and well documented functions), and build a library around taking these atomic, human-verified formulas and presented them in a way that is as transparent as a complete hand calculation. In addition to this primary aim, EIME also includes the following features:
- allows engineers to incorporate checks in their formulas that automatically get flagged in documentation
- engineers can build design procedures, that group commonly used formulas together
- engineers can also build calculators that expose and useful API to the design procedures to help collect inputs and perform checks
- formulas are built to allow large numpy arrays as inputs, allowing for large scale calculations to be performed extremely fast
- specific tables from different design codes can be stored as json and pull for calculations
- EIMES can be used in any visualization or output layer, like with a streamlit app, jupyter or marimo notebook, python script, or served as an API endpoint

# Structure and Terminology
The EIME framework is built on top of the following building blocks:
- Formula: the atomic building block of EIME. A formula is a single engineering calculation that takes inputs, performs calculations, and returns outputs. Formulas can also include checks that get flagged in documentation. It is crucial that these formulas remain simple and human-readable, as they are the core of EIME's transparency and verifiability. They contain clear and comprehensive documentation, and a latex representation of the calculation being performed for visualizations.
- Design Procedure: a collection of formulas that are commonly used together to perform a specific engineering task or calculation. Design procedures can be built by engineers to streamline their workflow and ensure consistency in their calculations.
- Calculator: a higher-level construct that exposes an API to interact with design procedures. Calculators can be used to collect inputs, perform calculations, and return results in a user-friendly manner.
- Tables: design code specific tables that can be stored as json and pulled into formulas for calculations.

# Current Codebase Overview
The current codebase contains an example use case for timber design, where batch results from an analysis software are read, preprocessed, and batch designed using EIME, and outputted to a streamlit app. The codebase therefore shows all the main building blocks of EIME, including formulas, design procedures, and calculators, as well as code specific tables. All of the EIMEs code is stored in the "eime.py" file under libraries.

# Refactor Objectives
The main objectives of the refactor are as follows:
- Break down the monolithic "eime.py" file into smaller, more manageable modules that adhere to the single responsibility principle, and save is under a folder called "eime". This folder must be kept general and not include any design code specific logic, and this eime folder will be the main python library that users will install and use, and the users will build their own design code specific logic on top of this library, like their formlas, design procedures, calculators, and tables.
- Move design code specifc logic into a folder called "design" that is separate from the main "eime" library. This folder will contain all design code specific logic, including formulas, design procedures, calculators, and tables. This folder will serve as an example of how users can build their own design code specific logic on top of the EIME library. withing this folder add a subfolder for the specific design code being implemented, in this case timber in canadian code, it'll be "design/csaO86-2025".
- include a folder for additional utiliy tools like a simple 2D FEM solver and visualization.
- include a folder for personal tests and experimentation
- implement a very simple way to run unit tests on the engineering formulas spefically. Include that in the eime library.
- Set up the codebase to be a proper python library that can be installed via pip, with proper setup files, requirements files, and documentation.
- use uv package manager
- Improve the organization and structure of the codebase to adhere to best software design practices, including proper naming conventions, file organization, and documentation.
- Ensure that the overall complexity of the program remains relatively low and similar to the current implementation, so that developers can still follow along easily.
- Discard any unused code to keep the codebase lean and maintainable (no backwards compatibility required).