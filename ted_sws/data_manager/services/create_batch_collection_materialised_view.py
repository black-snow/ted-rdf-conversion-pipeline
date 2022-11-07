from pymongo import MongoClient
from ted_sws import config
from ted_sws.data_manager.services import MONGO_DB_AGGREGATES_DATABASE_DEFAULT_NAME

NOTICE_PROCESS_BATCH_COLLECTION_NAME = "batch_events"
LOG_EVENTS_COLLECTION_NAME = "log_events"


def create_batch_collection_materialised_view(mongo_client: MongoClient):
    database = mongo_client[config.MONGO_DB_AGGREGATES_DATABASE_NAME or MONGO_DB_AGGREGATES_DATABASE_DEFAULT_NAME]
    batch_collection = database[LOG_EVENTS_COLLECTION_NAME]
    batch_collection.aggregate([
        {
            "$group": {
                "_id": {"process_id": "$metadata.process_id",
                        "nr_of_notices": "$kwargs.number_of_notices",
                        "caller_name": "execute"
                        },
                "exec_time": {"$sum": "$duration"},
                "nr_of_pipelines": {"$sum": 1},
                "batch_nr_of_notices": {"$last": "$kwargs.number_of_notices"}
            }
        },
        {
            "$out": NOTICE_PROCESS_BATCH_COLLECTION_NAME
        }
    ])
