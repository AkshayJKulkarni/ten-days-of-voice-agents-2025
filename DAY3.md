# Day 3 - Health & Wellness Voice Companion 🧘‍♀️

## Overview
Built a supportive voice companion that conducts daily wellness check-ins, tracks mood and goals, and maintains conversation history through JSON persistence for personalized follow-ups.

## Features Implemented

### ✅ Core Requirements (Day 3)
- **Daily Check-ins**: Voice-based wellness conversations
- **Mood & Energy Tracking**: Captures emotional and physical state
- **Goal Setting**: Tracks daily intentions and objectives
- **Stress Assessment**: Identifies current stressors and challenges
- **JSON Persistence**: Saves all sessions for continuity
- **Historical Context**: References previous check-ins

### ✅ Conversation Flow
1. **Mood Check**: "How are you feeling today?"
2. **Energy Assessment**: "What's your energy like?"
3. **Stress Identification**: "Anything stressing you out right now?"
4. **Goal Setting**: "What are 1-3 things you'd like to get done today?"
5. **Summary & Confirmation**: Recap and validate understanding

## Wellness Data Structure
```json
{
  "mood": "a little bit of tired",
  "energy": "bit low", 
  "stressors": "completing agent task, taking a walk",
  "goals": [],
  "summary": "Feeling a bit tired with low energy, and focused on completing an agent task and taking a walk today.",
  "timestamp": "2025-11-24T21:58:02.435362"
}
```

## Tech Stack
- **Backend**: LiveKit Agents (Python)
- **Frontend**: Next.js 15 + React 19
- **TTS**: Murf Falcon (fastest TTS API)
- **STT**: Deepgram Nova-3
- **LLM**: Google Gemini 2.5 Flash
- **Storage**: JSON file persistence

## File Structure
```
├── backend/
│   ├── src/
│   │   ├── agent.py              # Wellness companion agent
│   │   └── wellness_storage.py   # JSON persistence utilities
│   └── data/
│       └── wellness_log.json     # Stored wellness sessions
└── frontend/
    └── components/               # UI components (if needed)
```

## Key Components

### Wellness Storage System
- `load_wellness_log()`: Retrieves previous sessions
- `save_wellness_entry()`: Persists new check-in data
- Automatic data directory creation
- Error handling for corrupted files

### Wellness Companion Agent
- Grounded, supportive conversation style
- Non-medical, non-diagnostic approach
- Contextual follow-ups using historical data
- Structured data collection and validation

## Sample Wellness Session

**Agent**: "Hi! How are you feeling today?"
**User**: "A little bit tired"
**Agent**: "What's your energy like?"
**User**: "Bit low"
**Agent**: "Anything stressing you out right now?"
**User**: "Completing agent task, taking a walk"
**Agent**: "What would you like to get done today?"
**User**: "Nothing specific"
**Agent**: "So you're feeling a bit tired with low energy, focused on completing an agent task and taking a walk. Does this sound right?"

## Wellness Features

### ✅ Supportive Approach
- Non-judgmental conversation style
- Realistic, actionable suggestions
- Grounded advice (no medical claims)
- Encouraging tone and validation

### ✅ Data Continuity
- References previous sessions
- Tracks mood patterns over time
- Builds conversational context
- Maintains user history

### ✅ Privacy & Safety
- Local JSON storage
- No medical diagnosis
- Supportive companion role
- User-controlled data

## Quick Start

### 1. Start Services
```bash
# LiveKit Server
docker-compose up livekit

# Backend Agent  
cd backend/src
uv run python agent.py dev

# Frontend
cd frontend
pnpm dev
```

### 2. Daily Check-in
Navigate to `http://localhost:3000` and have your wellness conversation!

## Demo Results
Successfully completed wellness check-in:
- ✅ Captured mood: "a little bit tired"
- ✅ Assessed energy: "bit low"
- ✅ Identified stressors: "completing agent task, taking a walk"
- ✅ Tracked goals: No specific goals today
- ✅ Generated summary and confirmation
- ✅ Saved to `wellness_log.json` with timestamp

## Challenge Completion
**Day 3 Status**: ✅ COMPLETED
- All primary goals achieved
- JSON persistence working
- Historical context implemented
- Ready for Day 4 challenges

## Next Steps
- Continue daily check-ins to build history
- Agent will reference previous sessions
- Track wellness patterns over time
- Personalized follow-up conversations

---

*Built for the #MurfAIVoiceAgentsChallenge using the fastest TTS API - Murf Falcon*