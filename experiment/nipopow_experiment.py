import cPickle as pickle
import sys
import bitcoin
from bitcoin.core import CBlockHeader, CheckProofOfWork, CheckBlockHeader, CheckProofOfWorkError, _SelectCoreParams, uint256_from_compact, Hash, uint256_from_str
_SelectCoreParams('regtest')
from bitcoin.core import coreparams

###
# Block header object
###
class CBlockHeaderPopow(CBlockHeader):
    __slots__ = ['hashInterlink']

    def __init__(self, nVersion=2, hashPrevBlock=b'\x00'*32, hashMerkleRoot=b'\x00'*32, nTime=0, nBits=0, nNonce=0, hashInterlink=b'\x00'*32):
        super(CBlockHeaderPopow, self).__init__(nVersion, hashPrevBlock, hashMerkleRoot, nTime, nBits, nNonce)
        object.__setattr__(self, 'hashInterlink', hashInterlink)

    @classmethod
    def stream_deserialize(cls, f):
        self = super(CBlockHeaderPopow, cls).stream_deserialize(f)
        hashInterlink = f.read(32)
        object.__setattr__(self, 'hashInterlink', hashInterlink)
        return self

    def stream_serialize(self, f):
        super(CBlockHeaderPopow, self).stream_serialize(f)
        f.write(self.hashInterlink)

    def compute_level(self):
        target = bits_to_target(self.nBits)
        hash = uint256_from_str(self.GetHash())
        return (target/hash).bit_length()-1

def bits_to_target(bits):
    # bits to target
    bitsN = (bits >> 24) & 0xff
    # print('bitsN: %s' % bitsN)
    #assert bitsN >= 0x03 and bitsN <= 0x1d, "First part of bits should be in [0x03, 0x1d]"
    assert bitsN >= 0x03 and bitsN <= 0x20, "First part of bits should be in [0x03, 0x20] (regtest)"
    bitsBase = bits & 0xffffff
    # print('bitsBase: %s' % hex(bitsBase))
    assert bitsBase >= 0x8000 and bitsBase <= 0x7fffff, "Second part of bits should be in [0x8000, 0x7fffff]"
    target = bitsBase << (8 * (bitsN-3))
    return target


###
# Builds a merkle tree over an Interlink vector
###
def hash_interlink(vInterlink=[]):
    if len(vInterlink) >= 2:
        hashL = hash_interlink(vInterlink[:len(vInterlink)/2])
        hashR = hash_interlink(vInterlink[len(vInterlink)/2:])
        return Hash(hashL + hashR)
    elif len(vInterlink) == 1:
        return vInterlink[0]
    else:
        return b'\x00'*32

def prove_interlink(vInterlink, mu):
    # Merkle tree proof
    assert 0 <= mu < len(vInterlink)
    if len(vInterlink) >= 2:
        if mu < len(vInterlink)/2:
            hashR = hash_interlink(vInterlink[len(vInterlink)/2:])
            return [(0, hashR)] + prove_interlink(vInterlink[:len(vInterlink)/2], mu/2)
        else:
            hashL = hash_interlink(vInterlink[:len(vInterlink)/2])
            return [(1, hashL)] + prove_interlink(vInterlink[len(vInterlink)/2:], mu/2)
    elif len(vInterlink) == 1:
        return []
    else:
        raise Exception

###
# Cons lists (to enable pointer sharing when building the header chain)
###
def list_append(xs, x):
    if xs == (): return (x, ())
    else: return (xs[0], list_append(xs[1], x))

def list_flatten(xs):
    r = []
    while xs != ():
        x,xs = xs
        r.append(x)
    return r

def list_replace_first_n(xs, x, n):
    """
    returns a list the same as `xs`, except the first
    `n` elements are `x`

    > list_replace_first_n([], 'a', 3):
    ('a', ('a', ('a', ())))
    """
    if n <= 0: return xs
    else:
        if xs == ():
            return (x, list_replace_first_n(   (), x, n-1))
        else:
            return (x, list_replace_first_n(xs[1], x, n-1))
###
# Saving and loading
###
def save_blockchain(f, (header, headerMap, mapInterlink)):
    import cPickle as pickle
    headerMap = dict((k,v.serialize()) for (k,v) in headerMap.iteritems())
    pickle.dump((header.serialize(), headerMap, mapInterlink), f, True)

def load_blockchain(f):
    import cPickle as pickle
    header, headerMap, mapInterlink = pickle.load(f)
    headerMap = dict((k,CBlockHeaderPopow.deserialize(v)) for (k,v) in headerMap.iteritems())
    header = CBlockHeaderPopow.deserialize(header)
    return header, headerMap, mapInterlink

"""
Useful commands to run:

  header, headerMap, mapInterlink = load_blockchain(open('450k.pkl'))

To build again:
  header, headerMap, mapInterlink = create_blockchain()

Then to save:
  with open('450k.pkl','w') as f: save_blockchain(f, (header, headerMap, mapInterlink))

"""


###
# Simulate mining
###

def mine_block(hashPrevBlock=b'\xbb'*32, nBits=0x207fffff, vInterlink=[]):
    hashMerkleRoot = b'\xaa'*32
    for nNonce in xrange(2**31):
        header = CBlockHeaderPopow(hashPrevBlock=hashPrevBlock, hashMerkleRoot=hashMerkleRoot, nBits=nBits, nNonce=nNonce, hashInterlink=hash_interlink(vInterlink))
        try:
            CheckProofOfWork(header.GetHash(), header.nBits)
            break
        except CheckProofOfWorkError, e:
            continue
    return header

def create_blockchain():
    # This way of handling the mapInterlink only requires O(N) space
    # Rather than O(N log N) when done naively
    headerMap = {}
    heightMap = {}
    mapInterlink = {}

    listInterlink = ()
    for i in range(450000):
        vInterlink = list_flatten(listInterlink)
        if i == 0:
            genesis = header = mine_block()
        else:            
            header = mine_block(header.GetHash(), header.nBits, vInterlink)

        headerMap[header.GetHash()] = header # Persist the header
        mapInterlink[header.GetHash()] = listInterlink
        heightMap[header.GetHash()] = i

        mu = header.compute_level()
        # Update interlink vector, extending if necessary
        for u in range(mu+1):
            listInterlink = list_replace_first_n(listInterlink, header.GetHash(), mu+1)

        #print header.GetHash()[::-1].encode('hex')
        #print header.compute_level()
        if i % 10000 == 0:
            print '*'*(header.compute_level()+1)
        #print [h[::-1][:3].encode('hex') for h in vInterlink]
    return header, headerMap, mapInterlink


###
# Create NiPoPoW proofs
###

"""
To run: 
  proof = make_proof(header, headerMap, mapInterlink)
"""

def make_proof(header, headerMap, mapInterlink, m=15, k=15):
    # Try making proofs at the tallest levels down
    vInterlink = list_flatten(mapInterlink[header.GetHash()])

    # Start at the base level
    mu = 0
    from collections import defaultdict
    num_at_level = defaultdict(lambda:0)
    proof = []
    mp = []
    while True:
        # TODO: go for the first k blocks
        proof.append((header.GetHash(), mp))
        _mu = header.compute_level()
        for i in range(mu, _mu+1):
            num_at_level[i] += 1

        # Advance current-level if at least m samples at the next level
        while num_at_level[mu+1] >= m:
            mu += 1

        # Nothing else at current level
        if mu >= len(vInterlink):
            break

        # Skip to the next block at current level
        mp = prove_interlink(vInterlink, mu)
        header = headerMap[vInterlink[mu]]
        vInterlink = list_flatten(mapInterlink[header.GetHash()])

    for h,mp in proof:
        print '*'*(headerMap[h].compute_level()+1)
        print h[::-1][:3].encode('hex')
        vInterlink = list_flatten(mapInterlink[h])
        print [_h[::-1][:3].encode('hex') for _h in vInterlink]
        print [(b,h[::-1][:3].encode('hex')) for (b,h) in mp]
    return proof
