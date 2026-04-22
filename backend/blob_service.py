from azure.storage.blob import BlobServiceClient
import uuid
import os

CONNECTION_STRING = os.getenv("STORAGE_KEY") 

blob_service_client = BlobServiceClient.from_connection_string(CONNECTION_STRING)
container_client = blob_service_client.get_container_client("images")

def upload_image(file):
    filename = str(uuid.uuid4()) + ".jpg"
    blob_client = container_client.get_blob_client(filename)

    blob_client.upload_blob(file, overwrite=True)

    return blob_client.url