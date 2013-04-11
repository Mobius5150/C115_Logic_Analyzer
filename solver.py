
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
		Cover: List of Implicant
			All the prime implicants covering this one.
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
		self.MintermCoverCount = 0
		self.Minterms = [self]

		# for debugging, calculate minterm number from inputs
		# this will be overwritten for terms other than base terms
		num = 0
		for v in inputs:
			num += v
			num <<= 1
		num >>= 1
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
	#print("Do join...")
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

	# save a list of the level 1 implicants, the minterms
	minterm_list = [x for x in imp_list]

	# now, for repeatedly join terms at the curent number of either values
	# and add them to the next level
	for level in range(nvars+1):
		#print("====== Level: %d" % level)
		#clear the current covering data for the minterm level implicants
		for minterm in minterm_list:
			minterm.MintermCoverCount = 0

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
					# print("Trying to join: ", imp_to_string(imp_a, ['a', 'i', 'j']),
					# 	                      imp_to_string(imp_b, ['a', 'i', 'j']))
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
							#print("Can't join")
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
						# implicants were.
						new_imp = Implicant(newinputs, \
							               imp_a.Optional and imp_b.Optional)

						#print("Do join => ", imp_to_string(new_imp, ['a', 'i', 'j']))

						# set these implicants as covered by something, they
						# are not part of a prime implicant at that level.
						imp_a.Covered = True
						imp_b.Covered = True

						# add it to the list if we don't have it added already
						# Otherwise we could end up adding it twice, because 
						# for "odd parity" implicants, there are two different 
						# joins of implicants in the current level that could 
						# generate a given implicant in the next level.
						# EG: | + |, and -- + __ could both generate [_]
						# "Odd parity" being implicants with an odd number of
						# "maybe" terms. For even parity terms the result of a
						# join must be unique.
						# NOTE: above, we still set them as covered either 
						# way, because even if the implicants were joined to a
						# duplicate, they are not prime implicants.
						if new_imp.Hash not in next_level_hash_set:
							next_level_hash_set.add(new_imp.Hash)
							next_level_buckets[new_imp.OneCount].append(\
								                                      new_imp)
							#print("not duplicate, add")

							# minterms that form this one are the minterms
							# that form both it was merged from.
							new_imp.Minterms = imp_a.Minterms + imp_b.Minterms

							# increment the cover count on those minterms
							for mint in new_imp.Minterms:
								#print("with minterm:", mint.Group[0])
								mint.MintermCoverCount += 1
						else:
							pass
							#print("duplicate")

		# we have the buckets for the next level now. Look through the 
		# current level for all of the prime implicants, and then
		# discard the rest of them.
		for bucket in current_buckets:
			for imp in bucket:
				# if an implicant is not covered, and it is not optional
				# then it is an essential prime implicant.
				if not imp.Covered and not imp.Optional:
					essential_imp_list.append(imp)
					#print("Got EPI: %s" % imp_to_string(imp, ['a', 'i', 'j']))

		# now set the current buckets to the next, and continue
		current_buckets = next_level_buckets

		# Mark "false EPIs", which are covered completely by other implicants
		# from the new level,
		# We still need these implicants for the next join, but they should
		# not be found to be EPIs in the solution.
		#print("Search for false EPIs")
		for bucket in current_buckets:
			for imp in bucket:
				#print("imp:", imp_to_string(imp, ['a', 'i', 'j']))
				for mint in imp.Minterms:
					print(mint.Group[0], mint.MintermCoverCount)
					if mint.MintermCoverCount <= 1:
						break
				else:
					# all are >= 2, so mark this implicant as covered
					for mint in imp.Minterms:
						mint.MintermCoverCount -= 1
					imp.Covered = True

		# print("terms created:")
		# for bucket in current_buckets:
		# 	for imp in bucket:
		# 		print("|", imp_to_string(imp, ['a', 'i', 'j']))



	# now we have the essential prime implicants these give the simplest
	# possible and-or representation for the circuit.
	print("=> result: ", imp_list_to_string(essential_imp_list, ['a', 'i', 'j']))
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


def imp_list_to_ast(imp_list):
	"""
	Convert a list of essential prime implicants from the into an AST that can 
	be further simplified via factoring out of common terms.
	"""
	if not imp_list:
		#empty implicant list => 0 constant value
		return ['K', 0]

	# build a sum node of the essential prime implicants
	sumnode = ['+']
	for imp in imp_list:
		productnode = ['*']
		for i, val in enumerate(imp.Values):
			if val == ONE:
				productnode.append(['V', i])
			elif val == ZERO:
				productnode.append(['~', ['V', i]])
			else:
				pass # nothing to do
		if len(productnode) > 1:
			sumnode.append(productnode)
		else:
			# empty product = 1
			sumnode.append(['K', 1])

	if len(sumnode) == 2:
		# only one term? Just return the term
		return sumnode[1]
	else:
		return sumnode


def _count_vars(astnode):
	"""

	"""
	if astnode[0] == '+' or astnode[0] == '*':
		count = 0
		for i in range(1,len(astnode)):
			count += _count_vars(astnode[i])
		return count
	elif astnode[0] == '~':
		if astnode[1][0] == 'V':
			return 1
		else:
			return _count_vars(astnode[1])
	elif astnode[0] == 'V':
		return 1
	else:
		return 0


def _ast_equiv(nd1, nd2):
	if nd1[0] == 'V':
		if nd2[0] == 'V':
			return nd1[1] == nd2[1]
		else:
			return False
	if len(nd1) != len(nd2):
		return False
	if nd1[0] != nd2[0]:
		return False
	n1,n2 = sorted(nd1[1:]), sorted(nd2[1:])
	for i in range(len(n1)):
		if not _ast_equiv(n1[i], n2[i]):
			return False
	return True


def _ast_size(astnode):
	"""
	Get the visual size of an AST node

	"""
	#TODO
	return 0


def _ast_children(astnode):
	for i in range(1, len(astnode)):
		yield i, astnode[i]


def _simplify_sum(sumnode):
	"""
	Simplify a sum by pulling out sets of factors from terms. For example:
	ac + ad + bc + bd
	=>
	a(c+d) + b(c+d)
	=>
	(a+b)(c+d)
	"""
	# first make sure this is a sum node
	if sumnode[0] != '+':
		return sumnode

	best_term_index = None
	best_term_factors = None
	best_term_tojoinwith = None
	best_comb_heuristic = 0
	num_candidates = 0

	for term_inx, this_term in _ast_children(sumnode):
		# for each var factor the term, see how many other terms share it
		shares_per_factor = []
		if this_term[0] == '*':
			# factor, pull out terms
			for factor_inx, factor in _ast_children(this_term):
				# set of terms which share this factor
				sharing_terms = set()
				for otherterm_inx in range(term_inx+1, len(sumnode)):
					other_term = sumnode[otherterm_inx]
					for otherfac_inx, otherfac in _ast_children(other_term):
						if _ast_equiv(factor, otherfac):
							# are equivalent, add to shared set
							sharing_terms.add(otherterm_inx)

				# add the shares to the list of shares for the term, as long 
				# as there are at least two terms sharing this factor
				if len(sharing_terms) > 0:
					shares_per_factor.append((factor_inx, sharing_terms))
		else:
			# not a factor. Ignore it
			pass

		# now, look at all the combinations of shares and see which is the 
		# best var to pull out for this term, if there is one to pull out.
		for i in range(1, len(this_term)-1):
			# look for the best set of elements of that size
			for comb in itertools.combinations(shares_per_factor, i):
				total_intersection = comb[0][1]
				for factor_inx, sharing_terms in comb:
					total_intersection = \
						total_intersection.intersection(sharing_terms)
				# if there is an intersection between two or more terms, see
				# if it is the best intersection we've found so far
				if len(total_intersection) > 0:
					# hueristic is the number of vars we can pull out, times
					# the number of terms it can be pulled out of.
					if len(total_intersection)*i >= best_comb_heuristic:
						best_term_index = term_inx
						best_term_factors = [i for i,_ in comb]
						best_term_tojoinwith = [t for t in total_intersection]
						best_comb_heuristic = len(total_intersection)*i
						num_candidates += 1
	result = None


	if num_candidates > 0:
		# now we have a best combination to join. Do the join
		# get things
		base_term = sumnode[best_term_index]
		join_with = best_term_tojoinwith
		join_with.append(best_term_index)
		factors_to_pull = [fac for i,fac \
		                       in _ast_children(base_term) \
		                       if i in best_term_factors]

		# now pull factors out
		for term_inx in join_with:
			term = sumnode[term_inx]

			#now remove the values from the terms
			new_term = ['*']
			for _,current_fac in _ast_children(term):
				for fac_to_rem in factors_to_pull:
					if _ast_equiv(current_fac, fac_to_rem):
						break
				else:
					new_term.append(current_fac)

			#add the new term
			if len(new_term) == 2:
				# product of one factor
				sumnode[term_inx] = new_term[1]
			else:
				sumnode[term_inx] = new_term

		# make a new term with all the joined terms
		main_new_term = ['+']
		factor_part = ['*']
		factored_terms = ['+']
		main_new_term.append(factor_part)
		for fac in factors_to_pull:
			factor_part.append(fac)
		factor_part.append(factored_terms)

		for i,term in _ast_children(sumnode):
			if i in join_with:
				factored_terms.append(term)
			else:
				main_new_term.append(term)

		factor_part[-1] = _simplify_sum(factor_part[-1])

		if len(main_new_term) == 2:
			#sum of 1 elements
			result = main_new_term[1]
		else:
			result = main_new_term
	else:
		result = sumnode

	if num_candidates > 0:
		result = _simplify_sum(result)

	return result



def simplify_ast(ast):
	"""

	"""
	return _simplify_sum(ast)



def ast_to_string(ast, var_names):
	if ast[0] == '+':
		return ' + '.join([ast_to_string(ast[n], var_names) 
			               for n in range(1,len(ast))])
	elif ast[0] == '*':
		strs = []
		for _,ch in _ast_children(ast):
			if ch[0] == 'V' or ch[0] == 'K' or ch[0] == '~':
				strs.append(ast_to_string(ch, var_names))
			else:
				strs.append('(%s)' % ast_to_string(ch, var_names))
		return ''.join(strs)
	elif ast[0] == '~':
		if ast[1][0] == 'V' or ast[1][0] == 'K':
			return ast_to_string(ast[1], var_names) + "'"
		else:
			return "(%s)'" % ast_to_string(ast[1], var_names)
	elif ast[0] == 'V':
		return var_names[ast[1]]
	elif ast[0] == 'K':
		return str(ast[1])
	else:
		raise Exception('Bad ast entry')




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


if __name__ == "__main__":
	print(ast_to_string(simplify_ast(['+', ['*', ['V', 0], ['V', 2]], \
		                             ['*', ['V', 0], ['V', 3]], \
		                             ['*', ['V', 1], ['V', 2]], \
		                             ['*', ['V', 1], ['V', 3]]  ]), ['a', 'b', 'c', 'd']))
	# import doctest
	# doctest.testmod()





