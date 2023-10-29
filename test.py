import atexit
import os

from wget import filename_from_url
from loguru import logger

@atexit.register
def exit_function():
    logger.warning('ready to exit')

_default_log_path = 'default.log'

logger.remove(handler_id=None)
logger.add(
    sink=_default_log_path,
    level='INFO',
    rotation='00:00',
    retention='14 days',
    compression='zip',
    encoding='utf-8',
    enqueue=True,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {module}:{function}:{line} - {message}"
)

def set_log_name(name: str):
    logger.configure(handlers=[{'sink': name}])
    if os.path.exists(_default_log_path):
        os.remove(_default_log_path)

if __name__ == '__main__':
    url = 'https://test.com/download.zip'
    
    filename = filename_from_url(url).split('.')[0]
    set_log_name(f'logs/{filename}.log')

    logger.info('hello world')
    logger.info('this is a test')