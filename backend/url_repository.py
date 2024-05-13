import time
import json
from datetime import datetime

async def update_url_repository(url: str, url_repo: dict):
    timestamp = time.time()
    timestamp_string = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(timestamp))
    if url not in url_repo.keys():
        url_repo[url] = {"Date" : timestamp, "Date_String": timestamp_string}
        return True
    return False

# async def update_url_repository(url: str, url_repo: dict):
#     timestamp = time.time()
#     timestamp_string = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(timestamp))
#     sumURLascii = 0
#     for c in url:
#         sumURLascii += ord(c)
#     if sumURLascii not in url_repo.keys():
#         url_repo[sumURLascii] = {"Date" : timestamp, "Date_String": timestamp_string, "URL" : url}
#         return True
#     return False

def get_entries_sorted_by_date(file_path, page_number, page_size, sorting_norm):
    with open(file_path, "r") as json_file:
        data = json.load(json_file)
    # Sort the data by the Date key
    sorted_data = sorted(data.items(), key=lambda entry: entry[1]["Date"], reverse = sorting_norm)
    # Pagination logic
    start_index = (page_number - 1) * page_size
    end_index = min(start_index + page_size, len(sorted_data))
    paginated_data = sorted_data[start_index:end_index]
    return { "result" : paginated_data }
