# Define characters used by this game
define sensei = Character("先生", color="#c8ffc8", what_italic=False)
define player = Character("[player_name]", color="#c8c8ff")

# Define images
image bg classroom = "images/backgrounds/classroom.avif"
image bg cafe = "images/backgrounds/cafe.avif"
image bg street = "images/backgrounds/street.avif"
image bg conv_store = "images/backgrounds/conv_store.avif"
image bg ramen_shop = "images/backgrounds/ramen_shop.avif"
image bg store_traditional = "images/backgrounds/store_traditional.avif"

# Game variables
default player_name = "Student"
default current_lesson = "lesson1"
default current_scene = "intro"
default user_id = 1

# Import Python modules for API communication
init python:
    import os
    import json
    from python.api import APIService
    from python.jlpt import JLPTCurriculum
    from python.progress import ProgressTracker
    
    # Initialize API service and curriculum
    api = APIService()
    jlpt = JLPTCurriculum()
    
    # Helper functions that wrap the API service
    def save_progress(lesson_id, scene_id, completed=False):
        """Save player progress to the server"""
        result = api.save_progress(user_id, lesson_id, scene_id, completed)
        if "error" in result:
            renpy.notify(f"Failed to save progress: {result['error']}")
        return result
    
    def get_translation(text):
        """Get translation for Japanese text"""
        translation = api.get_translation(text, "ja", "en")
        if translation == "Translation failed":
            renpy.notify("Translation failed")
        return translation
    
    def get_audio(text, voice="ja-JP"):
        """Get audio for text using TTS service"""
        audio_path = api.get_audio(text, voice)
        if not audio_path:
            renpy.notify("TTS failed")
        return audio_path
    
    def add_vocabulary(japanese, reading=None, english=None):
        """Add vocabulary to player's list"""
        result = api.add_vocabulary(user_id, japanese, reading, english, current_lesson)
        if "error" in result:
            renpy.notify(f"Failed to add vocabulary: {result['error']}")
        return result
    
    def generate_image(prompt, image_type="background", negative_prompt=None, width=512, height=512):
        """Generate an image using the image generation service"""
        image_path = api.generate_image(prompt, image_type, negative_prompt, width, height)
        if not image_path:
            renpy.notify("Image generation failed")
        return image_path
    
    def generate_conversation(context, characters, grammar_points=None, vocabulary=None, num_exchanges=3):
        """Generate a dynamic conversation using the LLM"""
        conversation = api.generate_conversation(context, characters, grammar_points, vocabulary, num_exchanges)
        if not conversation:
            renpy.notify("Conversation generation failed")
        return conversation
    
    def generate_lesson(topic, grammar_points=None, vocabulary_focus=None, lesson_number=1, scene_setting="classroom"):
        """Generate a complete lesson using the LLM"""
        lesson = api.generate_lesson(topic, grammar_points, vocabulary_focus, lesson_number, scene_setting)
        if not lesson:
            renpy.notify("Lesson generation failed")
        return lesson

# Custom screen for translation
screen translation_button(text):
    vbox:
        xalign 0.98
        yalign 0.02
        textbutton "Translate" action Show("translation_popup", text=text)

screen translation_popup(text):
    modal True
    frame:
        xalign 0.5
        yalign 0.5
        xpadding 20
        ypadding 20
        vbox:
            spacing 10
            text "Japanese:" size 20
            text text size 24
            text "English:" size 20
            text get_translation(text) size 24
            textbutton "Close" action Hide("translation_popup")

# Custom screen for vocabulary
screen add_vocab_button(japanese, reading=None, english=None):
    vbox:
        xalign 0.02
        yalign 0.02
        textbutton "Add to Vocabulary" action [Function(add_vocabulary, japanese, reading, english), Show("vocab_added")]

screen vocab_added():
    timer 2.0 action Hide("vocab_added")
    frame:
        xalign 0.5
        yalign 0.3
        xpadding 20
        ypadding 10
        text "Added to vocabulary!" size 20

# The game starts here
label start:
    # Player name input
    $ player_name = renpy.input("What is your name?", "Student", length=20)
    $ player_name = player_name.strip()
    if player_name == "":
        $ player_name = "Student"
    
    # Save initial progress
    $ save_progress("lesson1", "intro")
    
    menu:
        "Choose how to start:"
        
        "Start with pre-made Lesson 1 (Basic Greetings)":
            jump lesson1_intro
            
        "Generate a custom lesson using AI":
            jump dynamic_lesson_generator

# Dynamic lesson generator
label dynamic_lesson_generator:
    scene bg classroom
    
    "Welcome to the dynamic lesson generator! Here you can create custom Japanese lessons."
    
    $ topic = renpy.input("What topic would you like to learn about?", "Basic Greetings", length=50)
    
    python:
        # Default grammar points for JLPT N5
        grammar_options = [
            "Basic sentence structure",
            "Desu/masu form",
            "Basic particles (wa, ga, o, ni, de)",
            "Question markers with ka",
            "Demonstratives (kore, sore, are)",
            "Te-form for requests",
            "Past tense",
            "Counting and numbers"
        ]
        
        # Let the player select grammar points
        selected_grammar = []
        for grammar in grammar_options[:3]:  # Limit to 3 for simplicity
            if renpy.call_screen("yes_no_prompt", message=f"Include '{grammar}' in your lesson?"):
                selected_grammar.append(grammar)
    
    "Generating your custom lesson on [topic]..."
    "This may take a moment as our AI creates your personalized content."
    
    $ lesson_data = generate_lesson(topic, selected_grammar, None, 1, "classroom")
    
    if lesson_data:
        $ lesson_title = lesson_data.get("metadata", {}).get("title", topic)
        $ dialogue_script = lesson_data.get("dialogue_script", [])
        $ vocabulary = lesson_data.get("vocabulary", [])
        
        "Your custom lesson '[lesson_title]' is ready!"
        
        # Display the lesson objectives
        python:
            objectives = lesson_data.get("metadata", {}).get("objectives", [])
            if objectives:
                renpy.say(None, "In this lesson, you will:")
                for objective in objectives:
                    renpy.say(None, "- " + objective)
        
        # Show the dialogue script
        if dialogue_script:
            "Let's begin the dialogue practice:"
            
            python:
                for exchange in dialogue_script:
                    speaker = exchange.get("speaker", "")
                    japanese_text = exchange.get("japanese", "")
                    english = exchange.get("english", "")
                    
                    # Determine which character is speaking
                    if speaker == "Sensei":
                        speaking_character = sensei
                    else:
                        speaking_character = player
                    
                    # Show the dialogue with translation option
                    renpy.show_screen("translation_button", japanese_text)
                    speaking_character(japanese_text)
                    renpy.hide_screen("translation_button")
                    
                    # For vocabulary words, we could add them automatically
                    for vocab in vocabulary:
                        if vocab.get("japanese") in japanese_text:
                            renpy.show_screen("add_vocab_button", 
                                vocab.get("japanese"), 
                                vocab.get("reading"), 
                                vocab.get("english"))
                            renpy.pause(0.5)
                            renpy.hide_screen("add_vocab_button")
        
        # Show practice exercises if available
        python:
            exercises = lesson_data.get("practice_exercises", [])
            if exercises:
                for i, exercise in enumerate(exercises):
                    question = exercise.get("question", "")
                    options = exercise.get("options", [])
                    correct_answer = exercise.get("correct_answer", 0)
                    explanation = exercise.get("explanation", "")
                    
                    renpy.say(None, f"Practice Question {i+1}: {question}")
                    
                    # Create a menu for the options
                    choices = [(option, idx) for idx, option in enumerate(options)]
                    result = renpy.display_menu(choices)
                    
                    if result == correct_answer:
                        renpy.say(sensei, "正解です！ (Correct!)")
                    else:
                        renpy.say(sensei, "違います。もう一度試してください。 (Incorrect. Please try again.)")
                    
                    renpy.say(sensei, explanation)
        
        # Show review summary
        python:
            review = lesson_data.get("review_summary", [])
            if review:
                renpy.say(None, "Let's review what we learned:")
                for point in review:
                    renpy.say(sensei, point)
        
        "You've completed your custom lesson on [lesson_title]!"
        
        menu:
            "What would you like to do next?"
            
            "Generate another custom lesson":
                jump dynamic_lesson_generator
                
            "Return to the main menu":
                return
    else:
        "Sorry, I couldn't generate a lesson right now. Let's try again later."
        return

# Screen for yes/no prompts
screen yes_no_prompt(message):
    modal True
    frame:
        xalign 0.5
        yalign 0.5
        xpadding 20
        ypadding 20
        vbox:
            spacing 10
            text message size 24
            hbox:
                spacing 20
                textbutton "Yes" action Return(True)
                textbutton "No" action Return(False)

# Lesson 1: Basic Greetings
label lesson1_intro:
    scene bg classroom
    
    show screen translation_button("これから日本語を勉強しましょう。")
    sensei "これから日本語を勉強しましょう。"
    hide screen translation_button
    
    show screen translation_button("私はあなたの先生です。")
    show screen add_vocab_button("先生", "せんせい", "teacher")
    sensei "私はあなたの先生です。"
    hide screen translation_button
    hide screen add_vocab_button
    
    show screen translation_button("よろしくお願いします。")
    show screen add_vocab_button("よろしくお願いします", "よろしくおねがいします", "Nice to meet you / Please treat me well")
    sensei "よろしくお願いします。"
    hide screen translation_button
    hide screen add_vocab_button
    
    show screen translation_button("[player_name]さん、おはようございます。")
    show screen add_vocab_button("おはようございます", "おはようございます", "Good morning")
    sensei "[player_name]さん、おはようございます。"
    hide screen translation_button
    hide screen add_vocab_button
    
    menu:
        "How should you respond?"
        
        "おはようございます。":
            show screen translation_button("おはようございます。")
            player "おはようございます。"
            hide screen translation_button
            
            sensei "素晴らしい！"
            $ save_progress("lesson1", "greeting", True)
            
        "こんにちは。":
            show screen translation_button("こんにちは。")
            player "こんにちは。"
            hide screen translation_button
            
            show screen translation_button("いいえ、朝は'おはようございます'と言います。")
            sensei "いいえ、朝は'おはようございます'と言います。"
            hide screen translation_button
            
            show screen translation_button("もう一度言ってみましょう。")
            sensei "もう一度言ってみましょう。"
            hide screen translation_button
            
            show screen translation_button("おはようございます。")
            player "おはようございます。"
            hide screen translation_button
            
            sensei "はい、正解です！"
            $ save_progress("lesson1", "greeting", True)
    
    jump lesson1_basic_conversation

label lesson1_basic_conversation:
    scene bg cafe
    
    show screen translation_button("カフェに来ました。")
    sensei "カフェに来ました。"
    hide screen translation_button
    
    show screen translation_button("ここで簡単な会話の練習をしましょう。")
    sensei "ここで簡単な会話の練習をしましょう。"
    hide screen translation_button
    
    show screen translation_button("[player_name]さん、お元気ですか？")
    show screen add_vocab_button("お元気ですか", "おげんきですか", "How are you?")
    sensei "[player_name]さん、お元気ですか？"
    hide screen translation_button
    hide screen add_vocab_button
    
    menu:
        "How will you respond?"
        
        "はい、元気です。":
            show screen translation_button("はい、元気です。")
            show screen add_vocab_button("元気です", "げんきです", "I'm fine/well.")
            player "はい、元気です。"
            hide screen translation_button
            hide screen add_vocab_button
            
            show screen translation_button("それはよかったです。")
            sensei "それはよかったです。"
            hide screen translation_button
            
        "いいえ、元気ではありません。":
            show screen translation_button("いいえ、元気ではありません。")
            player "いいえ、元気ではありません。"
            hide screen translation_button
            
            show screen translation_button("そうですか。大丈夫ですか？")
            show screen add_vocab_button("大丈夫ですか", "だいじょうぶですか", "Are you okay?")
            sensei "そうですか。大丈夫ですか？"
            hide screen translation_button
            hide screen add_vocab_button
    
    $ save_progress("lesson1", "conversation", True)
    
    jump lesson1_end

label lesson1_end:
    scene bg street
    
    show screen translation_button("今日はこれで終わりです。")
    sensei "今日はこれで終わりです。"
    hide screen translation_button
    
    show screen translation_button("よく頑張りました！")
    show screen add_vocab_button("頑張りました", "がんばりました", "You did your best")
    sensei "よく頑張りました！"
    hide screen translation_button
    hide screen add_vocab_button
    
    show screen translation_button("明日も勉強しましょう。")
    show screen add_vocab_button("明日", "あした", "tomorrow")
    sensei "明日も勉強しましょう。"
    hide screen translation_button
    hide screen add_vocab_button
    
    show screen translation_button("さようなら。")
    show screen add_vocab_button("さようなら", "さようなら", "goodbye")
    sensei "さようなら。"
    hide screen translation_button
    hide screen add_vocab_button
    
    menu:
        "Say goodbye:"
        
        "さようなら。":
            show screen translation_button("さようなら。")
            player "さようなら。"
            hide screen translation_button
    
    $ save_progress("lesson1", "end", True)
    
    "Lesson 1 Complete! You've learned basic Japanese greetings."
    
    menu:
        "Would you like to try a dynamic conversation practice?"
        
        "Yes, let's practice":
            jump dynamic_conversation_practice
            
        "No, end the lesson":
            return

# Dynamic conversation practice using LLM
label dynamic_conversation_practice:
    scene bg cafe
    
    "Let's practice what you've learned with a dynamic conversation."
    
    # Generate a conversation using the LLM
    $ context = "Two people meeting at a cafe in the morning. They are discussing how they are feeling and what they plan to do today."
    $ characters = ["Sensei", player_name]
    $ grammar_points = ["Basic greetings", "Question markers with か", "Basic です/ます form"]
    $ vocabulary = ["おはようございます", "元気", "今日", "何", "します"]
    
    $ conversation = generate_conversation(context, characters, grammar_points, vocabulary, 4)
    
    if conversation:
        "The conversation is starting..."
        
        # Display each exchange in the conversation
        python:
            for exchange in conversation:
                speaker = exchange.get("speaker", "")
                japanese_text = exchange.get("japanese_text", "")
                english_translation = exchange.get("english_translation", "")
                
                # Determine which character is speaking
                if speaker == "Sensei":
                    speaking_character = sensei
                else:
                    speaking_character = player
                
                # Show the dialogue with translation option
                renpy.show_screen("translation_button", japanese_text)
                speaking_character(japanese_text)
                renpy.hide_screen("translation_button")
                
                # For vocabulary words, we could add them automatically
                # but for simplicity, we'll skip that in this example
    else:
        "Sorry, I couldn't generate a conversation right now. Let's try again later."
    
    "That was good practice! You're making progress with your Japanese."
    
    $ save_progress("lesson1", "dynamic_practice", True)
    
    return