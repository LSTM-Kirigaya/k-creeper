from typing import *
import os

import ftplib
from loguru import logger

logger.add(
    sink='logs/DDSM.log', 
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}", 
    level="INFO"
)

ftp = ftplib.FTP(
    host='figment.csee.usf.edu',
    user='anonymous'
)

def walk_dir(ftp: ftplib.FTP, dirname: str) -> Generator[str, None, None]:
    ftp.cwd(dirname)

    callback_result: List[Tuple[str]] = []
    def callback(*lines) -> None:
        print_infos = lines[0].split()
        auth = print_infos[0]
        name = print_infos[-1]
        callback_result.append((auth, name))
    
    ftp.dir(callback)

    for auth, name in callback_result:
        item_path = dirname + '/' + name
        # 这是一个文件夹
        if auth.startswith('d'):
            for sub_item_path in walk_dir(ftp, item_path):
                yield sub_item_path
        else:
            yield item_path


for path in walk_dir(ftp, '/pub/DDSM/cases/normals/'):
    save_path = path.replace('/pub', '/data/multimodal-medical-database/storage')
    save_dirname = os.path.dirname(save_path)
    if not os.path.exists(save_dirname):
        os.makedirs(save_dirname)
    ftp_path = 'ftp://' + (ftp.host + path).replace('//', '/')
    try:
        fp = open(save_path, 'wb')
        logger.info('download {} to {}'.format(ftp_path, save_path))
        ftp.retrbinary('RETR ' + path, fp.write, blocksize=1024)
        fp.close()
    except Exception:
        logger.exception('exception happens when downloading ' + ftp_path)