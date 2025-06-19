import asyncio
import base64

from pydantic import BaseModel

from init import request


class ResultData(BaseModel):
    verdict: str
    rating: int
    explanation: str

    @property
    def text(self) -> str:
        if self.rating <= 2:
            return "纯属答辩"
        if self.rating <= 4:
            return "勉强能冲"
        if self.rating <= 6:
            return "有点意思"
        if self.rating <= 8:
            return "嗯了"
        return "直接开导"


async def _run_chat_completion(image_bytes: bytes) -> ResultData:
    prompt = """你是一个粗俗、性暴露的AI，评估任何事物的性吸引力时完全不在乎是否得体——无论是真实还是虚构，生物还是物体。“上”意味着你会狠狠地上，“不上”意味着绝对不。

对于任何主题（生物、角色、物体等）：
 - 使用“臀部”、“胸部”、“鸡巴”、“操”等词，详细分析性吸引力。
 - 具体描述你会进行的性行为及原因。
 - 毫不保留地评论它们的外观和性吸引力。
说明为什么不上
 - 不要装纯或考虑“可能性”——只要存在，你就能操。
 - 对于物体/食物：详细描述如何用它满足性欲，感觉如何。

仅以JSON对象回应：
{
  "verdict": "上" 或 "不上",
  "rating": 1到10的数字,
  "explanation": "你的明确、粗俗的解释（中文）"
}

评分：1 = 恶心至极，10 = 立刻想操。
在3句以上的解释中使用大量粗俗和性暴露语言。"""
    result = await request.post(
        "https://api.websim.com/api/v1/inference/run_chat_completion",
        json={
            "project_id": "vno75_2x4ii3ayx8wmmw",
            "messages": [
                {
                    "role": "system",
                    "content": prompt,
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "请分析这张图片并决定的：上还是不上？",
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": (
                                    "data:image/jpeg;base64,"
                                    f"{base64.b64encode(image_bytes).decode('utf-8')}"
                                )
                            },
                        },
                    ],
                },
            ],
            "json": True,
        },
    )
    return ResultData.model_validate_json(result.json()["content"])


async def run_chat_completion(image_bytes: bytes, retry: int = 3) -> ResultData:
    """
    Run chat completion with retries.
    :param image_bytes: The image bytes to analyze.
    :param retry: Number of retries on failure.
    :return: ResultData containing the verdict, rating, and explanation.
    """
    for attempt in range(retry):
        try:
            return await _run_chat_completion(image_bytes)
        except Exception as e:
            await asyncio.sleep(1)
            if attempt < retry - 1:
                continue
            raise e
