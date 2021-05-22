from unittest.mock import Mock

from bson.objectid import ObjectId

from app.utils.task_status import TaskStatus

task_id = '5fc03e2271108ecaaf2d6e8e'

task_request = {'cmd': 'ls'}

task_output = 'something'

saved_task_pending = {
    '_id': ObjectId(task_id),
    'cmd': 'ls',
    'status': TaskStatus.NOT_STARTED.status,
    'output': None,
}

saved_task_finished = {
    '_id': ObjectId(task_id),
    'cmd': 'ls',
    'status': TaskStatus.FINISHED.status,
    'output': task_output,
}

mongo_object_saved = Mock()
mongo_object_saved.inserted_id = task_id
