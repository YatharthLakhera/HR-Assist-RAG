from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx, time, uuid, heapq
from threading import Lock, Thread
from concurrent.futures import Future
from dataclasses import dataclass
from typing import List
import queue

# --- Constants ---
CLASSIFICATION_SERVER_URL = "http://localhost:8001/classify"
MAX_BATCH = 5

app = FastAPI(
    title="Priority-Queue Based Classification Proxy",
    description="Batches and prioritizes longest requests"
)

class ProxyRequest(BaseModel):
    sequence: str

class ProxyResponse(BaseModel):
    result: str

@dataclass(order=True)
class PrioritizedItem:
    priority: int  # negative length: max-heap
    id: str
    sequence: str
    future: Future

# --- Thread-safe max-heap priority queue ---
class PriorityQueue:
    def __init__(self):
        self._heap: List[PrioritizedItem] = []
        self._lock = Lock()

    def push(self, item: PrioritizedItem):
        with self._lock:
            heapq.heappush(self._heap, item)

    def pop_n(self, n: int) -> List[PrioritizedItem]:
        with self._lock:
            items = []
            for _ in range(min(n, len(self._heap))):
                items.append(heapq.heappop(self._heap))
            return items

    def __len__(self):
        with self._lock:
            return len(self._heap)

# --- Global queue and worker ---
pq = PriorityQueue()

def classification_worker():
    client = httpx.Client(timeout=30.0)
    while True:
        batch = []
        # Wait for there to be something to process
        # waiting_time = 0.0
        while len(pq) == 0:
            # waiting_time += 0.1
            time.sleep(0.001)
        # print(f"processing : {len(pq)}")
        # Always pop up to MAX_BATCH elements thread-safely
        batch = pq.pop_n(MAX_BATCH)
        sequences = [item.sequence for item in batch]
        # max_len = max((len(s) for s in sequences), default=0)
        # Send to classification server with robust error/429 handling
        request_data = {"sequences": sequences}
        for attempt in range(3):
            try:
                # start_time = time.time()
                resp = client.post(CLASSIFICATION_SERVER_URL, json=request_data)
                if resp.status_code == 429:
                    # Rate limited, wait and retry
                    print(f"retrying")
                    time.sleep(0.1 * (attempt + 1))
                    continue

                # print(f"{len(batch)} Max sequence ----> {max_len} : Processing time --> {(time.time() - start_time)}")
                resp.raise_for_status()
                results = resp.json()["results"]
                break  # Success!
            except Exception as e:
                print("Exception occured")
                if attempt == 2:  # Final attempt
                    results = [e] * len(batch)
                else:
                    time.sleep(0.05 * (attempt + 1))
        # Set results/errors for all Futures
        futures = [item.future for item in batch]
        for fut, res in zip(futures, results):
            if isinstance(res, Exception):
                fut.set_exception(res)
            else:
                fut.set_result(res)

worker_thread = Thread(target=classification_worker, daemon=True)
worker_thread.start()

# --- API endpoint: only enqueues, does no batching/sending itself ---
@app.post("/proxy_classify", response_model=ProxyResponse)
def proxy_classify(req: ProxyRequest):
    fut = Future()
    item = PrioritizedItem(
        priority=-len(req.sequence),  # max-heap: longer first
        id=str(uuid.uuid4()),
        sequence=req.sequence,
        future=fut,
    )
    pq.push(item)
    try:
        result = fut.result(timeout=30.0)
        return ProxyResponse(result=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Classification failed: {e}")
