import json
import uuid
import asyncio
from concurrent.futures import ThreadPoolExecutor
from qdrant_client import QdrantClient, models

executor = ThreadPoolExecutor(max_workers=4)

async def run_in_thread(func, *args, **kwargs):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(executor, lambda: func(*args, **kwargs))


async def ingest_data(client: QdrantClient, patch_collection: str, encoder, json_file: str):
    # Créer la collection si nécessaire (sync → thread)
    if not await run_in_thread(client.collection_exists, patch_collection):
        await run_in_thread(
            client.create_collection,
            patch_collection,
            vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE),
        )

    # Lecture JSON (I/O → thread)
    with open(json_file, "r", encoding="utf-8") as file:
        data = json.load(file)

    # Préparation
    documents = [f"{item['entity']} : {item['content']}" for item in data]
    ids = [str(uuid.uuid4()) for _ in data]
    metadatas = [
        {
            "entity": item["entity"],
            "patch": item["patch_version"],
            "source": item["url"],
            "raw_text": item["content"],
        }
        for item in data
    ]

    # Encodage (CPU bound → thread)
    vectors = await run_in_thread(encoder.encode, documents)
    vectors = vectors.tolist()

    # Upload vers Qdrant (lourd → thread)
    await run_in_thread(
        client.upload_collection,
        collection_name=patch_collection,
        vectors=vectors,
        payload=metadatas,
        ids=ids,
    )

    return {"items_indexed": len(documents), "patch": data[0]["patch_version"]}
