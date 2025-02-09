# Todo for setup of web interface

1. Choose the best model based on prompt responses.
2. Use the following structure (below, from Andrew Brown) to begin developing the initial program.
3. Look over example files to see if/how they will work within the program.
4. Modify the flow as necessary for functionality.


## Agent Flow

The following agent has the following states:
- Setup
- Attempt
- Clues

The starting state is always Setup

States have the following transitions:

Setup ->  Attempt
Setup -> Question
Clues -> Attempt
Attempt -> Clues
Attempt -> Setupt

Each state expects the following kinds of inputs and ouputs:
Inputs and ouputs contain expects components of text.

### Setup State

User Input:
- Target English Sentence
Assistant Output:
- Vocabulary Table
- Sentence Structure
- Clues, Considerations, Next Steps

### Attempt

User Input:
- Japanese Sentence Attempt
Assistant Output:
- Vocabulary Table
- Sentence Structure
- Clues, Considerations, Next Steps

### Clues
User Input:
- Student Question
Assistant Output:
- Clues, Considerations, Next Steps


## Components

### Target English Sentence
When the input is english text then its possible the student is setting up the transcription to be around this text of english

### Japanese Sentence Attempt
When the input is japanese text then the student is making an attempt at the anwser

### Student Question
When the input sounds like a question about langauge learning then we can assume the user is prompt to enter the Clues state

### Vocabulary Table
- the table should only include nouns, verbs, adverbs, adjectives
- the table of of vocabular should only have the following columns: Japanese, Romaji, English
- Do not provide particles in the vocabulary table, student needs to figure the correct particles to use
- ensure there are no repeats eg. if miru verb is repeated twice, show it only once
- if there is more than one version of a word, show the most common example

### Sentence Structure
- do not provide particles in the sentence structure
- do not provide tenses or conjugations in the sentence structure
- remember to consider beginner level sentence structures
- refernece the <file>sentence-structure-examples.xml</file> for good structure examples


### Clues, Considerations, Next Steps
- try and provide a non-nested bulleted list
- talk about the vocabulary but try to leave out the japanese words because the student can refer to the vocabulary table.
- refernece the <file>considerations-examples.xml</file> for good consideration examples


## Teacher Tests

Please read this file so you can see more examples to provide better output
<file>japanese-teaching-test.md</file>


## Last Checks

- Make sure you read all the example files tell me that you have.
- Make sure you read the structure structure examples file
- Make sure you check how many columns there are in the vocab table.