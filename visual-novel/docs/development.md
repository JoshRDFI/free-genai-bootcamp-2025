# Japanese Learning Visual Novel - Development Guide

## Project Overview

This visual novel is designed to teach Japanese language at the JLPT N5 level, with a gameplay style similar to Nekopara. It integrates with Docker services for LLM access, TTS, and image generation.

## Development Workflow

### 1. Ren'Py Development

#### Adding New Scenes

1. Create new scene scripts in `renpy/game/scenes/`
2. Follow the pattern in existing scenes:
   - Use translation screens for Japanese text
   - Add vocabulary buttons for important words
   - Include choices for player interaction
   - Save progress at key points
3. For dynamic scenes, use the LLM integration functions:
   - `generate_conversation()` for character dialogues
   - `generate_lesson()` for custom learning content

#### Example Scene Structure with LLM Integration

```python
label new_scene:
    scene bg location
    
    show screen translation_button("Japanese text")
    show screen add_vocab_button("Japanese", "reading", "English meaning")
    character "Japanese text"
    hide screen translation_button
    hide screen add_vocab_button
    
    # Generate a dynamic conversation using the LLM
    $ conversation = generate_conversation(
        context="At a cafe in Tokyo",
        characters=["Sensei", "Student"],
        grammar_points=["です/ます form", "question particles か"],
        vocabulary=["コーヒー", "紅茶", "注文する"],
        num_exchanges=3
    )
    
    # Display the generated conversation
    if conversation:
        python:
            for exchange in conversation["conversation"]:
                speaker = exchange["speaker"]
                japanese_text = exchange["japanese_text"]
                english = exchange["english_translation"]
                
                # Display with appropriate character
                if speaker == "Sensei":
                    renpy.say(sensei, japanese_text)
                elif speaker == "Student":
                    renpy.say(player, japanese_text)
    
    menu:
        "Question in English?"
        
        "Option 1 in Japanese":
            player "Japanese response"
            # Consequences
            
        "Option 2 in Japanese":
            player "Japanese response"
            # Consequences
    
    $ save_progress("lesson_id", "scene_id", True)
```

#### Adding Characters

Define new characters in `renpy/game/characters.rpy`:

```python
define new_character = Character("Character Name", color="#hexcolor")
```

### 2. Backend Development

#### Adding API Endpoints

1. Add new routes to `server/app.py`
2. Follow RESTful conventions
3. Document the API for frontend developers

#### Database Schema Changes

1. Update the database initialization in `server/app.py`
2. Add migration scripts if needed
3. Test thoroughly before deploying

### 3. OpenVINO Integration

#### Adding New Models

1. Place model files in `data/openvino_models/`
2. Update the model loading code in `openvino/image_generator.py`
3. Add new generation functions as needed

#### Optimizing Performance

1. Use OpenVINO's optimization tools for models
2. Consider caching generated images for common scenes
3. Monitor memory usage and response times

### 4. AI-Powered Features Development

#### LLM Integration for Real-Time Character Interactions

The visual novel now integrates with Ollama Llama 3.2 to provide dynamic, real-time character interactions:

1. **Configuration**: The LLM service is configured in `server/app.py` with the `LLM_TEXT_URL` environment variable
2. **API Endpoints**: Two main endpoints handle LLM interactions:
   - `/api/generate-conversation`: Creates dynamic dialogues between characters
   - `/api/generate-lesson`: Builds complete lessons on custom topics
3. **Ren'Py Integration**: Functions in `renpy/game/script.rpy` connect to these endpoints:
   - `generate_conversation()`: Creates dynamic conversations with specified parameters
   - `generate_lesson()`: Creates complete lessons on custom topics

#### Enhancing Dynamic Conversations

1. Modify the prompt template in `server/app.py` under the `/api/generate-conversation` endpoint
2. Adjust parameters like temperature and max_tokens to control generation quality
3. Add additional context or constraints to improve relevance
4. Customize the conversation format in the JSON structure

#### Customizing Lesson Generation

1. Update the lesson generation prompt in `server/app.py` under the `/api/generate-lesson` endpoint
2. Add new fields to the lesson JSON structure for additional content types
3. Implement new Ren'Py screens to display custom lesson components
4. Adjust the complexity level for different JLPT targets

#### Example: Adding a New AI Feature

To add a new AI-powered feature (e.g., a quiz generator):

1. Add a new endpoint to `server/app.py`:

```python
@app.route('/api/generate-quiz', methods=['POST'])
def generate_quiz():
    data = request.json
    topic = data.get('topic')
    difficulty = data.get('difficulty', 'beginner')
    num_questions = data.get('num_questions', 5)
    
    # Construct prompt for the LLM
    prompt = f"""Generate a Japanese language quiz on {topic} at {difficulty} level..."""
    
    # Call the LLM and process response
    # Return structured quiz data
```

2. Add a corresponding function to the Ren'Py script:

```python
def generate_quiz(topic, difficulty="beginner", num_questions=5):
    """Generate a quiz using the LLM"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/generate-quiz",
            json={
                "topic": topic,
                "difficulty": difficulty,
                "num_questions": num_questions
            }
        )
        
        return response.json()
    except Exception as e:
        renpy.notify(f"Failed to generate quiz: {str(e)}")
        return None
```

3. Create a new Ren'Py screen to display the quiz:

```python
screen quiz_screen(quiz_data):
    # Display quiz questions and handle user input
```

## JLPT N5 Curriculum Integration

### Lesson Planning

Organize lessons around these JLPT N5 topics:

1. **Basic Greetings and Introductions**
   - おはようございます、こんにちは、こんばんは
   - 私の名前は～です

2. **Numbers and Counting**
   - 1-100 in Japanese
   - Counters (～人、～円、etc.)

3. **Basic Verbs and Actions**
   - Present tense (食べます、飲みます、etc.)
   - Past tense (食べました、飲みました、etc.)

4. **Basic Adjectives**
   - い-adjectives (大きい、小さい、etc.)
   - な-adjectives (きれい、静か、etc.)

5. **Basic Particles**
   - は、が、を、に、で、etc.

6. **Basic Questions**
   - 何、誰、どこ、いつ、etc.

7. **Time and Calendar**
   - Days of the week
   - Months and dates
   - Telling time

### Vocabulary Integration

1. Introduce 5-10 new vocabulary words per lesson
2. Reinforce vocabulary through repetition
3. Use the vocabulary tracking system to monitor player progress

## Visual Novel Best Practices

### Storytelling

1. Create a cohesive narrative that ties lessons together
2. Develop relatable characters with distinct personalities
3. Set in environments relevant to language learning (school, cafe, etc.)

### Visual Design

1. Use consistent art style for characters and backgrounds
2. Ensure text is readable against all backgrounds
3. Use visual cues to highlight important language points
4. Background images use the AVIF format for better compression and quality

### Audio Design

1. Use TTS for all Japanese dialogue

## LLM Integration Best Practices

### Prompt Engineering

1. **Be Specific**: Provide clear instructions in prompts about JLPT level, grammar points, and vocabulary
2. **Include Examples**: Add example outputs in prompts to guide the LLM's response format
3. **Set Constraints**: Explicitly state limitations (e.g., "Use only JLPT N5 grammar")
4. **Test Thoroughly**: Verify that generated content is appropriate and accurate

### Error Handling

1. Always implement fallback content in case the LLM service is unavailable
2. Add robust error handling for JSON parsing issues
3. Implement retry logic for temporary service disruptions
4. Cache common responses to reduce dependency on the LLM service

### Performance Optimization

1. Pre-generate content where possible to avoid real-time delays
2. Use appropriate temperature settings (lower for more predictable responses)
3. Set reasonable token limits to balance detail and generation speed
4. Consider batching requests for multiple content pieces
2. Add background music appropriate to the scene
3. Include sound effects for interactions

## LLM Prompt Engineering

### Effective Prompts for Language Learning

1. **Be specific about language level**:
   - Always specify JLPT N5 level in prompts
   - Include constraints like "use only basic grammar patterns"
   - Request furigana/readings for all kanji

2. **Structure output format**:
   - Request JSON format for structured data
   - Specify exact fields needed (speaker, text, translation, etc.)
   - Include example output in the prompt

3. **Provide context**:
   - Include scene setting and character relationships
   - Specify the learning objective of the conversation
   - Reference previously learned material

### Troubleshooting LLM Responses

1. **Handling malformed JSON**:
   - Implement robust parsing with fallbacks
   - Use regex to extract JSON from text responses
   - Have error handling for unexpected formats

2. **Managing token limits**:
   - Break large lessons into smaller chunks
   - Prioritize essential content when approaching limits
   - Implement pagination for long responses

3. **Improving response quality**:
   - Adjust temperature (lower for more predictable responses)
   - Use system messages to set context
   - Fine-tune prompts based on response quality

## Testing

### Game Testing

1. Test all dialogue paths and choices
2. Verify progress saving and loading
3. Check all translations and vocabulary entries

### API Testing

1. Test all API endpoints with various inputs
2. Verify error handling and edge cases
3. Check performance under load

### Language Testing

1. Have native Japanese speakers review content
2. Verify JLPT N5 alignment with official standards
3. Test with actual language learners for feedback

### AI Feature Testing

1. Test dynamic conversation generation with various contexts
2. Verify lesson generation with different topics and grammar points
3. Check for appropriate difficulty level in generated content
4. Test error handling when LLM services are unavailable

## Deployment

### Web Deployment

1. Build the Ren'Py project for web
2. Copy the build to the web server directory
3. Update Docker configurations if needed

### Updates and Maintenance

1. Plan for regular content updates
2. Monitor server logs for issues
3. Gather user feedback for improvements