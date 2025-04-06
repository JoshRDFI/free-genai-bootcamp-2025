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

#### Example Scene Structure

```python
label new_scene:
    scene bg location
    
    show screen translation_button("Japanese text")
    show screen add_vocab_button("Japanese", "reading", "English meaning")
    character "Japanese text"
    hide screen translation_button
    hide screen add_vocab_button
    
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

### Audio Design

1. Use TTS for all Japanese dialogue
2. Add background music appropriate to the scene
3. Include sound effects for interactions

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

## Deployment

### Web Deployment

1. Build the Ren'Py project for web
2. Copy the build to the web server directory
3. Update Docker configurations if needed

### Updates and Maintenance

1. Plan for regular content updates
2. Monitor server logs for issues
3. Gather user feedback for improvements