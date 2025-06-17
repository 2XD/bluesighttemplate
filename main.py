from config import PARENT_PAGE_ID
from confluence_loader import process_page

if __name__ == "__main__":
    print("Starting Confluence to Markdown sync...")
    process_page(PARENT_PAGE_ID)
    print("Sync complete.")
