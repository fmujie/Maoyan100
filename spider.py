import re
import os
from hashlib import md5
import json
import pymongo
import requests
from config import *
from multiprocessing import Pool
from requests.exceptions import RequestException

client = pymongo.MongoClient(MONGO_URL)
db = client[MONGO_DB]
headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36'
    }


def get_one_page(url):
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.text
        return None
    except RequestException:
        return None


def parse_one_page(html):
    #compile 通过正则表达式的一个字符串，编译生成一个正则表达式对象
    #re.S匹配任意的字符，'.'可以代表任意的换行符\n
    pattern = re.compile('<dd>.*?board-index.*?>(\d+)</i>.*?data-src="(.*?)".*?name"><a'
                         +'.*?>(.*?)</a>.*?star">(.*?)</p>.*?releasetime">(.*?)</p>'
                         +'.*?integer">(.*?)</i>.*?fraction">(.*?)</i>.*?</dd>', re.S)
    items = re.findall(pattern, html)
    print(items)
    print(type(items))
    for item in items:
        yield {
            'index': item[0],
            'image': item[1],
            'title': item[2],
            'actor': item[3].strip()[3:],
            'time': item[4].strip()[5:],
            'score': item[5]+item[6]
        }


def write_to_file(content):
    print(type(content))
    with open('result.txt', 'a', encoding='utf-8') as f:
        f.write(json.dumps(content, ensure_ascii=False) + '\n')
        f.close()


def save_to_mongo(result):
    if db[MONGO_TABLE].insert(result):
        print('存储到MongoDB成功', result)
        return True
    else:
        return False


def download_image(url):
    print('正在下载：', url)
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            save_image(response.content)
        return None
    except RequestException:
        print('请求图片出错', url)
        return None


def save_image(content):
    file_path = '{0}\\{1}\\{2}.{3}'.format(os.getcwd(), 'images', md5(content).hexdigest(), '.png')
    # print(file_path)
    if not os.path.exists(file_path):
        with open(file_path, 'wb') as f:
            f.write(content)
            f.close()


def main(offsetVal):
    url = 'https://maoyan.com/board/4?offset=' + str(offsetVal)
    html = get_one_page(url)
    parse_one_page(html)
    for item in parse_one_page(html):
    #     print(item)
    #     print(item['image'])
        write_to_file(item)
        save_to_mongo(item)
        download_image(item['image'])


if __name__ == '__main__':
    pool = Pool()
    #map()将数组中的每一个元素拿出来当作函数的参数
    pool.map(main, [i*10 for i in range(10)])