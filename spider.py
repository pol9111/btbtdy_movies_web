import aiohttp
import asyncio
import re
import sys
import requests
from config import *


async def downloader(movie_ids):
    """设置下载任务"""
    base_url = 'http://www.btbtdy.net/vidlist/{}.html'
    sem = asyncio.Semaphore(1024)
    async with aiohttp.ClientSession() as session:
        for movie_id in movie_ids:
            url = base_url.format(str(int(movie_id)))
            tasks = [asyncio.ensure_future(fetch(sem, url, session, movie_id))]
        return await asyncio.gather(*tasks)


async def fetch(sem, url, session, movie_id):
    """执行下载任务"""
    async with sem:
        try:
            await asyncio.sleep(0.25)
            async with session.get(url, headers=HEADERS, timeout=20) as resp:
                html = await resp.text()
                await parse(html, movie_id)
        except Exception:
            print(movie_id, '请求失败!!')
            REDIS_COON.sadd(REDIS_RETRY, movie_id)
            pass


async def parse(html, movie_id):
    """解析页面"""
    titles = re.findall(r'title="(.*?)"', html, re.S)
    magnets = re.findall(r'href="(magnet.*?)">磁力', html, re.S)
    if titles and magnets and len(titles) == len(magnets):
        await save_to_redis(titles, magnets, movie_id)
    else:
        print('movie_id %s不可用' % movie_id)


async def save_to_redis(title, magnet, movie_id):
    """保存到redis"""
    for ti, mag in zip(title, magnet):
        data = {
            '标题': ti,
            '磁力': mag
        }
        REDIS_COON.lpush(REDIS_MOVIE, data)
        sys.stdout.write('%s 保存成功\n' % title)
    REDIS_COON.sadd(REDIS_DONE, movie_id)


def save_to_mongo():
    """数据持久化"""
    length = REDIS_COON.llen(REDIS_MOVIE)

    for i in range(1000, length, 1000):
        items_ = REDIS_COON.lrange(REDIS_MOVIE, 0, 1000)
        items = [eval(i) for i in items_]
        MONGO_TABLE.insert_many(items)

    remain = length % 1000
    items_ = REDIS_COON.lrange(REDIS_MOVIE, length - remain, length)
    items = [eval(i) for i in items_]
    MONGO_TABLE.insert_many(items)


def get_old_id():
    """获取上次爬取最后的id"""
    old_id = REDIS_COON.smembers(REDIS_DONE)
    if not old_id:
        return 0
    else:
        return max(old_id)


def get_newest_id(url):
    """获取最新的id"""
    resp = requests.get(url, headers=HEADERS, timeout=10)
    movie_id = re.findall(r'class="pic_link" href="/btdy/dy(\d+).html"', resp.text)
    movie_ids = [int(i) for i in movie_id]
    return max(movie_ids)


def start_requests(urls, loop):
    """开始请求任务"""
    sys.stdout.write('开始进行抓取\n')
    tasks = [asyncio.ensure_future(downloader(urls))]
    loop.run_until_complete(asyncio.wait(tasks))


def main():
    """运行"""
    sys.stdout.write('正在获取最新电影id\n')
    newest_id = get_newest_id(URL)
    todo_urls = [i for i in range(int(get_old_id()), newest_id)]
    loop = asyncio.get_event_loop()
    start_requests(todo_urls, loop)
    while REDIS_COON.scard(REDIS_RETRY) > 0:
        retry_list = []
        for _ in range(REDIS_COON.scard(REDIS_RETRY)):
            movie_id = REDIS_COON.spop(REDIS_RETRY)
            retry_list.append(movie_id)
        start_requests(retry_list, loop)
    else:
        loop.close()
        save_to_mongo()


if __name__ == '__main__':
    main()