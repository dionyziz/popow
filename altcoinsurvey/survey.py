from BeautifulSoup import BeautifulSoup as BS
from pylab import *
import glob

# CoinWarz scrapes
coins = [_.split('.')[0] for _ in glob.glob('coinwarz/*.html')]

broken = []
def parse_try(coin):
    global broken
    try:
        parse(coin)
    except Exception, e:
        broken.append(coin)
        print e
    
def parse(coin):
    global coindata
    fn = coin + '.html'
    global c,a
    c = open(fn).read()
    a = BS(c)
    table = a.findAll("table")
    print len(table)
    d = {}
    coindata[coin.split('/')[-1]] = d
    print coin
    for row in table[0].findAll("tr"):
        cells = row.findAll("td")
        key = cells[0].findChild('b').contents[0]
        value = cells[1]
        if key.startswith('Symbol'):
            d["Symbol"] = value.contents[0].strip()
        if key.startswith('Hash'):
            d[key] = value.contents[0].strip()
        if key.startswith('Proof'):
            d[key] = value.contents[0].strip()
        if key.startswith('Status'):
            d[key] = value.contents[0].strip()
        if key.startswith('Block Time'):
            d[key] = value.findChild('span').contents[0].strip()
        if key.startswith('Block Count'):
            d[key] = int(value.contents[0].strip().replace(',',''))
        #print key, value.contents
    print d

if not 'coindata' in globals():
    coindata = {}
    for c in coins:
        parse_try(c)

# Parse
def parse_marketcap():
    global market_cap
    market_cap = {}
    c = open('coinmarketcap.html').read()
    a = BS(c)
    table = a.findAll("table")
    for row in table[0].findAll("tr"):
        cells = row.findAll("td")
        if len(cells) != 10: continue
        key = cells[2].contents[0]
        val = cells[3].contents[0].strip()
        #print cells[0]
        val = 0 if val == '?' else int(val.replace(',','').replace('$',''))
        market_cap[key] = val

if not 'market_cap' in globals():
    parse_marketcap()
        
# Spot fixes
coindata['bytecoin']['Status'] = 'Healthy'

def sample():
    healthy = [d for d in coindata if 'Status' in coindata[d] and coindata[d]['Symbol'] in market_cap and market_cap[coindata[d]['Symbol']] > 100000]

    print 'healthy:', len(healthy)

    total = float(sum(market_cap[coindata[d]['Symbol']] for d in healthy))
    print 'total:', total
    samples = np.random.choice(healthy, 1000, p=[market_cap[coindata[d]['Symbol']]/total for d in healthy])
    print 'unique:', len(set(samples))

def histog():
    # Assume 80 bytes per header
    import humanize
    from collections import defaultdict

    global healthy
    #healthy = [d for d in coindata if 'Status' in coindata[d] and coindata[d]['Status'] == 'Healthy']
    healthy = [d for d in coindata if 'Status' in coindata[d] and coindata[d]['Symbol'] in market_cap and market_cap[coindata[d]['Symbol']] > 100000]
    print 'healthy:', len(healthy)
    
    data = defaultdict(lambda: dict(blocks=0, freq=0, coins=0))
    for d in healthy:
        symb = coindata[d]['Symbol']
        print d, coindata[d]['Symbol'], market_cap[symb] if symb in market_cap else '?'
        pp = coindata[d]['Hash Algorithm']
        time = coindata[d]['Block Time']
        try:
            amt = float(time.split(' ')[0])
        except: continue
        amt = amt * 60. if 'minute' in time else amt

        data[pp]['freq'] += 1./amt
        data[pp]['coins'] += 1
        data[pp]['blocks'] += coindata[d]['Block Count']

    print data
    for d in sorted(data, key=lambda d: data[d]['coins'], reverse=True):
        print '%s \t & %s \t & %s \t & %s / day \  \\\\' \
            % (d,
               data[d]['coins'],
               humanize.naturalsize(data[d]['blocks'] * 80),            
               humanize.naturalsize(data[d]['freq'] * 80 * 60 * 60 * 24),
               #data[d]['blocks'],
            )
    totcoins = sum(_['coins'] for _ in data.values())
    totblocks = sum(_['blocks'] for _ in data.values())
    totfreq = sum(_['freq'] for _ in data.values())
    print '\\hline'
    print '%s \t & %s  \t & \t %s \t & %s  / day  \\\\' \
        % ("Total",
           totcoins,
           humanize.naturalsize(totblocks * 80),
           humanize.naturalsize(totfreq * 80 * 60 * 60 * 24),
           #totblocks,
        )
    
    figure(1);
    clf();

    


# Run the simulation
from size import nipopow_size

def simulate(trials_per_day=500, days=60):

    import humanize
    # Prepare healthy
    healthy = [d for d in coindata if 'Status' in coindata[d] and coindata[d]['Symbol'] in market_cap and market_cap[coindata[d]['Symbol']] > 100000]

    for d in healthy:
        time = coindata[d]['Block Time']
        try:
            amt = float(time.split(' ')[0])
        except: continue
        amt = amt * 60. if 'minute' in time else amt
        coindata[d]['freq'] = 1./amt

    total = float(sum(market_cap[coindata[d]['Symbol']] for d in healthy))        

    # Initially empty state for the SPV client, initially X blocks
    state = dict((h,0) for h in healthy)
    blocks = dict((h, coindata[h]['Block Count']) for h in healthy)

    plainspv_size = 0

    #print "==" * 10    
    #print "Simulating %d transactions per day" % trials_per_day
    total_size = 0
    total_SPV_size = 0
    global total_today, total_SPV_today
    total_today = {}
    total_SPV_today = {}
    for day in range(days):
      #print '*'*10, 'Day', day, '*'*10
      
      for i in range(trials_per_day):
        # Update all the blocks!
        secs = (3600*24./trials_per_day)
        #print 'Time passed: %d seconds' % secs

        for h in healthy:
            blocks[h] += (secs * coindata[d]['freq']) # Updated however many blocks per second
        
        coin = np.random.choice(healthy, p=[market_cap[coindata[d]['Symbol']]/total for d in healthy])
        C = int(blocks[coin] - state[coin])
        state[coin] = blocks[coin]

        # Average number of Bitcoin transaction per block:
        # - 2000
        frac_of_bitcoin = float(market_cap[coindata[coin]['Symbol']]) / market_cap['BTC']
        tx_per_block = max(2, ceil(2000 * frac_of_bitcoin))
        # C: length of chain
        # x: # of transactions per block
        # m,k: params
        # block_header: prefix blocks 80
        # 48 - header size
        # coinbase transaction: ??
        # hash_size: 32
        m = 24
        C2 = max(C, 2*m+1)
        size = nipopow_size(C2, x=tx_per_block, m=24, k=6, block_header_size=80,
                            suffix_block_header_size=48, coinbase_size=200, hash_size=32)
        size = sum(size)
        # Otherwise just include the headers!
        #if size > C*48 + math.ceil(math.log(tx_per_block, 2)) * 32 + 200:
        #    print 'Falling back to SPV!'
        size = min(size, C*48 + math.ceil(math.log(tx_per_block, 2)) * 32 + 200)

        # Add just the total SPV
        total_SPV_size += math.ceil(math.log(tx_per_block, 2)) * 32 + 200 # Bytes in the merkle proof
        
        if 0 and coin not in ('bitcoin', 'ethereum'):
            print 'Drawing from coin', coin
            print 'difference:', C2, 'blocks:', blocks[coin]
            print humanize.naturalsize(size)
            print tx_per_block
        total_size += size

        total_today[day] = total_size
        total_SPV_today[day] = 48 * sum(blocks.values()) + total_SPV_size
    
    total_SPV_size += 48 * sum(blocks.values())
    
    marginal_size = (total_size-total_today[0])/(len(total_today))
    marginal_SPV_size = (total_SPV_size-total_SPV_today[0])/(len(total_SPV_today))
    #print 'Total:', humanize.naturalsize(total_size)
    #print 'Average marginal:', humanize.naturalsize(marginal_size)
    #print 'Total (SPV):', humanize.naturalsize(total_SPV_size)
    #print 'Average marginal:', humanize.naturalsize(marginal_SPV_size)
    #print state

    figure(1)
    clf()
    plot(np.array(total_SPV_today.values()) / (1024*1024.), label='Naive SPV')
    plot(np.array(total_today.values()) / (1024*1024.), label='NiPoPoW')
    return total_size, marginal_size, total_SPV_size, marginal_SPV_size

def experiment():
    import humanize
    global total_size, marginal_size, total_SPV_size, marginal_SPV_size
    #for tx_per_day in (100,500,1000):
    for tx_per_day in (100,500,1000,3000,):
      total_size, marginal_size, total_SPV_size, marginal_SPV_size = [],[],[],[]
      for i in range(10):
        a,b,c,d = simulate(tx_per_day)
        total_size.append(a)
        marginal_size.append(b)
        total_SPV_size.append(c)
        marginal_SPV_size.append(d)

      print '**'*10,
      print 'tx_per_day:', tx_per_day
      print 'total_size:', humanize.naturalsize(mean(total_size)), \
            'marginal_size:', humanize.naturalsize(mean(marginal_size)), \
            'total_SPV_size:', humanize.naturalsize(mean(total_SPV_size)), \
            'marginal_SPV_size:', humanize.naturalsize(mean(marginal_SPV_size)), \
            'fraction:', 1 - (mean(total_size) / mean(total_SPV_size)), \
            '()', 1 - (mean(marginal_size) / mean(marginal_SPV_size))
      print '%d &  %s & (%s)   & %s & (%s)   & %.25 (%.25)' % (tx_per_day, \
                humanize.naturalsize(mean(total_SPV_size)),
                humanize.naturalsize(mean(marginal_SPV_size)),
                humanize.naturalsize(mean(total_size)),
                humanize.naturalsize(mean(marginal_size)),
                1 - (mean(total_size) / mean(total_SPV_size)),
                1 - (mean(marginal_size) / mean(marginal_SPV_size)))
      
                                                           
                                      
    

def do_plots1():
    figure(1)
    clf()
    f, (ax, ax2) = subplots(2, 1, sharex=True, num=1)

    # Plot with broken axis
    # https://matplotlib.org/examples/pylab_examples/broken_axis.html
    
    ax.plot(np.array(total_SPV_today.values()) / (1024*1024.), label='Naive SPV')
    ax2.plot(np.array(total_SPV_today.values()) / (1024*1024.), label='Naive SPV')
    ax.plot(np.array(total_today.values()) / (1024*1024.), label='NiPoPoW')
    ax2.plot(np.array(total_today.values()) / (1024*1024.), label='NiPoPoW')
    ax.set_ylim(4500, 7000)  # outliers only
    ax2.set_ylim(0, 200)  # most of the data
    ax.spines['bottom'].set_visible(False)
    ax2.spines['top'].set_visible(False)
    ax.xaxis.tick_top()
    ax.tick_params(labeltop='off')  # don't put tick labels at the top
    ax2.xaxis.tick_bottom()
    d = .015  # how big to make the diagonal lines in axes coordinates

    # arguments to pass to plot, just so we don't keep repeating them
    kwargs = dict(transform=ax.transAxes, color='k', clip_on=False)
    ax.plot((-d, +d), (-d, +d), **kwargs)        # top-left diagonal
    ax.plot((1 - d, 1 + d), (-d, +d), **kwargs)  # top-right diagonal
    kwargs.update(transform=ax2.transAxes)  # switch to the bottom axes
    ax2.plot((-d, +d), (1 - d, 1 + d), **kwargs)  # bottom-left diagonal
    ax2.plot((1 - d, 1 + d), (1 - d, 1 + d), **kwargs)  # bottom-right diagonal
    ax.set_ylabel('Megabytes')
    ax2.set_ylabel('Megabytes')
    xlabel('Days')
    
