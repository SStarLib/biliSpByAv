from comtypes.automation import _
import requests, json, re, sys, os, urllib, argparse, time
from urllib.request import urlretrieve
from contextlib import closing
from urllib import parse
import xml2ass
from config import *
from bs4 import BeautifulSoup


class biliByAv:
    def __init__(self,dirname,avNum):
        self.dn_headers = {
            'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36',
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Referer': 'https://www.bilibili.com/video/'+str(avNum)
        }
        self.video_headers = {
            'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8'}

        self.danmu_header = {
            'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36',
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9'}

        self.dir = dirname
        self.sess = requests.Session()

    def get_download_url(self, url):
        try:
            req = self.sess.get(url=url,headers=self.video_headers,verify=False)
            pattern = re.compile('.__playinfo__=(.*)</script><script>window.__INITIAL_STATE__=', re.S)
            soup = BeautifulSoup(req.text, 'lxml')

            infos = re.findall(pattern, req.text)[0]
        except Exception:
            sys.stdout.write("下载异常\n")
            return '',''
        title = soup.title.string
        html = json.loads(infos)
        durl=html['durl']
        download_url = durl[0]['url']

        if 'mirrork' in download_url:
            oid = download_url.split('/')[6]
        else:
            oid = download_url.split('/')[7]
            if len(oid) >= 10:
                oid = download_url.split('/')[6]
        return title ,download_url, oid

    def video_downloader(self,video_url,video_name):
        size=0
        with closing(self.sess.get(video_url,headers=self.dn_headers,stream=True, verify=False)) as response:
            chunk_size = 1024
            content_size = int(response.headers['content-length'])
            if response.status_code==200:
                if CONFIG_ENABLE:
                    print('  [文件大小]:%0.2f MB\n' % (content_size / chunk_size / 1024))
                else:
                    sys.stdout.write('  [文件大小]:%0.2f MB\n' % (content_size / chunk_size / 1024))
                video_name=os.path.join(self.dir, video_name)
                with open(video_name, 'wb') as f:
                    for data in response.iter_content(chunk_size=chunk_size):
                        f.write(data)
                        size+=len(data)
                        f.flush()

                        if CONFIG_ENABLE:
                            print('  [下载进度]:%.2f%%' % float(size / content_size * 100) + '\r')
                        else:
                            sys.stdout.write('  [下载进度]:%.2f%%' % float(size / content_size * 100) + '\r')
                        if size / content_size == 1:
                            print('\n')
            else:
                print('链接异常')


    def download_xml(self, danmu_url, danmu_name):
        with closing(self.sess.get(danmu_url,headers=self.danmu_header, stream=True, verify=False)) as response:
            if response.status_code==200:
                with open(danmu_name, 'wb') as f:
                    for data in response.iter_content():
                        f.write(data)
                        f.flush()
            else:
                print('链接异常')

    def get_danmu(self, oid, filename):
        danmu_url=danmu_url = 'https://api.bilibili.com/x/v1/dm/list.so?oid={}'.format(oid)
        danmu_name = os.path.join(self.dir, filename + '.xml')
        danmu_ass = os.path.join(self.dir, filename + '.ass')
        self.download_xml(danmu_url, danmu_name)
        time.sleep(0.5)
        xml2ass.Danmaku2ASS(danmu_name, danmu_ass, 1280, 720)

    def download_video(self,avNum):
        if self.dir not in os.listdir():
            os.mkdir(self.dir)
        url = 'https://www.bilibili.com/video/'+str(avNum)
        # download_url ,oid= self.get_download_url(url)
        title,download_url,oid=self.get_download_url(url)
        title=title[:-26]
        for c in u'´☆❤◦\/:*?"<>【】|':
            title=title.replace(c, '')

        if title + '.flv' not in os.listdir(DIRNAME):
            if download_url != '' and oid != '':
                print('视频[ %s ]下载中:' % (title))
                self.video_downloader(download_url, title + '.flv')
                print('视频下载完成!')
                self.get_danmu(oid, title)
                print('弹幕下载完成')

if __name__ == '__main__':
    if CONFIG_ENABLE:
        bBa=biliByAv(DIRNAME, AVNUMBER)
        bBa.download_video(AVNUMBER)
    else:
        if len(sys.argv) == 1:
            sys.argv.append('--help')

        parser = argparse.ArgumentParser()
        parser.add_argument('-d', '--dir', required=True, help=('download path'))
        parser.add_argument('-a','--av', required=True, help=('av number'))

        args=parser.parse_args()
        bBa=biliByAv(args.dir,args.av)
        bBa.download_video(args.av)
    print('下载完毕！')

