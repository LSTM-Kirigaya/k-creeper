from urllib.parse import urlparse
import os
import sys
from tqdm import tqdm

import wget
import requests
import fake_useragent
from loguru import logger

logger.remove(handler_id=None)
logger.add(
    level='INFO',
    rotation='00:00',
    retention='14 days',
    compression='zip',
    encoding='utf-8',
    enqueue=True,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
)



_tqdm_progress_instance = None
_fake_useragent = fake_useragent.UserAgent(browsers=['chrome'])

_default_progress_kwargs = {
    'desc': 'Downloading',
    'unit': ' bytes',
    'unit_scale': 1,
    'colour': 'green'
}

_default_proxies = {  
    'http': 'http://localhost:7890',  
    'https': 'http://localhost:7890',  
}

_file_size_cache = {}

def _make_tqdm_progress(total: float, display_progress: bool, progress_kwargs: dict):
    if not display_progress:
        return
    global _tqdm_progress_instance
    _tqdm_progress_instance = tqdm(total=total, **progress_kwargs)


def _update_tqdm_progress(n: float, display_progress: bool):
    if not display_progress:
        return
    if isinstance(_tqdm_progress_instance, tqdm):
        _tqdm_progress_instance.update(n)


def _close_tqdm_progress(display_progress: bool):
    if not display_progress:
        return
    if isinstance(_tqdm_progress_instance, tqdm):
        _tqdm_progress_instance.close()


def get_actual_filesize_from_url(url):
    if url in _file_size_cache:
        return _file_size_cache[url]
    # 先使用 head， 如果没有结果用流式 GET
    response = requests.head(url)
    filesize = get_filesize_from_response(response)
    if filesize == 0:
        logger.info('HEAD is not available in {}, attempt to use stream GET instead'.format(url))
        response = make_download_response(url, False, 0)
        filesize = get_filesize_from_response(response)

    if filesize > 0:
        logger.info('size of {} is {}'.format(url, filesize))
        _file_size_cache[url] = filesize

    return filesize

def make_download_response(url: str, resume: bool, already_download_bytes: int) -> requests.Response:
    headers = {
        'User-Agent': _fake_useragent.random
    }

    if resume:
        headers['Range'] = 'bytes={}-'.format(already_download_bytes)
    
    response = requests.get(url, stream=True, headers=headers)
    return response

def get_filesize_from_response(response: requests.Response) -> int:
    return int(response.headers.get('content-length', 0))

def get_io_mode(resume: bool, already_download_bytes: int) -> str:
    if already_download_bytes == 0 or not resume:
        return 'wb'
    else:
        return 'ab'
    
def write_chunk(chunk, save_path: str):
    with open(save_path, 'ab') as fp:
        fp.write(chunk)

def download_file(url: str, save_name: str = None, save_dir: str = None, resume: bool=True, display_progress: bool = True, progress_kwargs: dict={}) -> int:
    if save_name is None:
        save_name = wget.filename_from_url(url)
    if save_dir is None:
        save_dir = '.'
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    # make save path
    save_path = os.path.join(os.path.abspath(save_dir), save_name)
    already_download_bytes = 0
    if os.path.exists(save_path):
        already_download_bytes = os.path.getsize(save_path)
    
    for default_key, default_value in _default_progress_kwargs.items():
        if default_key not in progress_kwargs:
            progress_kwargs.__setitem__(default_key, default_value)

    # 发送请求
    response = make_download_response(url, resume, already_download_bytes)
    
    if resume:
        total_bytes = get_actual_filesize_from_url(url)
    else:
        total_bytes = get_filesize_from_response(response)

    # 如果下载的字节数和服务器返回的大小一致，说明下载完成
    if total_bytes == already_download_bytes:
        return already_download_bytes
    
    support_resume = response.status_code == 206
    
    # 制作内层进度条
    _make_tqdm_progress(total_bytes, display_progress, progress_kwargs)
    
    # 如果要求 resume 但是服务器不支持，重新发送一个普通的下载请求
    if resume and not support_resume:
        resume = False
        already_download_bytes = 0
        response = make_download_response(url, resume, already_download_bytes)
    # 否则 更新进度条信息为“继续下载”并更新进度条进度初始值
    else:
        _tqdm_progress_instance.set_description_str('Continue Downloading')
        _update_tqdm_progress(already_download_bytes, display_progress)

    _tqdm_progress_instance.set_postfix({'file': save_name, 'resumable': str(resume)})

    for chunk in response.iter_content(chunk_size=1024):
        write_chunk(chunk, save_path)
        _update_tqdm_progress(len(chunk), display_progress)
    
    _close_tqdm_progress(display_progress)
    logger.info('download file saved to ' + save_path)
    return already_download_bytes


# TODO: do google driver download


# TODO: do FTP download

if __name__ == '__main__':
    url = 'https://kirigaya.cn/files/pdfs/endnote的基本用法.pdf'
    try:
        download_file(url, resume=True)
    except KeyboardInterrupt:
        pass
