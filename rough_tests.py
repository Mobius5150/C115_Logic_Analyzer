
"""

Rought testing: Takes function, probes it for a min-term expansion, and
reduces down all terms in the form: (X... + X'...) => (...)

"""

varcount = 5
varnames = ['A', 'B', 'C', 'D', 'E']


minterms = []


circuit = lambda a,b,c,d,e: (a or b or c) and (b or e or (c and b and d))
for i in range(2**varcount):
	args = []
	n = i
	for _ in range(varcount):
		args.append(n % 2)
		n = n // 2
	####
	if circuit(*args):
		mintermstr = ""
		for v in args:
			if v:
				mintermstr += '+'
			else:
				mintermstr += '-'
		minterms.append(mintermstr)


varterms = []
for vari in range(varcount):
	# make the sets
	varterms.append([set(), set()])

	# for each minterm
	for term in minterms:
		entry_asarray = []
		for j in range(varcount):
			if j == vari:
				entry_asarray.append(0)
			elif term[j] == '+':
				entry_asarray.append(1)
			else:
				entry_asarray.append(-1)
		entry = tuple(entry_asarray)
		if term[vari] == '+':
			varterms[vari][0].add(entry)
		else:
			varterms[vari][1].add(entry)

# = [
#     [ {(0,-1,1), (0,-1,-1)}, {(0,1,-1), (0,1,1) } ],
#     [ {(1,0,-1), (-1,0,-1)}, {(1,0,1),  (1,0,-1)} ],
#     ...
# ] 

from pprint import pprint
pprint(minterms)
pprint(varterms)

#print the result
resultset = set()
for vari in range(varcount):
	# pos terms
	for term in varterms[vari][0]:
		termstr = ""
		for varj in range(varcount):
			if varj == vari:
				termstr += varnames[varj]
			elif term[varj] == 1:
				termstr += varnames[varj]
			elif term[varj] == -1:
				termstr += varnames[varj]
				termstr += "'"
		resultset.add(termstr)

	# neg terms
	for term in varterms[vari][1]:
		termstr = ""
		for varj in range(varcount):
			if varj == vari:
				termstr += varnames[varj]
				termstr += "'"
			elif term[varj] == 1:
				termstr += varnames[varj]
			elif term[varj] == -1:
				termstr += varnames[varj]
				termstr += "'"
		resultset.add(termstr)

print(" + ".join(resultset))

############################################################################

# now perform the reduction steps to go to the minimal and-or 
# form of the logic
for vari in range(varcount):
	# intersect the minus and plus terms for this var to find 
	# what we can cancel
	tocancel = varterms[vari][0].intersection(varterms[vari][1])

	# for each term to cancel, remove it from the other termsets
	for termtocancel in tocancel:
		# first, remove it from the var it was for
		varterms[vari][0].remove(termtocancel)
		varterms[vari][1].remove(termtocancel)

		# then update it's entries in the other arrays
		for othervari in range(varcount):
			if othervari != vari:
				# construct the entry to remove from that array
				entry_asarray = []
				for i in range(varcount):
					if i == vari or i == othervari:
						entry_asarray.append(0)
					else:
						entry_asarray.append(termtocancel[i])
				#
				toadd = tuple(entry_asarray)
				entry_asarray[vari] = 1
				toremp = tuple(entry_asarray)
				entry_asarray[vari] = -1
				toremn = tuple(entry_asarray)
				#
				if toremp in varterms[othervari][0]:
					varterms[othervari][0].remove(toremp)
				if toremp in varterms[othervari][1]:
					varterms[othervari][1].remove(toremp)
				if toremn in varterms[othervari][0]:
					varterms[othervari][0].remove(toremn)
				if toremn in varterms[othervari][1]:
					varterms[othervari][1].remove(toremn)
				#
				if termtocancel[othervari] == 1:
					varterms[othervari][0].add(toadd)
				elif termtocancel[othervari] == -1:
					varterms[othervari][1].add(toadd)
				#

######################################################################

#print the result
resultset = set()
for vari in range(varcount):
	# pos terms
	for term in varterms[vari][0]:
		termstr = ""
		for varj in range(varcount):
			if varj == vari:
				termstr += varnames[varj]
			elif term[varj] == 1:
				termstr += varnames[varj]
			elif term[varj] == -1:
				termstr += varnames[varj]
				termstr += "'"
		resultset.add(termstr)

	# neg terms
	for term in varterms[vari][1]:
		termstr = ""
		for varj in range(varcount):
			if varj == vari:
				termstr += varnames[varj]
				termstr += "'"
			elif term[varj] == 1:
				termstr += varnames[varj]
			elif term[varj] == -1:
				termstr += varnames[varj]
				termstr += "'"
		resultset.add(termstr)

print("=>")
print(" + ".join(resultset))




		



