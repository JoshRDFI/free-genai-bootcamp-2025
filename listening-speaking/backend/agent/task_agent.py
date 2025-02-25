from backend.image.prompt_generator import ImagePromptGenerator
from backend.image.image_generator import ImageGenerator
from backend.database.knowledge_base import KnowledgeBase

class TaskAgent:
    def __init__(self, image_api_url: str, image_api_key: str):
        self.image_generator = ImageGenerator(image_api_url, image_api_key)
        self.knowledge_base = KnowledgeBase()

    def generate_image_for_question(self, question_id: int):
        """
        Generate an image for a specific question and update the database.
        Args:
            question_id (int): The ID of the question.
        """
        # Fetch the question from the database
        question = self.knowledge_base.get_question_by_id(question_id)
        if not question:
            raise ValueError(f"Question with ID {question_id} not found.")

        # Generate the image prompt
        prompt = ImagePromptGenerator.generate_prompt(
            question["question"], question["options"]
        )

        # Generate the image
        filename = f"question_{question_id}"
        image_path = self.image_generator.generate_image(prompt, filename)

        # Update the database with the image path
        self.knowledge_base.update_question_image_path(question_id, image_path)