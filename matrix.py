
class Matrix:
  def __init__(self, row_size, column_size, init_val=0):
		self.__column_size = column_size
		self.__row_size = row_size
		self.__rows = []
		self.__init_val = init_val

		# Load in empty data
		for i in range(row_size):
			self.__rows.append([])
			for j in range(column_size):
				self.__rows[i].append(init_val)

	def __repr__(self):
		return "Matrix()"

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

	def get_row(self, row):
		"""
		Returns the given row from the matrix.

		>>> M = Matrix(2, 2)
		>>> M.set_val(0, 1, 1)
		>>> M.get_row(0)
		[0, 1]
		"""
		return self.__rows[row]

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
				self.__rows[i].append(self.__init_val)

		self.__row_size = new_num_rows
		self.__column_size = new_num_columns


if __name__ == "__main__":
    import doctest
    doctest.testmod()
