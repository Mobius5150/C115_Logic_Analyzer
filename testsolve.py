
from matrix import Matrix
from solve import *

"""
Unit testing to make sure that the solver runs right during development.
"""

def test_function(f, inputcount):
	M = Matrix(2**inputcount, inputcount+1)
	for row in range(2**inputcount):
		args = []
		n = row
		for _ in range(inputcount):
			args.append(True if (n % 2) else False)
			n >>= 1
		args = args[::-1]
		v = (ONE if f(*args) else ZERO)
		n = (row << 1) + v
		M.bin_set_row(row, n, inputcount+1)

	o = solve_system(M, [x for x in range(inputcount)], [inputcount], [], [],
		                ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'], ['X'], [])

	print(o[0])


test_function(lambda a,b,c,d,e,f,g,h: ((a or b) and (c or d) and (e or f or g)) or h, 8)