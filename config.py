import redis
from fake_useragent import UserAgent
from pymongo import MongoClient

URL = 'http://www.btbtdy.net/btfl/dy1.html'
HEADERS = {
'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
'Accept-Encoding': 'gzip, deflate',
'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7,zh-TW;q=0.6',
'Cache-Control': 'no-cache',
'Host': 'www.btbtdy.net',
'Pragma': 'no-cache',
'Proxy-Connection': 'keep-alive',
'User-Agent':  UserAgent().random,
}

REDIS_POOL = redis.ConnectionPool(host='127.0.0.1', port=6379, db=2, max_connections=1024)
REDIS_COON = redis.StrictRedis(connection_pool=REDIS_POOL, decode_responses=True)
REDIS_RETRY = 'btbtdy:retry'
REDIS_DONE = 'btbtdy:done'
REDIS_MOVIE = 'btbtdy:moive'
# REDIS_MOVIES = 'btbtdy:moives'

MONGO_CLIENT = MongoClient('127.0.0.1')
MONGO_DB = MONGO_CLIENT['btbtdy']
MONGO_TABLE = MONGO_DB['movies']
