"""
Main logic analyzer class. Implements the main window GUI.
"""

import random
from circuit_probe import CircuitProbe

from tkinter import *
import tkinter.messagebox as MessageBox
# from bitflag import BitFlag


# Singleton GUI instance, only one allowed to be created, remember it for
# global access.
# These are module level variables, on the grounds that the module is the
# singleton instance, the GUI class is just something used to help implement
# the module.

gui = None
# debug = BitFlag()

class GUI():
	"""

	Constructor:

	GUI(init_fn=None, step_fn=None, title="Simulation"):

	The GUI constructor  will raise an exception if you try to create 
	more than one instance.
	
	init_fn() - is a function that is called on simulation start that
		sets up the initial conditions for the simulation.  

	step_fn() - is a function that is called on each time step of the
		simulation.  

	title is the text displayed on the top of the window

	The simulation does not begin until you invoke agentsim.gui.start()

	To get to the canvas in order to draw additional graphics use
		canvas = agentsim.gui.get_canvas()
	which resturns the canvas object, so that, for example, you can 
	add additional artifacts:

	agentsim.gui.get_canvas().create_oval(10, 20, 30, 40, fill='black')

	To get the dimensions of the canvas use
		(x_size, y_size) = agentsim.gui.get_canvas_size():

	To get the actual coordinate space of the canvas use
		(x_min, y_min, x_max, y_max) = agentsim.gui.get_canvas_coords():

	Two convenient clipping functions are provided to ensure that points
	(x,y) will be clipped to be within the canvas coordinate space
		new_x = agentsim.gui.clip_x(x)
		new_y = agentsim.gui.clip_y(y)

	"""

	# there can only be one instance of this class
	num_instances = 0

	def __init__(self, init_fn=None, step_fn=None, stop_fn=None, title="Logic Analyzer", probe=None):
		if GUI.num_instances != 0:
			raise Exception("GUI: can only have one instance of a simulation")
		GUI.num_instances = 1

		self._probe = probe

		self._canvas_x_size = 1000
		self._canvas_y_size = 500

		# if canvas is resized, the corners will change
		self._canvas_x_min = 0
		self._canvas_y_min = 0
		self._canvas_x_max = self._canvas_x_size
		self._canvas_y_max = self._canvas_y_size

		# simulation function hooks
		self._init_fn = init_fn
		self._step_fn = step_fn
		self._stop_fn = stop_fn

		# simulation state
		self._running = 0

		self._title = title

		self._root = Tk()

		self._root.wm_title(title)
		self._root.wm_geometry("+100+80")
		self._root.bind("<Key-q>", self._do_shutdown)

		# create a frame on top to hold settings
		self._settings_frame = Frame(self._root, relief='groove', borderwidth=2)

		# command that validates numerical entry boxes
		numerical_validate_command = (self._root.register(self._validate_numerical),
				'%d', '%i', '%P', '%s', '%S', '%v', '%V', '%W')

		# Command that validates floating point entry boxes
		floating_validate_command = (self._root.register(self._validate_floating),
				'%d', '%i', '%P', '%s', '%S', '%v', '%V', '%W')

		# Toolbar padding
		self._toolbar_pad_x = 2
		self._toolbar_pad_y = 2

		self._entries = {}

		# numerical inputs
		self._add_tk_entry(self._settings_frame, "Inputs:", "inputs", "1", "int", numerical_validate_command)
		self._add_tk_entry(self._settings_frame, "Outputs:", "outputs", "1", "int", numerical_validate_command)
		self._add_tk_entry(self._settings_frame, "States:", "states", "0", "int", numerical_validate_command)

		# floating point inputs
		self._add_tk_entry(self._settings_frame, "Propogation Time (seconds):", "propogation time", "0.01", "float", floating_validate_command)
		self._add_tk_entry(self._settings_frame, "Clock Time (seconds):", "clock time", "0.01", "float", floating_validate_command)

		# pack the settings frame
		self._settings_frame.pack(side=TOP, fill=X)

		# create a frame on the left to hold our controls
		self._frame = Frame(self._root, relief='groove', borderwidth=2)
		self._frame.pack(side='left', fill='y')

		# Add set of buttons bound to specific actions
		#   Analyze 		Runs analysis on the circuit as configured.
		#   Reset    		Resets the canvas
		#   View Stategraph Opens the stategraph for the analyzed circuit
		#   Power On        Powers the circuit on
		# 	Power Off 		Powers the circuit off

		self._b1 = Button(self._frame,
			text='Analyze',
			command=self._do_analysis
			)

		self._b1.pack(anchor='w', fill='x')

		self._b2 = Button(self._frame,
			text='Reset',
			command=self._do_reset
			)

		self._b2.pack(anchor='w', fill='x')

		self._b3 = Button(self._frame,
			text='View Stategraph',
			command=self._do_view_stategraph
			)

		self._b3.pack(anchor='w', fill='x')

		self._b4 = Button(self._frame,
			text='Power On',
			command=self._do_power_on
			)

		self._b4.pack(anchor='w', fill='x')

		self._b4 = Button(self._frame,
			text='Power Off',
			command=self._do_power_off
			)

		self._b4.pack(anchor='w', fill='x')

		self._cf = Frame(self._root)

		self._cf.pack(side='right', fill='both', expand=1)

		self._cf.grid_rowconfigure(0, weight=1)
		self._cf.grid_columnconfigure(0, weight=1)

		self._hscroll = Scrollbar(self._cf,
			orient='horizontal',
			)
		self._hscroll.grid(row=1, column=0, sticky='ew')

		self._vscroll = Scrollbar(self._cf,
			orient='vertical', 
			)

		self._vscroll.grid(row=0, column=1, sticky='ns')

		self._canvas = Canvas(self._cf,
			width=self._canvas_x_size,
			height=self._canvas_y_size,
			scrollregion=(0, 0, self._canvas_x_size, self._canvas_y_size),
			highlightthickness=0,
			borderwidth=0,
			yscrollcommand=self._vscroll.set,
			xscrollcommand=self._hscroll.set,
			)

		self._canvas.grid(column=0, row=0, sticky='nwes')

		self._hscroll.configure( command=self._canvas.xview )
		self._vscroll.configure( command=self._canvas.yview )

		def _do_resize(ev):
			self._canvas_resize(ev.width, ev.height)

		self._canvas.bind( "<Configure>", _do_resize)

	def _add_tk_entry(self, parent, text, shortname, default, entry_type, validation_command):
		self._entries[shortname] = {"label": None, "entry":None, "variable": StringVar(), "type": entry_type}

		self._entries[shortname]["variable"].set(default)

		self._entries[shortname]["label"] = Label(parent,
			text=text)
		self._entries[shortname]["label"].pack(side=LEFT, padx=self._toolbar_pad_x, pady=self._toolbar_pad_y)

		self._entries[shortname]["entry"] = Entry(parent, 
			validate = 'key', 
			validatecommand = validation_command,
			textvariable= self._entries[shortname]["variable"],
			width=8)

		self._entries[shortname]["entry"].pack(side=LEFT, padx=self._toolbar_pad_x, pady=self._toolbar_pad_y)


	def _validate_numerical(self, action, index, value_if_allowed,
					   prior_value, text, validation_type, trigger_type, widget_name):
		if len(text) == 0:
			return True
		if text in '0123456789':
			try:
				int(value_if_allowed)
				return True
			except ValueError:
				return False
		else:
			return False

	def _validate_floating(self, action, index, value_if_allowed,
					   prior_value, text, validation_type, trigger_type, widget_name):
		if len(text) == 0:
			return True
		if text in '0123456789.':
			try:
				float(value_if_allowed)
				return True
			except ValueError:
				return False
		else:
			return False

	def draw_io_graph(self):
		"""
		Draws the graph of IO from the CircuitProbe on the canvas.
		"""
		

		
	# actions attached to buttons are prefixed with _do_
	def do_shutdown(self):
		self._do_shutdown(None)

	def _do_shutdown(self, ev):
		print("Program terminated.")
		# quit()

	def _do_reset(self):
		print("_do_reset not implemented.")
		pass

	def _do_analysis(self):
		# Clear any current state
		self._analysis_complete = False
		self._do_reset()

		# Parse inputs from textbox
		vals = {}
		for i in self._entries:
			entry = self._entries[i]
			val = entry["entry"].get()
			if entry["type"] == "int":
				if len(val) and ((i != "states" and int(val) > 0) or (i == "states" and int(val) >= 0)):
					vals[i] = int(val)
				else:
					MessageBox.showerror(
						"Analyzer Configuration Error",
						"The number of {} entered is invalid.".format(i)
					)
					return

			elif entry["type"] == "float":
				if len(val) and float(val) > 0:
					vals[i] = float(val)
				else:
					MessageBox.showerror(
						"Analyzer Configuration Error",
						"The {} entered is invalid.".format(i)
					)
					return

		# Create the circuit probe with correct configuration or reset the probe with the correct configuration
		if not self._probe:
			self._probe = CircuitProbe(vals["inputs"], vals["outputs"], vals["states"], propogation_time = vals["propogation time"])
		else:
			self._probe.reset(vals["inputs"], vals["outputs"], vals["states"], propogation_time = vals["propogation time"])

		# Run the analysis
		unreachable = self._probe.probe()

		print("Analysis Complete with unreachable states: {}".format(unreachable))
		print("Acquired data:")
		print(self._probe.get_matrix())

	def _do_view_stategraph(self):
		print("_do_view_stategraph not implemented.")
		pass

	def _do_power_on(self):
		if self._probe:
			self._probe.power_on()

	def _do_power_off(self):
		if self._probe:
			self._probe.power_off()

	def get_canvas(self):
		return self._canvas

	def get_canvas_size(self):
		return (self._canvas_x_size, self._canvas_y_size)

	def get_canvas_coords(self):
		return (self._canvas_x_min, self._canvas_y_min,
				self._canvas_x_max, self._canvas_y_max)

	def clip_x(self, x):
		return max(self._canvas_x_min, min(self._canvas_x_max, x))

	def clip_y(self, y):
		return max(self._canvas_y_min, min(self._canvas_y_max, y))

	def canvas_resize(self, new_width, new_height):
		self._canvas_resize(new_width, new_height)

	def _canvas_resize(self, new_x_size, new_y_size):
		"""
		It is not clear what happens when you resize the canvas during
		a simulation.  The positions will eventually get clipped by a
		move_by, but that may be after quite sime time!
		"""
		# don't let x get smaller than 400 or y smaller than 250

		# x only needs to be adjusted to increase
		self._canvas_x_max = max(400, new_x_size)
		self._canvas_x_size = self._canvas_x_max - self._canvas_x_min

		# y min needs to go negative since drawing axis is flipped from model 
		# axis
		self._canvas_y_max = max(250, new_y_size)
		self._canvas_y_size = self._canvas_y_max - self._canvas_y_min

		# adjust the actual size to match the model.  Thus we actually never
		# get the scrollbars enabled unless we make the canvas smaller than
		# the scroll region
		self._canvas.configure(
		  scrollregion=(0, 0, self._canvas_x_size, self._canvas_y_size),
		  )

		# now we also have to move all the objects that are off the canvas
		# into it, or they are in lala land.


def rgb_to_color(r, g, b):
	"""
	Utility to generate a Tk color rgb string from  integer r, g, b, 
	where 0 <= r, g, b <= 1

	Use as in
		agentsim.gui.get_canvas().create_oval(10, 20, 30, 40, 
			fill=agentsim.rgb_to_color(.8, .8, 0) )
	"""

	return '#{0:02x}{1:02x}{2:02x}'.format(
		int((r * 255) % 256), int((g * 255) % 256), int((b * 255) % 256), )


if __name__ == "__main__":
	# Run the program
	gui = GUI()