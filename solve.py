
from solver import *

def solve_system(m, input_i, output_i, state_i, nstate_i, input_n, output_n, state_n):
	"""
	Solve a system with data gathered in the matrix m, and the input / output
	/ state names / indicies in that matrix specified. 
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

		# then the next state J and K values
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
		new_m.bin_set_row(row_i, newrow, ncols)


	# now, we need to gather the results for each output in terms of a set of
	# input and current state.
	result_list = [] # [ (name,simplified expression) ]

	# get arguments for simplifier
	all_input_index_list = []
	all_input_name_list = []
	# add inputs and states
	for i in range(len(input_i)):
		all_input_name_list.append(input_n[i])
		all_input_index_list.append(i)
	for i in range(len(state_i)):
		all_input_name_list.append(state_n[i])
		all_input_index_list.append(len(input_i) + i)

	# first get the outputs in terms of the inputs
	for out_i in range(len(output_i)):
		implicant_list = solve_and_or(new_m, 
		                              len(input_i)+len(state_i)+out_i,
		                              all_input_index_list)
		result = imp_list_to_string(implicant_list, all_input_name_list)
		result_list.append((output_n[out_i], result))

	# then get the next-state JK inputs
	for st_i in range(len(state_i)):
		# J input
		implicant_list = solve_and_or(new_m,
		                              len(input_i)+len(state_i)+len(output_i)\
		                              +2*st_i,
		                              all_input_index_list)
		result = imp_list_to_string(implicant_list, all_input_name_list)
		result_list.append((state_n[st_i]+'_J', result))

		# K input
		implicant_list = solve_and_or(new_m,
		                              len(input_i)+len(state_i)+len(output_i)\
		                              +2*st_i+1,
		                              all_input_index_list)
		result = imp_list_to_string(implicant_list, all_input_name_list)
		result_list.append((state_n[st_i]+'_K', result))

	# and return that result list
	return result_list
