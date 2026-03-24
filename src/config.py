import logging
from logging.handlers import RotatingFileHandler

from dotenv import dotenv_values

# env
env = dotenv_values()
S3_ID = env['S3_ID'] or ''
S3_KEY = env['S3_KEY'] or ''
S3_ADDR = env['S3_ADDR'] or ''
DB_NAME = env['DB_NAME'] or ''
DB_PASS = env['DB_PASS'] or ''
DB_ADDR = env['DB_ADDR'] or ''
ML_MODE = env['ML_MODE'] or ''
TRAIN_MODE = env['TRAIN_MODE'] or ''
PROXIES = [k for i in range(100) if (k := env.get(f'PROXY{i}'))]

# logger
fmt = '%(asctime)s | [%(levelname)s] | %(funcName)s | %(message)s'
datefmt = '%Y-%m-%d %H:%M:%S'
default = {'maxBytes': 10 * 1024**2, 'backupCount': 12, 'encoding': 'utf-8'}
service = RotatingFileHandler('logs/service.log', **default)
service.setFormatter(logging.Formatter(fmt, datefmt))
service.addFilter(lambda record: record.levelno < logging.ERROR)

error = RotatingFileHandler('logs/error.log', **default)
error.setFormatter(logging.Formatter(fmt, datefmt))
error.setLevel(logging.ERROR)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(service)
logger.addHandler(error)
