import sys
sys.path.append('electrum')
from lib.blockchain import Blockchain
from collections import namedtuple
import math
import sys
import progressbar
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

Config = namedtuple('Config', ['path'])
config = Config(path='./electrum/electrum_data')
network = None

def bits_to_target(bits):
    # bits to target
    bitsN = (bits >> 24) & 0xff
    # print('bitsN: %s' % bitsN)
    assert bitsN >= 0x03 and bitsN <= 0x1d, "First part of bits should be in [0x03, 0x1d]"
    bitsBase = bits & 0xffffff
    # print('bitsBase: %s' % hex(bitsBase))
    assert bitsBase >= 0x8000 and bitsBase <= 0x7fffff, "Second part of bits should be in [0x8000, 0x7fffff]"
    target = bitsBase << (8 * (bitsN-3))
    return target

# import pdb

def construct_inner_chain(i, boundary, lastblockid, interlinks):
    # pdb.set_trace()
    inner_chain = []
    B = lastblockid
    count = 0
    while boundary is None or count != boundary:
        count += 1
        if not i in interlinks[B]:
            break
        # print B
        inner_chain.append(interlinks[B][i])
        B = interlinks[B][i]
    return inner_chain

def prove(m, k, lastblockid, interlinks):
    # pdb.set_trace()
    i = len(interlinks[lastblockid]) - 1
    proofs = {}
    # print 'Constructing proof at level %i' % i
    proofs[i] = construct_inner_chain(i, None, lastblockid, interlinks)
    while i > 0:
        boundary = max(m, len(proofs[i]))
        i -= 1
        # print 'Constructing proof at level %i' % i
        proofs[i] = construct_inner_chain(i, boundary, lastblockid, interlinks)
    blocks = []
    for i in proofs:
        blocks.extend(proofs[i])
    return blocks

blockchain = Blockchain(config, network)
blockchain.init()
block_height = 10000
block = blockchain.read_header(block_height)

max_height = blockchain.height()
bar = progressbar.ProgressBar(max_value = max_height, redirect_stdout=True)

MIN_M = 1
MAX_M = 10
MIN_K = 1
MAX_K = 10

levels = {}
samples = []
interlink = {}
interlinks = {}
max_level = 0
count = 0

height_by_hash = {}
level_by_hash = {}

while block is not None:
    if (block_height + 1) % 10000 == 0:
        print '%i%%' % (100 * round(float(block_height) / max_height, 2))
        # bar.update(block_height)
        # break
    bits = block['bits']
    # print(hex(bits))
    target = bits_to_target(bits)
    hash = blockchain.hash_header(block)
    blockid = int(hash, 16)
    level = -int(math.ceil(math.log(float(blockid) / target, 2)))
    level_by_hash[blockid] = level
    height_by_hash[blockid] = block_height
    if not level in levels:
        levels[level] = 0
    levels[level] += 1
    interlinks[blockid] = interlink.copy()
    interlink[level] = blockid
    lastblockid = blockid
    if level < 0:
        print level
    if level > 16:
        print 'Level %i at block %s' % (level, hash)
    # print('Target_: %s' % target)
    # print('Blockid: %s' % blockid)
    # print('Level: %i' % level)
    block_height += 1
    block = blockchain.read_header(block_height)
    for j in range(level + 1):
        samples.append(j)
    max_level = max(max_level, level)
    count += 1
    # print blockid
    # if count == 100:
    #     break
# bar.update(max_height)
print(levels)
print('done')
print(interlinks[lastblockid])
proof = prove(20, 20, lastblockid, interlinks)
print('Size of proof: %i' % len(proof))
print(proof)

for j in range(max_level):
    if not j in levels:
        levels[j] = 0

# plt.hist(x=np.array(samples), bins=max_level, log=True)
plt.bar(levels.keys(), levels.values(), align='center', log=True)
plt.title('Bitcoin blockchain superblocks histogram')
plt.ylabel('Number of blocks')
plt.xlabel('Superblock level')
plt.xlim([-0.5, max_level + 0.5])
plt.ylim([0.5, 2 * levels[0]])
plt.savefig('plot.png')

plt.clf();
xs = []
ys = []
for h in proof:
    xs.append(max_height + 1 - height_by_hash[h])
    ys.append(level_by_hash[h])
plt.scatter(xs, ys, marker='+')
plt.xscale('log')
plt.xlabel('Depth of blocks (# of blocks behind current head)')
plt.ylabel('Bits of 0')
plt.title('Compact PoPoW for Block Height %d' % max_height)
plt.savefig('scatterplot.png')
