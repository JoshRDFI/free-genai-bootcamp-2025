# Define characters used by this game
define sensei = Character("先生", color="#c8ffc8", what_italic=False)
define player = Character("[player_name]", color="#c8c8ff")

# Define character images
image sensei = "images/characters/sensei.png"
image sensei happy = "images/characters/sensei_happy.png"
image sensei serious = "images/characters/sensei_serious.png"
# Add more expressions as needed

# Define background images with proper scaling
image bg classroom = im.Scale("images/backgrounds/classroom.png", 1920, 1080)
image bg cafe = im.Scale("images/backgrounds/cafe.png", 1920, 1080)
image bg street = im.Scale("images/backgrounds/street.png", 1920, 1080)
image bg conv_store = im.Scale("images/backgrounds/conv_store.png", 1920, 1080)
image bg ramen_shop = im.Scale("images/backgrounds/ramen_shop.png", 1920, 1080)
image bg store_traditional = im.Scale("images/backgrounds/store_traditional.png", 1920, 1080)

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
            
            # Process each dialogue line
            python:
                for line in dialogue_script:
                    speaker = line.get("speaker", "")
                    text = line.get("text", "")
                    translation = line.get("translation", "")
                    
                    if speaker == "Sensei":
                        renpy.say(sensei, text)
                        if translation:
                            renpy.say(None, translation)
                    elif speaker == "Player":
                        renpy.say(player, text)
                        if translation:
                            renpy.say(None, translation)
                    else:
                        renpy.say(None, text)
                        if translation:
                            renpy.say(None, translation)
        
        # Show vocabulary list
        if vocabulary:
            "Let's review the vocabulary from this lesson:"
            
            python:
                for word in vocabulary:
                    japanese = word.get("japanese", "")
                    reading = word.get("reading", "")
                    english = word.get("english", "")
                    
                    display_text = f"{japanese} - {reading} - {english}"
                    renpy.say(sensei, display_text)
                    renpy.show_screen("add_vocab_button", japanese, reading, english)
                    renpy.pause(1.0)
                    renpy.hide_screen("add_vocab_button")
        
        # Save progress
        $ save_progress("custom", "completed", True)
        
        "Congratulations! You've completed this custom lesson."
        
        menu:
            "What would you like to do next?"
            
            "Generate another custom lesson":
                jump dynamic_lesson_generator
                
            "Return to main menu":
                jump start
    else:
        "Sorry, there was an error generating your lesson. Please try again with a different topic."
        jump dynamic_lesson_generator

# Lesson 1: Basic Greetings
label lesson1_intro:
    scene bg classroom
    $ current_lesson = "lesson1"
    $ current_scene = "intro"
    
    "Welcome to Lesson 1: Basic Greetings!"
    
    show sensei at center
    sensei "こんにちは！私は田中先生です。よろしくお願いします。"
    show screen translation_button("こんにちは！私は田中先生です。よろしくお願いします。")
    
    "Let me introduce myself. My name is Tanaka-sensei. I'll be your Japanese teacher."
    
    hide screen translation_button
    
    sensei "まず、基本的な挨拶を学びましょう。"
    show screen translation_button("まず、基本的な挨拶を学びましょう。")
    
    "First, let's learn some basic greetings."
    
    hide screen translation_button
    
    # Greeting 1: Hello
    sensei "こんにちは - Konnichiwa - Hello/Good afternoon"
    show screen add_vocab_button("こんにちは", "Konnichiwa", "Hello/Good afternoon")
    
    "This is how you say hello or good afternoon in Japanese."
    
    hide screen add_vocab_button
    
    # Greeting 2: Good morning
    sensei "おはようございます - Ohayou gozaimasu - Good morning"
    show screen add_vocab_button("おはようございます", "Ohayou gozaimasu", "Good morning")
    
    "Use this greeting in the morning."
    
    hide screen add_vocab_button
    
    # Greeting 3: Good evening
    sensei "こんばんは - Konbanwa - Good evening"
    show screen add_vocab_button("こんばんは", "Konbanwa", "Good evening")
    
    "Use this greeting in the evening."
    
    hide screen add_vocab_button
    
    # Let's practice
    sensei "では、練習しましょう。"
    show screen translation_button("では、練習しましょう。")
    
    "Now, let's practice."
    
    hide screen translation_button
    
    sensei "朝、何と言いますか？"
    show screen translation_button("朝、何と言いますか？")
    
    "What do you say in the morning?"
    
    hide screen translation_button
    
    menu:
        "Choose the correct greeting for morning:"
        
        "こんにちは":
            sensei "違います。それは昼の挨拶です。"
            show screen translation_button("違います。それは昼の挨拶です。")
            "No, that's a greeting for daytime."
            hide screen translation_button
        
        "おはようございます":
            sensei "正解です！おはようございます！"
            show screen translation_button("正解です！おはようございます！")
            "Correct! Good morning!"
            hide screen translation_button
        
        "こんばんは":
            sensei "違います。それは夜の挨拶です。"
            show screen translation_button("違います。それは夜の挨拶です。")
            "No, that's a greeting for evening."
            hide screen translation_button
    
    # Introduction
    sensei "次に、自己紹介をしましょう。"
    show screen translation_button("次に、自己紹介をしましょう。")
    
    "Next, let's learn how to introduce yourself."
    
    hide screen translation_button
    
    sensei "私は[player_name]です。 - Watashi wa [player_name] desu. - I am [player_name]."
    show screen add_vocab_button("私は～です", "Watashi wa ~ desu", "I am ~")
    
    "This is how you introduce yourself in Japanese."
    
    hide screen add_vocab_button
    
    sensei "はじめまして、[player_name]さん。"
    show screen translation_button("はじめまして、[player_name]さん。")
    
    "Nice to meet you, [player_name]."
    
    hide screen translation_button
    
    # Goodbye expressions
    sensei "最後に、別れの挨拶を学びましょう。"
    show screen translation_button("最後に、別れの挨拶を学びましょう。")
    
    "Finally, let's learn how to say goodbye."
    
    hide screen translation_button
    
    sensei "さようなら - Sayounara - Goodbye"
    show screen add_vocab_button("さようなら", "Sayounara", "Goodbye")
    
    "This is a formal way to say goodbye, often used when you won't see the person for a while."
    
    hide screen add_vocab_button
    
    sensei "また明日 - Mata ashita - See you tomorrow"
    show screen add_vocab_button("また明日", "Mata ashita", "See you tomorrow")
    
    "Use this when you'll see the person the next day."
    
    hide screen add_vocab_button
    
    sensei "お疲れ様でした - Otsukaresama deshita - Good work today/Thank you for your hard work"
    show screen add_vocab_button("お疲れ様でした", "Otsukaresama deshita", "Good work today/Thank you for your hard work")
    
    "This is commonly used when leaving work or after completing a task together."
    
    hide screen add_vocab_button
    
    # Lesson summary
    sensei "今日は基本的な挨拶を学びました。よくできました！"
    show screen translation_button("今日は基本的な挨拶を学びました。よくできました！")
    
    "Today we learned basic greetings. Well done!"
    
    hide screen translation_button
    
    # Save progress
    $ save_progress("lesson1", "completed", True)
    
    # End of lesson menu
    menu:
        "What would you like to do next?"
        
        "Review this lesson again":
            jump lesson1_intro
        
        "Go to Lesson 2 (At the Cafe)":
            jump lesson2_intro
        
        "Return to main menu":
            jump start

# Lesson 2: At the Cafe
label lesson2_intro:
    scene bg cafe
    $ current_lesson = "lesson2"
    $ current_scene = "intro"
    
    "Welcome to Lesson 2: At the Cafe!"
    
    show sensei at center
    sensei "こんにちは！今日はカフェでの会話を勉強しましょう。"
    show screen translation_button("こんにちは！今日はカフェでの会話を勉強しましょう。")
    
    "Hello! Today, let's study conversations at a cafe."
    
    hide screen translation_button
    
    # Basic cafe vocabulary
    sensei "まず、カフェで使う基本的な単語を学びましょう。"
    show screen translation_button("まず、カフェで使う基本的な単語を学びましょう。")
    
    "First, let's learn some basic vocabulary used at cafes."
    
    hide screen translation_button
    
    # Vocabulary list
    sensei "コーヒー - Koohii - Coffee"
    show screen add_vocab_button("コーヒー", "Koohii", "Coffee")
    hide screen add_vocab_button
    
    sensei "紅茶 - Koucha - Tea"
    show screen add_vocab_button("紅茶", "Koucha", "Tea")
    hide screen add_vocab_button
    
    sensei "ケーキ - Keeki - Cake"
    show screen add_vocab_button("ケーキ", "Keeki", "Cake")
    hide screen add_vocab_button
    
    sensei "水 - Mizu - Water"
    show screen add_vocab_button("水", "Mizu", "Water")
    hide screen add_vocab_button
    
    sensei "メニュー - Menyuu - Menu"
    show screen add_vocab_button("メニュー", "Menyuu", "Menu")
    hide screen add_vocab_button
    
    # Ordering phrases
    sensei "次に、注文するときに使うフレーズを学びましょう。"
    show screen translation_button("次に、注文するときに使うフレーズを学びましょう。")
    
    "Next, let's learn phrases used when ordering."
    
    hide screen translation_button
    
    sensei "～をください - ~ wo kudasai - Please give me ~"
    show screen add_vocab_button("～をください", "~ wo kudasai", "Please give me ~")
    
    "This is how you order something in Japanese. For example, 'Coffee please' would be 'Koohii wo kudasai'."
    
    hide screen add_vocab_button
    
    sensei "注文してもいいですか？ - Chuumon shite mo ii desu ka? - May I order?"
    show screen add_vocab_button("注文してもいいですか？", "Chuumon shite mo ii desu ka?", "May I order?")
    hide screen add_vocab_button
    
    sensei "お勘定をお願いします - Okanjou wo onegaishimasu - Check, please"
    show screen add_vocab_button("お勘定をお願いします", "Okanjou wo onegaishimasu", "Check, please")
    hide screen add_vocab_button
    
    # Practice dialogue
    sensei "では、カフェでの会話を練習しましょう。"
    show screen translation_button("では、カフェでの会話を練習しましょう。")
    
    "Now, let's practice a conversation at a cafe."
    
    hide screen translation_button
    
    # Dialogue begins
    "Imagine you're at a cafe and want to order something."
    
    sensei "いらっしゃいませ！"
    show screen translation_button("いらっしゃいませ！")
    
    "Welcome! (This is what staff say when you enter a shop or restaurant)"
    
    hide screen translation_button
    
    menu:
        "How would you ask for the menu?"
        
        "メニューをください":
            sensei "はい、どうぞ。"
            show screen translation_button("はい、どうぞ。")
            "Yes, here you are."
            hide screen translation_button
        
        "メニューはどこですか？":
            sensei "はい、こちらです。"
            show screen translation_button("はい、こちらです。")
            "Yes, here it is."
            hide screen translation_button
    
    "You look at the menu and decide what to order."
    
    menu:
        "What would you like to order?"
        
        "コーヒーをください":
            $ ordered_item = "コーヒー"
            sensei "コーヒーですね。かしこまりました。"
            show screen translation_button("コーヒーですね。かしこまりました。")
            "Coffee, right. Certainly."
            hide screen translation_button
        
        "紅茶をください":
            $ ordered_item = "紅茶"
            sensei "紅茶ですね。かしこまりました。"
            show screen translation_button("紅茶ですね。かしこまりました。")
            "Tea, right. Certainly."
            hide screen translation_button
        
        "ケーキをください":
            $ ordered_item = "ケーキ"
            sensei "ケーキですね。かしこまりました。"
            show screen translation_button("ケーキですね。かしこまりました。")
            "Cake, right. Certainly."
            hide screen translation_button
    
    "After a while, the server brings your order."
    
    sensei "お待たせしました。[ordered_item]になります。"
    show screen translation_button("お待たせしました。[ordered_item]になります。")
    
    "Sorry to keep you waiting. Here's your [ordered_item]."
    
    hide screen translation_button
    
    menu:
        "How do you say thank you?"
        
        "ありがとうございます":
            sensei "どういたしまして。ごゆっくりどうぞ。"
            show screen translation_button("どういたしまして。ごゆっくりどうぞ。")
            "You're welcome. Please take your time."
            hide screen translation_button
        
        "すみません":
            sensei "いいえ、どういたしまして。ごゆっくりどうぞ。"
            show screen translation_button("いいえ、どういたしまして。ごゆっくりどうぞ。")
            "No problem. Please take your time."
            hide screen translation_button
    
    "After enjoying your [ordered_item], you want to pay."
    
    menu:
        "How do you ask for the check?"
        
        "お勘定をお願いします":
            sensei "はい、[ordered_item]で300円になります。"
            show screen translation_button("はい、[ordered_item]で300円になります。")
            "Yes, that's 300 yen for the [ordered_item]."
            hide screen translation_button
        
        "支払いをしたいです":
            sensei "はい、[ordered_item]で300円になります。"
            show screen translation_button("はい、[ordered_item]で300円になります。")
            "Yes, that's 300 yen for the [ordered_item]."
            hide screen translation_button
    
    "You pay and prepare to leave."
    
    menu:
        "How do you say goodbye?"
        
        "ありがとうございました":
            sensei "ありがとうございました。またお越しください。"
            show screen translation_button("ありがとうございました。またお越しください。")
            "Thank you very much. Please come again."
            hide screen translation_button
        
        "さようなら":
            sensei "ありがとうございました。またお越しください。"
            show screen translation_button("ありがとうございました。またお越しください。")
            "Thank you very much. Please come again."
            hide screen translation_button
    
    # Lesson summary
    sensei "今日はカフェでの会話を練習しました。とてもよくできました！"
    show screen translation_button("今日はカフェでの会話を練習しました。とてもよくできました！")
    
    "Today we practiced conversations at a cafe. You did very well!"
    
    hide screen translation_button
    
    # Grammar point
    sensei "今日の文法ポイント: 「～をください」は何かを頼むときに使います。"
    show screen translation_button("今日の文法ポイント: 「～をください」は何かを頼むときに使います。")
    
    "Today's grammar point: '~ wo kudasai' is used when asking for something."
    
    hide screen translation_button
    
    # Cultural note
    sensei "文化ノート: 日本のカフェでは、通常チップを払う必要はありません。"
    show screen translation_button("文化ノート: 日本のカフェでは、通常チップを払う必要はありません。")
    
    "Cultural note: In Japanese cafes, you typically don't need to pay a tip."
    
    hide screen translation_button
    
    # Save progress
    $ save_progress("lesson2", "completed", True)
    
    # End of lesson menu
    menu:
        "What would you like to do next?"
        
        "Review this lesson again":
            jump lesson2_intro
        
        "Go to Lesson 3 (Shopping)":
            jump lesson3_intro
        
        "Return to main menu":
            jump start

# Lesson 3: Shopping
label lesson3_intro:
    scene bg store_traditional
    $ current_lesson = "lesson3"
    $ current_scene = "intro"
    
    "Welcome to Lesson 3: Shopping!"
    
    show sensei at center
    sensei "今日は、買い物の会話を練習しましょう。"
    show screen translation_button("今日は、買い物の会話を練習しましょう。")
    
    "Today, we'll practice shopping conversations."
    
    hide screen translation_button
    
    # Basic shopping vocabulary
    sensei "まず、買い物で使う基本的な単語を学びましょう。"
    show screen translation_button("まず、買い物で使う基本的な単語を学びましょう。")
    
    "First, let's learn some basic vocabulary used when shopping."
    
    hide screen translation_button
    
    # Vocabulary list
    sensei "いくらですか - Ikura desu ka - How much is it?"
    show screen add_vocab_button("いくらですか", "Ikura desu ka", "How much is it?")
    hide screen add_vocab_button
    
    sensei "これをください - Kore wo kudasai - I'll take this, please"
    show screen add_vocab_button("これをください", "Kore wo kudasai", "I'll take this, please")
    hide screen add_vocab_button
    
    sensei "安い - Yasui - Cheap/Inexpensive"
    show screen add_vocab_button("安い", "Yasui", "Cheap/Inexpensive")
    hide screen add_vocab_button
    
    sensei "高い - Takai - Expensive/Tall"
    show screen add_vocab_button("高い", "Takai", "Expensive/Tall")
    hide screen add_vocab_button
    
    sensei "試着してもいいですか - Shichaku shite mo ii desu ka - May I try it on?"
    show screen add_vocab_button("試着してもいいですか", "Shichaku shite mo ii desu ka", "May I try it on?")
    hide screen add_vocab_button
    
    # Shopping phrases
    sensei "次に、買い物するときに使うフレーズを学びましょう。"
    show screen translation_button("次に、買い物するときに使うフレーズを学びましょう。")
    
    "Next, let's learn phrases used when shopping."
    
    hide screen translation_button
    
    sensei "何をお探しですか？ - Nani wo osagashi desu ka? - What are you looking for?"
    show screen add_vocab_button("何をお探しですか？", "Nani wo osagashi desu ka?", "What are you looking for?")
    hide screen add_vocab_button
    
    sensei "カードで払えますか？ - Kaado de haraemasuka? - Can I pay by card?"
    show screen add_vocab_button("カードで払えますか？", "Kaado de haraemasuka?", "Can I pay by card?")
    hide screen add_vocab_button
    
    sensei "袋をください - Fukuro wo kudasai - A bag, please"
    show screen add_vocab_button("袋をください", "Fukuro wo kudasai", "A bag, please")
    hide screen add_vocab_button
    
    # Practice dialogue
    sensei "では、お店での会話を練習しましょう。"
    show screen translation_button("では、お店での会話を練習しましょう。")
    
    "Now, let's practice a conversation at a store."
    
    hide screen translation_button
    
    # Dialogue begins
    scene bg conv_store
    
    "You enter a convenience store to buy some snacks."
    
    show sensei at center
    
    sensei "いらっしゃいませ！"
    show screen translation_button("いらっしゃいませ！")
    
    "Welcome!"
    
    hide screen translation_button
    
    "You look around and find some items you're interested in."
    
    menu:
        "What would you like to ask about?"
        
        "このお菓子はいくらですか？":
            sensei "そのお菓子は200円です。"
            show screen translation_button("そのお菓子は200円です。")
            "That snack is 200 yen."
            hide screen translation_button
        
        "水はどこですか？":
            sensei "水は冷蔵庫にあります。こちらです。"
            show screen translation_button("水は冷蔵庫にあります。こちらです。")
            "The water is in the refrigerator. This way."
            hide screen translation_button
    
    "You decide to buy a snack and a drink."
    
    menu:
        "How would you tell the clerk what you want?"
        
        "これとこれをください":
            sensei "はい、お菓子と飲み物ですね。合計で350円になります。"
            show screen translation_button("はい、お菓子と飲み物ですね。合計で350円になります。")
            "Yes, a snack and a drink. That will be 350 yen in total."
            hide screen translation_button
        
        "これを買いたいです":
            sensei "はい、お菓子と飲み物ですね。合計で350円になります。"
            show screen translation_button("はい、お菓子と飲み物ですね。合計で350円になります。")
            "Yes, a snack and a drink. That will be 350 yen in total."
            hide screen translation_button
    
    menu:
        "How would you ask if you can pay by card?"
        
        "カードで払えますか？":
            sensei "はい、もちろんです。こちらにカードを入れてください。"
            show screen translation_button("はい、もちろんです。こちらにカードを入れてください。")
            "Yes, of course. Please insert your card here."
            hide screen translation_button
        
        "現金だけですか？":
            sensei "いいえ、カードも使えます。こちらにカードを入れてください。"
            show screen translation_button("いいえ、カードも使えます。こちらにカードを入れてください。")
            "No, you can use a card too. Please insert your card here."
            hide screen translation_button
    
    "After paying, the clerk asks you a question."
    
    sensei "袋はご入用ですか？"
    show screen translation_button("袋はご入用ですか？")
    
    "Do you need a bag?"
    
    hide screen translation_button
    
    menu:
        "How would you respond?"
        
        "はい、お願いします":
            sensei "かしこまりました。こちらにお入れします。"
            show screen translation_button("かしこまりました。こちらにお入れします。")
            "Certainly. I'll put them in here."
            hide screen translation_button
        
        "いいえ、結構です":
            sensei "かしこまりました。そのままでどうぞ。"
            show screen translation_button("かしこまりました。そのままでどうぞ。")
            "Understood. Here you are then."
            hide screen translation_button
    
    "You complete your purchase and prepare to leave."
    
    sensei "ありがとうございました。またお越しください。"
    show screen translation_button("ありがとうございました。またお越しください。")
    
    "Thank you very much. Please come again."
    
    hide screen translation_button
    
    # Change scene to traditional store
    scene bg store_traditional
    
    "Later, you visit a traditional Japanese shop selling crafts."
    
    show sensei at center
    
    sensei "いらっしゃいませ！何かお探しですか？"
    show screen translation_button("いらっしゃいませ！何かお探しですか？")
    
    "Welcome! Are you looking for something?"
    
    hide screen translation_button
    
    menu:
        "How would you respond?"
        
        "ちょっと見ているだけです":
            sensei "はい、どうぞごゆっくり。"
            show screen translation_button("はい、どうぞごゆっくり。")
            "Yes, please take your time."
            hide screen translation_button
        
        "お土産を探しています":
            sensei "お土産でしたら、こちらがおすすめです。"
            show screen translation_button("お土産でしたら、こちらがおすすめです。")
            "If you're looking for souvenirs, I recommend these."
            hide screen translation_button
    
    "You find a beautiful traditional craft item."
    
    menu:
        "How would you ask about the price?"
        
        "これはいくらですか？":
            sensei "それは3000円です。伝統的な手作りの品です。"
            show screen translation_button("それは3000円です。伝統的な手作りの品です。")
            "That's 3000 yen. It's a traditional handmade item."
            hide screen translation_button
        
        "高いですか？":
            sensei "3000円です。伝統的な手作りの品なので、この価格です。"
            show screen translation_button("3000円です。伝統的な手作りの品なので、この価格です。")
            "It's 3000 yen. It's priced this way because it's a traditional handmade item."
            hide screen translation_button
    
    "You decide to buy the item as a souvenir."
    
    menu:
        "How would you tell the shopkeeper you'll take it?"
        
        "これをください":
            sensei "ありがとうございます。素敵な選択です。"
            show screen translation_button("ありがとうございます。素敵な選択です。")
            "Thank you. That's a wonderful choice."
            hide screen translation_button
        
        "これを買います":
            sensei "ありがとうございます。素敵な選択です。"
            show screen translation_button("ありがとうございます。素敵な選択です。")
            "Thank you. That's a wonderful choice."
            hide screen translation_button
    
    # Lesson summary
    sensei "今日は買い物の会話を練習しました。上手にできましたね！"
    show screen translation_button("今日は買い物の会話を練習しました。上手にできましたね！")
    
    "Today we practiced shopping conversations. You did well!"
    
    hide screen translation_button
    
    # Grammar point
    sensei "今日の文法ポイント: 「～をください」は何かを買うときにも使えます。"
    show screen translation_button("今日の文法ポイント: 「～をください」は何かを買うときにも使えます。")
    
    "Today's grammar point: '~ wo kudasai' can also be used when buying something."
    
    hide screen translation_button
    
    # Cultural note
    sensei "文化ノート: 日本の多くの店では、商品を丁寧に包装してくれます。これは「おもてなし」の文化の一部です。"
    show screen translation_button("文化ノート: 日本の多くの店では、商品を丁寧に包装してくれます。これは「おもてなし」の文化の一部です。")
    
    "Cultural note: In many Japanese stores, items are carefully wrapped. This is part of the 'omotenashi' (hospitality) culture."
    
    hide screen translation_button
    
    # Save progress
    $ save_progress("lesson3", "completed", True)
    
    # End of lesson menu
    menu:
        "What would you like to do next?"
        
        "Review this lesson again":
            jump lesson3_intro
        
        "Generate a custom lesson":
            jump dynamic_lesson_generator
        
        "Return to main menu":
            jump start