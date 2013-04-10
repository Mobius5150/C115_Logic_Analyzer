
from matrix import Matrix
from solve import solve_system

# build a matrix
M = Matrix(16, 7)

M.bin_set_row(0 , 0b0000000, 7)
M.bin_set_row(1 , 0b0100000, 7)
M.bin_set_row(2 , 0b1001000, 7)
M.bin_set_row(3 , 0b0011000, 7)
M.bin_set_row(4 , 0b0110000, 7)
M.bin_set_row(5 , 0b1101000, 7)
M.bin_set_row(6 , 0b1011000, 7)
M.bin_set_row(7 , 0b1110000, 7)

print(M)

o = solve_system(M, [0,1], [], [2], [3], ['a', 'b'], [], ['i'])
for name, val in o:
	print("%s = %s" % (name, val))