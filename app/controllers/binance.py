from flask import request, Blueprint, jsonify

from app.services import redis as redis_service
from app.utils.decorators import subscribe

bp_binance_detect_mooning_management = Blueprint('binance/detect_mooning/management', __name__)

def _return_status_response():
    status = redis_service.binance_detect_mooning_job_status()
    return {'status': 'ON' if status else 'OFF'}, 200

@subscribe(bp_binance_detect_mooning_management, '/binance/detect_mooning/management/status', methods=['GET'])
def get_status():
    return _return_status_response()

@subscribe(bp_binance_detect_mooning_management, '/binance/detect_mooning/management/start', methods=['POST'])
def start():
    redis_service.binance_detect_mooning_job_start()
    return _return_status_response()

@subscribe(bp_binance_detect_mooning_management, '/binance/detect_mooning/management/stop', methods=['POST'])
def stop():
    redis_service.binance_detect_mooning_job_stop()
    return _return_status_response()

