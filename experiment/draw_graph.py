###
# Graphing (Caution! Makes use of global variables and hacks 
###

def compute_heights(header, headerMap):
    global scores
    global mapHeight
    if 'mapHeight' not in globals():
        mapHeight = {}
    scores = []
    front = header # Save for later
    for i in xrange(10000000): # FIXME: fix this dynamically somehow?
        header = headerMap[header.hashPrevBlock]
        if header.hashPrevBlock == b'\xbb'*32: break
    num_blocks = i+1
    header = front
    for i in xrange(num_blocks):
        scores.append(header.compute_level())
        mapHeight[header.GetHash()] = num_blocks-i
        header = headerMap[header.hashPrevBlock]

def fullgraph(scores):
    xs = np.arange(len(scores))
    size = np.array(scores)**2 / 10.
    colors = np.concatenate( (len(scores)*[[0,0,1]], np.array(scores).reshape(-1,1)/20.), axis=1)
    figure(1)
    clf();
    scatter(-xs, scores, s=size, c=colors, linewidths=0, edgecolors='none')
    ylim(0,20)
    xlim(-450000,10000)

def draw_proof():
    proof = make_proof(header, headerMap, mapInterlink)
    xs = []
    ys = []
    for (hs,_) in proof:
        h = Hash(hs)
        xs.append(mapHeight[h])
        ys.append(headerMap[h].compute_level())
    size = np.array(ys)**2 / 10.
    figure(2)
    clf()
    # Standard
    scatter(-np.array(xs)-1, ys, s=size, edgecolors='none')
    xlim(-450000,1000)
    # Log plot
    figure(3)
    clf()
    scatter(-np.array(xs)-1, ys, s=20, edgecolors='none')
    xscale('symlog')
    xlim(-450000,0)

def draw_fork(header1, header2):
    proof1 = make_proof(header1, headerMap, mapInterlink)
    proof2 = make_proof(header2, headerMap, mapInterlink)
    set1 = set(hs for (hs,_) in proof1)
    set2 = set(hs for (hs,_) in proof2)
    both = set.intersection(set1,set2)

    xs = [[],[],[],[],[]]
    ys = [[],[],[],[],[]]
    # Latest Common Ancestor
    lca = max(mapHeight[Hash(hs)] for hs in both)
    print 'LCA height:', lca
    lca_level, = [headerMap[Hash(hs)].compute_level() for hs in both if mapHeight[Hash(hs)] == lca]
    # Just the prefix
    for hs in both:
        h = Hash(hs)
        xs[0].append(mapHeight[h])
        ys[0].append(headerMap[h].compute_level())
    # Just in one or the other
    for hs in set1.difference(both):
        h = Hash(hs)
        if mapHeight[h] <= lca:
            xs[1].append(mapHeight[h])
            ys[1].append(headerMap[h].compute_level())
        else:
            xs[3].append(mapHeight[h])
            ys[3].append(headerMap[h].compute_level())
    for hs in set2.difference(both):
        h = Hash(hs)
        if mapHeight[h] <= lca:
            xs[2].append(mapHeight[h])
            ys[2].append(headerMap[h].compute_level())
        else:
            xs[4].append(mapHeight[h])
            ys[4].append(headerMap[h].compute_level())
    size = [np.array(ys[t])**2 / 10. for t in (0,1,2,3,4)]

    figure(2)
    clf()
    # Standard
    num_blocks = max(mapHeight[Hash(k)] for (k,_) in proof2)
    scatter(np.array(xs[0])-num_blocks-1, ys[0], s=size[0], marker='+', edgecolors='none', c='k')
    scatter(np.array(xs[1])-num_blocks-1, ys[1], s=size[1], marker='+', edgecolors='none', c='r')
    scatter(np.array(xs[2])-num_blocks-1, ys[2], s=size[2], marker='+', edgecolors='none', c='b')
    scatter(np.array(xs[3])-num_blocks-1, ys[3], s=size[3], edgecolors='none', c='r')
    scatter(np.array(xs[4])-num_blocks-1, ys[4], s=size[4], edgecolors='none', c='b')
    xlim(-450000,1000)
    # Log plot
    figure(3)
    clf()
    scatter(np.array(xs[0])-num_blocks-1, ys[0], s=20, marker='+', edgecolors='none', c='k')
    scatter(np.array(xs[1])-num_blocks-1, ys[1], s=20, marker='+', edgecolors='none', c='r')
    scatter(np.array(xs[2])-num_blocks-1, ys[2], s=20, marker='+', edgecolors='none', c='b')
    scatter(np.array(xs[3])-num_blocks-1, ys[3], s=20, edgecolors='none', c='r')
    scatter(np.array(xs[4])-num_blocks-1, ys[4], s=20, edgecolors='none', c='b')
    # Draw the LCA
    scatter(lca-num_blocks-1, lca_level, s=200, marker='*', c='k')
    plot([lca-num_blocks-1,lca-num_blocks-1],[-5,20],'k')
    xscale('symlog')
    xlim(-450000,0)
    ylim(-1,20)
    legend(['in common','<LCA','<LCA','>LCA','>LCA'], loc='best')
    
def do_plot():
    figure(1);
    clf();
    xs = []
    ys = []
    for h in proof:
        xs.append(max_height + 1 - height_by_hash[h])
        ys.append(level_by_hash[h])
    scatter(xs, ys, marker='+')
    xscale('log')
    xlabel('Depth of blocks (# of blocks behind current head)')
    ylabel('Bits of 0')
    title('Compact PoPoW for Block Height %d' % max_height)
    show()
