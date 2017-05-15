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
        
if not 'coindata' in globals():
    coindata = {}
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

# Spot fixes
coindata['bytecoin']['Status'] = 'Healthy'

def histog():
    # Assume 80 bytes per header
    import humanize
    from collections import defaultdict

    healthy = [d for d in coindata if 'Status' in coindata[d] and coindata[d]['Status'] == 'Healthy']
    #healthy = [d for d in coindata if 'Status' in coindata[d]]
    print 'healthy:', len(healthy)
    
    data = defaultdict(lambda: dict(blocks=0, freq=0, coins=0))
    for d in healthy:
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

    
