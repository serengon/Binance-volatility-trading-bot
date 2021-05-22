from unittest import mock
from unittest.mock import Mock

from app.jobs.execute_tasks import execute_task
from tests.mocks import task as task_mocks


class TestExecuteTask:

    def test_execute_task(self):
        mongo_mock = Mock()
        mongo_mock.update_one.return_value = task_mocks.saved_task_finished

        subprocess_run_mock = Mock()
        subprocess_run_mock.stdout = task_mocks.task_output.encode('utf-8')

        with mock.patch('app.services.task.mongo_tasks', return_value=mongo_mock):
            with mock.patch('app.jobs.execute_tasks.subprocess.run', return_value=subprocess_run_mock):
                executed_task = execute_task(task_mocks.saved_task_pending)
                assert executed_task == task_mocks.saved_task_finished
                mongo_mock.update_one.assert_called_with(
                    task_mocks.saved_task_pending,
                    {'$set': {'output': 'something', 'status': 'finished'}},
                )
