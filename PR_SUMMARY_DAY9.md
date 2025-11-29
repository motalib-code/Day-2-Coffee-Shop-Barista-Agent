# Day 9: E-commerce Agent (ACP Lite)

## 🛍️ Overview
This PR implements the Day 9 challenge: a voice-driven E-commerce Agent inspired by the Agentic Commerce Protocol (ACP).

## ✨ Features
- **Persona**: "Natalie" - A helpful shop assistant for TechStyle Store.
- **Catalog**: 15 developer-themed products (Mugs, Hoodies, Stickers, etc.) in INR.
- **Cart System**: Add to cart, view cart, and checkout functionality.
- **Order Management**: ACP-style order creation with buyer info and line items.
- **Persistence**: Orders are saved to `backend/shared-data/ecommerce_orders.json`.
- **Tech Stack**: LiveKit, Murf TTS (Arjun), Deepgram STT, OpenAI LLM.

## 📂 Files Added/Modified
- `backend/src/day9_agent.py`: Main agent logic.
- `backend/src/day9_merchant.py`: Merchant layer (Catalog, Cart, Orders).
- `backend/day9_data/catalog.json`: Product database.
- `backend/verify_day9.py`: Verification script.
- `backend/DAY9_ECOMMERCE.md`: Documentation.
- `README.md`: Updated progress.

## 🧪 Verification
Run `python backend/verify_day9.py` to test the commerce logic.
