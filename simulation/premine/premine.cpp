#include <cstdio>
#include <cstdlib>
#include <ctime>
#include <vector>
#include <cassert>

using namespace std;

typedef unsigned long long int blockid_t;

const int NUMBER_OF_TRIALS = 1000000;
const int n = 10; // number of total parties
const int t = 1; // number of adversarially-corrupted parties
const int MIN_M = 1; // nipopow security parameter min
const int MAX_M = 10; // and max
const int k = 6; // bitcoin block stability security parameter
const int NUM_ROUNDS_OF_PREMINING = 100;
const int MAX_MU = 63; // maximum superblock level
const blockid_t T = (blockid_t)1 << MAX_MU; // blockid range

/*
 * Given a blockid, it returns its highest superblock level by counting the
 * leading zeroes in the binary representation of the blockid.
 */
inline int level(blockid_t blockid) {
    return __builtin_clz(blockid) - 1;
}

/*
 * Mines a block and returns its highest superblock level.
 */
inline int mine() {
    blockid_t blockid = rand() % T;

    return level(blockid);
}

/*
 * Determines whether a given block is adversarial. Returns true with
 * probability t / n.
 */
inline bool is_adversarial_block() {
    return (rand() % n) < t;
}

/*
 * Given an adversarial and honest chain that are common (for example they are
 * empty), it runs the mining simulation for the given number of rounds,
 * assuming the adversary follows the strategy in which they maintain a
 * completely disjoint secret chain.
 */
void mine_prefix(int rounds, vector<int> &adversary_chain, vector<int> &honest_chain) {
    for (int round = 0; round < rounds; ++round) {
        int level = mine();
        if (is_adversarial_block()) {
            adversary_chain.push_back(level);
        }
        else {
            honest_chain.push_back(level);
        }
    }
}

/*
 * Given an adversarial and an honest chain, it runs the mining simulation
 * until the adversary is able to mine a k-long suffix on top of her current
 * chain.
 */
void mine_suffix(int k, vector<int> &adversary_chain, vector<int> &honest_chain) {
    int chi_size = 0;
    while (chi_size < k) {
        int level = mine();
        if (is_adversarial_block()) {
            ++chi_size;
            adversary_chain.push_back(level);
        }
        else {
            honest_chain.push_back(level);
        }
    }
}

/*
 * Given two chains and the parameter k, it prunes the k-long suffix from both
 * chains.
 */
bool prune_suffix(int k, vector<int> &adversary_chain, vector<int> &honest_chain) {
    for (int i = 0; i < k; ++i) {
        assert(!adversary_chain.empty());
        adversary_chain.pop_back();
        if (honest_chain.empty()) {
            return false;
        }
        honest_chain.pop_back();
    }
    return true;
}

/*
 * Given two chains, it produces a NIPoPoWs for each and compares the two,
 * returning the winning chain under the given security parameter m.
 *
 * Return value: Pair of bool and int. Bool indicates whether the first chain
 * won. Int indicates the superblock level at which the comparison took place.
 */
pair<bool, int> max_chain(int m, vector<int> &adversary_chain, vector<int> &honest_chain) {
    int adversary_numblocks_by_level[MAX_MU],
        honest_numblocks_by_level[MAX_MU];

    memset(adversary_numblocks_by_level, 0, MAX_MU * sizeof(int));
    memset(honest_numblocks_by_level, 0, MAX_MU * sizeof(int));

    for (auto level: adversary_chain) {
        // Count block at its level and below
        for (int ll = level; ll >= 0; --ll) {
            ++adversary_numblocks_by_level[ll];
        }
    }
    for (auto level: honest_chain) {
        for (int ll = level; ll >= 0; --ll) {
            ++honest_numblocks_by_level[ll];
        }
    }

    for (int mu = MAX_MU - 1; mu >= 0; --mu) {
        if (adversary_numblocks_by_level[mu] >= m || honest_numblocks_by_level[mu] >= m) {
            if (adversary_numblocks_by_level[mu] < m) {
                return make_pair(false, mu);
            }
            if (honest_numblocks_by_level[mu] < m) {
                return make_pair(true, mu);
            }
            return make_pair(adversary_numblocks_by_level[mu] >= honest_numblocks_by_level[mu], mu);
        }
    }
    assert(false);
}

void print_chain(vector<int> C, int highlight_level = MAX_MU) {
    printf("[ ");
    for (auto level: C) {
        if (level >= highlight_level) {
            printf("\033[1;31m");
        }
        printf("%i ", level);
        if (level >= highlight_level) {
            printf("\033[0m");
        }
    }
    printf("]\n");
}

int main() {
    vector<int> adversary_chain,
                honest_chain;
    bool bad;

    srand(time(NULL));

    for (int m = MIN_M; m < MAX_M; ++m) {
        int count_bad = 0;
        int count_all = 0;

        for (int monte_carlo = 0; monte_carlo < NUMBER_OF_TRIALS; ++monte_carlo) {
            // Start new execution simulation with empty chains
            adversary_chain.clear();
            honest_chain.clear();
            bad = false;
            // Produce adversarial $\pi$ part of nipopow
            mine_prefix(NUM_ROUNDS_OF_PREMINING, adversary_chain, honest_chain);
            // Produce adversarial $\chi$ part of nipopow
            mine_suffix(k, adversary_chain, honest_chain);
            // Remove the chi suffix from both chains
            if (!prune_suffix(k, adversary_chain, honest_chain)) {
                bad = true;
            }
            else {
                auto result = max_chain(m, adversary_chain, honest_chain);
                bad = result.first;

                /*
                if (bad) {
                    printf("Adversary chain:\n");
                    print_chain(adversary_chain, result.second);
                    printf("Honest chain:\n");
                    print_chain(honest_chain, result.second);
                }
                */
            }
            count_bad += bad;
            ++count_all;
        }
        printf("Pr[BAD | m = %i] = %.7f\n", m, float(count_bad) / count_all);
    }
    return 0;
}
