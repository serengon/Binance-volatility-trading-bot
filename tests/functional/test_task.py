import json
from unittest import mock
from unittest.mock import Mock

import pytest
from bson.objectid import ObjectId

from tests.functional.base import BaseTestCase
from tests.mocks import task as task_mocks

TASK_POST_URL = '/new_task'
TASK_GET_URL = '/get_output/{task_id}'

headers = {
    'Accept': 'application/json',
    'Content-Type': 'application/json'
}


class TestNewTask(BaseTestCase):

    def test_new_task_ok(self):
        mongo_mock = Mock()
        mongo_mock.insert_one.return_value = task_mocks.mongo_object_saved

        with mock.patch('app.services.task.mongo_tasks', return_value=mongo_mock):
            resp = self.app.post(TASK_POST_URL, headers=headers, data=json.dumps({'cmd': 'ls'}))
            assert resp.status_code == 201
            assert json.loads(resp.data)['id'] == task_mocks.task_id
            mongo_mock.insert_one.assert_called_with({'cmd': 'ls', 'status': 'not_started', 'output': None})

    def test_new_task_error_wrong_body(self):
        resp = self.app.post(TASK_POST_URL, headers=headers, data=json.dumps({'cmds': 'ls'}))
        assert resp.status_code == 400
        assert 'Missing key: cmd' in json.loads(resp.data)['message']

    def test_new_task_error_exception_saving(self):
        mongo_mock = Mock()
        exception_msg = 'Error saving to mongo'
        mongo_mock.insert_one.side_effect = Exception(exception_msg)

        with mock.patch('app.services.task.mongo_tasks', return_value=mongo_mock):
            resp = self.app.post(TASK_POST_URL, headers=headers, data=json.dumps({'cmd': 'ls'}))
            mongo_mock.insert_one.assert_called_with({'cmd': 'ls', 'status': 'not_started', 'output': None})
            assert resp.status_code == 500
            assert json.loads(resp.data)['message'] == exception_msg


class TestGetOutput(BaseTestCase):

    @pytest.mark.parametrize(
        'saved_task,expected_output',
        [
            (task_mocks.saved_task_finished, task_mocks.task_output),
            (task_mocks.saved_task_pending, None),
        ]
    )
    def test_get_output_ok(self, saved_task, expected_output):
        mongo_mock = Mock()
        mongo_mock.find_one.return_value = saved_task

        with mock.patch('app.services.task.mongo_tasks', return_value=mongo_mock):
            resp = self.app.get(TASK_GET_URL.format(task_id=task_mocks.task_id), headers=headers)
            mongo_mock.find_one.assert_called_with({'_id': ObjectId(task_mocks.task_id)})
            assert resp.status_code == 200
            assert json.loads(resp.data)['output'] == expected_output

    def test_get_output_error_not_found(self):
        mongo_mock = Mock()
        mongo_mock.find_one.return_value = None

        with mock.patch('app.services.task.mongo_tasks', return_value=mongo_mock):
            resp = self.app.get(TASK_GET_URL.format(task_id=task_mocks.task_id), headers=headers)
            mongo_mock.find_one.assert_called_with({'_id': ObjectId(task_mocks.task_id)})
            assert resp.status_code == 404
            assert json.loads(resp.data)['message'] == "Task doesn't exists."

    def test_get_output_error_exception_finding(self):
        mongo_mock = Mock()
        exception_msg = 'Error searching in mongo'
        mongo_mock.find_one.side_effect = Exception(exception_msg)

        with mock.patch('app.services.task.mongo_tasks', return_value=mongo_mock):
            resp = self.app.get(TASK_GET_URL.format(task_id=task_mocks.task_id), headers=headers)
            mongo_mock.find_one.assert_called_with({'_id': ObjectId(task_mocks.task_id)})
            assert resp.status_code == 500
            assert json.loads(resp.data)['message'] == exception_msg
