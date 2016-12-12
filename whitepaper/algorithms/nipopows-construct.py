def ConstructInnerChain(C, i, boundary):
    B = C[C.length]
    while B != boundary:
        blockid = B.interlink[i]
        B = blockById(blockid)
        InnerChain.append(B.interlink[i])
    return InnerChain

def ConstructProof(C, m, interlink):
    size = C.length - (k - 1)
    i = C[size].interlink.length
    Proof[i] = ConstuctInnerChain(DropSuffix(C, k - 1), i, genesis)
    while i > 0:
        boundary = min(m, Proof[i].length)
        i -= 1
        Proof[i] = ConstructInnerChain(DropSuffix(C, k - 1), i, boundary)
    return Proof
