
from matrix import Matrix
from solve import solve_system

# build a matrix
M = Matrix(16, 5)

M.bin_set_row(0 , 0b00000, 5)
M.bin_set_row(1 , 0b00111, 5)
M.bin_set_row(2 , 0b01001, 5)
M.bin_set_row(3 , 0b01111, 5)
M.bin_set_row(4 , 0b10010, 5)
M.bin_set_row(5 , 0b10101, 5)
M.bin_set_row(6 , 0b11011, 5)
M.bin_set_row(7 , 0b11101, 5)

print(M)

o = solve_system(M, [0,1], [4], [2], [3], ['a', 'b'], ['y'], ['s'])
for name, val in o:
	print("%s = `%s`" % (name, val))