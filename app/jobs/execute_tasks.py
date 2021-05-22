import subprocess
import time

from app.services import task as task_service
from app.utils.task_status import TaskStatus


def run():
    while True:
        time.sleep(1)
        tasks_to_process = task_service.find_tasks_by_status(TaskStatus.NOT_STARTED)
        for task in tasks_to_process:
            execute_task(task)


def execute_task(task: dict):
    result = subprocess.run(task['cmd'].split(' '), stdout=subprocess.PIPE)
    return task_service.update_task_result(
        task=task,
        output=str(result.stdout.decode('utf-8')),
    )


if __name__ == '__main__':
    run()
