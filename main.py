from fastapi import FastAPI, HTTPException, BackgroundTasks
from bs4 import BeautifulSoup
from typing import List
import asyncio
import httpx
import json
from backend.utils import preprocess_text, summarize_text, preprocess_text_cosine_matrix, calculate_cosine_distance_matrix, clean_links
from backend.url_repository import update_url_repository, get_entries_sorted_by_date
from backend.constants import URL_REPO_FILE_PATH, COMPRESSION_PERCENTAGE

app = FastAPI()

result_queue = asyncio.Queue()
url_repo = {}
vectorized_embeddings = {}
processing_completed = asyncio.Event()

@app.post('/scrape_page/')
async def scrape_page(url: str):
    global vectorized_embeddings
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=5)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                # H1 Heading of the page - Page Title
                page_title = soup.find('h1').get_text() if soup.find('h1') else None

                # Page Summary
                paragraphs = soup.find_all("p")
                text = " ".join([p.get_text() for p in paragraphs])
                sentences, words = preprocess_text(text)
                summary = summarize_text(sentences, words, COMPRESSION_PERCENTAGE)
                if url not in vectorized_embeddings.keys():
                    vectorized_embeddings[url] = preprocess_text_cosine_matrix(text)
                # Array of links embedded in the page
                links = [link.get('href') for link in soup.find_all('a')]
                links = clean_links(url, links)
                return {"url_link": url,"title": page_title, "summary": summary, "links": links}
    except httpx.HTTPStatusError as e:
        # If request fails, raise HTTPException
        raise HTTPException(status_code=e.response.status_code, detail="Failed to fetch page")

async def url_processing_in_background(urls: List[str]):
    global url_repo, result_queue, processing_completed
    results = []
    for url in urls:
        if await update_url_repository(url, url_repo):
            with open(URL_REPO_FILE_PATH, "w") as json_file:
               json.dump(url_repo, json_file)
        # Call the /scrape_page API for each URL and append the result to the list
        result = await scrape_page(url)
        results.append(result)
    await result_queue.put(results)
    processing_completed.set()
    print("Processing Done")

@app.post("/crawl_bulk_urls/")
async def crawl_bulk_urls(background_tasks: BackgroundTasks, urls: List[str]):
    # Start crawling in the background
    processing_completed.clear()
    background_tasks.add_task(url_processing_in_background, urls)
    return {"message": "Success - Crawling has begun!"}
    
@app.post('/results/')
async def processResults():
    global result_queue, processing_completed
    if not processing_completed.is_set():
        return {"message": "In Process"}
    elif result_queue.empty():
        return {"message": "In Process"}
    else:
        results = await result_queue.get()
        return {"message": "Completed", "results": results}

@app.get("/get_report")
async def reportPagination(pg_no: int, pg_size: int, sorting_norm: bool):
    return get_entries_sorted_by_date(URL_REPO_FILE_PATH, pg_no, pg_size, sorting_norm)

@app.post('/cosine_matrix')
async def compute_cosine_matrix():
    global vectorized_embeddings
    return {"result" : calculate_cosine_distance_matrix(vectorized_embeddings)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

