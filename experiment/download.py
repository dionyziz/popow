from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship, backref
import requests, sys

BLOCKCHAIN_INFO_LATESTBLOCK = 'https://blockchain.info/latestblock'
BLOCKCHAIN_INFO_RAWBLOCK = 'https://blockchain.info/rawblock/%s'
GENESIS_PREVHASH = '0000000000000000000000000000000000000000000000000000000000000000'
BATCH_PROCESSING_COUNT = 20
BLOCKCHAIN_INFO_BLOCKHEADER_BYTES = 600

mysql = {
    'username': 'dionyziz',
    'password': '38944b101de41bd5a7f5d2a6442dc3bb231ef1a4',
    'database': 'dionyziz_blockchain',
    'host': 'localhost'
};

engine = create_engine(
    'mysql://%s:%s@%s/%s' %
    (mysql['username'], mysql['password'], mysql['host'], mysql['database']),
    echo=True
)

Session = sessionmaker(bind=engine)
session = Session()

Base = declarative_base()

class Block(Base):
    __tablename__ = 'block'

    id = Column(Integer, primary_key=True)
    hash = Column(String(64), unique=True)
    prevhash = Column(String(64), ForeignKey('block.hash'))
    bits = Column(String(64))
    children = relationship(
        'Block', backref=backref('parent', remote_side=[hash])
    )

def download_block(hash):
    url = BLOCKCHAIN_INFO_RAWBLOCK % hash
    print 'Downloading block %s' % hash
    print 'HTTP GET %s' % url
    headers = {'range': BLOCKCHAIN_INFO_BLOCKHEADER_BYTES}
    r = requests.get(url)
    block_info = r.json()
    return {
        'hash': block_info['hash'],
        'prevhash': block_info['prev_block'],
        'bits': block_info['bits']
    }

def process_block(block):
    print 'Processing block %s' % block.hash
    block_info = download_block(block.hash)
    print block_info
    block.bits = block_info['bits']
    if block_info['prevhash'] == GENESIS_PREVHASH:
        print 'Arrived at genesis block'
        return None
    block.parent = Block(hash=block_info['prevhash'])
    session.add(block.parent)
    return block.parent

def download_latest_block_hash():
    url = BLOCKCHAIN_INFO_LATESTBLOCK
    r = requests.get(url)
    block_info = r.json()
    return block_info['hash']

def process_latest_block():
    hash = download_latest_block_hash()
    block_info = download_block(hash)
    block = Block(hash=hash)
    session.add(block)
    return block

def get_orphan():
    orphans = session.query(Block).filter(Block.parent == None).limit(1)
    if orphans:
        return orphans[0]
    else:
        return None

block = process_latest_block()

orphan = get_orphan()
while orphan is not None:
    print 'Orphan block found: %s' % orphan.hash

    current_block = block
    for i in range(BATCH_PROCESSING_COUNT):
        current_block = process_block(current_block)
        if current_block is None:
            break

    session.commit()
