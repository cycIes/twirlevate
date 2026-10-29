# Create fake dancers with random characteristics

from random_dancers import generate_dancers, record_dancers
from dancer import Dancer
from ortools.sat.python import cp_model
from matching_helper import pair_dancers_to_many, score_pair

# Generate random dancers to match

dancers = generate_dancers(16, seed=40)
# for dancer in dancers:
# 	print(dancer)
 
record_dancers(dancers, "dancers_list")

# Find all possible pairings of dancers

possible_pairs, shared_style_count = pair_dancers_to_many(dancers)

for pair in possible_pairs:
    print(pair)

print("\n")
print("Number of shared styles per pair (with role compatability)")
for shared_style in shared_style_count:
	print(shared_style, shared_style_count[shared_style])

# Score all the possible pairs

scored_pairs = {}

for pair in possible_pairs:
	score = score_pair(pair, dancers, shared_style_count)
	pair["score"] = score
	scored_pairs[(pair["dancers"][0], pair["dancers"][1], pair['style'])] = score
	print(pair)

print(scored_pairs)

model = cp_model.CpModel()

# create boolean variable for each pair (pair is either partnered or not)
is_paired = {}
for pair in possible_pairs:
	dancer_i_id = pair["dancers"][0]
	dancer_j_id = pair["dancers"][1]
	style = pair["style"]
	key = (dancer_i_id, dancer_j_id, style)
	is_paired[key] = model.NewBoolVar(f"is_paired_{dancer_i_id}_{dancer_j_id}_{style}")

# constrain to one partner per dancer in a given style
for dancer in dancers:
	for style in Dancer.STYLES:
		model.Add(sum(is_paired[key] for key in is_paired if dancer["id"] in key[:2] and key[2] == style) <= 1)

# create boolean variable for each dancer (whether the dancer has a partner or not)
has_partner = {}
for dancer in dancers:
	has_partner[dancer["id"]] = model.NewBoolVar(f"has_partner_{dancer['id']}")

	# link it to whether any of their pairings are active, in any style
	relevant_vars = [
			is_paired[key] for key in is_paired
			if dancer["id"] in key[:2]
	]
	# has_partner can only be 1 if at least one pairing involving them is 1
	model.Add(sum(relevant_vars) >= has_partner[dancer["id"]])
	# and it can't be 1 if none of them are (optional but keeps it tight —
	# not strictly required since Maximize will naturally push it to 1 whenever possible)

# maximize number of people who get a partner
model.Maximize(sum(has_partner[dancer["id"]] for dancer in dancers))

solver = cp_model.CpSolver()
status = solver.Solve(model)

max_coverage = solver.ObjectiveValue()
print("Max dancers covered:", max_coverage)

# lock in the coverage result as a hard constraint
model.Add(sum(has_partner[dancer["id"]] for dancer in dancers) == int(max_coverage))

# maximize total pairings
# constrained to only search among solutions that already hit max coverage
model.Maximize(sum(is_paired[key] for key in is_paired))

status = solver.Solve(model)

print("Total pairings, given max coverage held:", solver.ObjectiveValue())

# maximize score across pairs
model.Maximize(sum(is_paired[key] * scored_pairs[key] for key in is_paired))

solver = cp_model.CpSolver()
status = solver.Solve(model)

if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
	print(f"Total score: {solver.ObjectiveValue()}")

final_matches = []

for (dancer_i_id, dancer_j_id, style), is_paired_var in is_paired.items():
	if solver.BooleanValue(is_paired_var):
		final_matches.append({
				"dancers": [dancer_i_id, dancer_j_id],
				"style": style,
				"score": scored_pairs[(dancer_i_id, dancer_j_id, style)]
		})

for match in final_matches:
	print(match)