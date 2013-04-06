"""
Designed to probe a circuit for analysis.


Restrictions:
	For for combinatorial circuits:

	For stateful circuits:
		All flip flops should be clocked to the exact same edge. 
"""


from matrix import Matrix
import RPi.GPIO as GPIO
import time
class CircuitProbe:
	# Number of available GPIO pins
	NUM_GPIO = 8

	# All of the availble GPIO pins
	reserved_pins = { "power": 2, "clock": 3 }
	available_pins = [4, 7, 8, 9, 10, 11, 14, 15, 17, 18, 22, 23, 24, 25, 27]

	def __init__(self, inputs, outputs, states = 0, enable_powercycle = False, propogation_time = 0.01):
		# Setup the base state
		self.reset(inputs = inputs, outputs = outputs, states = states, enable_powercycle = enable_powercycle, propogation_time = propogation_time)

	def __valid_num_io(self, inputs, outputs, states):
		"""
		Checks that the number of inputs/outputs/states is valid for the number of GPIO pins available.

		>>> CP = CircuitProbe(1, 1)
		>>> CP.__valid_num_io__(4, 3, 1)
		True

		>>> CP.__valid_num_io__(4, 3, 2)
		True

		>>> CP.__valid_num_io__(5, 3, 1)
		False

		>>> CP.__valid_num_io__(4, 4, 1)
		False

		>>> CP.__valid_num_io__(0, 3, 1)
		False

		>>> CP.__valid_num_io__(4, 0, 1)
		False

		>>> CP.__valid_num_io__(4, 3, 0)
		False
		"""
		return (NUM_GPIO < inputs + states and inputs > 0 and outputs > 0 and states >= 0)

	def reset(self, inputs = None, outputs = None, states = None, enable_powercycle = False, propogation_time = 0.01):
		"""
		Resets the CircuitProbe to its base unanalysed state. You can use this to change
		the number of inputs/outputs/states, if not specified the number of inputs/outputs/states
		is not changed.
		"""
		if inputs is not None and outputs is not None and states is not None:
			if not self.__valid_num_io(inputs, outputs, states):
				raise Exception("Invalid number of inputs/outputs/states specified for CircuitProbe: {}, {}, {}".format(inputs, outputs, states))

			# Set the inputs/outputs/states
			self.__inputs = inputs
			self.__outputs = outputs
			self.__states = states

			# If theres no state machines, mark that theres one state
			if self.__states <= 0:
				self.__states = 1

			# Keep track of the largest input given the number of available inputs
			self.__max_input = (2**inputs) - 1

		self.Matrix = Matrix(1, self.__inputs + self.__outputs + 2*self.__states)
		self.analyzed_outputs = []
		self.__powercycle_enabled = enable_powercycle
		self.__circuit_propogation_time = propogation_time

	def __powercycle(self):
		"""
		Powercycles the circuit and sleeps for the circuit timeout time before returning.
		"""
		if not self.__powercycle_enabled:
			return

		# Power cycle pin is the first pin
		GPIO.output(reserved_pins["power"], GPIO.LOW)
		time.sleep(self.__circuit_propogation_time)		
		GPIO.output(reserved_pins["power"], GPIO.HIGH)

	def get_to_state(self, state):
		"""
		Attempts to pathfind from the current circuit state to the desired state.

		Usage:
		CP.get_to_state([0, 1]) # Goes to state 01
		"""

	def get_current_state(self):
		"""
		Checks the state probes to determine what state the circuit is currently in and returns a state list
		"""
		state_list = []
		for i in range(self.__states):
			state_list.append(bool(GPIO.input(CircuitProbe.available_pins[self.__outputs + i])))

		return state_list

	def get_current_output(self):
		"""
		Checks the current state of all circuit outputs
		"""
		output_list = []

		for i in range(self.__outputs):
			state_list.append(bool(GPIO.input(CircuitProbe.available_pins[self.__outputs + self.__states + i])))

		return output_list


	def set_inputs(self, val):
		"""
		Sets the ouputs to the binary representation of val

		"""
		for i in range(0, self.inputs):
			GPIO.output(available_pins[i], (self.inputs-i)>>i & 1)


	def pulse_clock(self):
		"""
		Generates one clock cycle on the output and waits for one propogation_time.
		"""
		GPIO.output(reserved_pins["clock"], GPIO.HIGH)
		time.sleep(self.__circuit_propogation_time)
		GPIO.output(reserved_pins["clock"], GPIO.LOW)
		time.sleep(self.__circuit_propogation_time)

	def test_and_record(self, current_state, test_val):
		"""
		Applies a test input to the circuit and record what the output of the circuit becomes 
		and which state it goes to. Returns the new state.
		"""
		# Probe the next circuit inputs for this state
		self.set_inputs(test_val)

		# Clock the circuit
		self.pulse_clock()

		# Record the output of the circuit
		self.matrix.insert_row()
		self.matrix.bin_set_row(-1,test_val, self.__inputs)
		self.matrix.bin_set_row(-1,current_state, self.__states, start_offset = self.__inputs)
		self.matrix.bin_set_row(-1,self.get_current_output(), self.__outputs, start_offset = self.__inputs + self.__states)

		# Check which state the circuit went to
		current_state = self.get_current_state()

		# Record the state in the matrix
		self.matrix.bin_set_row(-1,current_state, self.__states, start_offset = self.__inputs + self.__states + self.__outputs)

		return current_state

	def __get_binary_state_representation__(self, state):
		rep = [ 0 ]
		index = 0
		shifted = state >> index
		while shifted:
			rep[index] = shifted & 1

			# Advance the shift
			index += 1
			shifted >> 1

		return reversed(rep)
			
	def get_closest_untested_state(self, untested, current_state, base_state, edges):
		"""
		Finds the closest untested or partially untested state from the current one. If one is found
		and is reachable, returns the path to the state as a list of inputs needed to get there.

		If there are no reachable partially untested states returns None.

		Performs a BFS for the closest state.
		"""
		# Current cost

		# Check that there are known connected states to this one
		queue = { current_state: 0, base_state: 1 }

	    # List of previous nodes
		previous = {}

		while queue:
			# Get the item with min cost in the queue
			(currentElement, currentCost) = min(queue.items(), key=lambda item: item[1])

			# Remove that element from the queue
			queue.pop(currentElement)

			# Check if the current element is within the untested set
			if currentElement in untested:
				# Walk backwards in history until we get to the source node
				path = [ currentElement ]
				while path[-1] != current_state:
					# Use path.append for speed and reverse later
					path.append( previous[ path[-1] ] )

				# The path is now backwards, reverse and return
				path.reverse()
				return path

			# and append to the queue with history
			if currentElement in edges:
				for child in edges[currentElement]:
					if child in previous.keys(): continue
					previous[child] = currentElement

					# The cost of each step is onex
					queue[child] = currentCost + 1

		return None


	def probe(self):
		"""
		Probes the circuit.
		"""

		# Can't do anything if all outputs have been analyzed
		if len(self.analyzed_outputs) >= self.__outputs:
			return

		tested = {}

		last_state = base_state = self.get_current_state()

		# Edges contains the path from each state to each state that can be reached from that state
		# Destinations are contained in a tuple: (destination, input) Where input is the required input
		# from the source state to get to the destination
		edges = {}

		# Start by applying inputs sequentially to whatever state the circuit is currently in.
		# This should reduce path lengths generated by the pathfinding
		while True:
			# Check the current state
			state = self.get_current_state()

			# Check the next test value
			if last_state in tested:
				# Check if this state has received all possible inputs
				if tested[last_state] < self.__max_input:
					tested[last_state] += 1
				else:
					# It has received all inputs. Exit the while loop
					break

			else:
				tested[last_state] = 0

			# Apply the input value
			t_last_state = last_state
			last_state = self.test_and_record(last_state, tested[last_state])

			# Add this to the edges if we've moved between states
			if t_last_state != last_state:
				if t_last_state not in edges:
					edges[t_last_state] = [ (base_state, None) ] # Each state can go to the base state by resetting
				edges(t_last_state).append((last_state, tested[last_state]))

		# Start by building a list of states/inputs that require testing
		untested = {}
		for i in range(self.__states):
			# Get a binary representation of the state
			i_state = self.__get_binary_state_representation__(i)

			# Check if this state has untested inputs
			if tested[i_state] != self.__max_input:
				if i_state not in untested:
					untested[i_state] = []

				# State has untested inputs
				for j in range(tested[i_state] + 1, self.__max_input + 1):
					untested[i_state].append(j)

		# If there are no untested states, we can stop here!
		if len(untested) == 0:
			return [] # Return empty list for no unreachable states

		# Now attempt to get to each of these test cases
		while untested:
			# Check if state has untested inputs
			if last_state in untested:
				# The current state has untested inputs, try the next one
				t_last_state = last_state
				last_state = self.test_and_record(last_state, untested[last_state])

				# Add this to the edges if we've moved between states
				if t_last_state != last_state:
					if t_last_state not in edges:
						edges[t_last_state] = [ (base_state, None) ] # Each state can go to the base state by resetting

					edges(t_last_state).append((last_state, tested[last_state]))

				# Check if this was the last untested input for the state and remove if yes
				if untested[last_state] == self.__max_input:
					untested.pop(last_state)
				else: 
					untested[last_state] += 1
			else:
				# This state has no untested inputs, pathfind to the closest state with untested inputs
				pass

if __name__ == "__main__":
	import doctest
	doctest.testmod()