from pathlib import Path


def load_creative_analysis_prompt(version: str = "v2") -> str:
    prompt_path = Path(__file__).parent / "prompts" / "creative_analysis" / f"{version}.md"
    return prompt_path.read_text(encoding="utf-8")
