C115_Logic_Analyzer
===================

A basic digital logic circuit analyzer. Works by first providing the number of 
inputs/outputs the circuit has in addition to the number of stateful elements it
has (flip flops). You then connect the analyzer to the circuit and click 
"Analyze" in the GUI. This will begin manipulating circuit inputs to try and 
discover as much information as possible about the circuit.

The Logic Analyzer GUI
======================
The main Logic Analyzer program is located within logic_analyzer.py. It
implements the GUI for the program. It uses the Tkinter framework to create its
graphical interface. It also implements the methods responsible for displaying
the input/output/state graph within the main window and for taking the matrix
data and turning it into a Digraph to be displayed whrn the user requests a
stategraph for the circuit.

The Circuit Probe
=================
The CircuitProbe class (located within circuit_probe.py) implements the data 
collection algorithm for the project. It is responsible for all manipulation of 
the circuit and reading of output/state values. While analyzing a circuit it 
does the following:
	1. Walk through the circuit, following the natural flow of states. Each
	   time it encounters a new state the first untested input (starting with 0)
	   is attempted. Once a state has had all inputs tried on it this step ends.
    2. Pathfind through the circuit. Now that the probe has walked through the
       circuit it attempts to use the basic map to find all possible reachable
       states. It does this by using Dijkstra's algorithm to search for the
       closest untested input within the known states that it knows how to get
       to, and goes there. A note: the probe is able to powercycle a circuit
       in order to reset it to its base state. This ability is considered within
       the pathfinding algorithm.

The Solver
==========
The program contains a general expression solver, which can take in a set of
inputs -> output pairs and generate an expression for the output in terms of
those inputs. Note: The solver can handle some of the pairs having an output
of "unspecified", and will choose the better choice towards optimizing the
expression to the smallest possible form. This code is located in solver.py

This base solver has no actual notion of actual input/output/state circuits, it
simply knows how to generate an expression for inputs in terms of outputs. In
order for the GUI to easily call on simplification of the data, there is an
extra translation utility function to solve a whole system. This function takes
a system of inputs, outputs, and states, and solves each of the outputs in terms
of the inputs, as well as solving the J/K inputs to JKflip-flops that could be
used to implement the state of the cirtuit. This code is located in solve.py

Overall workflow:
input matrix from probe -> system solver -> solve several expressions

The base implementation expression solver uses two main phases to do the
simplification:

1) Quine–McCluskey Algorithm

The Quine–McCluskey algorithm is first run on the input to get a minimal and-or
form expression for the output. This involves first taking all of the implicants
containing only one minterm. Then repeatedly joining adjacent implicants into
larger ones, and marking all of the remaining implicants as essential. The final
result is all of those prime implicants.

2) Factoring Engine

The remaining terms in the and-or form solution may still have common factors
that can be pulled out from them to reduce the complexity of the resulting
expression. The factoring engine recursively factors expressions out of the main
expression, using the heuristic:
Maximize: (size of expression to factor out)*(number of terms that contain it)
This gives a result fairly close to the optimal number of and/or gates to
implement a given expression.

In order to keep the modular design of the project, the GUI elements of the
program only have to call on the system-solver located in solve.py, and do not
have to touch the base expression solving function.

solver.py also contains some utilites for pretty printing and formatting outputs
from the various simplification functions.


The Matrix Class
================
The CircuitProbe and the Solver required a convenient container for storing all
circuit data and for processing it. To this end a basic Matrix class was 
implemented with matrix.py. It provides convenient functions for working with
matrices of binary values.
