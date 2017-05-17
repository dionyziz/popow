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

def simulate():

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

    trials_per_day = 80
    print "==" * 10    
    print "Simulating %d transactions per day" % trials_per_day
    total_size = 0
    for day in range(365):
      print '*'*10, 'Day', day, '*'*10
      for i in range(trials_per_day):
        # Update all the blocks!
        secs = (3600*24/trials_per_day)
        #print 'Time passed: %d seconds' % secs

        for h in healthy:
            blocks[h] += int(secs * coindata[d]['freq']) # Updated however many blocks per second
        
        coin = np.random.choice(healthy, p=[market_cap[coindata[d]['Symbol']]/total for d in healthy])
        C = blocks[coin] - state[coin]
        state[coin] = blocks[coin]

        # C: length of chain
        # x: # of transactions per block
        # m,k: params
        # block_header: prefix blocks 80
        # 48 - header size
        # coinbase transaction: ??
        # hash_size: 32
        size = nipopow_size(C, x=1, m=6, k=6, block_header_size=80,
                            suffix_block_header_size=48, coinbase_size=0, hash_size=32)
        if coin not in ('bitcoin', 'ethereum'):
            print 'Drawing from coin', coin
            print 'difference:', C, 'blocks:', blocks[coin]
            print humanize.naturalsize(sum(size))
        total_size += sum(size)
    print 'Total:', humanize.naturalsize(total_size)
