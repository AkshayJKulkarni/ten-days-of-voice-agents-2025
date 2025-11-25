# Day 4 – Teach-the-Tutor Voice Agent

For Day 4, your objective is to build a **Teach-the-Tutor** voice agent that helps students learn programming concepts through active recall and multiple learning modes.

## Primary Goal (Required)

- **Persona**: Transform the agent into a supportive programming tutor with three distinct learning modes.
- **Content**: Use JSON-based course content for programming concepts (variables, loops, functions, conditionals).
- **Active Recall**: Implement teach-back functionality where students explain concepts to reinforce learning.

### Three Learning Modes

The agent supports three distinct tutoring modes, each with its own voice:

#### 1. **Learn Mode** (Voice: Matthew)
- Explains programming concepts using clear summaries
- Provides foundational knowledge before testing
- Example: *"Let me explain Variables. Variables are containers that store data values..."*

#### 2. **Quiz Mode** (Voice: Alicia) 
- Asks sample questions to test understanding
- Challenges students with concept-specific questions
- Example: *"What is a variable and how do you create one in Python?"*

#### 3. **Teach Back Mode** (Voice: Ken)
- Students explain concepts back to the tutor
- Provides encouraging feedback with strengths and suggestions
- Supports active recall learning methodology

### Voice Intent Detection

Students can switch modes naturally using voice commands:
- *"Learn mode"* or *"Switch to learn"* → Learn Mode
- *"Quiz mode"* or *"Switch to quiz"* → Quiz Mode  
- *"Teach back mode"* or *"Switch to teach back"* → Teach Back Mode

Mode switching preserves the selected concept, allowing seamless transitions between learning approaches.

### Course Content Structure

The agent uses `backend/data/course_content.json` with this structure:

```json
{
  "concepts": [
    {
      "id": "variables",
      "title": "Variables", 
      "summary": "Variables are containers that store data values...",
      "sample_question": "What is a variable and how do you create one in Python?"
    }
  ]
}
```

**Available Concepts:**
- Variables
- Loops  
- Functions
- Conditionals

## How to Run

### Prerequisites
- Python 3.9+ with uv package manager
- Node.js 18+ with pnpm
- LiveKit Server running locally

### Backend Setup
```bash
cd backend
uv sync
cp .env.example .env.local
# Configure your API keys in .env.local
uv run python src/agent.py dev
```

### Frontend Setup  
```bash
cd frontend
pnpm install
cp .env.example .env.local
# Configure LiveKit credentials
pnpm dev
```

### Start LiveKit Server
```bash
livekit-server --dev
```

Then open http://localhost:3000 in your browser!

## Active Recall Learning System

The Teach-the-Tutor system implements proven active recall techniques:

### **Learning Progression**
1. **Input** (Learn Mode): Receive clear explanations
2. **Testing** (Quiz Mode): Answer questions to check understanding  
3. **Output** (Teach Back): Explain concepts in your own words

### **Intelligent Feedback**
The teach-back mode provides:
- **Encouraging tone**: Always supportive and positive
- **Strength identification**: Highlights 1-2 things done well
- **Improvement suggestions**: One specific tip for enhancement
- **Concept-specific analysis**: Tailored feedback per programming topic

### **Example Feedback**
*"Great effort! I noticed you mentioned the concept by name and provided examples. To make it even better, try explaining when you might use a loop in real programming. You're doing well with programming concepts!"*

## Conversation Flow

1. **Mode Selection**: Agent asks for preferred learning mode
2. **Concept Choice**: Select from available programming concepts  
3. **Mode Execution**: Experience the chosen learning approach
4. **Seamless Switching**: Change modes while keeping the same concept
5. **Continuous Learning**: Cycle through modes for comprehensive understanding

## Educational Benefits

- **Active Recall**: Strengthens memory through retrieval practice
- **Multi-Modal Learning**: Visual, auditory, and kinesthetic engagement
- **Personalized Feedback**: Adaptive responses based on student explanations
- **Confidence Building**: Encouraging feedback promotes continued learning
- **Flexible Pacing**: Student-controlled mode switching and concept selection

---

**Step 1**: Set up and run the Teach-the-Tutor agent following the instructions above.
**Step 2**: Successfully connect and experience all three learning modes with a programming concept.
**Step 3**: Record a short video demonstrating mode switching and teach-back functionality.
**Step 4**: Post the video on LinkedIn with a description of your Day 4 experience. Mention you're building with Murf Falcon TTS, tag the official Murf AI handle, and use hashtags **#MurfAIVoiceAgentsChallenge** and **#10DaysofAIVoiceAgents**.

Once your agent is running and your LinkedIn post is live, you've completed Day 4!