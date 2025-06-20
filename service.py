# service.py
import bentoml
from bentoml.io import JSON
from gpt_module import generate_gpt_response

svc = bentoml.Service("plants_gpt_service")

@svc.api(input=JSON(), output=JSON())
async def chat(data):
    template = data.get("template", "")
    detail = data.get("detail", "")
    task = data.get("task", "")
    goal = data.get("goal", "")

    result = generate_gpt_response(template, detail, task, goal)
    return {"response": result}
