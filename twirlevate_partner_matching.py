# Create fake dancers with random characteristics

from random_dancers import generate_dancers
from dancer import Dancer
from ortools.sat.python import cp_model

dancers = generate_dancers(16, seed=40)
for dancer in dancers:
    print(dancer)

ACCEPTABLE_ROLE_MATCHES = [{"Leader", "Follower"}, {"Leader", "Switch"}, {"Follower", "Switch"}, {"Switch", "Switch"}]

possible_pairs = []
shared_style_count = {}

for i in range(len(dancers) - 1):
  dancer_i = dancers[i]
  for style_i in dancer_i["styles"]:
    for j in range(i + 1, len(dancers)):
      dancer_j = dancers[j]
      for style_j in dancer_j["styles"]:
        # Check that styles match
        if style_i == style_j:
          # Check if roles are compatible
          if {dancer_i["styles"][style_i]["role"], dancer_j["styles"][style_j]["role"]} in ACCEPTABLE_ROLE_MATCHES:
            possible_pairs.append({"dancers": [dancer_i["id"], dancer_j["id"]], "style": style_i, "score": 0})
            if (dancer_i["id"], dancer_j["id"]) not in shared_style_count:
              shared_style_count[(dancer_i["id"], dancer_j["id"])] = 1
            else:
              shared_style_count[(dancer_i["id"], dancer_j["id"])] += 1

for pair in possible_pairs:
  print(pair)

print("\n")
print("Number of shared styles per pair (with role compatability)")
for shared_style in shared_style_count:
  print(shared_style, shared_style_count[shared_style])

ATTR_BASE_SCORES = {"level": 100, "want": 100, "mutual_want": 100, "height": 100, "shared_styles": 100}
# attr_weights = {"level": 1, "height": 0.5, "location": 0.3}

scored_pairs = {}

def score_pair(pair):

  # dancers list needs to be sorted
  dancer_i = dancers[pair["dancers"][0] - 1]
  dancer_j = dancers[pair["dancers"][1] - 1]
  score = 0

  # score 0 if at least one dancer doesn't want to dance with the other
  if dancer_i["id"] in dancer_j["excludes"] or dancer_j["id"] in dancer_i["excludes"]:
    scored_pairs[(dancer_i["id"], dancer_j["id"], pair['style'])] = score
    return

  # level match
  level_difference = Dancer.LEVEL_VALUES[dancer_i["styles"][pair["style"]]["level"]] - Dancer.LEVEL_VALUES[dancer_j["styles"][pair["style"]]["level"]]
  score += (Dancer.MAX_LEVEL_DIFFERENCE - abs(level_difference)) * ATTR_BASE_SCORES["level"]
  # TODO: make level_difference bonus change exponentially

  # wants partner bonus
  if dancer_i["id"] in dancer_j["wants"]:
    score += ATTR_BASE_SCORES["want"]
  if dancer_j["id"] in dancer_i["wants"]:
    score += ATTR_BASE_SCORES["want"]

  # height match
  height_difference = abs(dancer_i["height_in"] - dancer_j["height_in"])
  score += (ATTR_BASE_SCORES["height"] - height_difference)

  # shared styles
  # shared_styles = [s for s in dancer_i["styles"] if s in dancer_j["styles"]]
  shared_styles = shared_style_count[(dancer_i["id"], dancer_j["id"])]
  score += shared_styles * ATTR_BASE_SCORES["shared_styles"]

  # normalize


  norm_score = score / (Dancer.MAX_LEVEL_DIFFERENCE * ATTR_BASE_SCORES["level"] + ATTR_BASE_SCORES["want"] + ATTR_BASE_SCORES["mutual_want"] + len(Dancer.STYLES) * ATTR_BASE_SCORES["shared_styles"])
  pair["score"] = norm_score
  scored_pairs[(dancer_i["id"], dancer_j["id"], pair['style'])] = norm_score

for pair in possible_pairs:
  score_pair(pair)
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