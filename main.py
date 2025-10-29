import os

from app.agent import MangaFormatAgent

if __name__ == "__main__":
    this_dir = os.path.dirname(os.path.abspath(__file__))
    prompt_path = os.path.join(os.path.join(this_dir, "prompts"), "base.txt")
    with open(prompt_path) as f:
        system_prompt = f.read()

    agent = MangaFormatAgent(system_prompt=system_prompt)
    text = input("> ")
    agent.orchestrate(text)