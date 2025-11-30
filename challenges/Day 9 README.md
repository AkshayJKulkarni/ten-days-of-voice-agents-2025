# Day 9 – E-commerce Agent (Agentic Commerce Protocol)

For Day 9, your objective is to build a **voice-driven shopping assistant** that follows a lite version of the Agentic Commerce Protocol (ACP) pattern.

## Primary Goal (Required)

- **ACP-Inspired Architecture**: Clear separation between conversation layer and commerce logic
- **Product Catalog**: Browse products by voice with filtering capabilities
- **Voice Ordering**: Place orders through natural voice commands
- **Order Management**: Persist orders and provide status updates

### Agentic Commerce Protocol (ACP) Concepts

The ACP is an open standard for AI-driven commerce. Key concepts implemented:

#### 1. **Separation of Concerns**
- **Conversation Layer**: LLM + voice interaction
- **Commerce Layer**: Product catalog and order management functions
- **Structured Data**: JSON-based products and orders

#### 2. **Commerce Functions**
- `list_products()`: Browse catalog with filters
- `create_order()`: Generate orders from line items
- `get_last_order()`: Retrieve order status

#### 3. **Structured Objects**
- **Products**: ID, name, price, category, attributes
- **Orders**: ID, line items, totals, timestamps

### Voice Shopping Capabilities

#### **Product Discovery**
- *"Show me all coffee mugs"*
- *"Do you have any t-shirts under 1000?"*
- *"I'm looking for a black hoodie"*
- *"Does this coffee mug come in blue?"*

#### **Order Placement**
- *"I'll buy the second hoodie you mentioned"*
- *"I want the blue mug"*
- *"Order 2 of the black t-shirts"*

#### **Order Status**
- *"What did I just buy?"*
- *"Show me my last order"*

### Product Catalog

Current catalog includes:

```json
{
  "id": "mug-001",
  "name": "Stoneware Coffee Mug",
  "description": "Handcrafted ceramic mug perfect for morning coffee",
  "price": 800,
  "currency": "INR",
  "category": "mug",
  "color": "white",
  "size": "350ml"
}
```

**Available Products:**
- **Mugs**: Stoneware (white), Blue Ceramic
- **Clothing**: Cotton T-Shirt (black), Hoodies (black/gray)

### Order Structure

Orders follow ACP-inspired format:

```json
{
  "id": "abc12345",
  "items": [
    {
      "product_id": "mug-001",
      "product_name": "Stoneware Coffee Mug",
      "quantity": 1,
      "unit_price": 800,
      "total_price": 800,
      "currency": "INR"
    }
  ],
  "total": 800,
  "currency": "INR",
  "status": "CONFIRMED",
  "created_at": "2024-01-03T14:30:52.123456"
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

### **Voice-First Shopping**
- Natural language product discovery
- Conversational order placement
- Voice-based order confirmation

### **Smart Product Resolution**
- Handles ambiguous references ("the second one")
- Color and category matching
- Price-based filtering

### **ACP Architecture**
- Clean separation of concerns
- Structured data models
- Function-based commerce operations

### **Order Management**
- Automatic order ID generation
- Persistent order storage
- Order status tracking

## File Structure

```
backend/
├── src/
│   ├── agent.py              # E-commerce voice agent
│   └── commerce_backend.py   # ACP-inspired commerce layer
└── data/
    └── ecommerce_orders.json # Persistent order storage
```

## Commerce Functions

### **Product Browsing**
```python
list_products(filters={
    "category": "mug",
    "max_price": 1000,
    "color": "blue"
})
```

### **Order Creation**
```python
create_order(line_items=[
    {"product_id": "mug-001", "quantity": 1}
])
```

### **Order Retrieval**
```python
get_last_order()  # Returns most recent order
```

## Conversation Flow

1. **Welcome**: Agent greets and asks what customer is looking for
2. **Discovery**: Browse products by category, price, or attributes
3. **Selection**: Help resolve product references and quantities
4. **Ordering**: Create order with confirmation details
5. **Status**: Provide order summaries and tracking

## Advanced Features (Optional)

### **ACP-Style Merchant API**
- HTTP endpoints for catalog and orders
- RESTful API design
- JSON-based request/response

### **Shopping Cart**
- Multi-item cart management
- Add/remove/update operations
- Checkout workflow

### **Order History**
- Multiple order tracking
- Purchase history queries
- Spending analytics

---

**Step 1**: Set up and run the E-commerce agent following the instructions above.
**Step 2**: Successfully browse products and place an order using voice commands.
**Step 3**: Record a short video demonstrating the voice shopping experience.
**Step 4**: Post the video on LinkedIn with a description of your Day 9 experience. Mention you're building with Murf Falcon TTS, tag the official Murf AI handle, and use hashtags **#MurfAIVoiceAgentsChallenge** and **#10DaysofAIVoiceAgents**.

Once your agent is running and your LinkedIn post is live, you've completed Day 9!