import time
from log import logger

class QuestionGenerator:
    def generate_question(self, question: str, options: list, correct_answer: str) -> dict:
        """Generate a complete question with all components"""
        try:
            # Generate image prompts for each option
            prompts = self.image_prompt_generator.generate_prompts(question, options)
            
            # Generate images for each option
            base_filename = f"question_{int(time.time())}"
            image_paths = self.image_generator.generate_option_images(prompts, base_filename)
            
            # Create the question object
            question_obj = {
                "question": question,
                "options": options,
                "correct_answer": correct_answer,
                "images": image_paths  # Dictionary of image paths keyed by option letter
            }
            
            return question_obj
            
        except Exception as e:
            logger.error(f"Error generating question: {str(e)}")
            return None

    def generate_questions(self, count: int = 1) -> list:
        """Generate multiple questions"""
        questions = []
        for i in range(count):
            try:
                # Generate question content
                question_content = self._generate_question_content()
                if not question_content:
                    continue
                
                # Generate image prompts and images
                prompts = self.image_prompt_generator.generate_prompts(
                    question_content["question"],
                    question_content["options"]
                )
                
                # Generate images for each option
                base_filename = f"question_{int(time.time())}_{i}"
                image_paths = self.image_generator.generate_option_images(prompts, base_filename)
                
                # Create complete question object
                question = {
                    "question": question_content["question"],
                    "options": question_content["options"],
                    "correct_answer": question_content["correct_answer"],
                    "images": image_paths  # Dictionary of image paths keyed by option letter
                }
                
                questions.append(question)
                logger.info(f"Successfully generated question {i+1}/{count}")
                
            except Exception as e:
                logger.error(f"Error generating question {i+1}: {str(e)}")
                continue
        
        return questions 