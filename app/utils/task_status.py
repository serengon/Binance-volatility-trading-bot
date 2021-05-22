import enum


class TaskStatus(enum.Enum):
    NOT_STARTED = ('not_started', 'Task not started')
    FINISHED = ('finished', 'Task finished')

    def __init__(self, status, msg):
        self.status = status
        self.msg = msg
