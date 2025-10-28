import openai
from app.env import SandboxEnvironment
from config import settings

class MangaFormatAgent:
    def __init__(self, system_prompt: str):
        self.system_prompt = system_prompt
        self.memory = []
        self.sandbox_env = SandboxEnvironment(settings.download_dir, settings.archive_dir)
        self.client = openai.OpenAI(
            api_key=settings.openai_key,
            base_url="https://api.openai.com/v1"
        )

    def run(self, text: str):
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": text}
        ]
        response = self.client.chat.completions.create(
            "gpt-5-nano-2025-08-07",
            messages=messages,
            tools=self.sandbox_env.as_tools()
        )
        print(response)