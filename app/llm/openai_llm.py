from openai import OpenAI
import os

class OpenAILLM:
    def __init__(self, model="gpt-4o-mini"):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = model

    def __call__(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a precise structured output engine."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )

        return response.choices[0].message.content