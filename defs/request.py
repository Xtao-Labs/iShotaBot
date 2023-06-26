from io import BytesIO
from pathlib import Path

import aiofiles

from init import request
from scheduler import add_delete_file_job

cache_dir = Path("data") / "cache"
cache_dir.mkdir(exist_ok=True, parents=True)


def get_cache_path(url: str) -> Path:
    """Generate a filepath for the cache file."""
    return cache_dir / f"{hash(url)}"


async def cache_file(url: str) -> BytesIO:
    """Download a file and cache it."""
    cache_path = get_cache_path(url)
    if cache_path.exists():
        async with aiofiles.open(cache_path, "rb") as f:
            content = await f.read()
    else:
        response = await request.get(url)
        response.raise_for_status()
        content = response.read()
        async with aiofiles.open(cache_path, "wb") as f:
            await f.write(content)
        add_delete_file_job(str(cache_path))
    io = BytesIO(content)
    io.name = url.split("/")[-1] if len(url.split("/")) > 1 else "file"
    return io
