from typing import Optional

import httpx


async def forward_json(url: str, payload: dict) -> dict:
	async with httpx.AsyncClient(timeout=30.0) as client:
		r = await client.post(url, json=payload)
		r.raise_for_status()
		return r.json()


async def forward_multipart(url: str, files: dict, data: Optional[dict] = None) -> dict:
	async with httpx.AsyncClient(timeout=120.0) as client:
		r = await client.post(url, files=files, data=data or {})
		r.raise_for_status()
		return r.json()


async def get_json(url: str) -> dict:
	async with httpx.AsyncClient(timeout=10.0) as client:
		r = await client.get(url)
		r.raise_for_status()
		return r.json()


async def stream_file(url: str):
	async with httpx.AsyncClient(timeout=120.0) as client:
		async with client.stream("GET", url) as r:
			r.raise_for_status()
			async for chunk in r.aiter_bytes():
				yield chunk
