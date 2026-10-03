from dancer import Dancer
import random

def make_dancer(dancer_id, all_ids):
    # Assign any combination of the 4 styles, each having any combination of roles and levels
    danced_styles = random.sample(Dancer.STYLES, k=random.randint(1, 4))
    styles = {style: {"role": None, "level": None} for style in danced_styles}
    for style in styles:
      styles[style]["role"] = random.choice(Dancer.ROLES)
      styles[style]["level"] = random.choice(Dancer.LEVELS)

    # partner preferences: 0-2 wanted, 0-1 excluded (excluding self)
    others = [i for i in all_ids if i != dancer_id]
    wants = random.sample(others, k=min(random.randint(0, 2), len(others)))
    remaining = [i for i in others if i not in wants]
    excludes = random.sample(remaining, k=min(random.randint(0, 1), len(remaining)))

    return {
        "id": dancer_id,
        "name": f"Dancer_{dancer_id}",
        "styles": styles,
        "height_in": round(random.uniform(60, 76), 1),  # inches, no shoes
        "wants": wants,
        "excludes": excludes,
    }

def generate_dancers(n=10, seed=None):
    if seed is not None:
        random.seed(seed)
    ids = list(range(1, n + 1))
    return [make_dancer(i, ids) for i in ids]