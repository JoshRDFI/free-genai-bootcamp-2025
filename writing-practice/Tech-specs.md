# Technical Specs


## Initialization Step
When the app first initializes it needs to the following:
Fetch from the GET localhost:5000/api/groups/:id/raw, this will return a collection of words in a json structure. It will have japanese words with their english translation. We need to store this collection of words in memory -- this means a JSON file with words/sentences needs to be created from either the LLM (Ollama running Llama-3.2 inside a docker container -- the port is accessable when running, see current code for API info and port)

## Page States

Page states describes the state the single page application should behaviour from a user's perspective. 

### Setup State
When a user first starts up the app, they will see a group of buttons to select which type of words they would like to study and below that, a button called "Generate Sentence"
When they press the button, The app will generate a sentence using
the Sentence Genreator LLM, and the state will move to Practice State

### Practice State
When a user in is a practice state,
they will see an english sentence,
They will also see an upload field under the english sentence
They will see a button called "Submit for Review"
When they press the Submit for Review Button an uploaded image
will be passed to the Grading System and then will transition to the Review State

### Review State
 When a user in is the review review state,
 The user will still see the english sentence.
 The upload field will be gone.
 The user will now see a review of the output from the Grading System:
- Transcription of Image
- Translation of Transcription
- Grading
  - a letter score using the S Rank to score
  - a description of whether the attempt was accurarte to the english sentence and suggestions.
There will be a button called "Next Question" when clicked
it will it generate a new question and place the app into Practice State


## Sentence Generator LLM Prompt
Generate a simple sentence using the following word: {{word}}
The grammar should be scoped to JLPT N5 grammar.
You can use the following (please use my categories I have added) vocabulary to construct a simple sentence:
- simple objects eg. book, car, ramen, sushi
- simple verbs, to drink, to eat, to meet
- simple times eg. tommorrow, today, yesterday

## Grading System
The Grading System will do the following:
- It will transcribe the image using MangaOCR
- It will use an LLM to produce a literal translation of the transcription
- It will use another LLM to produce a grade
- It then return this data to the frontend app