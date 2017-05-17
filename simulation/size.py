from math import log, ceil

# suffix:
# C: length of chain
# x: # of transactions per block
# m,k: params
# block_header: prefix blocks 80
# 48 - header size
# coinbase transaction: ??
# hash_size: 32

def nipopow_size(C, x, m, k, block_header_size, suffix_block_header_size, coinbase_size, hash_size):
    mu = ceil(log(C, 2) - log(m, 2))
    count_pi_blocks = m * (mu - 2)
    count_chi_blocks = k + 2 * m
    blocks_size = (block_header_size + coinbase_size) * count_pi_blocks + suffix_block_header_size * count_chi_blocks
    count_pointer_inclusion = ceil(log(mu, 2)) * count_pi_blocks
    count_coinbase_inclusion = ceil(log(x, 2)) * count_pi_blocks
    hashes_size = (count_pointer_inclusion + count_coinbase_inclusion) * hash_size
    return (hashes_size + blocks_size), count_pi_blocks + count_chi_blocks, count_pointer_inclusion + count_coinbase_inclusion

for m in (6, 15, 30, 50, 100, 127):
    size, blocks, hashes = nipopow_size(400000, 2000, m, 6, 80, 48, 180, 32)
    print 'm = %i, size = %i, blocks = %i, hashes = %i' % (m, size, blocks, hashes)
