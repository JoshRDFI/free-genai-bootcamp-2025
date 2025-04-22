-- Insert into word_groups
INSERT INTO word_groups (id, name, level) VALUES (1, 'Animals', 'N5');
INSERT INTO word_groups (id, name, level) VALUES (2, 'Food', 'N5');
INSERT INTO word_groups (id, name, level) VALUES (3, 'Numbers', 'N5');
INSERT INTO word_groups (id, name, level) VALUES (4, 'Colors', 'N5');
INSERT INTO word_groups (id, name, level) VALUES (5, 'Family', 'N5');

-- Insert into words
INSERT INTO words (id, kanji, romaji, english, group_id) VALUES (1, '犬', 'inu', 'dog', 1);
INSERT INTO words (id, kanji, romaji, english, group_id) VALUES (2, '猫', 'neko', 'cat', 1);
INSERT INTO words (id, kanji, romaji, english, group_id) VALUES (3, '鳥', 'tori', 'bird', 1);
INSERT INTO words (id, kanji, romaji, english, group_id) VALUES (4, '魚', 'sakana', 'fish', 1);
INSERT INTO words (id, kanji, romaji, english, group_id) VALUES (5, '馬', 'uma', 'horse', 1);

INSERT INTO words (id, kanji, romaji, english, group_id) VALUES (6, '米', 'kome', 'rice', 2);
INSERT INTO words (id, kanji, romaji, english, group_id) VALUES (7, '肉', 'niku', 'meat', 2);
INSERT INTO words (id, kanji, romaji, english, group_id) VALUES (8, '魚', 'sakana', 'fish', 2);
INSERT INTO words (id, kanji, romaji, english, group_id) VALUES (9, '野菜', 'yasai', 'vegetable', 2);
INSERT INTO words (id, kanji, romaji, english, group_id) VALUES (10, '果物', 'kudamono', 'fruit', 2);

INSERT INTO words (id, kanji, romaji, english, group_id) VALUES (11, '一', 'ichi', 'one', 3);
INSERT INTO words (id, kanji, romaji, english, group_id) VALUES (12, '二', 'ni', 'two', 3);
INSERT INTO words (id, kanji, romaji, english, group_id) VALUES (13, '三', 'san', 'three', 3);
INSERT INTO words (id, kanji, romaji, english, group_id) VALUES (14, '四', 'yon', 'four', 3);
INSERT INTO words (id, kanji, romaji, english, group_id) VALUES (15, '五', 'go', 'five', 3);

INSERT INTO words (id, kanji, romaji, english, group_id) VALUES (16, '赤', 'aka', 'red', 4);
INSERT INTO words (id, kanji, romaji, english, group_id) VALUES (17, '青', 'ao', 'blue', 4);
INSERT INTO words (id, kanji, romaji, english, group_id) VALUES (18, '黄', 'ki', 'yellow', 4);
INSERT INTO words (id, kanji, romaji, english, group_id) VALUES (19, '緑', 'midori', 'green', 4);
INSERT INTO words (id, kanji, romaji, english, group_id) VALUES (20, '白', 'shiro', 'white', 4);

INSERT INTO words (id, kanji, romaji, english, group_id) VALUES (21, '父', 'chichi', 'father', 5);
INSERT INTO words (id, kanji, romaji, english, group_id) VALUES (22, '母', 'haha', 'mother', 5);
INSERT INTO words (id, kanji, romaji, english, group_id) VALUES (23, '兄', 'ani', 'older brother', 5);
INSERT INTO words (id, kanji, romaji, english, group_id) VALUES (24, '姉', 'ane', 'older sister', 5);
INSERT INTO words (id, kanji, romaji, english, group_id) VALUES (25, '弟', 'otouto', 'younger brother', 5);

-- Insert into sentences
INSERT INTO sentences (id, japanese, english, level, category) VALUES (1, '犬は元気です。', 'The dog is energetic.', 'N5', 'Generated');

-- Insert into writing_submissions
INSERT INTO writing_submissions (id, sentence_id, transcription, translation, grade, feedback) VALUES (1, 1, '犬は元気です。', 'The dog is energetic.', 'S', 'Perfect! Your writing matches exactly!');

-- Insert into word_groups (new set with unique IDs)
INSERT INTO word_groups (id, name, level) VALUES (6, 'Basic Greetings', 'N5');
INSERT INTO word_groups (id, name, level) VALUES (7, 'Food & Dining', 'N5');
INSERT INTO word_groups (id, name, level) VALUES (8, 'Travel Phrases', 'N5');
INSERT INTO word_groups (id, name, level) VALUES (9, 'Daily Activities', 'N5');
INSERT INTO word_groups (id, name, level) VALUES (10, 'Numbers & Time', 'N5');

-- Insert into words (new set with unique IDs)
-- Basic Greetings
INSERT INTO words (id, kanji, romaji, english, group_id) VALUES (26, 'こんにちは', 'konnichiwa', 'hello', 6);
INSERT INTO words (id, kanji, romaji, english, group_id) VALUES (27, 'ありがとう', 'arigatou', 'thank you', 6);
INSERT INTO words (id, kanji, romaji, english, group_id) VALUES (28, 'さようなら', 'sayounara', 'goodbye', 6);
INSERT INTO words (id, kanji, romaji, english, group_id) VALUES (29, 'おはよう', 'ohayou', 'good morning', 6);
INSERT INTO words (id, kanji, romaji, english, group_id) VALUES (30, 'こんばんは', 'konbanwa', 'good evening', 6);

-- Food & Dining
INSERT INTO words (id, kanji, romaji, english, group_id) VALUES (31, 'ごはん', 'gohan', 'rice', 7);
INSERT INTO words (id, kanji, romaji, english, group_id) VALUES (32, 'みそしる', 'misoshiru', 'miso soup', 7);
INSERT INTO words (id, kanji, romaji, english, group_id) VALUES (33, 'てんぷら', 'tenpura', 'tempura', 7);
INSERT INTO words (id, kanji, romaji, english, group_id) VALUES (34, 'すし', 'sushi', 'sushi', 7);
INSERT INTO words (id, kanji, romaji, english, group_id) VALUES (35, 'ラーメン', 'raamen', 'ramen', 7);

-- Travel Phrases
INSERT INTO words (id, kanji, romaji, english, group_id) VALUES (36, 'どこ', 'doko', 'where', 8);
INSERT INTO words (id, kanji, romaji, english, group_id) VALUES (37, 'いくら', 'ikura', 'how much', 8);
INSERT INTO words (id, kanji, romaji, english, group_id) VALUES (38, 'えき', 'eki', 'station', 8);
INSERT INTO words (id, kanji, romaji, english, group_id) VALUES (39, 'ホテル', 'hoteru', 'hotel', 8);
INSERT INTO words (id, kanji, romaji, english, group_id) VALUES (40, 'タクシー', 'takushii', 'taxi', 8);

-- Daily Activities
INSERT INTO words (id, kanji, romaji, english, group_id) VALUES (41, 'ねる', 'neru', 'to sleep', 9);
INSERT INTO words (id, kanji, romaji, english, group_id) VALUES (42, 'たべる', 'taberu', 'to eat', 9);
INSERT INTO words (id, kanji, romaji, english, group_id) VALUES (43, 'のむ', 'nomu', 'to drink', 9);
INSERT INTO words (id, kanji, romaji, english, group_id) VALUES (44, 'はたらく', 'hataraku', 'to work', 9);
INSERT INTO words (id, kanji, romaji, english, group_id) VALUES (45, 'あそぶ', 'asobu', 'to play', 9);

-- Numbers & Time
INSERT INTO words (id, kanji, romaji, english, group_id) VALUES (46, 'いち', 'ichi', 'one', 10);
INSERT INTO words (id, kanji, romaji, english, group_id) VALUES (47, 'に', 'ni', 'two', 10);
INSERT INTO words (id, kanji, romaji, english, group_id) VALUES (48, 'さん', 'san', 'three', 10);
INSERT INTO words (id, kanji, romaji, english, group_id) VALUES (49, 'よん', 'yon', 'four', 10);
INSERT INTO words (id, kanji, romaji, english, group_id) VALUES (50, 'ご', 'go', 'five', 10);

-- Insert into sentences (new set with unique IDs)
INSERT INTO sentences (id, japanese, english, level, category) VALUES (2, 'こんにちは、ありがとう。', 'Hello, thank you.', 'N5', 'Generated');

-- Insert into writing_submissions (new set with unique IDs)
INSERT INTO writing_submissions (id, sentence_id, transcription, translation, grade, feedback) VALUES (2, 2, 'こんにちは、ありがとう。', 'Hello, thank you.', 'S', 'Perfect! Your writing matches exactly!');