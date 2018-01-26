from ethereum import tester
from ethereum import utils
from ethereum._solidity import get_solidity
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
s = tester.state()
s.mine()
tester.gas_limit = 3141592

# Create the contract
contract = s.abi_contract(None, path='./contractNipopow.sol', language='solidity', contract_name='contractNipopow.sol:Nipopow')


# Sample block
sampleBlock = "f8912eb0b65eedfe76e7e63e053d98c02b9cfb03dae5970a86ed85fddf2d8efe020000002717f5042fac9869b9b2ca9284ec87980bd2efc5a33c6353c8158a9ccc62b833aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa00000000ffff7f2000000000".decode('hex')

import cPickle as pickle
proof = pickle.load(open('proof.pkl'))


def str_to_bytes32(s):
    r = []
    for start in range(0,len(s),32):
        r.append(s[start:start+32])
    return r

def submit_proof():
    assert len(sampleBlock) == 112
    r = str_to_bytes32(sampleBlock)
    print r
    contract.submitProof([r])


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
