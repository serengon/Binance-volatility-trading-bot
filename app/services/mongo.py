import pymongo


def mongo():
    return pymongo.MongoClient(
        'mongo',
        port=27017,
    )


def mongo_tasks():
    client = mongo()
    client.server_info()
    return client.task_db.tasks
