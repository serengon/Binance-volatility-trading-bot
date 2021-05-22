import redis
from app.constants import redis as redis_constants

r = redis.Redis(host='redis', port=6379, db=0)

def binance_detect_mooning_job_stop():
    r.set(redis_constants.BINANCE_DETECT_MOONING_JOB_STATUS, redis_constants.BINANCE_JOB_STATUS_STOPPED)

def binance_detect_mooning_job_start():
    r.set(redis_constants.BINANCE_DETECT_MOONING_JOB_STATUS, redis_constants.BINANCE_JOB_STATUS_STARTED)

def binance_detect_mooning_job_status():
    current_status = int(r.get(redis_constants.BINANCE_DETECT_MOONING_JOB_STATUS))
    return current_status == redis_constants.BINANCE_JOB_STATUS_STARTED
