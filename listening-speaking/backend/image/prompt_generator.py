from backend.image.llm_client import LLMClient

class ImagePromptGenerator:
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    def translate_to_english(self, japanese_text: str) -> str:
        """Translate Japanese text to English using LLM"""
        prompt = f"Translate this Japanese text to English: {japanese_text}"
        return self.llm_client.generate_response(prompt)

    def generate_option_prompt(self, option: str, option_letter: str) -> str:
        """Generate a prompt for a single option"""
        eng_option = self.translate_to_english(option)
        return (
            f"Create an anime-style image of {eng_option}. "
            f"The image should be clear and simple, with the letter {option_letter} in the corner. "
            f"Use a clean, minimalist style with clear visual elements. "
            f"No text except the letter {option_letter} should be present."
        )

    def generate_prompts(self, question: str, options: list) -> dict:
        """Generate prompts for all options"""
        # Translate question for context
        eng_question = self.translate_to_english(question)
        
        # Generate prompts for each option
        prompts = {}
        for i, option in enumerate(options):
            option_letter = chr(65 + i)  # A, B, C, D
            prompts[option_letter] = self.generate_option_prompt(option, option_letter)
        
        return prompts