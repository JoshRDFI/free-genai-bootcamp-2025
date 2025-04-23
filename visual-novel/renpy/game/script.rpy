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
            
        "Start with pre-made Lesson 2 (At the Cafe)":
            jump lesson2_intro
            
        "Start with pre-made Lesson 3 (Shopping)":
            jump lesson3_intro
            
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
                    
                    # Display the Japanese text with translation button
                    renpy.show_screen("translation_button", japanese_text)
                    renpy.show_screen("add_vocab_button", japanese_text, None, english)
                    
                    # Say the line
                    speaking_character(japanese_text)
                    
                    # Generate and play audio if available
                    audio_path = get_audio(japanese_text)
                    if audio_path:
                        renpy.play(audio_path, channel="voice")
        
        # Show grammar points
        python:
            grammar_points = lesson_data.get("grammar_points", [])
            if grammar_points:
                renpy.say(None, "Let's review the grammar points from this lesson:")
                for i, grammar in enumerate(grammar_points):
                    pattern = grammar.get("pattern", "")
                    explanation = grammar.get("explanation", "")
                    examples = grammar.get("examples", [])
                    
                    renpy.say(sensei, f"Grammar Point {i+1}: {pattern}")
                    renpy.say(sensei, explanation)
                    
                    if examples:
                        renpy.say(sensei, "Examples:")
                        for example in examples:
                            renpy.say(sensei, example)
        
        # Show exercises if available
        python:
            exercises = lesson_data.get("exercises", [])
            if exercises:
                renpy.say(None, "Let's practice with some exercises:")
                for i, exercise in enumerate(exercises):
                    question = exercise.get("question", "")
                    options = exercise.get("options", [])
                    correct_answer = exercise.get("correct_answer", "")
                    
                    renpy.say(sensei, f"Question {i+1}: {question}")
                    
                    # Create a menu for the options
                    choices = [(option, option) for option in options]
                    answer = renpy.display_menu(choices)
                    
                    if answer == correct_answer:
                        renpy.say(sensei, "Correct! Well done!")
                    else:
                        renpy.say(sensei, f"Not quite. The correct answer is: {correct_answer}")
        
        # Show cultural note if available
        $ cultural_note = lesson_data.get("cultural_note", "")
        if cultural_note:
            sensei "Cultural Note: [cultural_note]"
        
        # Lesson completion
        "Congratulations! You've completed your custom lesson on [lesson_title]."
        
        # Save progress
        $ save_progress(f"custom_{topic.replace(' ', '_')}", "completed", True)
        
        menu:
            "What would you like to do next?"
            
            "Review this lesson again":
                jump dynamic_lesson_generator
                
            "Create a new custom lesson":
                jump dynamic_lesson_generator
                
            "Return to main menu":
                jump start
    else:
        "Sorry, there was an error generating your lesson. Please try again with a different topic."
        jump dynamic_lesson_generator

# Pre-made Lesson 1: Basic Greetings
label lesson1_intro:
    scene bg classroom
    
    "Welcome to your first Japanese lesson!"
    
    show sensei at center
    
    sensei "こんにちは！私は田中先生です。よろしくお願いします。"
    show screen translation_button("こんにちは！私は田中先生です。よろしくお願いします。")
    show screen add_vocab_button("こんにちは", "こんにちは", "Hello")
    
    "The teacher introduces herself as Tanaka-sensei."
    
    sensei "In this lesson, we'll learn basic greetings in Japanese."
    
    sensei "Let's start with 'こんにちは' (konnichiwa), which means 'hello' or 'good afternoon'."
    show screen add_vocab_button("こんにちは", "こんにちは", "Hello/Good afternoon")
    
    sensei "Now, repeat after me: こんにちは"
    
    # Generate and play audio
    $ audio_path = get_audio("こんにちは")
    if audio_path:
        play sound audio_path
    
    sensei "Great! Now let's learn 'おはようございます' (ohayou gozaimasu), which means 'good morning'."
    show screen add_vocab_button("おはようございます", "おはようございます", "Good morning")
    
    sensei "Repeat after me: おはようございます"
    
    # Generate and play audio
    $ audio_path = get_audio("おはようございます")
    if audio_path:
        play sound audio_path
    
    sensei "Excellent! Next is 'こんばんは' (konbanwa), which means 'good evening'."
    show screen add_vocab_button("こんばんは", "こんばんは", "Good evening")
    
    sensei "Repeat after me: こんばんは"
    
    # Generate and play audio
    $ audio_path = get_audio("こんばんは")
    if audio_path:
        play sound audio_path
    
    sensei "Now, let's learn how to say goodbye. 'さようなら' (sayounara) means 'goodbye'."
    show screen add_vocab_button("さようなら", "さようなら", "Goodbye")
    
    sensei "Repeat after me: さようなら"
    
    # Generate and play audio
    $ audio_path = get_audio("さようなら")
    if audio_path:
        play sound audio_path
    
    sensei "Great job! Let's practice a simple conversation."
    
    sensei "When someone says 'こんにちは', you can respond with 'こんにちは'."
    
    sensei "こんにちは, [player_name]-san."
    show screen translation_button("こんにちは, [player_name]-san.")
    
    menu:
        "How do you respond?"
        
        "こんにちは, 田中先生.":
            player "こんにちは, 田中先生."
            sensei "Very good!"
            $ save_progress("lesson1", "greeting", True)
        
        "さようなら, 田中先生.":
            player "さようなら, 田中先生."
            sensei "Not quite. 'さようなら' means 'goodbye'. Let's try again."
            sensei "こんにちは, [player_name]-san."
            player "こんにちは, 田中先生."
            sensei "That's better!"
            $ save_progress("lesson1", "greeting", True)
    
    sensei "Now, let's learn how to introduce yourself."
    
    sensei "To say 'My name is...', you can say '私の名前は...(name)...です' (watashi no namae wa ... desu)."
    show screen add_vocab_button("私の名前は", "わたしのなまえは", "My name is")
    
    sensei "Repeat after me: 私の名前は[player_name]です"
    
    # Generate and play audio
    $ audio_path = get_audio("私の名前は田中です")
    if audio_path:
        play sound audio_path
    
    sensei "Excellent! Now you can introduce yourself in Japanese."
    
    sensei "Let's review what we've learned today:"
    sensei "1. こんにちは - Hello/Good afternoon"
    sensei "2. おはようございます - Good morning"
    sensei "3. こんばんは - Good evening"
    sensei "4. さようなら - Goodbye"
    sensei "5. 私の名前は...です - My name is..."
    
    sensei "You've completed your first Japanese lesson! おめでとうございます (Congratulations)!"
    show screen add_vocab_button("おめでとうございます", "おめでとうございます", "Congratulations")
    
    $ save_progress("lesson1", "completed", True)
    
    menu:
        "What would you like to do next?"
        
        "Continue to Lesson 2 (At the Cafe)":
            jump lesson2_intro
        
        "Return to the main menu":
            jump start

# Pre-made Lesson 2: At the Cafe
label lesson2_intro:
    scene bg cafe
    
    "Welcome to your second Japanese lesson!"
    
    show sensei at center
    
    sensei "こんにちは！今日はカフェで日本語を勉強しましょう。"
    show screen translation_button("こんにちは！今日はカフェで日本語を勉強しましょう。")
    show screen add_vocab_button("カフェ", "カフェ", "Cafe")
    show screen add_vocab_button("勉強しましょう", "べんきょうしましょう", "Let's study")
    
    "Tanaka-sensei suggests studying Japanese at a cafe today."
    
    sensei "In this lesson, we'll learn how to order food and drinks in Japanese."
    
    sensei "First, let's learn some vocabulary for drinks."
    
    sensei "'コーヒー' (koohii) means 'coffee'."
    show screen add_vocab_button("コーヒー", "コーヒー", "Coffee")
    
    sensei "'お茶' (ocha) means 'tea'."
    show screen add_vocab_button("お茶", "おちゃ", "Tea")
    
    sensei "'水' (mizu) means 'water'."
    show screen add_vocab_button("水", "みず", "Water")
    
    sensei "Now, let's learn some vocabulary for food."
    
    sensei "'ケーキ' (keeki) means 'cake'."
    show screen add_vocab_button("ケーキ", "ケーキ", "Cake")
    
    sensei "'サンドイッチ' (sandoicchi) means 'sandwich'."
    show screen add_vocab_button("サンドイッチ", "サンドイッチ", "Sandwich")
    
    sensei "'パン' (pan) means 'bread'."
    show screen add_vocab_button("パン", "パン", "Bread")
    
    sensei "Now, let's learn how to order in Japanese."
    
    sensei "To say 'I would like...', you can say '...をください' (... wo kudasai)."
    show screen add_vocab_button("をください", "をください", "Please give me")
    
    sensei "For example, 'コーヒーをください' means 'Coffee, please'."
    show screen translation_button("コーヒーをください")
    
    sensei "Let's practice ordering. Imagine you're at a cafe and want to order coffee."
    
    menu:
        "What would you like to order?"
        
        "コーヒーをください":
            player "コーヒーをください。"
            sensei "Perfect! That means 'Coffee, please.'"
            $ save_progress("lesson2", "ordering", True)
        
        "お茶をください":
            player "お茶をください。"
            sensei "Very good! That means 'Tea, please.'"
            $ save_progress("lesson2", "ordering", True)
        
        "水をください":
            player "水をください。"
            sensei "Excellent! That means 'Water, please.'"
            $ save_progress("lesson2", "ordering", True)
    
    sensei "Now, let's learn how to ask for the price."
    
    sensei "To ask 'How much is this?', you can say 'これはいくらですか' (kore wa ikura desu ka)."
    show screen add_vocab_button("これはいくらですか", "これはいくらですか", "How much is this?")
    
    sensei "Let's practice asking for the price."
    
    sensei "Imagine you want to know the price of a cake."
    
    menu:
        "How would you ask for the price?"
        
        "これはいくらですか":
            player "これはいくらですか。"
            sensei "Perfect! That means 'How much is this?'"
            sensei "The cake costs 500円 (yen)."
            $ save_progress("lesson2", "price", True)
        
        "ケーキをください":
            player "ケーキをください。"
            sensei "That means 'Cake, please.' But if you want to know the price, you should say 'これはいくらですか'."
            player "これはいくらですか。"
            sensei "Good! The cake costs 500円 (yen)."
            $ save_progress("lesson2", "price", True)
    
    sensei "Now, let's learn how to say 'thank you' and 'you're welcome'."
    
    sensei "'ありがとうございます' (arigatou gozaimasu) means 'thank you'."
    show screen add_vocab_button("ありがとうございます", "ありがとうございます", "Thank you")
    
    sensei "'どういたしまして' (dou itashimashite) means 'you're welcome'."
    show screen add_vocab_button("どういたしまして", "どういたしまして", "You're welcome")
    
    sensei "Let's practice a complete cafe interaction."
    
    "Waiter" "いらっしゃいませ！ご注文は何ですか？"
    show screen translation_button("いらっしゃいませ！ご注文は何ですか？")
    show screen add_vocab_button("いらっしゃいませ", "いらっしゃいませ", "Welcome (to a shop)")
    show screen add_vocab_button("ご注文は何ですか", "ごちゅうもんはなんですか", "What would you like to order?")
    
    menu:
        "How do you respond?"
        
        "コーヒーをください":
            player "コーヒーをください。"
        
        "お茶をください":
            player "お茶をください。"
        
        "水をください":
            player "水をください。"
    
    "Waiter" "かしこまりました。少々お待ちください。"
    show screen translation_button("かしこまりました。少々お待ちください。")
    show screen add_vocab_button("かしこまりました", "かしこまりました", "Certainly/Understood")
    show screen add_vocab_button("少々お待ちください", "しょうしょうおまちください", "Please wait a moment")
    
    "The waiter brings your order."
    
    "Waiter" "お待たせしました。こちらになります。"
    show screen translation_button("お待たせしました。こちらになります。")
    show screen add_vocab_button("お待たせしました", "おまたせしました", "Sorry to keep you waiting")
    show screen add_vocab_button("こちらになります", "こちらになります", "Here you are")
    
    menu:
        "How do you respond?"
        
        "ありがとうございます":
            player "ありがとうございます。"
            "Waiter" "どういたしまして。"
            $ save_progress("lesson2", "thanking", True)
    
    sensei "Excellent! You've learned how to order at a cafe in Japanese."
    
    sensei "Let's review what we've learned today:"
    sensei "1. Drink vocabulary: コーヒー, お茶, 水"
    sensei "2. Food vocabulary: ケーキ, サンドイッチ, パン"
    sensei "3. Ordering: ...をください"
    sensei "4. Asking for price: これはいくらですか"
    sensei "5. Thanking: ありがとうございます, どういたしまして"
    
    sensei "You've completed your second Japanese lesson! おめでとうございます!"
    
    $ save_progress("lesson2", "completed", True)
    
    menu:
        "What would you like to do next?"
        
        "Continue to Lesson 3 (Shopping)":
            jump lesson3_intro
        
        "Return to the main menu":
            jump start

# Pre-made Lesson 3: Shopping
label lesson3_intro:
    scene bg store_traditional
    
    "Welcome to your third Japanese lesson!"
    
    show sensei at center
    
    sensei "こんにちは！今日は買い物について勉強しましょう。"
    show screen translation_button("こんにちは！今日は買い物について勉強しましょう。")
    show screen add_vocab_button("買い物", "かいもの", "Shopping")
    
    "Tanaka-sensei suggests learning about shopping in Japanese today."
    
    sensei "In this lesson, we'll learn vocabulary and phrases for shopping."
    
    sensei "First, let's learn some vocabulary for clothing items."
    
    sensei "'シャツ' (shatsu) means 'shirt'."
    show screen add_vocab_button("シャツ", "シャツ", "Shirt")
    
    $ audio_path = get_audio("シャツ")
    if audio_path:
        play voice audio_path
    
    sensei "'ズボン' (zubon) means 'pants'."
    show screen add_vocab_button("ズボン", "ズボン", "Pants")
    
    $ audio_path = get_audio("ズボン")
    if audio_path:
        play voice audio_path
    
    sensei "'帽子' (boushi) means 'hat'."
    show screen add_vocab_button("帽子", "ぼうし", "Hat")
    
    $ audio_path = get_audio("帽子")
    if audio_path:
        play voice audio_path
    
    sensei "Now, let's learn some vocabulary for colors."
    
    sensei "This means 'I am Teacher Tanaka.'"
    
    sensei "The pattern is: 私は (watashi wa) + your name + です (desu)."
    
    sensei "Now, try introducing yourself."
    
    menu:
        "Introduce yourself"
        
        "私は[player_name]です。":
            sensei "素晴らしい！(Subarashii!) Excellent!"
            
        "I need help":
            sensei "Let me help you. Say: 私は (watashi wa) + your name + です (desu)."
            sensei "For example: 私は[player_name]です。"
    
    sensei "Great job! Let's continue with more greetings."
    
    # Save progress
    $ save_progress("lesson1", "intro", True)
    
    jump lesson1_greetings

# Lesson 1 continued: More greetings
label lesson1_greetings:
    scene bg classroom
    
    show sensei at center
    
    sensei "Let's learn more greetings for different times of day."
    
    sensei "おはようございます (Ohayou gozaimasu) - Good morning"
    show screen translation_button("おはようございます")
    show screen add_vocab_button("おはようございます", "おはようございます", "Good morning")
    
    $ audio_path = get_audio("おはようございます")
    if audio_path:
        play voice audio_path
    
    sensei "こんばんは (Konbanwa) - Good evening"
    show screen translation_button("こんばんは")
    show screen add_vocab_button("こんばんは", "こんばんは", "Good evening")
    
    $ audio_path = get_audio("こんばんは")
    if audio_path:
        play voice audio_path
    
    sensei "さようなら (Sayounara) - Goodbye"
    show screen translation_button("さようなら")
    show screen add_vocab_button("さようなら", "さようなら", "Goodbye")
    
    $ audio_path = get_audio("さようなら")
    if audio_path:
        play voice audio_path
    
    sensei "Let's practice these greetings in a conversation."
    
    # Generate a simple conversation using the LLM
    $ conversation = generate_conversation(
        "A student and teacher meeting in the morning and saying goodbye in the evening",
        ["Sensei", player_name],
        ["Basic greetings", "Self-introduction"],
        ["おはようございます", "こんにちは", "こんばんは", "さようなら"],
        3
    )
    
    if conversation:
        python:
            for exchange in conversation:
                speaker = exchange.get("speaker", "")
                japanese_text = exchange.get("japanese", "")
                english = exchange.get("english", "")
                
                # Determine which character is speaking
                if speaker == "Sensei":
                    speaking_character = sensei
                else:
                    speaking_character = player
                
                # Display the Japanese text with translation button
                renpy.show_screen("translation_button", japanese_text)
                
                # Say the line
                speaking_character(japanese_text)
                
                # Generate and play audio if available
                audio_path = get_audio(japanese_text)
                if audio_path:
                    renpy.play(audio_path, channel="voice")
    else:
        # Fallback conversation if generation fails
        sensei "おはようございます、[player_name]さん。"
        show screen translation_button("おはようございます、[player_name]さん。")
        
        player "おはようございます、先生。"
        show screen translation_button("おはようございます、先生。")
        
        sensei "今日の授業は終わりです。さようなら。"
        show screen translation_button("今日の授業は終わりです。さようなら。")
        
        player "さようなら、先生。また明日。"
        show screen translation_button("さようなら、先生。また明日。")
    
    sensei "Excellent! You've learned the basic greetings in Japanese."
    
    # Save progress
    $ save_progress("lesson1", "greetings", True)
    
    "Congratulations! You've completed Lesson 1: Basic Greetings."
    
    menu:
        "What would you like to do next?"
        
        "Review Lesson 1 again":
            jump lesson1_intro
            
        "Create a custom lesson":
            jump dynamic_lesson_generator
            
        "Return to main menu":
            jump start

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