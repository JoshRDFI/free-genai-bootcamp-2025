# Define characters used by this game
define sensei = Character("先生", color="#c8ffc8", what_italic=False)
define player = Character("[player_name]", color="#c8c8ff")

# Define images
image bg classroom = "images/backgrounds/classroom.png"
image bg cafe = "images/backgrounds/cafe.png"
image bg street = "images/backgrounds/street.png"

# Game variables
default player_name = "Student"
default current_lesson = "lesson1"
default current_scene = "intro"
default user_id = 1

# Python functions for API communication
init python:
    import requests
    import json
    import os
    
    # API endpoint
    API_BASE_URL = "http://localhost:8080/api"
    
    def save_progress(lesson_id, scene_id, completed=False):
        """Save player progress to the server"""
        try:
            response = requests.post(
                f"{API_BASE_URL}/progress",
                json={
                    "user_id": user_id,
                    "lesson_id": lesson_id,
                    "scene_id": scene_id,
                    "completed": completed
                }
            )
            return response.json()
        except Exception as e:
            renpy.notify(f"Failed to save progress: {str(e)}")
            return None
    
    def get_translation(text):
        """Get translation for Japanese text"""
        try:
            response = requests.post(
                f"{API_BASE_URL}/translate",
                json={
                    "text": text,
                    "source_lang": "ja",
                    "target_lang": "en"
                }
            )
            result = response.json()
            return result.get("text", "Translation failed")
        except Exception as e:
            renpy.notify(f"Translation failed: {str(e)}")
            return "Translation failed"
    
    def get_audio(text, voice="ja-JP"):
        """Get audio for text using TTS service"""
        try:
            response = requests.post(
                f"{API_BASE_URL}/tts",
                json={
                    "text": text,
                    "voice": voice
                }
            )
            result = response.json()
            audio_path = result.get("audio_path")
            if audio_path:
                return audio_path
            return None
        except Exception as e:
            renpy.notify(f"TTS failed: {str(e)}")
            return None
    
    def add_vocabulary(japanese, reading=None, english=None):
        """Add vocabulary to player's list"""
        try:
            response = requests.post(
                f"{API_BASE_URL}/vocabulary",
                json={
                    "user_id": user_id,
                    "japanese": japanese,
                    "reading": reading,
                    "english": english,
                    "lesson_id": current_lesson
                }
            )
            return response.json()
        except Exception as e:
            renpy.notify(f"Failed to add vocabulary: {str(e)}")
            return None

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
    
    # Start the first lesson
    jump lesson1_intro

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
    
    return