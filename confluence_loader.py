import requests
from markdownify import markdownify as md
from requests.auth import HTTPBasicAuth
from datetime import datetime
import os
import urllib3
from config import CONFLUENCE_TOKEN, CONFLUENCE_BASE_URL, CONFLUENCE_USER
from azure_blob_uploader import upload_to_blob

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HEADERS = {
    'Authorization': f'Bearer {CONFLUENCE_TOKEN}',
    'Accept': 'application/json'
}

def get_child_pages(page_id: str):
    url = f"{CONFLUENCE_BASE_URL}/{page_id}/child/page"
    response = requests.get(url, headers=HEADERS, verify=False)
    response.raise_for_status()
    return response.json().get('results', [])

def get_page_content(page_id: str):
    url = f"{CONFLUENCE_BASE_URL}/{page_id}"
    params = {'expand': 'body.storage,version'}
    response = requests.get(url, headers=HEADERS, params=params, verify=False)
    response.raise_for_status()
    data = response.json()
    title = data['title']
    html_body = data['body']['storage']['value']
    created_date = data['version']['when']
    return title, html_body, created_date

def process_page(page_id: str, path=''):
    try:
        title, html_content, created_date = get_page_content(page_id)
        markdown = md(html_content)

        clean_title = title.replace("/", "-").replace("\\", "-")
        blob_path = os.path.join(path, f"{clean_title}.md").replace("\\", "/")

        metadata = {
            'created_date': datetime.fromisoformat(created_date.replace("Z", "+00:00")).strftime('%Y-%m-%d'),
            'source_page': f"{CONFLUENCE_BASE_URL}/{page_id}"
        }
        upload_to_blob(markdown, blob_path, metadata)

        for child in get_child_pages(page_id):
            process_page(child['id'], os.path.join(path, clean_title))
    except Exception as e:
        print(f"[!] Error processing page {page_id}: {e}")

azure_blob_uploader.py
from azure.storage.blob import BlobServiceClient
from config import AZURE_STORAGE_CONNECTION_STRING, AZURE_CONTAINER_NAME

blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
container_client = blob_service_client.get_container_client(AZURE_CONTAINER_NAME)

try:
    container_client.create_container()
except Exception:
    pass  # Already exists

def upload_to_blob(content: str, blob_name: str, metadata: dict):
    try:
        blob_client = container_client.get_blob_client(blob_name)
        blob_client.upload_blob(content, overwrite=True)
        blob_client.set_blob_metadata(metadata)
        print(f"[✓] Uploaded: {blob_name}")
    except Exception as e:
        print(f"[!] Failed to upload {blob_name}: {e}")
