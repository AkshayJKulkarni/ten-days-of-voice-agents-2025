Day 2 – Coffee Shop Barista Voice Agent
AI Voice Agents Challenge – Murf AI × LiveKit
by Akshay J Kulkarni
🚀 Overview

For Day 2 of the Murf AI Voice Agents Challenge, I transformed my Day-1 starter voice agent into an interactive Coffee Shop Barista Agent.

This agent can take complete coffee orders using voice, clarifies missing information, maintains state, and finally saves a JSON summary of the order.

Built using:

LiveKit Agents (Real-time voice pipeline)

Murf Falcon (Fastest TTS API)

Python Backend

Next.js + React Frontend

🎯 Objectives Completed
✔️ 1. Persona: Friendly Coffee Barista

The agent now speaks like a warm, polite barista from a coffee brand of my choice.

✔️ 2. Order State Tracking

Maintains the order in this format:

{
  "drinkType": "",
  "size": "",
  "milk": "",
  "extras": [],
  "name": ""
}


The agent asks step-by-step questions to fill each field.

✔️ 3. Intelligent Conversation Flow

The agent:

Asks for drink type

Confirms size

Checks milk preference

Asks for extras (sugar, vanilla, whipped cream, etc.)

Finally asks the customer’s name

If something is missing, it asks again until all fields are filled.

✔️ 4. Saves Order to JSON File Automatically

Once the order is complete, the agent:

Confirms order

Saves it as:
backend/orders/order_<timestamp>.json

Sends the summary back to the frontend

Resets state for the next customer

✔️ 5. Frontend Order Summary Display

I added a custom UI section that:

Fetches the latest saved order

Displays drink type, size, milk, extras, customer name

Updates automatically when a new order is completed

🗂️ Folder Structure
backend/
  ├── src/agent.py
  ├── orders/ (generated JSON files)
  ├── .env.local

frontend/
  ├── components/OrderSummary.tsx
  ├── app/api/orders/route.ts
  ├── app/page.tsx (UI integration)

▶️ Running the Project
Backend
cd backend
uv run python src/agent.py dev

Frontend
cd frontend
npm install
npm run dev


Open in browser:
👉 http://localhost:3000
