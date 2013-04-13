"""
The Circuit Probe
=================
The CircuitProbe class implements the data 
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


Restrictions for stateful circuits:
	All flip flops must be indicated as a stateful element and should have 
	state inputs directly connected to them.
"""


from matrix import Matrix
import RPi.GPIO as GPIO
import time
class CircuitProbe:
	# Number of available GPIO pins
	NUM_GPIO = 15

	# All of the availble GPIO pins
	reserved_pins = { "power": 3, "clock": 5 }
	available_pins = [7, 8, 10, 11, 12, 13, 15, 16, 18, 19, 21, 22, 23, 24, 27]

	# Controls default debug state
	default_debug_state = True

	def __init__(self, inputs, outputs, states = 0, enable_powercycle = True, propogation_time = .01, debug = None):
		"""
		If debug is None, it will default to the default debug state of the CircuitProbe class. To enable or disable debug mode
		Initialize CircuitProbe with debug = True of debug = False.
		"""
		if debug is None:
			debug = CircuitProbe.default_debug_state

		# Enable or disable debug mode
		self.set_debug(debug)

		# Set the pin numbering mode
		GPIO.setmode(GPIO.BOARD)

		# Setup the power and clock pins	
		for i in CircuitProbe.reserved_pins:
			pin = CircuitProbe.reserved_pins[i]
			if self.__debug:
				print("Setting pin {} as {}".format(pin, i))
			GPIO.setup(pin, GPIO.OUT, initial=GPIO.HIGH)
			

		# Setup the base state
		self.reset(inputs = inputs, outputs = outputs, states = states, 
			enable_powercycle = enable_powercycle, propogation_time = propogation_time)

	def get_type_for_column(self, col):
		"""
		Returns the type string for the column.
		"""
		row_type = "Input"
		if col >= self.__inputs:
			row_type = "State"
		if col >= self.__inputs + self.__states:
			row_type = "Output"
		if col >= self.__inputs + self.__states + self.__outputs:
			row_type = "Next State"

		return row_type

	def get_title_for_column(self, col):
		"""
		Returns the type string for the column.
		"""
		row_var = chr(ord('A') + col)
		if col >= self.__inputs:
			row_var = col - self.__inputs
		if col >= self.__inputs + self.__states:
			row_var = col - self.__inputs - self.__states
		if col >= self.__inputs + self.__states + self.__outputs:
			row_var = col - self.__inputs - self.__states - self.__outputs

		return row_var

	def get_channel_for_column(self, col):
		"""
		Returns the GPIO channel number for the column.
		"""
		return CircuitProbe.available_pins[col]

	def get_num_inputs(self):
		return self.__inputs

	def get_num_outputs(self):
		return self.__outputs

	def get_num_states(self):
		return self.__states

	def set_debug(self, debug):
		"""
		Enables or disables circuit probe debug mode which prints additional output.
		"""
		self.__debug = debug
		GPIO.setwarnings(debug)

	def __valid_num_io(self, inputs, outputs, states):
		"""
		Checks that the number of inputs/outputs/states is valid for the number of GPIO pins available.

		>>> CP = CircuitProbe(1, 1)
		>>> CP.reset(4, 3, 1)

		>>> CP.reset(4, 3, 2)

		>>> CP.reset(5, 3, 1)

		>>> CP.reset(4, 4, 1)

		>>> CP.reset(4, 3, 0)
		"""
		return (CircuitProbe.NUM_GPIO > (inputs + states) and inputs > 0 and outputs > 0 and states >= 0)

	def reset(self, inputs = None, outputs = None, states = None, enable_powercycle = True,
			  propogation_time = 0.01, clock_time = 0.01):
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

			# Keep track of the largest input given the number of available inputs
			self.__max_input = (2**inputs) - 1

		## Setup GPIO pins
		# Configure inputs
		for i in CircuitProbe.available_pins[:self.__inputs]:
			if self.__debug:
				print("Setting channel {} as circuit input.".format(i))
			GPIO.setup(i, GPIO.OUT, initial=GPIO.LOW)

		# Configure states
		for i in CircuitProbe.available_pins[self.__inputs:(self.__inputs + self.__states)]:
			if self.__debug:
				print("Setting channel {} as circuit state.".format(i))
			GPIO.setup(i, GPIO.IN)

		# Configure outputs
		for i in CircuitProbe.available_pins[(self.__inputs + self.__states):(self.__inputs + self.__states + self.__outputs)]:
			if self.__debug:
				print("Setting channel {} as circuit output".format(i))
			GPIO.setup(i, GPIO.IN)

		# Initialize the matrix for holding values
		self.matrix = Matrix(0, self.__inputs + self.__outputs + 2*self.__states)
		self.analyzed_outputs = []

		# Some internal state stuff
		self.__powercycle_enabled = enable_powercycle
		self.__circuit_propogation_time = propogation_time
		self.__circuit_clock_time = clock_time

	def powercycle(self):
		"""
		Turns the circuit off, sleeps then turns back on. Then sleeps for the circuit timeout time before returning.
		"""
		if not self.__powercycle_enabled:
			if self.__debug:
				print("Powercycling not enabled.")

			return

		if self.__debug:
			print("Powercycling circuit.")

		# Power cycle pin is the first pin
		GPIO.output(CircuitProbe.reserved_pins["power"], GPIO.LOW)
		time.sleep(self.__circuit_propogation_time)
		GPIO.output(CircuitProbe.reserved_pins["power"], GPIO.HIGH)
		time.sleep(self.__circuit_propogation_time)

	def power_on(self):
		"""
		Turns the circuit power on and waits the propogation time.
		"""
		if self.__debug:
			print("Circuit power on.")
		GPIO.output(CircuitProbe.reserved_pins["power"], GPIO.HIGH)
		time.sleep(self.__circuit_propogation_time)

	def power_off(self):
		"""
		Turns the circuit power off and waits the propogation time.
		"""
		if self.__debug:
			print("Circuit power off.")
		GPIO.output(CircuitProbe.reserved_pins["power"], GPIO.LOW)
		time.sleep(self.__circuit_propogation_time)

	def get_matrix(self):
		return self.matrix

	def get_current_state(self):
		"""
		Checks the state probes to determine what state the circuit is currently in and returns a state list
		"""
		state_list = []
		for i in range(self.__states):
			state_list.append(bool(GPIO.input(CircuitProbe.available_pins[self.__inputs + i])))
			print("Output on: {} is {}".format(CircuitProbe.available_pins[self.__inputs + i], state_list[-1]))

		return state_list

	def get_current_output(self):
		"""
		Checks the current state of all circuit outputs
		"""
		output_list = []

		for i in range(self.__outputs):
			output_list.append(GPIO.input(CircuitProbe.available_pins[self.__inputs + self.__states + i]))
			if self.__debug:
				print("Pin {} output: {}".format(CircuitProbe.available_pins[self.__inputs + self.__states + i], output_list[-1]))

		return output_list


	def set_inputs(self, val):
		"""
		Sets the ouputs to the binary representation of val

		"""
		for i in range(0, self.__inputs):
			GPIO.output(CircuitProbe.available_pins[i], val>>(self.__inputs-i-1) & 1)


	def pulse_clock(self):
		"""
		Generates one clock cycle on the output and waits for one propogation_time.
		"""
		GPIO.output(CircuitProbe.reserved_pins["clock"], GPIO.HIGH)
		time.sleep(self.__circuit_clock_time)
		GPIO.output(CircuitProbe.reserved_pins["clock"], GPIO.LOW)
		time.sleep(self.__circuit_clock_time)

	def test_and_record(self, current_state, test_val):
		"""
		Applies a test input to the circuit and record what the output of the circuit becomes 
		and which state it goes to. Returns the new state.

		Order of operations:
		Set inputs -> Measure output -> Pulse Clock -> Record Next State
		"""
		# Probe the next circuit inputs for this state
		self.set_inputs(test_val)

		# Wait a propogation time
		time.sleep(self.__circuit_propogation_time)

		# Record the state we're in
		current_state_bin = self.get_binary_state_representation(current_state)

		# Record the input/output of the circuit
		self.matrix.insert_row()
		self.matrix.bin_set_row(-1,test_val, self.__inputs)
		self.matrix.bin_set_row(-1,current_state_bin, self.__states, start_offset = self.__inputs)
		self.matrix.bin_set_row(-1,self.get_current_output(), self.__outputs, 
			start_offset = self.__inputs + self.__states)

		# Clock the circuit
		self.pulse_clock()

		# Record the state we went to

		# Check which state the circuit went to
		current_state = self.get_numerical_state_representation(self.get_current_state())

		# Record the state in the matrix
		self.matrix.bin_set_row(-1,current_state, self.__states, start_offset = self.__inputs + self.__states + self.__outputs)

		return current_state

	def get_ordered_output_matrix(self):
		"""
		Returns a "sorted" copy of the output matrix. Sort is done by circuit inputs and states only. Outputs are not sorted
		"""
		# Build "indices for each row"
		row_index = lambda r: (self.get_numerical_state_representation(r[:self.__inputs]) +
			(self.get_numerical_state_representation(r[self.__inputs:self.__inputs + self.__states]) * (2**self.__states)))
		
		self.matrix.sort(key=row_index)

		return self.matrix

	def get_binary_state_representation(self, num):
		"""
		Takes an input number and returns an array of bits to represent that number.

		The length of the representation is always the number of states for the circuit probe.

		>>> cp = CircuitProbe(3, 3, 0)
		>>> cp.get_binary_state_representation(0)
		[]
		>>> cp.get_binary_state_representation(1)
		[]
		>>> cp.get_binary_state_representation(2)
		[]

		>>> cp = CircuitProbe(3, 3, 2)
		>>> cp.get_binary_state_representation(0)
		[0, 0]

		>>> cp.get_binary_state_representation(1)
		[0, 1]

		>>> cp.get_binary_state_representation(2)
		[1, 0]

		>>> cp.get_binary_state_representation(3)
		[1, 1]
		"""
		rep = []
		index = 0
		shifted = num
		while index < self.__states:
			rep.append(shifted & 1)

			# Advance the shift
			index += 1
			shifted >>= 1

		return rep[::-1]

	def get_numerical_state_representation(self, num):
		"""
		Takes an input list of bytes and returns it as a number

		>>> cp = CircuitProbe(3, 3, 0)
		>>> cp.get_numerical_state_representation([0, 0])
		0
		>>> cp.get_numerical_state_representation([0, 1])
		1
		>>> cp.get_numerical_state_representation([1, 0])
		2
		>>> cp.get_numerical_state_representation([1, 1])
		3

		>>> cp.get_numerical_state_representation([])
		0
		>>> cp.get_numerical_state_representation([0])
		0
		>>> cp.get_numerical_state_representation([1])
		1
		>>> cp.get_numerical_state_representation([0, 0, 0])
		0
		"""
		index = 0
		shifted = 0

		for i in num[::-1]:
			shifted |= (i<<index)
			index += 1

		return shifted
			
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
		previous = { 0: None }

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
					# None is the shortcut for powercycling the circuit
					if path[-1] is None:
						break

					# Use path.append for speed and reverse later
					path.append( previous[ 
						path[-1] ] )

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
		Probes the circuit. Returns a list of unreachable states.
		"""

		# Can't do anything if all outputs have been analyzed
		if len(self.analyzed_outputs) >= self.__outputs:
			if self.__debug:
				print("All outputs have been analyzed")
			return

		tested = {}

		# Power cycle the circuit and check its base state
		self.power_on()
		self.powercycle()
		last_state = base_state = self.get_numerical_state_representation(self.get_current_state())
		if self.__debug:
			print("Circuit base state: {}".format(base_state))

		# Edges contains the path from each state to each state that can be reached from that state
		# Destinations are contained in a tuple: (destination, input) Where input is the required input
		# from the source state to get to the destination
		edges = {}

		# Start by applying inputs sequentially to whatever state the circuit is currently in.
		# This should reduce path lengths generated by the pathfinding
		while True:
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

			if self.__debug:
				print("Testing state {} with input {}".format(last_state, tested[last_state]))

			# Apply the input value
			t_last_state = last_state
			last_state = self.test_and_record(last_state, tested[last_state])

			# Add this to the edges if we've moved between states
			if t_last_state != last_state:
				if t_last_state not in edges:
					edges[t_last_state] = [ (base_state, None) ] # Each state can go to the base state by resetting
				edges[t_last_state].append((last_state, tested[t_last_state]))
				if self.__debug:
					print("Edges are now: ")
					print(edges)

		if self.__debug:
			print("Test stage 1 finished.")

		# Start by building a list of states/inputs that require testing
		untested = {}
		for i in range(self.__states):
			# Get a binary representation of the state
			i_state = self.get_binary_state_representation(i)

			# Check if this state has untested inputs
			if i not in tested or tested[i] != self.__max_input:
				if i not in untested:
					untested[i] = []

				# State has untested inputs
				if i not in tested:
					untested[i] = 0
				else:
					untested[i] = tested[i]

				# for j in range(tested[i] + 1, self.__max_input + 1):
				# 	untested[i].append(j)

		if self.__debug:
			print("Untested states for part 2: {}".format(untested))

		# If there are no untested states, we can stop here!
		if len(untested) == 0:
			self.power_off()
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

					edges[t_last_state].append((last_state, tested[last_state]))

				# Check if this was the last untested input for the state and remove if yes
				if untested[t_last_state] == self.__max_input:
					untested.pop(t_last_state)
				else: 
					untested[t_last_state] += 1
			else:
				# This state has no untested inputs, pathfind to the closest state with untested inputs
				path_to_closest = self.get_closest_untested_state(untested, last_state, base_state, edges)
				print("Closest state: {}".format(path_to_closest))

				# None indicates there is no path to any state we need to check
				if path_to_closest is None:
					break

				# The force is strong here... This path we should follow...
				# follow_path(path_to_closest)
				for i in path_to_closest:
					# For each direction, apply the needed input and check where we are
					if i is None:
						# None indicates a powercycle is needed
						self.powercycle()
					else:
						# Get the input thats going to go from this state to the next
						required_input = [e[1] for e in edges if e[0] == i][0]

						print("Required Input: {}".format(required_input))

						# Set the inputs and pulse the clock to go!
						self.set_inputs(required_input)
						self.pulse_clock()

					last_state = self.get_numerical_state_representation(self.get_current_state())
					if last_state in untested:
						# If the current state has untested stuff, break free!
						print("State found!")
						breaks

		# If we made it this far, then we most likely introduced duplicate rows in the matrix.
		self.matrix.remove_duplicate_rows()

		self.power_off()
		return untested

if __name__ == "__main__":
	# Disable debug mode
	CircuitProbe.default_debug_state = False
	import doctest
	doctest.testmod()