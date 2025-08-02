import time
import gzip
import json
import requests
import argparse
import logging
from threading import Lock
import concurrent.futures
import uuid

from qdrant_client import QdrantClient
from qdrant_client.http import models as rest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === CONFIGURATION ===
TOTAL_BATCHES = 39
STREAMING_ENDPOINT_BASE = ""
QDRANT_API_KEY = ""
QDRANT_CLOUD_URL = ""
QDRANT_COLLECTION = ""
MAX_RETRIES = 5
NUM_THREADS = 5

# Initialize Qdrant client
qdrant = QdrantClient(
    url=QDRANT_CLOUD_URL,
    api_key=QDRANT_API_KEY,
)

# Ensure collection exists with vector and payload schema
def ensure_collection():
    try:
        qdrant.get_collection(QDRANT_COLLECTION)
        logger.info(f"Collection '{QDRANT_COLLECTION}' already exists")
    except Exception:
        logger.info(f"Creating collection '{QDRANT_COLLECTION}'")
        qdrant.recreate_collection(
            collection_name=QDRANT_COLLECTION,
            vectors_config=rest.VectorParams(
                size=1024,            # adjust to your embedding dim
                distance=rest.Distance.COSINE,
            ),
            # No explicit payload schema needed in Qdrant; any payload is allowed
        )

def fetch_and_upsert_batch(batch_num: int):
    endpoint = f"{STREAMING_ENDPOINT_BASE}/{batch_num}"
    logger.info(f"Fetching batch {batch_num} from {endpoint}")

    try:
        resp = requests.get(endpoint, stream=True, timeout=600)
        resp.raise_for_status()

        compressed = b"".join(resp.iter_content(chunk_size=64*1024))
        decompressed = gzip.decompress(compressed).decode("utf-8")
    except Exception as e:
        logger.error(f"Error fetching/decompressing batch {batch_num}: {e}")
        return 0

    points = []
    for line in decompressed.splitlines():
        if not line.strip():
            continue
        try:
            doc = json.loads(line)
        except json.JSONDecodeError:
            continue
        # skip if no embedding
        embedding = doc.get("embedding")
        if not embedding:
            continue

        point = rest.PointStruct(
            id=str(uuid.uuid4()),    # Qdrant can accept string IDs
            vector=embedding,
            payload={
                "mongo_id": str(doc["_id"]),
                "yearsOfWorkExperience": int(doc.get("yearsOfWorkExperience", 0)),
                "prestigeScore": float(doc.get("prestigeScore", 0)),
                "country": str(doc.get("country", "")),
            },
        )
        points.append(point)

    print(f"batch no : {batch_num} -> total points to upsert: {len(points)}")

    if not points:
        logger.info(f"No valid points in batch {batch_num}")
        return 0

    BATCH_SIZE = 500
    total_upserted = 0

    # Split points into chunks of 500 and upsert each chunk separately
    for i in range(0, len(points), BATCH_SIZE):
        chunk = points[i : i + BATCH_SIZE]

        for attempt in range(MAX_RETRIES):
            try:
                qdrant.upsert(
                    collection_name=QDRANT_COLLECTION,
                    wait=True,
                    points=chunk,
                )
                logger.info(f"Upserted {len(chunk)} points from batch {batch_num} (chunk {i//BATCH_SIZE + 1})")
                total_upserted += len(chunk)
                break
            except Exception as e:
                logger.error(f"Upsert error (batch {batch_num}, chunk {i//BATCH_SIZE + 1}, attempt {attempt+1}): {e}")
                time.sleep(2 ** attempt)
        else:
            logger.error(f"Failed to upsert chunk {i//BATCH_SIZE + 1} of batch {batch_num} after {MAX_RETRIES} attempts")

    return total_upserted


def delete_collection():
    try:
        qdrant.delete_collection(collection_name=QDRANT_COLLECTION)
        logger.info(f"Deleted collection '{QDRANT_COLLECTION}'")
    except Exception as e:
        logger.warning(f"Could not delete collection: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Migrate resumes to Qdrant")
    parser.add_argument("action", choices=["delete", "migrate"], nargs="?", default="migrate")
    args = parser.parse_args()

    if args.action == "delete":
        delete_collection()
        exit(0)

    ensure_collection()
    batch_nums = list(range(TOTAL_BATCHES))
    total = 0
    lock = Lock()

    with concurrent.futures.ThreadPoolExecutor(max_workers=NUM_THREADS) as pool:
        futures = [pool.submit(fetch_and_upsert_batch, bn) for bn in batch_nums]
        for f in concurrent.futures.as_completed(futures):
            count = f.result() or 0
            with lock:
                total += count
            logger.info(f"Total upserted so far: {total}")

    logger.info(f"Migration complete. Total points upserted: {total}")
