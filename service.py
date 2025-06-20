from bentoml import Service, Runnable, runners
from bentoml.io import JSON
import openai
import os
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Раннер для обработки сообщений
class ProPlantsRunnable(Runnable):
    def __init__(self):
        pass

    @Runnable.method(batchable=False)
    def chat(self, data: dict) -> dict:
        user_prompt = data.get("prompt", "")
        if not user_prompt:
            return {"error": "Пустой prompt"}

        try:
            completion = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": user_prompt}],
                temperature=0.7
            )
            result = completion.choices[0].message["content"]
            return {"response": result}
        except Exception as e:
            return {"error": str(e)}

# Создание раннера и сервиса
runner = runners.RunnableRunner(ProPlantsRunnable)()
svc = Service("ProPlants", runners=[runner])

# API endpoint
@svc.api(input=JSON(), output=JSON())
def chat(data: dict) -> dict:
    return runner.chat(data)
