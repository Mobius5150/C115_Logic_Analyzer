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
The solver attempts to determine logical expressions for the outputs of the
circuit in terms of the circuit inputs and state machines.

The solver is called by the GUI after the Circuit Probe has finished collecting
data. It takes the matrix of data that has been acquired and begins by trying
to combine implicants with their logical neighbhours. After each step the solver
advances to a higher level and combines the non-prime implicants to try and form
the largest possible common block. 

At this point, if the circuit contains any stateful elements (assumed to be
JK Flip Flops) the solver determines the input equations for the J and K inputs
to the flip flops.

Once a minimal representation is found the solver then applies a heuristic
factoring algorithm to try and factor the known terms of the outputs into
a more human friendly form for displaying.

In order to keep the modular design of the project, the main algorithm for the 
solver is located within solver.py, whereas the interface to the solver for the
main application (GUI) is located within solve.py as it is specific to the 
needs of the project, but seperate from the actual solver logic.

The Matrix Class
================
The CircuitProbe and the Solver required a convenient container for storing all
circuit data and for processing it. To this end a basic Matrix class was 
implemented with matrix.py. It provides convenient functions for working with
matrices of binary values.