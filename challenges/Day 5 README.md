# Day 5 – Sales Development Representative (SDR) Voice Agent

For Day 5, your objective is to build a **Sales Development Representative (SDR)** voice agent that qualifies leads through natural conversation and accurate product information.

## Primary Goal (Required)

- **Persona**: Transform the agent into a warm, friendly SDR for your company
- **FAQ Integration**: Answer questions strictly from JSON-based company data
- **Lead Qualification**: Naturally collect prospect information during conversation
- **Data Persistence**: Save qualified leads to JSON files automatically

### SDR Behaviors

The agent acts as a professional sales representative with these capabilities:

#### 1. **Warm Greeting & Discovery**
- Welcomes visitors with company name
- Asks what brought them to the company
- Focuses on understanding user needs first

#### 2. **FAQ-Based Responses**
- Answers product/company/pricing questions from JSON data only
- No hallucination - strictly factual responses
- Covers common sales objections and questions

#### 3. **Natural Lead Collection**
- Collects information conversationally throughout the session
- Required fields: name, company, email, role, use_case, team_size, timeline
- Progressive qualification without being pushy

#### 4. **Intelligent Conversation End**
- Detects ending phrases: "that's all", "I'm done", "thanks", etc.
- Generates verbal summary of collected information
- Saves lead data automatically to JSON file
- Politely closes conversation

### Company FAQ Structure

The agent uses `backend/data/day5_company_faq.json`:

```json
{
  "company": "YourCompanyName",
  "description": "Short explanation of what the company does.",
  "pricing": "Basic pricing or free tier info.",
  "faq": [
    {
      "question": "what does your product do",
      "answer": "Placeholder answer about product functionality."
    }
  ]
}
```

### Lead Data Collection

Automatically saves leads to `backend/leads/lead_<timestamp>.json`:

```json
{
  "name": "John Smith",
  "company": "TechCorp",
  "email": "john@techcorp.com",
  "role": "Engineering Manager",
  "use_case": "Team workflow automation",
  "team_size": "15 people",
  "timeline": "Next quarter",
  "timestamp": "2024-01-03T14:30:52.123456"
}
```

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

## Key Features

### **FAQ Integration**
- Loads company information at startup
- Keyword-based question matching
- Accurate, non-hallucinated responses
- Covers product, pricing, and company questions

### **Lead Qualification Flow**
1. **Discovery**: "What brought you here today?"
2. **Information**: Answer questions from FAQ data
3. **Qualification**: Naturally collect lead details
4. **Closure**: Summarize and save when conversation ends

### **Conversation Management**
- Global lead state persists throughout session
- Progressive information collection
- Natural conversation flow
- Automatic data persistence

### **Professional SDR Approach**
- Consultative selling methodology
- Needs-first approach
- Non-pushy qualification
- Helpful and informative responses

## File Structure

```
backend/
├── src/
│   ├── agent.py          # Main SDR agent
│   └── faq_loader.py     # FAQ data loader
├── data/
│   └── day5_company_faq.json  # Company information
└── leads/                # Auto-generated lead files

frontend/
└── components/app/
    └── tutor-status.tsx  # (Can be repurposed for lead status)
```

## Customization

### 1. **Update Company Information**
Edit `backend/data/day5_company_faq.json` with your:
- Company name and description
- Product information
- Pricing details
- Common FAQ responses

### 2. **Modify Lead Fields**
Adjust the `lead_state` dictionary in `agent.py` to collect different information based on your sales process.

### 3. **Customize Conversation Flow**
Update the SDR persona instructions to match your company's sales methodology and tone.

## Sales Benefits

- **Consistent Messaging**: All prospects get accurate, consistent information
- **Lead Qualification**: Systematic collection of key prospect data
- **Conversation Intelligence**: Automatic capture and storage of lead information
- **Scalable Sales**: Handle multiple prospects simultaneously
- **Data-Driven**: JSON-based lead data for CRM integration

---

**Step 1**: Set up and run the SDR agent following the instructions above.
**Step 2**: Successfully connect and have a complete sales conversation with lead qualification.
**Step 3**: Record a short video demonstrating FAQ responses and lead collection.
**Step 4**: Post the video on LinkedIn with a description of your Day 5 experience. Mention you're building with Murf Falcon TTS, tag the official Murf AI handle, and use hashtags **#MurfAIVoiceAgentsChallenge** and **#10DaysofAIVoiceAgents**.

Once your agent is running and your LinkedIn post is live, you've completed Day 5!