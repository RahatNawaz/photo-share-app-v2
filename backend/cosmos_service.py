import os
import uuid
from azure.cosmos import CosmosClient
from dotenv import load_dotenv

load_dotenv()

COSMOS_ENDPOINT = os.getenv("COSMOS_ENDPOINT")
COSMOS_KEY = os.getenv("COSMOS_KEY")
DATABASE_NAME = os.getenv("COSMOS_DATABASE", "PhotoShareDB")
CONTAINER_NAME = os.getenv("COSMOS_CONTAINER", "Images")

client = CosmosClient(COSMOS_ENDPOINT, credential=COSMOS_KEY)

database = client.get_database_client(DATABASE_NAME)
container = database.get_container_client(CONTAINER_NAME)

def save_metadata(data):
    data["id"] = str(uuid.uuid4())
    container.create_item(body=data)
    return data

def get_all_images():
    return list(container.query_items(
        query="SELECT * FROM c WHERE IS_DEFINED(c.imageUrl)",
        enable_cross_partition_query=True
    ))

def search_images(keyword):
    query = """
    SELECT * FROM c
    WHERE IS_DEFINED(c.imageUrl)
    AND (
        CONTAINS(LOWER(c.title), LOWER(@keyword))
        OR CONTAINS(LOWER(c.caption), LOWER(@keyword))
        OR CONTAINS(LOWER(c.location), LOWER(@keyword))
        OR CONTAINS(LOWER(c.people), LOWER(@keyword))
        OR ARRAY_CONTAINS(c.tags, @keyword)
    )
    """
    parameters = [
        {"name": "@keyword", "value": keyword.lower()}
    ]

    return list(container.query_items(
        query=query,
        parameters=parameters,
        enable_cross_partition_query=True
    ))