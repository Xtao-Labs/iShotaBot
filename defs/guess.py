import json

from init import request


async def guess_str(key):
    if key == '':
        return ''
    text = {'text': key}
    guess_json = (await request.post("https://lab.magiconch.com/api/nbnhhsh/guess", data=text, verify=False)).json()
    if len(guess_json) == 0:
        return ""
    guess_res = []
    for num in range(len(guess_json)):
        guess_res1 = json.loads(json.dumps(guess_json[num]))
        guess_res1_name = guess_res1['name']
        try:
            guess_res1_ans = ", ".join(guess_res1['trans'])
        except:
            try:
                guess_res1_ans = ", ".join(guess_res1['inputting'])
            except:
                guess_res1_ans = "尚未录入"
        guess_res.extend([f"词组：{guess_res1_name}" + "\n释义：" + guess_res1_ans])
    return "\n\n".join(guess_res)
