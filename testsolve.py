
from matrix import Matrix
from solve import solve_system

# build a matrix
M = Matrix(16, 8)

M.bin_set_row(0 , 0b0001110, 7)
M.bin_set_row(1 , 0b1000111, 7)
M.bin_set_row(2 , 0b0011110, 7)
M.bin_set_row(3 , 0b1011111, 7)
M.bin_set_row(4 , 0b0100110, 7)
M.bin_set_row(5 , 0b1100111, 7)
M.bin_set_row(6 , 0b0110010, 7)
M.bin_set_row(7 , 0b1111010, 7)

print(M)

o = solve_system(M, [0,1,2], [4], [], [], ['a','i','j'], ['x', 'y', 'z'], [])
for name, val in o:
	print("%s = %s" % (name, val))