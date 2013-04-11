
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
	algorithms. If the "size" (number of "maybe" bits) of the implicant is
	zero then the implicant represents a minterm.
	Properties:
		Values: Array of state values
			The values for the inputs for this implicant. If all are 0/1
			then this implicant just represents a single minterm, but once
			"either" values are introduced, it represents multiple minterms.
		Optional: Bool
			Is this minterm really a don't care term?
		OneCount: Integer
			The number of 1's in the possible inputs for this implicant.
		Covered: Boolean
			Is there an implicant covering this 
		Minterms: Array of Implicant
			All of the minterm implicants that were joined to from this one.
		MintermCoverCount: Integer
			Temporary value during simplification, the number of implicants at
			the current level which are covering this implicant.
			Only set for implicants which are minterms. 
		Hash: Integer
			Unique integer representing Values array, can be used to test
			implicants for equivalence.

	"""
	def __init__(self, inputs, optional = False):
		"""
		Construct an implicant from a set of inputs and a specification of
		whether or not it is optional.
		"""
		self.Optional = optional
		self.OneCount = 0
		self.Covered = False
		self.MintermCoverCount = 0
		self.Minterms = [self]

		# traverse the values list initializing the one and maybe count
		self.Values = inputs
		for v in inputs:
			if v == ONE:
				self.OneCount += 1

		# create a hash value, from the inputs for quick testing of 
		# equivalence
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
	Simplify a set of implicants.

	Joins adjacent same-sized minterms until the minimal two-level AND-OR form
	of the given logical function is reached (which can again be represented
	as a list of implicants, the essential prime implicants to be exact)

	Work on each "size" of implicant consecutively, halfing the number of 
	implicants at each step up in size of the implicants.

	The general algorithm is to look at the set of implicants at each "size",
	that is, a given number of "either" values for each variable.
	And for each of those sets of implicants, generate the _next_ set of 
	implicants by joining pairs differing by only one value. Each of these
	sets of implicants makes up one of the "levels".

	Although n^2 at first glance, this turns out to be pretty efficient, as
	only terms differing by one "1/0 pair" can be joined. This means that we
	can maintain the count of 1's in every implicant and sort them into
	buckets based on that number. Then the set of terms in a given bucket need
	only be compared to the terms in the next bucket.

	The result is achieved by finding the terms at each "level" that are not
	totally covered by either terms of that level or the next one. These terms
	cannot possibly be covered by any further levels, which are only generated
	via joins of implicants, so they must be the "essential prime implicants",
	AKA the "EPIs".

	The algorithm consists of gathering the EPIs at each level as we walk
	throught the levels doing joins. The result is the list of all the EPIs
	gathered at all levels.
	"""
	# Essential implicant list. To be built up as the algorithm progresses
	essential_imp_list = []

	# Sort the initial implicants into buckets based on the number of 1's in 
	# each.
	# Buckets is indexed as buckets[onecount]
	current_buckets = [[] for i in range(nvars+1)]
	for imp in imp_list:
		current_buckets[imp.OneCount].append(imp)

	# save a list of the level 1 implicants, the minterms. We need this to
	# detemine which implicants are covered by implicants of the same level.
	minterm_list = [x for x in imp_list]

	# Now, for repeatedly join terms at the curent number of either values
	# and add them to the next level
	for level in range(nvars+1):
		#clear the current covering data for the minterm level implicants
		for minterm in minterm_list:
			minterm.MintermCoverCount = 0

		# make the buckets for the next level
		next_level_buckets = [[] for i in range(nvars+1)]
		next_level_hash_set = set()

		# for each number of ones
		# note: we only want to go to the -1'th element, but the list length
		#       is nvars+1, because we can have [0,nvars] inclusive as values,
		#       so we end up just iterating range(nvars).
		for nvars_a in range(nvars):
			# loop over the pairs: implicants with that number of ones, and 
			# that number of ones +1.
			for imp_a in current_buckets[nvars_a]:
				for imp_b in current_buckets[nvars_a+1]:
					# try to join the implicants. They should only differ in
					# one place, where one contains a 0 and the other
					# contains a 1.
					# We know the only differ by one digit, so the only case
					# where they can't be joind is where they are unequal and
					# not a 0/1 pair.
					for i in range(nvars):
						a = imp_a.Values[i]
						b = imp_b.Values[i]
						if a != b and (a != ZERO or b != ONE):
							break
					else:
						# no "bad" value found, join
						# build the set of inputs for the new joined minterm.
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

							# minterms that form this one are the minterms
							# that form both it was merged from.
							new_imp.Minterms = imp_a.Minterms + imp_b.Minterms

							# increment the cover count on those minterms
							for mint in new_imp.Minterms:
								mint.MintermCoverCount += 1


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


		# Mark "false EPIs" in the new level, which are covered completely by 
		# other implicants from the new level.
		# We do this by finding implicants that are formed only by minterms
		# that are covered by >= 2 implicants. These implicants can be
		# "subtracted" away from the minterms and marked as covered.
		# They may be further covered by the next join, but not necesarily.
		for bucket in current_buckets:
			for imp in bucket:
				# check that all the minterms are good.
				for mint in imp.Minterms:
					if mint.MintermCoverCount <= 1:
						break
				else:
					# all are >= 2, so mark this implicant as covered
					for mint in imp.Minterms:
						mint.MintermCoverCount -= 1
					imp.Covered = True

	# now we have the essential prime implicants these give the simplest
	# possible and-or representation for the circuit. Return as the result
	return essential_imp_list




def solve_and_or(m, output_index, input_index_list):
	"""
	Finds the minimal and-or circuit representation for the given function.
	This reduction can be further simplified through other means, but this 
	provides a stable algorithm to reduce the logic to a reasonable size 
	initially, from the big table of input data read during data collection.

	The and-or circuit is a good choice for this, because typically real-world 
	circuits tend to have a very low truth-density, leading to few terms being
	needed in the minimal and-or form. This this is a good starting point for
	more simplifications.

	Arguments: 
		m: data matrix, with rows representing inputs => outputs sets
		output_index: the column number of the output to solve for
		input_index_list: the inputs that the col number depends on.

	Notes:
		Input cols should contain either 0 or 1 for every row.

		The output col may contain 0, 1, but also "either" for every row, and
		the simplification algorithm will find the best value for any either
		outputs given.
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

	# return the implicant list
	return imp_list




def imp_list_to_ast(imp_list):
	"""
	Convert a list of essential prime implicants from the into an AST that can 
	be further simplified via factoring out of common terms.

	AST format:
	<var> := 
		['V', <number>]

	<const> := 
		| ['K', 0]
		| ['K', 1]

	<base> := 
		| <var>
		| <const> 

	<product> :=
		['*', <node>, <node>, ...]

	<sum> :=
		['+', <node>, <node>, ...]

	<negation> :=
		['~', <node>]

	<node> :=
		| <sum>
		| <product>
		| <negation>

	<ast> :=
		<node>
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




def _ast_equiv(nd1, nd2):
	"""
	Test two AST nodes for equivalence.
	Tests only up to and including order. No transformations are done other
	than re-ordering of sum / product terms.
	Note: Has O(nmlogn) complexity where n is the typical size of nodes, and
	      m is the number of nodes in the trees for nd1 and nd2.
	      However, behaves close to O(1) in most cases since it can bail out
	      early on clearly dissimilar nodes.
	"""
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




def _ast_children(astnode):
	"""
	generator, returning all the (index, node) pairs for children of an AST 
	node. Index is given such that astnode[index] = node
	"""
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
	With one call to _simplify_sum

	sumnode should be a sum node node

	General Algorithm. We repeatedly try to find "best factor" to pull out of
	the set of terms given in the sum node.

	The "best factor" is given as the factor such that the heuristic:
	>	(#of terms to factor out of) * (number of variables in the factor)
	Is maximized.

	This should gaurantee that products that can be represented in the form:
	>	(a+b+...)(c+d+...)...(w+z+...) + ...
	Will always be simplified down to that form.

	The algorithm is applied repeatedly until no factors to pull out are
	found in a given pass. The algorithm returns the resulting AST at that
	point.

	Note: This algorithm assumes that there are no redundant terms in the
	      input to begin with. It will not eliminate redundant terms.
	      Where "redundant terms" means terms that can be removed without
	      changing the meaning of the sum.
	"""
	# first make sure this is actually a sum node, for convineince.
	if sumnode[0] != '+':
		return sumnode

	# best factor to pull out: 
	best_term_index = None       # the "base term" to find the factor in
	best_term_factors = None     # the factor of the base term to factor out
	best_term_tojoinwith = None  # which terms share that factor
	best_comb_heuristic = 0      # heuristic value of the current best factor
	num_candidates = 0           # how many candidates were tested in total?

	# go through every term in the sum
	for term_inx, this_term in _ast_children(sumnode):
		# for each factor the current term, see how many other terms share it
		# we will generate an array of sets of terms which share a given
		# factor. This is useful because we can do intersections on those sets
		# to find terms which share given groups of multiple factors quickly.
		shares_per_factor = []
		if this_term[0] == '*':
			# look at all the factors in the term
			for factor_inx, factor in _ast_children(this_term):
				# set of terms which share this factor
				sharing_terms = set()

				# for each other term, see if they share this factor
				for otherterm_inx in range(term_inx+1, len(sumnode)):
					other_term = sumnode[otherterm_inx]
					for otherfac_inx, otherfac in _ast_children(other_term):
						if _ast_equiv(factor, otherfac):
							# are equivalent, add to shared set
							sharing_terms.add(otherterm_inx)

				# add the shares to the list of shares for the term, as long 
				# as there are at least two terms sharing this factor. If
				# there are not it will not be needed in the next step, as
				# it cannot be factored out.
				if len(sharing_terms) > 0:
					shares_per_factor.append((factor_inx, sharing_terms))
		else:
			# not a factor. Ignore it. Note: In theory it could be something
			# we could pull out such as:
			# a + ab => a(1+b)  [ Note: = a ]
			# but it will never be this way given our no redundant terms
			# precondition on the input sum.
			pass

		# now, look at all the combinations of shares and see which is the 
		# best var to pull out for this term, if there is one to pull out.
		for i in range(1, len(this_term)-1):
			# for each combination of factors.
			for comb in itertools.combinations(shares_per_factor, i):
				# find how many terms share this combination of factors,
				# by doing a running intersection of all of the shared sets.
				total_intersection = comb[0][1]
				for factor_inx, sharing_terms in comb:
					total_intersection = \
						total_intersection.intersection(sharing_terms)

				# if there is an intersection between two or more terms, see
				# if it is the best intersection we've found so far
				if len(total_intersection) > 0:
					# "best":
					# heuristic is the number of vars we can pull out, times
					# the number of terms it can be pulled out of.
					if len(total_intersection)*i >= best_comb_heuristic:
						best_term_index = term_inx
						best_term_factors = [i for i,_ in comb]
						best_term_tojoinwith = [t for t in total_intersection]
						best_comb_heuristic = len(total_intersection)*i
						num_candidates += 1
	
	# result var, to be returned at the end of the function. We use this
	# because regardless of the way the result was generated we may do
	# some fixups on it right before it is returned.
	result = None

	# if there is a best combination
	if num_candidates > 0:
		# now we have a best combination to join. Do the join
		
		# get things the factors to pull out in a convinient format.
		base_term = sumnode[best_term_index]
		join_with = best_term_tojoinwith
		join_with.append(best_term_index)
		factors_to_pull = [fac for i,fac \
		                       in _ast_children(base_term) \
		                       if i in best_term_factors]

		# now pull factors out. For each term, remove them from it.
		for term_inx in join_with:
			term = sumnode[term_inx]

			#now remove the factors from the term
			new_term = ['*']
			for _,current_fac in _ast_children(term):
				for fac_to_rem in factors_to_pull:
					if _ast_equiv(current_fac, fac_to_rem):
						break
				else:
					new_term.append(current_fac)

			#add the new term
			if len(new_term) == 2:
				# product of one factor, just give the factor
				sumnode[term_inx] = new_term[1]
			else:
				sumnode[term_inx] = new_term

		# make a new term with all the joined terms
		main_new_term = ['+']
		factor_part = ['*']
		factored_terms = ['+']
		main_new_term.append(factor_part)

		# build the new factor pulled out of all of the terms
		for fac in factors_to_pull:
			factor_part.append(fac)
		factor_part.append(factored_terms)

		# build the new set of terms to multiply the factor by
		# we may have a "remaineder" left that the factor was not pulled out
		# of, so we separate all of the terms into main_new_term, the main sum 
		# left, and factored_terms, the ones that we did pull the factor out
		# of.
		for i,term in _ast_children(sumnode):
			if i in join_with:
				factored_terms.append(term)
			else:
				main_new_term.append(term)

		# do further simplification on the sum that we factored stuff out of.
		# we factored out of all of these terms, but there may be a subset of
		# them left that can have further things simplified out.
		factor_part[-1] = _simplify_sum(factor_part[-1])

		if len(main_new_term) == 2:
			#sum of 1 elements, we just return the one element of the sum
			result = main_new_term[1]
		else:
			result = main_new_term
	else:
		# nothig to factor.
		# result is just the input.
		result = sumnode

	# if we did do simplifications, repeat the process. There may be new
	# things to factor out if we got something equivalent to an expression
	# such as:
	# (a + b)(c + d)
	# as the input.
	if num_candidates > 0:
		result = _simplify_sum(result)

	# return the final result.
	return result




def simplify_ast(ast):
	"""
	Do many simplifications on an AST to try to get it down to a smaller
	total size. "size" being the number of operations applied.
	Return the new simplified AST. 
	"""
	return _simplify_sum(ast)


def _sort_and_flatten_ast(node):
	t = node[0]
	if t == '*':
		new_node = []
		total_complexity = 0
		for i,ch in _ast_children(node):
			if ch[0] == '*':
				ch,_ = _sort_and_flatten_ast(ch)
				for ii, chh in _ast_children(ch):
					res = _sort_and_flatten_ast(chh)
					total_complexity += res[1]
					new_node.append(res)				
			else:
				res = _sort_and_flatten_ast(ch)
				total_complexity += res[1]
				new_node.append(res)
		new_node.sort(key = lambda x: x[1])
		new_node = [x[0] for x in new_node]
		return new_node

	elif t == '+':
		new_node = []
		total_complexity = 0
		for i,ch in _ast_children(node):
			if ch[0] == '+':
				ch,_ = _sort_and_flatten_ast(ch)
				for ii, chh in _ast_children(ch):
					res = _sort_and_flatten_ast(chh)
					total_complexity += res[1]
					new_node.append(res)				
			else:
				res = _sort_and_flatten_ast(ch)
				total_complexity += res[1]
				new_node.append(res)
		new_node.sort(key = lambda x: x[1])
		new_node = [x[0] for x in new_node]
		return new_node

	elif t == '~':
		new_node = ['~']
		res,cost = _sort_and_flatten_ast(node[1])
		new_node.append(res)
		return new_node,cost

	elif t == 'V':
		return node, 1000+node[1]

	elif t == 'K':
		pass




def sort_and_flatten_ast(ast):
	"""
	Sort and flatten sorts an AST into least complexity, lexographical order,
	as well as flattening terms like: ((a + b) + c) into (a + b + c)
	"""




def ast_to_string(ast, var_names):
	"""
	Convert an AST to a string.
	var_names is any lookup mapping variable numbers to their repspective 
	names as they should be displayed.
	"""
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
	var_names is any lookup mapping variable numbers to their repspective 
	names as they should be displayed.

	>>> imp_to_string(Implicant([1,1,0]), ['A', 'B', 'C'])
	"ABC'"

	>>> imp_to_string(Implicant([0,EITHER,1]), ['A', 'B', 'C'])
	"A'C"
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
	var_names is any lookup mapping variable numbers to their repspective 
	names as they should be displayed.
	"""
	return ' + '.join([imp_to_string(imp, var_names) for imp in imp_list])



# doctest footer
if __name__ == "__main__":
	import doctest
	doctest.testmod()





