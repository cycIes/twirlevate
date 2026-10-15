from dancer import Dancer

ACCEPTABLE_ROLE_MATCHES = [{"Leader", "Follower"}, {"Leader", "Switch"}, {"Follower", "Switch"}, {"Switch", "Switch"}]
ATTR_BASE_SCORES = {"level": 100, "want": 100, "mutual_want": 100, "height": 100, "shared_styles": 100}
# attr_weights = {"level": 1, "height": 0.5, "location": 0.3}

def create_possible_pairs(dancers):
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
    return possible_pairs, shared_style_count

def score_pair(pair, dancers, shared_style_count):
    scored_pairs = {}

    # dancers list needs to be sorted
    dancer_i = dancers[pair["dancers"][0] - 1]
    dancer_j = dancers[pair["dancers"][1] - 1]
    score = 0

    # score 0 if at least one dancer doesn't want to dance with the other
    if dancer_i["id"] in dancer_j["excludes"] or dancer_j["id"] in dancer_i["excludes"]:
        return score

    # level match
    level_difference = Dancer.LEVEL_VALUES[dancer_i["styles"][pair["style"]]["level"]] - Dancer.LEVEL_VALUES[dancer_j["styles"][pair["style"]]["level"]]
    
    if level_difference > 1:
        return score
    
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
    return norm_score
