import litellm

class MangaFormatAgent:
    def __init__(self, system_prompt: str):
        self.system_prompt = system_prompt
        self.client = None