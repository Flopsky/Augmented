# Task Reminder Application Structure

## Project Layout
```
task-reminder/
├── frontend/                 # React + TypeScript frontend
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── hooks/          # Custom React hooks
│   │   ├── types/          # TypeScript type definitions
│   │   ├── utils/          # Utility functions
│   │   └── App.tsx         # Main app component
│   ├── package.json
│   ├── vite.config.ts
│   └── tailwind.config.js
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API routes
│   │   ├── core/           # Core functionality
│   │   ├── models/         # Database models
│   │   ├── services/       # Business logic
│   │   └── main.py         # FastAPI app
│   ├── requirements.txt
│   └── Dockerfile
├── docker-compose.yml       # Development environment
└── README.md
```

## Tech Stack
- Frontend: React + TypeScript + Vite + Tailwind CSS + Framer Motion
- Backend: FastAPI + SQLAlchemy + WebSockets + Instructor
- AI: Claude Sonnet API + faster-whisper + kokoro-tts
- Database: SQLite
- Deployment: Docker + Docker Compose