
from matrix import Matrix
import itertools

"""
Possible "state values"
"""
ZERO = 0
ONE = 1
EITHER = 2


class Implicant:
	"""
	Implicant class
	Stores the information about an implicant for use in simplification
	algorithms.
	Properties:
		Values: Array of state values
			The values for the inputs for this implicant. If all are 0/1
			then this implicant just represents a single minterm, but once
			"either" values are introduced, it represents multiple minterms.
		Group: List of integers
			All the minterms that are contained in this implicant.
		Optional: Bool
			Is this minterm really a don't care term?
		OneCount: Integer
			The number of 1's in the possible inputs for this implicant.
		Covered: Bool
			Has this implicant been covered? (and is thus redundant)
		Hash: Integer
			Unique integer representing Values array, can be used to test
			implicants for equivalence.

	"""
	def __init__(self, inputs, optional = False):
		"""
		Construct an implicant from a set of inputs and a specification of
		whether or not it is optional.
		"""
		self.Group = []
		self.Optional = optional
		self.OneCount = 0
		self.Covered = False

		# for debugging, calculate minterm number from inputs
		# this will be overwritten for terms other than base terms
		num = 0
		for v in inputs:
			num += v
			num <<= 1
		num >>= num
		self.Group.append(num)

		# traverse the values list initializing the one and maybe count
		self.Values = inputs
		for v in inputs:
			if v == ONE:
				self.OneCount += 1

		# create a hash value, for quick testing of equivalence
		self.Hash = 2
		for v in inputs:
			self.Hash += v
			self.Hash <<= 2

 
	def __str__(self):
		"""
		Generate a string representation of the minterm. This is a pretty
		representation, good for debugging, but not suitable for final
		display to a user.
		"""
		s = ''
		for i in range(nvars):
			# if self.Values[i] == ONE:
			# 	s += varnames[i]
			# elif self.Values[i] == ZERO:
			# 	s += varnames[i]
			# 	s += "'"
			if self.Values[i] == ONE:
				s += '1'
			elif self.Values[i] == ZERO:
				s += '0'
			elif self.Values[i] == EITHER:
				s += '-'
			else:
				raise Exception("Illegal State")
		return s


def _fast_bucketed_join(imp_list, nvars):
	"""
	Joins adjacent same-sized minterms.
	Work on each size, creating halfing the number of implicants at each
	step up in size of the implicants.
	The general algorithm is to look at the set of implicants at each "size",
	that is, a given number of "either" values for each variable.
	And for each of those sets of implicants, generate the _next_ set of 
	implicants by joining pairs differing by only one value.
	Although n^2 at first glance, this turns out to be pretty efficient, as
	only terms differing by one "1/0 pair" can be joined. This means that we
	can maintain the count of 1's in every implicant and sort them into
	buckets based on that number. Then the set of terms in a given bucket need
	only be compared to the terms in the next bucket. 
	"""
	# essential implicant list. To be built up as the algorithm progresses
	essential_imp_list = []

	# sort the implicants into buckets based on the number of 1's in each
	# buckets is indexed as buckets[onecount]
	# where "size" is the number of "either" values in a term
	current_buckets = [[] for i in range(nvars+1)]
	for imp in imp_list:
		current_buckets[imp.OneCount].append(imp)

	# now, for repeatedly join terms at the curent number of either values
	# and add them to the next level
	for level in range(nvars+1):
		# make the buckets for the next level
		next_level_buckets = [[] for i in range(nvars+1)]
		next_level_hash_set = set()

		# for each number of ones
		# note: we only want to go to the -1'th element, but the list length
		#       is nvars+1, so we end up using range(nvars).
		for nvars_a in range(nvars):
			# loop over the pairs for that number of ones, and that number
			# of ones +1.
			for imp_a in current_buckets[nvars_a]:
				for imp_b in current_buckets[nvars_a+1]:
					# try to join the implicants. They should only differ in
					# one place, where one contains a 0 and the other
					# contains a 1.
					# We know the only differ by one digit, so the only case
					# where they can't be joind is where they are unequal and
					# not a 0/1 pair.
					hasbadvalue = True
					for i in range(nvars):
						a = imp_a.Values[i]
						b = imp_b.Values[i]
						if a != b and (a != ZERO or b != ONE):
							break
					else:
						# no bad value found, join
						# form the new inputs
						newinputs = []
						for i in range(nvars):
							if imp_a.Values[i] != imp_b.Values[i]:
								newinputs.append(EITHER)
							else:
								newinputs.append(imp_a.Values[i])

						# make new implicant. Optional if both the joined 
						# implicants were group consists of both of the old 
						# implicant's groups.
						new_imp = Implicant(newinputs, \
							               imp_a.Optional and imp_b.Optional)
						new_imp.Group = imp_a.Group + imp_b.Group

						# set the covered of the old implicants to true
						imp_a.Covered = True
						imp_b.Covered = True

						# add it to the list
						if new_imp.Hash not in next_level_hash_set:
							next_level_hash_set.add(new_imp.Hash)
							next_level_buckets[new_imp.OneCount].append(\
								                                      new_imp)

		# we have the buckets for the next level now. Look through the 
		# current level for all of the prime implicants, and then
		# discard the rest of them.
		for bucket in current_buckets:
			for imp in bucket:
				# if an implicant is not covered, and it is not optional
				# then it is an essential prime implicant.
				if not imp.Covered and not imp.Optional:
					essential_imp_list.append(imp)

		# now set the current buckets to the next, and continue
		current_buckets = next_level_buckets

	# now we have the essential prime implicants these give the simplest
	# possible and-or representation for the circuit.
	return essential_imp_list


def solve_and_or(m, output_index, input_index_list):
	"""
	Finds the minimal and-or circuit representation for the given function.
	This expansion can be further simplified through other means,
	but this provides a stable algorithm to reduce the logic to
	a reasonable size initially, from the big table of input data
	read during data collection.
	The and-or circuit is a good choice for this, because typically real-world 
	circuits tend to have a very low truth-density, leading to few terms being
	needed in the minimal and-or form.

	Input cols should contain either 0 or 1 for every row.
	The output col should contain 0, 1, or "either" for every row.

	The output is a list of implicants, which can be passed to other
	simplification functions, or 
	"""

	# first we need to turn the output matrix into a list of implicants
	imp_list = []
	for row_n in range(m.get_num_rows()):
		row = m.get_row(row_n)
		if row[output_index] == ONE or row[output_index] == EITHER:
			# add this minterm as an implicant
			values = []
			for i in input_index_list:
				values.append(row[i])
			implicant = Implicant(values, (row[output_index] == EITHER))
			imp_list.append(implicant)

	# now, we perform a joining algorithm on the implicants. This will give
	# a minimal and-or circuit representation for the logic.
	imp_list = _fast_bucketed_join(imp_list, len(input_index_list))

	return imp_list


def imp_to_string(imp, var_names):
	"""
	Gives the string formatting of an implicant.

	>>> imp_to_string(Implicant([1,1,0]), ['A', 'B', 'C'])
	ABC'

	>>> imp_to_string(Implicant([0,EITHER,1]), ['A', 'B', 'C'])
	A'C
	"""
	s = ""
	for i, v in enumerate(imp.Values):
		if v == ZERO:
			s += var_names[i]+"'"
		elif v == ONE:
			s += var_names[i]
	if len(s) == 0:
		s = "1"
	return s


def imp_list_to_string(imp_list, var_names):
	"""
	Gives a string formatting of an implicant list
	"""
	return ' + '.join([imp_to_string(imp, var_names) for imp in imp_list])


def test():
	# inputs
	func = lambda a,b,c,d: a or not c
	varnames = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
	nvars = 4

	# build table
	m = Matrix(2**nvars, nvars+1, 0)
	for row in range(2**nvars):
		args = []
		n = row
		for i in range(nvars):
			args.append(n%2 == 1)
			n >>= 1
		m.bin_set_row(row, row, nvars)
		m.set_val(row, nvars, 1 if func(*(args[::-1])) else 0)

	#print(m)

	res = solve_and_or(m, nvars, [x for x in range(nvars)])
	#print("=> Done: ")
	print(imp_list_to_string(res, varnames))

if __name__ == "__main__":
	test()





