import os
import uuid
from azure.cosmos import CosmosClient
from dotenv import load_dotenv

load_dotenv()

COSMOS_ENDPOINT = os.getenv("COSMOS_ENDPOINT")
COSMOS_KEY = os.getenv("COSMOS_KEY")
DATABASE_NAME = os.getenv("COSMOS_DATABASE")
CONTAINER_NAME = os.getenv("COSMOS_CONTAINER")

client = CosmosClient(COSMOS_ENDPOINT, credential=COSMOS_KEY)

database = client.create_database_if_not_exists(id=DATABASE_NAME)

container = database.create_container_if_not_exists(
    id=CONTAINER_NAME,
    partition_key="/id"
)

def save_metadata(data):
    data["id"] = str(uuid.uuid4())
    container.create_item(body=data)
    return data

def get_all_images():
    query = "SELECT * FROM c"
    return list(container.query_items(
        query=query,
        enable_cross_partition_query=True
    ))

def search_images(keyword):
    query = """
    SELECT * FROM c 
    WHERE CONTAINS(LOWER(c.title), LOWER(@keyword))
    OR CONTAINS(LOWER(c.caption), LOWER(@keyword))
    OR CONTAINS(LOWER(c.location), LOWER(@keyword))
    """

    parameters = [
        {"name": "@keyword", "value": keyword}
    ]

    return list(container.query_items(
        query=query,
        parameters=parameters,
        enable_cross_partition_query=True
    ))