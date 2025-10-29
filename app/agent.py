import openai
from app.env import SandboxEnvironment
from config import settings
import json

class MangaFormatAgent:
    def __init__(self, system_prompt: str):
        self.system_prompt = system_prompt
        self.memory = []
        self.sandbox_env = SandboxEnvironment(settings.download_dir, settings.archive_dir)
        self.client = openai.OpenAI(
            api_key=settings.openai_key,
            base_url="https://api.openai.com/v1"
        )

    def orchestrate(self, text: str, print_responses=False):
        self.memory = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": text}
        ]
        response = self.client.chat.completions.create(
            model="gpt-5-nano-2025-08-07",
            messages=self.memory,
            tools=self.sandbox_env.as_tools()
        )
        tool_calls = response.choices[0].message.tool_calls
        while tool_calls:
            if print_responses: 
                if response_message := response.choices[0].message.content:
                    print(response_message)
            for tool_call in tool_calls:
                tool_call_id = tool_call.id
                function_name = tool_call.function.name
                args = json.loads(tool_call.function.arguments)
                if print_responses: print(f"[$] {function_name}({', '.join(f'{key}={repr(value)}' for key, value in args.items())})")
                tool_call_output = self.sandbox_env.run_tool(function_name, args)
                tool_call_response = {
                    "type": "function_call",
                    "call_id": tool_call_id,
                    "output": tool_call_output
                }
                self.memory.append(tool_call_response)
            response = self.client.chat.completions.create(
                model="gpt-5-nano-2025-08-07",
                messages=self.memory,
                tools=self.sandbox_env.as_tools()
            )