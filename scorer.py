MATCH_WEIGHT = 0.6
INTEREST_WEIGHT = 0.4


def final_score(match_score, interest_score):
    return round(MATCH_WEIGHT * match_score + INTEREST_WEIGHT * interest_score, 2)