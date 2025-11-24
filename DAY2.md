# Day 2 - Coffee Shop Barista Agent ☕

## Overview
Built a complete voice-powered coffee shop barista agent using LiveKit Agents and Murf Falcon TTS that takes customer orders, maintains order state, and saves completed orders to JSON files.

## Features Implemented

### ✅ Core Requirements (Day 2)
- **Friendly Barista Persona**: Conversational coffee shop assistant
- **Order State Management**: Tracks all order details in real-time
- **Step-by-step Ordering**: Guides customers through complete order process
- **JSON Order Saving**: Automatically saves completed orders with timestamps

### ✅ Enhanced Features (Beyond Requirements)
- **Live Order Summary Panel**: Real-time UI showing current order progress
- **Order History API**: REST endpoint to fetch all saved orders
- **Instant Order Updates**: Frontend updates immediately when orders complete
- **Order Validation**: Ensures all required fields before saving

## Order State Structure
```json
{
  "drinkType": "latte",
  "size": "medium", 
  "milk": "oat milk",
  "extras": ["vanilla"],
  "name": "John"
}
```

## Tech Stack
- **Backend**: LiveKit Agents (Python)
- **Frontend**: Next.js 15 + React 19
- **TTS**: Murf Falcon (fastest TTS API)
- **STT**: Deepgram Nova-3
- **LLM**: Google Gemini 2.5 Flash
- **Styling**: Tailwind CSS

## Quick Start

### 1. Start LiveKit Server
```bash
docker-compose up livekit
```

### 2. Start Backend Agent
```bash
cd backend/src
uv run python agent.py dev
```

### 3. Start Frontend
```bash
cd frontend
pnpm dev
```

### 4. Open Browser
Navigate to `http://localhost:3000` and start ordering coffee!

## How It Works

1. **Customer speaks**: "I want a latte"
2. **Agent responds**: "What size would you like?"
3. **Order state updates**: Live panel shows progress
4. **Order completion**: JSON file saved to `backend/orders/`
5. **Reset**: Agent ready for next customer

## File Structure
```
├── backend/
│   ├── src/
│   │   ├── agent.py           # Main barista agent
│   │   └── order_helper.py    # Order management utilities
│   └── orders/                # Saved order JSON files
├── frontend/
│   ├── components/
│   │   ├── OrderSummary.tsx   # Live order display
│   │   └── app/order-summary.tsx
│   └── app/api/orders/        # Order history API
└── docker-compose.yml         # LiveKit server setup
```

## Sample Order Flow
1. **Drink**: "I'd like a cappuccino"
2. **Size**: "Large please"
3. **Milk**: "Almond milk"
4. **Extras**: "Extra shot and vanilla syrup"
5. **Name**: "Sarah"
6. **Complete**: Order saved as `order_20250103_143052.json`

## Key Components

### CoffeeShopBarista Agent
- Maintains conversation state
- Uses function tools to update order
- Guides customers step-by-step
- Saves and resets on completion

### Order Helper Functions
- `save_order_to_json()`: Saves with timestamp
- `is_order_complete()`: Validates all fields filled

### Frontend Order Summary
- Real-time order state display
- Auto-refreshes every 2 seconds
- Shows latest completed orders

## Demo
The agent successfully:
- ✅ Takes complete voice orders
- ✅ Maintains order state throughout conversation
- ✅ Saves orders to JSON files
- ✅ Displays live order progress
- ✅ Handles multiple customers

## Challenge Completion
**Day 2 Status**: ✅ COMPLETED
- Primary goal achieved with enhanced features
- Ready for Day 3 challenges

---

*Built for the #MurfAIVoiceAgentsChallenge using the fastest TTS API - Murf Falcon*