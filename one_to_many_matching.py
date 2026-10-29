# Create fake dancers with random characteristics

from random_dancers import generate_dancers, record_dancers
from dancer import Dancer
from ortools.sat.python import cp_model
from matching_helper import pair_dancers_to_one, score_pair

# Generate random dancers to match

dancers = generate_dancers(50, seed=50)
# for dancer in dancers:
# 	print(dancer)

record_dancers(dancers, "dancers_list")
 
# Generate dancer user
user = generate_dancers(1, seed=10)[0]
user["id"] = len(dancers) + 1
user["name"] = f"Dancer_{user['id']}"
# print("\nUser: ")
# print(user)
record_dancers([user], "user")

# Find all possible pairings of dancers

possible_pairs, shared_style_count = pair_dancers_to_one(user, dancers)

for pair in possible_pairs:
	print(pair)

print("\n")
print("Number of shared styles per pair (with role compatability)")
for shared_style in shared_style_count:
	print(shared_style, shared_style_count[shared_style])

# Score all the possible pairs

dancers.append(user)

scored_pairs = {}

for pair in possible_pairs:
	score = score_pair(pair, dancers, shared_style_count)
	pair["score"] = score
	scored_pairs[(pair["dancers"][0], pair["dancers"][1], pair['style'])] = score
	print(pair)

def pair_score(pair):
    return pair[1]

ranked_matches = []
for pair in scored_pairs.items():
    if pair[1] != 0:
    	ranked_matches.append(pair)
ranked_matches.sort(key=pair_score, reverse=True)
print("\nRankings:")
for i in range(min(10, len(ranked_matches))):
	print(ranked_matches[i])