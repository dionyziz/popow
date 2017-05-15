import random
from math import log, floor

MAX_MU = 32
ROUNDS = 20
CONFIDENCE = 1000
MAX_TARGET = 2**MAX_MU
m = 10

# adversary power
q = 1.0 / 10

def level(blockid):
    return MAX_MU - log(blockid, 2)

def mine_block():
    blockid = random.randint(1, MAX_TARGET) - 1
    return blockid

def adversary_gets_block():
    outcome = random.randint(1, floor(1 / q))
    return outcome == 1.0

def count_level_blocks(C, mu):
    return len(filter(lambda x: x >= mu, C))

def proof_level(C):
    if len(C) < 2 * m:
        return 0

    superblocks = 0
    for mu in range(MAX_MU):
        if count_level_blocks(C, mu) < 2 * m:
            return mu - 1
    assert(False)

def max_chain(C1, C2):
    level1 = proof_level(C1)
    level2 = proof_level(C2)

    if level1 > level2:
        return True
    elif level1 < level2:
        return False

    return count_level_blocks(C1, level1) >= count_level_blocks(C2, level2)

def run():
    good = (ROUNDS + 1) * [0]
    bad = (ROUNDS + 1) * [0]

    for monte_carlo in range(CONFIDENCE):
        adversary_chain = []
        honest_chain = []

        for successful_round in range(ROUNDS):
            if adversary_gets_block():
                adversary_chain.append(level(mine_block()))
            else:
                honest_chain.append(level(mine_block()))
            z = len(honest_chain)
            if max_chain(adversary_chain, honest_chain):
                bad[successful_round] += 1
            else:
                good[successful_round] += 1

    for z in range(ROUNDS + 1):
        if bad[z] > 0 and good[z] > 0:
            print 'Pr[BAD|z = %i, m = %i, q = %f] = %.10f' % (z, m, q, float(bad[z]) / (bad[z] + good[z]))
