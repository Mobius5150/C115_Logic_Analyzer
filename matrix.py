"""
Implements a very simple matrix class with doctests.
"""

class Matrix:
	def __init__(self, row_size, column_size, init_val=0):
		self.__column_size = column_size
		self.__row_size = row_size
		self.__rows = []
		self.__init_val = init_val

		# Build a matrix of initial values
		self.__rows = [[init_val for col in range(column_size)] \
		                         for row in range(row_size)]

	def __repr__(self):
		return self.__str__()

	def __str__(self):
		rep = ""
		for i in self.__rows:
			rep += str(i) + "\n"

		# Removes the last newline character
		return rep[:len(rep)-1]

	def get_val(self, row, column):
		"""
		Gets a value from the given position in the matrix.

		>>> M = Matrix(2, 2)
		>>> M.get_val(0,0)
		0

		>>> M.set_val(0,0, 1)
		>>> M.set_val(0,1, 0)
		>>> M.get_val(0,0)
		1
		>>> M.get_val(0,1)
		0
		"""
		return self.__rows[row][column]

	def set_val(self, row, column, value):
		"""
		Sets the value at the given (row, column).

		>>> M = Matrix(2, 2)
		>>> M.set_val(0, 0, 1)
		>>> M.set_val(1, 1, 1)
		>>> print(M)
		[1, 0]
		[0, 1]

		"""
		self.__rows[row][column] = value

	def set_init_val(self, init_val):
		"""
		Sets the value used to initialize new rows/colums
		"""
		self.__init_val = init_val

	def bin_set_row(self, row, num, num_bits, start_offset = 0):
		"""
		Takes the last num_bits of num and inserts them into the row.
		num = 0 0 0 0 0 0 1 0 1 1
		row =           # # # # # # # # #
		Then bin_set_row, with num_bits = 5 will give row:
		row = 0 1 0 1 1 # # # #

		>>> M = Matrix(1, 6)
		>>> M.bin_set_row(0, 11, 5)
		>>> M.get_row(0)
		[0, 1, 0, 1, 1, 0]

		>>> M = Matrix(1, 6)
		>>> M.bin_set_row(0, 11, 4)
		>>> M.get_row(0)
		[1, 0, 1, 1, 0, 0]

		>>> M = Matrix(1, 6)
		>>> M.bin_set_row(0, 11, 4, start_offset = 1)
		>>> M.get_row(0)
		[0, 1, 0, 1, 1, 0]

		>>> M = Matrix(1, 6)
		>>> M.bin_set_row(0, 11, 4, start_offset = 2)
		>>> M.get_row(0)
		[0, 0, 1, 0, 1, 1]

		>>> M = Matrix(1, 6)
		>>> M.bin_set_row(0, [1, 0, 1, 1], 4)
		>>> M.get_row(0)
		[1, 0, 1, 1, 0, 0]

		>>> M = Matrix(1, 6)
		>>> M.bin_set_row(0, [1, 0, 1, 1], 4, start_offset = 2)
		>>> M.get_row(0)
		[0, 0, 1, 0, 1, 1]
		"""
		if num_bits + start_offset <= 0:
			return

		if num_bits + start_offset > self.__column_size:
			raise Exception("Num bits cannot be larger than num columns")

		if type(num) is list:
			num.reverse()
			for i in range(0, num_bits):
				self.__rows[row][num_bits + start_offset -1-i] = (num[i]) & 1
			num.reverse()
		else:
			for i in range(0, num_bits):
				self.__rows[row][num_bits + start_offset -1-i] = (num >> i) & 1

	def get_num_rows(self):
		return self.__row_size

	def get_num_cols(self):
		return self.__column_size

	def get_row(self, row):
		"""
		Returns the given row from the matrix.

		>>> M = Matrix(2, 2)
		>>> M.set_val(0, 1, 1)
		>>> M.get_row(0)
		[0, 1]
		"""
		return self.__rows[row]

	def insert_row(self):
		"""
		Adds a row to the end of the matrix.

		>>> M = Matrix(2, 2)
		>>> M.insert_row()
		>>> print(M)
		[0, 0]
		[0, 0]
		[0, 0]

		>>> M.expand(3, 3)
		>>> M.insert_row()
		>>> M
		[0, 0, 0]
		[0, 0, 0]
		[0, 0, 0]
		[0, 0, 0]
		"""
		self.__row_size += 1
		new_row = [self.__init_val for i in range(self.__column_size)]
		
		self.__rows.append(new_row)


	def insert_row_at_position(self, row_position, new_row = None):
		"""
		Inserts a blank row after the given row.

		>>> M = Matrix(2, 2, 1)
		>>> M.set_init_val(0)
		>>> M.insert_row_at_position(1)
		>>> print(M)
		[1, 1]
		[0, 0]
		[1, 1]

		>>> M.insert_row_at_position(1, [-1, -1])
		>>> print(M)
		[1, 1]
		[-1, -1]
		[0, 0]
		[1, 1]

		"""
		if new_row is None:
			new_row = [self.__init_val for i in range(self.__column_size)]

		if len(new_row) < self.__column_size:
			raise Exception("Error: Specified column too small.")
		
		self.__row_size += 1
		self.__rows.insert(row_position, new_row)

	def get_column(self, column):
		"""
		Returns the given column from the matrix.

		>>> M = Matrix(2, 2)
		>>> M.set_val(1, 1, 1)
		>>> M.get_column(0)
		[0, 0]
		>>> M.get_column(1)
		[0, 1]
		"""
		col = []

		for row in self.__rows:
			col.append(row[column])

		return col

	def expand(self, new_num_rows, new_num_columns):
		""" 
		Expands the matrix.

		>>> M = Matrix(2, 2)
		>>> M.set_val(1, 1, 1)
		>>> M.expand(3, 3)
		>>> M.get_row(0)
		[0, 0, 0]
		>>> M.get_row(1)
		[0, 1, 0]
		>>> M.get_column(0)
		[0, 0, 0]
		>>> M.get_column(1)
		[0, 1, 0]

		"""
		if new_num_rows < self.__row_size or new_num_columns < self.__column_size:
			raise Exception("Expand cannot shrink matrix.")

		# Add new columns
		for row in self.__rows:
			for j in range(self.__column_size, new_num_columns):
				row.append(self.__init_val)

		# Add new rows
		for i in range(self.__row_size, new_num_rows):
			self.__rows.append([])
			for j in range(new_num_columns):
				self.__rows[-1].append(self.__init_val)

		self.__row_size = new_num_rows
		self.__column_size = new_num_columns

	def filter_rows(self, row_filter=None):
		"""
		Returns an array of rows filtered by the given filter function.

		If no filter is specified returns the whole matrix.

		>>> M = Matrix(3, 3)
		>>> M.set_val(0, 0, 1)
		>>> M.set_val(2, 2, 1)
		>>> M.filter_rows()
		[[1, 0, 0], [0, 0, 0], [0, 0, 1]]
		>>> M.filter_rows(lambda row: 1 in row)
		[[1, 0, 0], [0, 0, 1]]
		"""
		if row_filter is None:
			return self.__rows

		return_array = []
		for row in self.__rows:
			if row_filter(row):
				return_array.append(row)

		return return_array


def matrix_generator(inputs=0, states=0, outputs=0):
	# Calculate the number of columns we need
	num_cols = inputs+outputs+2*states
	return Matrix(1, num_cols)


if __name__ == "__main__":
	import doctest
	doctest.testmod()