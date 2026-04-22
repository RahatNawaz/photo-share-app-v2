import os
from azure.cosmos import CosmosClient

COSMOS_URL = os.getenv("COSMOS_URL")
COSMOS_KEY = os.getenv("COSMOS_KEY")

client = CosmosClient(COSMOS_URL, COSMOS_KEY)

database = client.create_database_if_not_exists("photoDB")

container = database.create_container_if_not_exists(
    id="images",
    partition_key="/id"
)

def save_metadata(data):
    container.upsert_item(data)

def get_all_images():
    query = "SELECT * FROM images"
    return list(container.query_items(
        query=query,
        enable_cross_partition_query=True
    ))