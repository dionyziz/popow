import ethereum.config as config
from ethereum.tools import tester
from ethereum import utils
from ethereum.tools._solidity import (
    get_solidity,
    compile_file,
    solidity_get_contract_data
    )
SOLIDITY_AVAILABLE = get_solidity() is not None

def sha256(s):
    import hashlib
    return hashlib.sha256(s).digest()

from ethereum import slogging
#slogging.configure(':INFO,eth.vm:INFO')
#slogging.configure(':DEBUG')

# Create the simulated blockchain
tester.Chain().chain.config['BLOCK_GAS_LIMIT'] = 3141592000
tester.Chain().chain.config['START_GAS_LIMIT'] = 3141592000

s = tester.Chain()
s.mine()

contract_path = './contractNipopow.sol'
contract_name = 'Crosschain'
contract_compiled = compile_file(contract_path)

contract_data = solidity_get_contract_data(
    contract_compiled,
    contract_path,
    contract_name,)

contract_address = s.contract(contract_data['bin'], language='evm')

contract_abi = tester.ABIContract(
    s,
    contract_data['abi'],
    contract_address)

import cPickle as pickle
proof = pickle.load(open('proof.pkl'))
proof_f = pickle.load(open('proof-fork50k.pkl'))
proof2 = pickle.load(open('proof-2.pkl'))
proof3 = pickle.load(open('proof-3.pkl'))
proof4 = pickle.load(open('proof-4.pkl'))

# Take a snapshot before trying out test cases
#try: s.revert(s.snapshot())
#except: pass # FIXME: I HAVE NO IDEA WHY THIS IS REQUIRED
s.mine()
base = s.snapshot()

def initialize_test(): 
    try:
        s.revert(base)
    except AssertionError as e:
        if 'block boundaries' not in str(e):
            raise

def str_to_bytes32(s):
    r = []
    for start in range(0,len(s),32):
        r.append(s[start:start+32])
    return r

def extract_headers_siblings(proof = proof):
    headers = []
    hashed_headers = []
    siblings = []
    # mp stands for merkle proof
    # hs stands for headers.
    for hs, mp in proof:
        # Copy the header to an array of 4 bytes32
        header = str_to_bytes32(hs)
        # Encode the Merkle bits (mu) in the largest byte
        # Encode the mp size in the next largest byte
        assert 0 <= len(mp) < 256
        mu = sum(bit << i for (i,(bit,_)) in enumerate(mp[::-1]))
        assert 0 <= mu < 256
        #header[3] = chr(len(mp)) + chr(mu) + header[3][2:]
        header[3] = header[3] + ('\x00'*14) + chr(len(mp)) + chr(mu)
        headers.append(header)

        for (_,sibling) in mp:
            siblings.append(sibling)

    return headers, siblings

def submit_event_proof_good(proof=proof):

    initialize_test()

    #headers_f, siblings_f = extract_headers_siblings(proof_f)
    headers, siblings = extract_headers_siblings()
    g = s.head_state.gas_used

    #header[100] as our block of interest. We know that it's in the proof.
    success = contract_abi.submit_event_proof(
        headers, siblings, headers[100], sender = tester.k1,
        value = pow(10, 17), startgas = 100000000)

    print 'Gas used:', s.head_state.gas_used - g

    assert(success)

    print "Test: OK"

def submit_event_proof_bad(proof=proof):

    initialize_test()

    headers_f, siblings_f = extract_headers_siblings(proof_f)
    headers, siblings = extract_headers_siblings()
    g = s.head_state.gas_used

    #header[100] as our block of interest. We know that it's in the proof.
    success = contract_abi.submit_event_proof(
        headers, siblings, headers_f[100],
        value = pow(10, 17) , startgas = 100000000)

    print 'Gas used:', s.head_state.gas_used - g

    assert(success == False)

    print "Test: OK"

def submit_contesting_proof_succeeded():

    initialize_test()

    collateral = pow(10, 17)
    balance1 = s.chain.state.get_balance(tester.accounts[1])
    balance2 = s.chain.state.get_balance(tester.accounts[2])

    headers_f, siblings_f = extract_headers_siblings(proof_f)
    headers, siblings = extract_headers_siblings()

    success1 = contract_abi.submit_event_proof(
        headers_f, siblings_f, headers_f[100],
        value = collateral, sender = tester.k1, startgas = 100000000)

    assert(success1)

    s.mine()

    g = s.head_state.gas_used

    # We provide a better proof that shows that headers_f[100] is not in the 
    # true chain.
    success2 = contract_abi.submit_contesting_proof(
        headers, siblings, headers_f[100], sender = tester.k2, startgas = 100000000)

    print 'Gas used:', s.head_state.gas_used - g

    assert(success2)

    s.mine()

    # User who contested the proof get the collateral.
    assert(s.chain.state.get_balance(tester.accounts[2]) 
        == (balance2 + collateral))

    assert(s.chain.state.get_balance(tester.accounts[1]) 
        == (balance1 - collateral))

    print "Test: OK"

def submit_contesting_proof_failed():

    initialize_test()

    collateral = pow(10, 17)
    balance1 = s.chain.state.get_balance(tester.accounts[1])
    balance2 = s.chain.state.get_balance(tester.accounts[2])

    headers_f, siblings_f = extract_headers_siblings(proof_f)
    headers, siblings = extract_headers_siblings()

    success1 = contract_abi.submit_event_proof(
        headers, siblings, headers[100],
        value = collateral, sender = tester.k1, startgas = 100000000)

    assert(success1)

    s.mine()

    g = s.head_state.gas_used

    # We provide a better proof that shows that headers_f[100] is not in the 
    # true chain.
    success2 = contract_abi.submit_contesting_proof(
        headers_f, siblings_f, headers[100], sender = tester.k2, startgas = 100000000)

    print 'Gas used:', s.head_state.gas_used - g

    assert(success2 == False)

    s.mine()

    # User2 who contested the proof does not get the collateral.
    assert(s.chain.state.get_balance(tester.accounts[2]) 
        == (balance2))

    #User1 has to wait for the event to be finalized.
    assert(s.chain.state.get_balance(tester.accounts[1]) 
        == (balance1 - collateral))

    print "Test: OK"

def finalize_event_successful():
    initialize_test()

    balance1 = s.chain.state.get_balance(tester.accounts[1])
    headers, siblings = extract_headers_siblings()

    #header[100] as our block of interest. We know that it's in the proof.
    success = contract_abi.submit_event_proof(
        headers, siblings, headers[100], sender = tester.k1,
        value = pow(10, 17), startgas = 100000000)

    s.mine(7)

    # It doesn't matter who finalizes the event.
    success = contract_abi.finalize_event(headers[100], sender = tester.k2)

    assert(success)

    s.mine()

    success = contract_abi.event_exists(headers[100], sender = tester.k0)

    assert(success)

    assert(balance1 == s.chain.state.get_balance(tester.accounts[1]))

    print "Test: OK"

def finalize_event_failed():

    headers, siblings = extract_headers_siblings()
    
    success = contract_abi.submit_event_proof(
        headers, siblings, headers[100], sender = tester.k1,
        value = pow(10, 17), startgas = 100000000)

    s.mine()

    success = contract_abi.finalize_event(headers[100], sender = tester.k1)

    assert (success == False)

    print "Test: OK"

"""
def measure_compare_gas():

    headers, hashed_interlink, siblings, merkle_indices, merkle_branch_sizes = extract_vars(proof)
    #headers2, siblings2 = extract_headers_siblings(proof_f) # forked proof

    hash_headers2 = []
    for header, _ in proof_f:
        hash_headers2.append(sha256(sha256(header)))

    s_better = contract_abi.submit_nipopow(
        headers, hashed_interlink, siblings, merkle_branch_sizes, merkle_indices, startgas = 100000000)

    g = s.head_state.gas_used
    better_proof = contract_abi.compare_proofs(hash_headers2, startgas = 100000000)
    print 'Was it a better proof', better_proof
    print 'Gas used:', s.head_state.gas_used - g


# The following tests/debugging functions require the functions to be set to public. 
def test_best_argument():

    hash_headers1 = []
    hash_headers2 = []
    for header, _ in proof:
        hash_headers1.append(sha256(sha256(header)))
    for header, _ in proof_f:
        hash_headers2.append(sha256(sha256(header)))

    best_arg_1 = contract_abi.best_arg(hash_headers1, 198, startgas = 100000000)
    best_arg_2 = contract_abi.best_arg(hash_headers2, 112, startgas = 100000000)

    print "Best argument 1", best_arg_1
    print "Best argument 2", best_arg_2

def test_get_lca():

    headers1, siblings1 = extract_headers_siblings(proof)
    headers2, siblings2 = extract_headers_siblings(proof_f) # forked proof

    hash_headers2 = []
    for header, _ in proof_f:
        hash_headers2.append(sha256(sha256(header)))

    contract_abi.submit_nipopow(headers1, siblings1, startgas = 100000000)
    contract_abi.store_proof_in_map(headers2, startgas = 100000000)
    b_lca, c_lca = contract_abi.get_lca(hash_headers2)

    print "Stored proof lca", b_lca, "Current proof lca", c_lca

def test_get_level(proof, lca):
    levels = {}
    pr_levels = []
    for i in range(0, lca):
        hs, _ = proof[i]
        level = contract_abi.get_level(sha256(sha256(hs)))
        pr_levels.append(level)
        if level in levels:
            levels[level] = levels[level] + 1
        else:
            levels[level] = 1

    for level in levels:
        print level, "->", levels[level]

    print pr_levels
"""

submit_event_proof_good()
