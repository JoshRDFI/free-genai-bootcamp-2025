# Japanese Learning Visual Novel

A visual novel style game designed to teach Japanese at the JLPT N5 level, with gameplay similar to Nekopara. This project integrates with Docker services for LLM access, TTS, and image generation using OpenVINO.

## Features

- **Interactive Storytelling**: Learn Japanese through an engaging visual novel experience
- **JLPT N5 Curriculum**: Comprehensive coverage of vocabulary and grammar for JLPT N5
- **Text-to-Speech**: Japanese dialogue spoken using XTTS
- **AI-Generated Backgrounds**: Scene backgrounds generated with OpenVINO
- **Translation Assistance**: On-demand translation for difficult phrases
- **Progress Tracking**: Save your learning progress and vocabulary
- **Dynamic AI Conversations**: Practice with unlimited AI-generated Japanese conversations at JLPT N5 level
- **Custom Lesson Generator**: Create personalized lessons on any topic using the LLM

## AI-Powered Learning

This visual novel leverages Ollama Llama 3.2 to create a truly adaptive learning experience:

### Dynamic Conversation Practice

After completing structured lessons, engage in dynamic conversation practice where the LLM generates contextually appropriate JLPT N5 level dialogues. These conversations:

- Use grammar points and vocabulary you've learned
- Adapt to different contexts and scenarios
- Provide translation support for new phrases
- Offer virtually unlimited practice opportunities

### Custom Lesson Generator

Create personalized Japanese lessons on any topic that interests you:

1. Choose a topic (e.g., "Ordering Food", "Shopping", "Traveling")
2. Select grammar points to focus on
3. The AI generates a complete lesson including:
   - Vocabulary with readings and translations
   - Grammar explanations with examples
   - Interactive dialogue practice
   - Exercises with feedback
   - Review summaries

This feature ensures you never run out of learning material and can focus on topics relevant to your interests and goals.

## Technology Stack

- **Ren'Py**: Visual novel engine with web export capabilities
- **Docker**: Containerized services for backend functionality
- **OpenVINO**: Optimized image generation
- **Flask**: API server for game services
- **SQLite**: Database for progress tracking
- **Ollama Llama 3.2**: LLM for dynamic content generation

## Project Structure

The project is organized into several components:

- `renpy/`: Ren'Py visual novel files
- `server/`: Game server and API gateway
- `openvino/`: OpenVINO integration for image generation
- `docker/`: Docker configuration files
- `curriculum/`: JLPT N5 curriculum content
- `docs/`: Documentation

## Getting Started

See the [Setup Guide](docs/setup.md) for detailed installation instructions.

## Development

Refer to the [Development Guide](docs/development.md) for information on extending the game.

## JLPT N5 Curriculum

The game covers the complete JLPT N5 curriculum, including:

- Basic greetings and introductions
- Numbers and counting
- Basic verbs and adjectives
- Essential particles
- Time and calendar expressions
- And more!

See the [Curriculum Outline](curriculum/jlpt-n5-outline.md) for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.