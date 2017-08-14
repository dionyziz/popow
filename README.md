Non-interactive proofs-of-proofs-of-work for proof-of-work-based blockchains.

# Proofs-of-proofs-of-work

Proofs-of-proofs-of-work are short arguments that prove that some proof-of-work
has taken place. The argument includes proof that the proof-of-work is included
in a particular blockchain by proving that the proof-of-work begins at a
particular genesis block. It also includes proof of the amount of work that has
taken place in computational hours destroyed.

Proofs-of-proofs of work are sublinear in size with respect to the blockchain
length. They can be constant size with respect to the underlying blockchain
length in the optimistic case, or logarithmic size with respect to the
underlying blockchain length in the worst case.

Unlike SPV proofs which are linear in length, PoPoWs are very succinct and can
fit in just a couple of KB. They are ideal for long-lived quickly growing
blockchains such as the financial blockchains of bitcoin and ethereum.

# Interactive PoPoWs

For the original interactive PoPoWs theory work, see our paper [Proofs of
Proofs of Work with Sublinear
Complexity](http://fc16.ifca.ai/bitcoin/papers/KLS16.pdf) at Financial Crypto
2016.

# Non-interactive PoPoWs

Non-interactive PoPoWs (NIPOPOWs) can be used as succinct proofs for multi-
currency SPV clients, or in [pegged sidechains](https://blockstream.com/sidechains.pdf). 
This provides secure non-interactive proofs between chains that can be challenged in 
the case an adversary produces an invalid proof.

# BIP

In order to enable PoPoWs in bitcoin, we require a simple backwards-compatible
change in bitcoin blocks: A 32-byte merkle tree root hash of a tree containing
hierarchical references to lg(n) previous superblocks must be included in each
block. This can be part of a transaction included in the transactions merkle
tree whose root hash is included in block headers. As such, this requires only
a hard fork.

This repository will contain the BIP once it is written.

# Prototype implementation

We will provide a prototype implementation of a miner who includes and verifies
hierarchical references in their blocks.
