
from solver import *

def solve_system(m, input_i, output_i, state_i, nstate_i, input_n, output_n, state_n):
	"""
	Solve a system with data gathered in the matrix m, and the input / output
	/ state names / indicies in that matrix specified. 

	The _n name arrays are contain the names of the given col indicies into 
	the matrix given in the _i arrays. For example, if my inputs, called A and
	B are in cols 1 and 3, then I would pass:
	input_i = [0,2]
	input_n = ['A', 'B']

	state_i and nstate_i are the state and new state column sets. They must
	have the same length, as every state must have the next state given for
	every row. Both of these use the names given in state_n.

	Results are returned in a list of tuples:
		(result name: string, result expression: string)

	Example:
	column |   quanitity
	-----------------------
	   0   |  input `a`
	   1   |  state `i`
	   2   |  state `j`
	   3   |   Unused
	   4   |  output `x`
	   5   |  output `y`
	   6   |  nextstate `i`
	   7   |  nextstate `j`

	Construct matrix:
	>>> M = Matrix(16, 8)
	>>> M.bin_set_row(0 , 0b0001110, 7)
	>>> M.bin_set_row(1 , 0b1000111, 7)
	>>> M.bin_set_row(2 , 0b0011110, 7)
	>>> M.bin_set_row(3 , 0b1011111, 7)
	>>> M.bin_set_row(4 , 0b0100110, 7)
	>>> M.bin_set_row(5 , 0b1100111, 7)
	>>> M.bin_set_row(6 , 0b0110010, 7)
	>>> M.bin_set_row(7 , 0b1111010, 7)

	Run solver:
	>>> result_list = solve_system(M, [0], [4,5], [1,2], [6,7], ['a'], ['x', 'y'], ['i','j'])

	Result for the output variables x and y in cols 4 and 5:
	>>> result_list[4]
	('x', "i' + j'")
	>>> result_list[5]
	('y', '1')

	"""
	# total cols in the matrix to solve
	ncols = len(input_i)+len(output_i)+len(state_i)*3

	# the new matrix to populate
	new_m = Matrix(m.get_num_rows(), ncols, 0)

	# transcribe the rows of the data matrix into the new matrix
	for row_i in range(m.get_num_rows()):
		row = m.get_row(row_i)
		newrow = []

		# row format:
		# [ input | curstate | output | nextstate JK ]

		# first, the inputs
		for in_i in input_i:
			newrow.append(row[in_i])

		# then the current state
		for st_i in state_i:
			newrow.append(row[st_i])

		# then the outputs
		for out_i in output_i:
			newrow.append(row[out_i])

		# then the next state J and K values (implement state transitions
		# as if using JKFF to implement state)
		for ns_i in range(len(nstate_i)):
			a = row[state_i[ns_i]]
			b = row[nstate_i[ns_i]]
			if a == 0 and b == 1:
				# 0->1, JK = 1X
				newrow.append(1)
				newrow.append(EITHER)
			elif a == 0 and b == 0:
				# 0->0, JK = 0X
				newrow.append(0)
				newrow.append(EITHER)
			elif a == 1 and b == 0:
				# 1->0, JK = X1
				newrow.append(EITHER)
				newrow.append(1)
			else:
				# 1->1, JK = X0
				newrow.append(EITHER)
				newrow.append(0)

		# and add the row
		for i,v in enumerate(newrow):
			new_m.set_val(row_i, i, v)

	# now, we need to gather the results for each output in terms of a set of
	# input and current state.
	result_list = [] # [ (name,simplified expression) ]

	# get arguments for simplifier, and formatting code
	all_input_index_list = []
	all_input_name_list = []
	# populate those lists
	for i in range(len(input_i)):
		all_input_name_list.append(input_n[i])
		all_input_index_list.append(i)
	for i in range(len(state_i)):
		all_input_name_list.append(state_n[i])
		all_input_index_list.append(len(input_i) + i)

	# get the next-state JK inputs in terms of the inputs
	for st_i in range(len(state_i)):
		# J input
		implicant_list = solve_and_or(new_m,
		                              len(input_i)+len(state_i)+len(output_i)\
		                              +2*st_i,
		                              all_input_index_list)
		ast = imp_list_to_ast(implicant_list)
		ast = simplify_ast(ast)
		result = ast_to_string(ast, all_input_name_list) 
		result_list.append((state_n[st_i]+'_J', result))

		# K input
		implicant_list = solve_and_or(new_m,
		                              len(input_i)+len(state_i)+len(output_i)\
		                              +2*st_i+1,
		                              all_input_index_list)
		ast = imp_list_to_ast(implicant_list)
		ast = simplify_ast(ast)
		result = ast_to_string(ast, all_input_name_list)
		result_list.append((state_n[st_i]+'_K', result))

	# get the outputs in terms of the inputs
	for out_i in range(len(output_i)):
		implicant_list = solve_and_or(new_m, 
		                              len(input_i)+len(state_i)+out_i,
		                              all_input_index_list)
		ast = imp_list_to_ast(implicant_list)
		ast = simplify_ast(ast)
		result = ast_to_string(ast, all_input_name_list)
		result_list.append((output_n[out_i], result))

	# and return that result list
	return result_list



# doctest footer
if __name__ == "__main__":
	import doctest
	doctest.testmod()
