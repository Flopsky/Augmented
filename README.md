# 🎯 Task Reminder Application with Voice Interaction

A minimalist task reminder application with voice interaction capabilities, built with React + TypeScript frontend and FastAPI backend. The application embodies simplicity and elegance while providing powerful task management through natural conversation.

## ✨ Features

### 🎙️ Voice Interaction
- **Animated Circle Button**: 150px diameter with gradient design (purple to blue)
- **Voice Commands**: Natural language processing for task management
- **Real-time Feedback**: Pulsing animation during listening, wave animation when speaking
- **Speech-to-Text**: Powered by faster-whisper for accurate transcription
- **Text-to-Speech**: Ready for kokoro-tts integration

### 📋 Task Management
- **Real-time Updates**: WebSocket connection for instant task synchronization
- **Priority Indicators**: Visual priority levels with color coding
- **Smooth Animations**: Framer Motion for elegant transitions
- **Dark Theme**: High contrast design for better visibility
- **Minimal UI**: Clean, card-based task display

### 🤖 AI Integration
- **Claude Sonnet**: Natural language understanding via Anthropic API
- **Instructor**: Structured LLM outputs with Pydantic validation
- **Fuzzy Matching**: Intelligent task identification and completion
- **Context Awareness**: Understands task relationships and batch operations

## 🚀 Tech Stack

### Backend
- **FastAPI** - High-performance async web framework
- **SQLAlchemy** - Database ORM with SQLite
- **WebSockets** - Real-time bidirectional communication
- **Claude Sonnet** - AI-powered natural language processing
- **Faster-whisper** - Efficient speech-to-text conversion
- **Instructor** - Structured AI outputs with Pydantic

### Frontend
- **React 18** - Modern UI library with hooks
- **TypeScript** - Type-safe development
- **Vite** - Fast build tool and dev server
- **Tailwind CSS** - Utility-first styling
- **Framer Motion** - Smooth animations and transitions
- **React Query** - Server state management
- **WebRTC** - Audio recording capabilities

### Infrastructure
- **Docker** - Containerized deployment
- **Nginx** - Reverse proxy for production
- **SQLite** - Lightweight database
- **WebSocket** - Real-time communication

## 🔧 Setup Instructions

### Prerequisites
- Node.js 18+ and npm
- Python 3.12+
- Docker and Docker Compose (optional)
- Anthropic API key

### 1. Clone Repository
```bash
git clone https://github.com/Flopsky/Augmented.git
cd Augmented
```

### 2. Environment Configuration
```bash
cp .env.example .env
# Edit .env and add your Anthropic API key:
# ANTHROPIC_API_KEY=your_actual_api_key_here
```

### 3. Option A: Docker Setup (Recommended)
```bash
docker-compose up --build
```

### 3. Option B: Manual Setup

#### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

## 🎮 Usage

### Voice Commands
- **Add Tasks**: "Add buy groceries to my list"
- **Complete Tasks**: "Mark groceries as complete" or "I finished the groceries"
- **List Tasks**: "What's on my list?" or "Show me my tasks"
- **Modify Tasks**: "Change the meeting to 3 PM"
- **Clear Completed**: "Remove all completed tasks"

### UI Interaction
1. Click the animated circle button to start voice recording
2. Speak your command naturally
3. Watch tasks update in real-time on the right side
4. Receive voice feedback for all operations

## 📱 Ports & URLs

- **Frontend**: http://localhost:3000 (or configured port)
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **WebSocket**: ws://localhost:8000/ws

## 🎨 UI Design

### Voice Button
- **Gradient**: Soft purple to blue (ChatGPT-inspired)
- **States**: Idle, listening (pulsing), speaking (wave animation)
- **Size**: 150px diameter, centered on screen
- **Responsive**: Adapts to different screen sizes

### Task List
- **Layout**: Right side of screen
- **Cards**: Minimal design with priority indicators
- **Animations**: Smooth enter/exit transitions
- **Priority**: Color-coded importance levels
- **Status**: Visual completion indicators

## 🔑 API Keys Required

### Anthropic API Key
1. Sign up at [Anthropic Console](https://console.anthropic.com/)
2. Create a new API key
3. Add to `.env` file: `ANTHROPIC_API_KEY=your_key_here`
4. Restart the backend server

## 📊 API Endpoints

### REST API
- `GET /api/tasks` - Retrieve all tasks
- `POST /api/tasks` - Create new task
- `PUT /api/tasks/{id}` - Update task
- `DELETE /api/tasks/{id}` - Delete task
- `POST /api/voice/speech-to-text` - Convert audio to text
- `POST /api/voice/process-command` - Process voice command
- `GET /api/voice/tts/{text}` - Generate speech audio

### WebSocket
- `WS /ws` - Real-time task updates and notifications

## 🧪 Testing

### Backend Testing
```bash
cd backend
source venv/bin/activate
pytest tests/
```

### Frontend Testing
```bash
cd frontend
npm test
```

### API Testing
Visit http://localhost:8000/docs for interactive API documentation.

## 🔮 Roadmap & TODOs

See [TODO.md](TODO.md) for detailed development roadmap and pending features.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Anthropic** for Claude Sonnet API
- **OpenAI** for inspiration from ChatGPT's voice mode
- **Systran** for faster-whisper implementation
- **Vercel** for deployment platform
- **Tailwind CSS** for utility-first styling

## 📞 Support

For support, email support@augmented.dev or open an issue on GitHub.

---

**Built with ❤️ for seamless voice-powered task management**
