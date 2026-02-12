# Local Voice AI Agent - Project Analysis

## Project Overview

**Local Voice AI Agent** is an open-source real-time voice chat application that enables voice conversations with AI models running entirely on your local machine. The project is licensed under MIT License and was created by Jesús Copado.

## What This Project Does

This application creates a complete voice-to-voice AI conversation system that runs locally without requiring cloud services. Users can speak to an AI assistant, and the AI responds with synthesized speech, creating a natural voice conversation experience.

### Key Capabilities:
- **Real-time voice interaction**: Speak naturally and receive audio responses
- **Local processing**: All AI processing happens on your machine (privacy-focused)
- **Multiple interfaces**: Web UI or phone number interface options
- **No cloud dependency**: Everything runs locally using open-source models

## Architecture & Components

The application uses a pipeline architecture with the following components:

### 1. **FastRTC** (`fastrtc`)
   - Handles WebRTC communication for real-time audio streaming
   - Provides both web UI (Gradio) and phone number interface options
   - Manages bidirectional audio streams

### 2. **Moonshine** (via `fastrtc[stt]`)
   - Local speech-to-text (STT) conversion
   - Converts spoken audio to text transcriptions
   - Model: `moonshine/base`

### 3. **Kokoro** (`kokoro-onnx`)
   - Text-to-speech (TTS) synthesis
   - Converts LLM text responses into natural-sounding speech
   - Streams audio chunks for real-time playback

### 4. **Ollama** (`ollama`)
   - Local LLM inference engine
   - Runs Gemma models locally
   - Handles conversation logic and response generation

### 5. **Gemma Models**
   - `gemma3:1b` - Smaller, faster model (basic version)
   - `gemma3:4b` - Larger, more capable model (advanced version)

## Project Structure

```
local-voice-ai-agent/
├── local_voice_chat.py          # Basic voice chat implementation
├── local_voice_chat_advanced.py  # Advanced version with system prompts
├── pyproject.toml                # Python project configuration
├── uv.lock                       # Dependency lock file
├── .python-version               # Python version specification (3.13)
├── README.md                     # Project documentation
├── LICENSE                       # MIT License
└── .gitignore                    # Git ignore rules
```

## Dependencies

### Core Dependencies (from `pyproject.toml`):
- `fastrtc[stt]>=0.0.19` - WebRTC framework with speech-to-text support
- `kokoro-onnx>=0.4.7` - Text-to-speech synthesis
- `loguru>=0.7.3` - Logging framework
- `ollama>=0.4.7` - Local LLM inference client

### System Requirements:
- **OS**: macOS (as specified in README)
- **Python**: >=3.13 (specified in `.python-version` and `pyproject.toml`)
- **Package Manager**: `uv` (fast Python package installer)

### External Services:
- **Ollama**: Must be installed and running locally
- **FastRTC Phone Service**: Required only if using `--phone` flag (provides temporary phone numbers)

## How It Works - Technical Flow

### Basic Flow:
1. **Audio Input**: User speaks into microphone
2. **Speech-to-Text**: Moonshine STT model converts audio → text transcript
3. **LLM Processing**: Transcript sent to Ollama running Gemma model
4. **Response Generation**: LLM generates text response
5. **Text-to-Speech**: Kokoro TTS converts response text → audio chunks
6. **Audio Output**: Audio streamed back to user via FastRTC

### Implementation Details:

#### Basic Version (`local_voice_chat.py`):
- Simple echo function that processes audio
- Uses `gemma3:1b` model
- No system prompt
- Direct user message → LLM → response

#### Advanced Version (`local_voice_chat_advanced.py`):
- Enhanced with system prompt for better responses
- Uses `gemma3:4b` model (more capable)
- Includes logging with Loguru
- System prompt instructs LLM to be helpful and avoid emojis/special characters
- Limits response length (`num_predict: 200`)
- Supports both web UI and phone interface modes

## Installation & Setup Guide

### Prerequisites Installation:

```bash
# Install Ollama (for local LLM inference)
brew install ollama

# Install uv (Python package manager)
brew install uv
```

### Project Setup:

```bash
# 1. Navigate to project directory
cd local-voice-ai-agent

# 2. Create Python virtual environment
uv venv

# 3. Activate virtual environment
source .venv/bin/activate

# 4. Install all Python dependencies
uv sync
```

### Model Setup:

```bash
# Start Ollama service (if not already running)
ollama serve

# Download required models
ollama pull gemma3:1b    # For basic version
ollama pull gemma3:4b    # For advanced version
```

## How to Run / Spin Up

### Option 1: Basic Voice Chat

```bash
# Make sure virtual environment is activated
source .venv/bin/activate

# Run basic version
python local_voice_chat.py
```

This will:
- Launch a Gradio web interface
- Use `gemma3:1b` model
- Provide basic voice chat functionality

### Option 2: Advanced Voice Chat (Web UI)

```bash
# Make sure virtual environment is activated
source .venv/bin/activate

# Run advanced version with web UI
python local_voice_chat_advanced.py
```

This will:
- Launch a Gradio web interface
- Use `gemma3:4b` model (more capable)
- Include system prompt for better responses
- Show debug logs in terminal

### Option 3: Advanced Voice Chat (Phone Interface)

```bash
# Make sure virtual environment is activated
source .venv/bin/activate

# Run advanced version with phone interface
python local_voice_chat_advanced.py --phone
```

This will:
- Provide a temporary phone number
- Allow anyone to call the number to interact with AI
- Use `gemma3:4b` model
- Enable voice interaction via phone calls

## Code Analysis

### `local_voice_chat.py` (Basic):
- **Lines**: 20 lines
- **Functionality**: Minimal implementation
- **Model**: `gemma3:1b`
- **Features**: Basic STT → LLM → TTS pipeline
- **UI**: Gradio web interface

### `local_voice_chat_advanced.py` (Advanced):
- **Lines**: 56 lines
- **Functionality**: Enhanced with system prompts and logging
- **Model**: `gemma3:4b`
- **Features**: 
  - System prompt for better AI behavior
  - Debug logging with Loguru
  - Response length limiting
  - Dual interface support (web/phone)
- **UI**: Gradio web interface OR FastRTC phone interface

## Key Features Comparison

| Feature | Basic Version | Advanced Version |
|---------|--------------|------------------|
| Model | gemma3:1b | gemma3:4b |
| System Prompt | No | Yes |
| Logging | No | Yes (Loguru) |
| Response Limit | No | Yes (200 tokens) |
| Phone Interface | No | Yes (--phone flag) |
| Code Complexity | Simple | Enhanced |

## Troubleshooting Notes

1. **Python Version**: Requires Python 3.13+ (check with `python --version`)
2. **Ollama Service**: Must be running (`ollama serve` or auto-starts)
3. **Model Availability**: Ensure models are pulled before running
4. **Virtual Environment**: Always activate before running scripts
5. **macOS Requirement**: Currently optimized for macOS (may work on Linux with modifications)

## Use Cases

- **Privacy-focused AI conversations**: All processing happens locally
- **Voice assistant development**: Foundation for building custom voice assistants
- **Educational purposes**: Learn about STT, LLM, and TTS integration
- **Prototyping**: Quick way to test voice AI interactions
- **Phone-based AI**: Enable AI interactions via phone calls

## License

MIT License - Free to use, modify, and distribute.

## Repository Information

- **GitHub**: https://github.com/jesuscopado/local-voice-ai-agent
- **Author**: Jesús Copado
- **License**: MIT
- **Language**: Python 3.13+
- **Package Manager**: uv

---

## Quick Start Summary

1. Install: `brew install ollama uv`
2. Setup: `uv venv && source .venv/bin/activate && uv sync`
3. Models: `ollama pull gemma3:1b && ollama pull gemma3:4b`
4. Run: `python local_voice_chat_advanced.py`
5. Access: Open web UI in browser or use `--phone` flag for phone interface
