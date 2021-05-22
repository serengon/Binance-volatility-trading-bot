from bson.objectid import ObjectId

from app.services.mongo import mongo_tasks
from app.utils.error_codes import ErrorCode
from app.utils.error_handler import ErrorHandler
from app.utils.task_status import TaskStatus


def new_task(body):
    cmd = body['cmd']
    return mongo_tasks().insert_one(
        {
            'cmd': cmd,
            'status': TaskStatus.NOT_STARTED.status,
            'output': None,
        }
    )


def get_task_by_id(task_id: str):
    task = mongo_tasks().find_one({'_id': ObjectId(task_id)})
    if not task:
        msg = "Task doesn't exists."
        ErrorHandler.not_found(ErrorCode.NOT_FOUND, msg=msg)
    return task


def find_tasks_by_status(task_status: TaskStatus):
    return mongo_tasks().find({'status': task_status.status})


def update_task_result(task, output):
    return mongo_tasks().update_one(task, {'$set': {'output': output, 'status': TaskStatus.FINISHED.status}})
