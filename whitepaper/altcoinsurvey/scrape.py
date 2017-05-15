from gevent import monkey, pool
monkey.patch_all()

import requests
from BeautifulSoup import BeautifulSoup as BS

# Scrapes from the Coinwarz site

# Get the index
def get_main():
    req = requests.get("http://www.coinwarz.com/cryptocurrency/coins")
    c = req.content
    a = BS(c)
    coins = a.findAll("div", {"class":"coinCardIcon"})
    for c in coins:
         yield c.find('a')['href']

# coins = list(get_main())
POOL = pool.Pool(10)

def get_coin(coin):
    import time
    time.sleep(1)
    assert coin.startswith('/cryptocurrency/')
    global c
    fn = coin.split('/')[-1] + '.html'
    print fn
    url = 'http://www.coinwarz.com/' + coin
    print url
    req = requests.get(url)
    c = req.content
    with open(fn, 'w') as f:
        f.write(c)

    print 'OK'
    

    
    
