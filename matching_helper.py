from dancer import Dancer

ACCEPTABLE_ROLE_MATCHES = [{"Leader", "Follower"}, {"Leader", "Switch"}, {"Follower", "Switch"}, {"Switch", "Switch"}]
ATTR_BASE_SCORES = {"lvl": 100, "want": 100, "mutual_want": 100, "height": 100, "shared_styles": 100}
# attr_weights = {"lvl": 1, "height": 0.5, "location": 0.3}

def pair_dancers_to_many(dancers):
    possible_pairs = []
    shared_style_count = {}

    for i in range(len(dancers) - 1):
        dancer_i = dancers[i]
        other_dancers = dancers[i + 1:]
        possible_pairs_i, shared_style_count_i = pair_dancers_to_one(dancer_i, other_dancers)
        possible_pairs = possible_pairs + (possible_pairs_i)
        shared_style_count |= (shared_style_count_i)

    return possible_pairs, shared_style_count

def pair_dancers_to_one(target, dancers):
    possible_pairs = []
    shared_style_count = {}
    dancer_j = target
    
    for i in range(len(dancers) - 1):
        dancer_i = dancers[i]
        for style_i in dancer_i["styles"]:
            for style_j in target["styles"]:
                # Check that styles match
                if style_i == style_j:
                # Check if roles are compatible
                    if {dancer_i["styles"][style_i]["role"], dancer_j["styles"][style_j]["role"]} in ACCEPTABLE_ROLE_MATCHES:
                        possible_pairs.append({"dancers": [dancer_i["id"], dancer_j["id"]], "style": style_i, "score": 0})
                        if (dancer_i["id"], dancer_j["id"]) not in shared_style_count:
                            shared_style_count[(dancer_i["id"], dancer_j["id"])] = 1
                        else:
                            shared_style_count[(dancer_i["id"], dancer_j["id"])] += 1
    return possible_pairs, shared_style_count

def score_pair(pair, dancers, shared_style_count):
    # dancers list needs to be sorted
    dancer_i = dancers[pair["dancers"][0] - 1]
    dancer_j = dancers[pair["dancers"][1] - 1]
    score = 0

    # score 0 if at least one dancer doesn't want to dance with the other
    if dancer_i["id"] in dancer_j["excludes"] or dancer_j["id"] in dancer_i["excludes"]:
        return score

    # level match
    lvl_difference = abs(Dancer.LVL_VALS[dancer_i["styles"][pair["style"]]["lvl"]] - Dancer.LVL_VALS[dancer_j["styles"][pair["style"]]["lvl"]])
    
    if lvl_difference > 1:
        return score
    
    if lvl_difference == 0:
        score += 100

    # wants partner bonus
    if dancer_i["id"] in dancer_j["wants"]:
        score += ATTR_BASE_SCORES["want"]
    if dancer_j["id"] in dancer_i["wants"]:
        score += ATTR_BASE_SCORES["want"]

    # height match
    height_difference = abs(dancer_i["height_in"] - dancer_j["height_in"])
    score += (ATTR_BASE_SCORES["height"] - height_difference)

    # shared styles
    shared_styles = shared_style_count[(dancer_i["id"], dancer_j["id"])]
    score += shared_styles * ATTR_BASE_SCORES["shared_styles"]

    # normalize
    norm_score = score / (Dancer.MAX_LVL_DIFF * ATTR_BASE_SCORES["lvl"] + ATTR_BASE_SCORES["want"] + ATTR_BASE_SCORES["mutual_want"] + len(Dancer.STYLES) * ATTR_BASE_SCORES["shared_styles"])
    return norm_score
