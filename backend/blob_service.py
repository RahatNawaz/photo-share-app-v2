import os
import uuid
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv

load_dotenv()

CONNECTION_STRING = os.getenv("STORAGE_CONNECTION_STRING")
CONTAINER_NAME = "images"

# this is a test comment to test yml 2
blob_service_client = BlobServiceClient.from_connection_string(CONNECTION_STRING)
container_client = blob_service_client.get_container_client(CONTAINER_NAME)

def upload_image(file):
    filename = str(uuid.uuid4()) + "_" + file.filename
    blob_client = container_client.get_blob_client(filename)

    blob_client.upload_blob(file, overwrite=True)

    return blob_client.url