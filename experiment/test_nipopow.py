#import 
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

##
# Logging - change these to configure what solidity prints out
##
from ethereum import slogging
#slogging.configure(':INFO,eth.vm:INFO')
slogging.configure(':DEBUG')
#slogging.configure(':DEBUG,eth.vm:TRACE')

##
# Some utilities for pyethereum tester
##
xor = lambda (x,y): chr(ord(x) ^ ord(y))
xors = lambda x,y: ''.join(map(xor,zip(x,y)))
zfill = lambda s: (32-len(s))*'\x00' + s
flatten = lambda x: [z for y in x for z in y]

# Create the simulated blockchain

env = config.Env()
env.config['BLOCK_GAS_LIMIT'] = 3141592000
env.config['START_GAS_LIMIT'] = 3141592000
s = tester.Chain(env = env)
# Need to increase the gas limit. These are some large contracts!
s.mine()

contract_path = './contractNipopow.sol'
contract_name = 'Nipopow'
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

# Sample block
sampleBlock = "f8912eb0b65eedfe76e7e63e053d98c02b9cfb03dae5970a86ed85fddf2d8efe020000002717f5042fac9869b9b2ca9284ec87980bd2efc5a33c6353c8158a9ccc62b833aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa00000000ffff7f2000000000".decode('hex')

import cPickle as pickle
proof = pickle.load(open('proof.pkl'))
proof_f = pickle.load(open('proof-fork50k.pkl'))
proof2 = pickle.load(open('proof-2.pkl'))
proof3 = pickle.load(open('proof-3.pkl'))
proof4 = pickle.load(open('proof-4.pkl'))

def str_to_bytes32(s):
    r = []
    for start in range(0,len(s),32):
        r.append(s[start:start+32])
    return r

def extract_headers_siblings(proof = proof):
    headers = []
    siblings = []
    # mp stands for merkle proof
    # hs stands for headers. (probably)
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
        #print repr(sha256(sha256(hs)))

        for (_,sibling) in mp:
            siblings.append(sibling)

    return headers, siblings

def compare_header_proofs(proof1 = proof, proof2 = proof_f):

    headers1, _ = extract_headers_siblings(proof1)
    headers2, _ = extract_headers_siblings(proof2)

    cnt = 0

    for i in range(0, len(headers1)):
        for j in range(0, len(headers2)):
            if headers1[i] == headers2[j]:
                cnt = cnt + 1
                print "Match found! ", i, " ", j

    # How many headers are the same in both chains.
    print cnt

def submit_proof(proof=proof):

    headers, siblings = extract_headers_siblings(proof)

    #assert len(sampleBlock) == 112
    #headers = [str_to_bytes32(sampleBlock)]

    g = s.head_state.gas_used
    contract_abi.submit_nipopow(headers, siblings, startgas = 100000000)
    print 'Gas used:', s.head_state.gas_used - g

# Take a snapshot before trying out test cases
#try: s.revert(s.snapshot())
#except: pass # FIXME: I HAVE NO IDEA WHY THIS IS REQUIRED
s.mine()
base = s.snapshot()

def test_OK():
    #s.revert(base)  # Restore the snapshot

    # To measure gas... TODO: make into a decorator
    g = s.block.gas_used
    contract.load_proof()
    s.block.gas_used - g
