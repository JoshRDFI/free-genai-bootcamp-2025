class ImagePromptGenerator:
    def __init__(self, llm_client):
        self.llm_client = llm_client  # Ollama API client

    def translate_to_english(self, japanese_text: str) -> str:
        """Translate Japanese text to English using Ollama"""
        prompt = f"Translate this Japanese text to English: {japanese_text}"
        response = self.llm_client.generate_response(prompt)
        return response.strip()

    def generate_prompt(self, question: str, options: list) -> str:
        """Generate an image prompt from Japanese question and options"""
        # Translate question and options
        eng_question = self.translate_to_english(question)
        eng_options = [self.translate_to_english(opt) for opt in options]

        # Generate the image prompt
        prompt = (
            "Create a minimalist 2x2 grid image with simple black line drawings on white background. "
            "Each panel should be labeled (a,b,c,d) and contain a single object: "
        )
        for i, option in enumerate(eng_options):
            prompt += f"\nPanel {chr(97 + i)}: A simple line drawing of {option}"

        return prompt