import io
import time
import traceback
from typing import Tuple, List, Optional, BinaryIO

import httpx
from pydantic import BaseModel

from defs.glover import predict_url, predict_token

from PIL import Image, ImageDraw

headers = {"x-token": predict_token}
request = httpx.AsyncClient(timeout=60.0, headers=headers, verify=False)


class FacialAreaRegion(BaseModel):
    x: float
    y: float
    w: float
    h: float
    left_eye: Tuple[int, int]
    right_eye: Tuple[int, int]
    confidence: float


class Result(BaseModel):
    code: int
    msg: str
    faces: List[FacialAreaRegion] = []


class Face(BaseModel):
    predict_time: float
    draw_time: float


async def predict_photo(img_byte_arr: BinaryIO) -> Optional[Result]:
    files = {"file": ("image.png", img_byte_arr, "image/png")}
    try:
        req = await request.post(predict_url, files=files, headers=headers)
        return Result(**req.json())
    except Exception:
        traceback.print_exc()
        return None


async def predict(file: BinaryIO) -> Tuple[Optional[Face], Optional[BinaryIO]]:
    image = Image.open(file)
    file.seek(0)  # 重置指针到开始位置
    time1 = time.time()
    data = await predict_photo(file)
    time2 = time.time()
    if not data or not data.faces:
        return None, None
    for face in data.faces:
        # 框出人脸
        draw = ImageDraw.Draw(image)
        x1, y1 = face.x, face.y
        x2, y2 = x1 + face.w, y1 + face.h
        draw.rectangle([x1, y1, x2, y2], outline="red", width=2)
        # 画出眼睛
        draw.ellipse(
            [
                face.left_eye[0] - 2,
                face.left_eye[1] - 2,
                face.left_eye[0] + 2,
                face.left_eye[1] + 2,
            ],
            fill="red",
        )
        draw.ellipse(
            [
                face.right_eye[0] - 2,
                face.right_eye[1] - 2,
                face.right_eye[0] + 2,
                face.right_eye[1] + 2,
            ],
            fill="red",
        )
    binary_io = io.BytesIO()
    image.save(binary_io, "JPEG")
    binary_io.seek(0)
    time3 = time.time()
    return Face(predict_time=time2 - time1, draw_time=time3 - time2), binary_io
