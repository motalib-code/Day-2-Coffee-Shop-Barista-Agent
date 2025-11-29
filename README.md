# AI Voice Agents Challenge - Starter Repository

Welcome to the **AI Voice Agents Challenge** by [murf.ai](https://murf.ai)!

## About the Challenge

We just launched **Murf Falcon** – the consistently fastest TTS API, and you're going to be among the first to test it out in ways never thought before!

**Build 10 AI Voice Agents over the course of 10 Days** along with help from our devs and the community champs, and win rewards!

### How It Works

- One task to be provided everyday along with a GitHub repo for reference
- Build a voice agent with specific personas and skills
- Post on GitHub and share with the world on LinkedIn!

## Challenge Progress

- Day 1: ✅ Get Your Starter Voice Agent Running - COMPLETED
- Day 2: ✅ Day2 Completed – Coffee Shop Barista Agent ☕🗣️
- Day 3: ✅ Health & Wellness Voice Companion - COMPLETED 🧘‍♀️💚
- Day 4: ✅ Day 4 - Teach-the-Tutor Implementation Plan - COMPLETED 🎓🧠
- Day 5: ✅ Primary Goal – Simple FAQ SDR + Lead Capture - COMPLETED 💼📋
- Day 6: ✅ Fraud Alert Agent - COMPLETED 🔐🚨
- Day 7: ✅ Food & Grocery Ordering Voice Agent - COMPLETED 🛒🍕
- Day 8: ✅ Voice Game Master (D&D-Style Adventure) - COMPLETED 🎲🐉
- Day 9: ✅ E-commerce Agent (ACP Lite) - COMPLETED 🛍️🤖

## Repository Structure

This is a **monorepo** that contains both the backend and frontend for building voice agent applications. It's designed to be your starting point for each day's challenge task.

```
falcon-tdova-nov25-livekit/
├── backend/          # LiveKit Agents backend with Murf Falcon TTS
├── frontend/         # React/Next.js frontend for voice interaction
├── start_app.sh      # Convenience script to start all services
└── README.md         # This file
```

### Backend

The backend is based on [LiveKit's agent-starter-python](https://github.com/livekit-examples/agent-starter-python) with modifications to integrate **Murf Falcon TTS** for ultra-fast, high-quality voice synthesis.

**Features:**

- Complete voice AI agent framework using LiveKit Agents
- Murf Falcon TTS integration for fastest text-to-speech
- LiveKit Turn Detector for contextually-aware speaker detection
- Background voice cancellation
- Integrated metrics and logging
- Complete test suite with evaluation framework
- Production-ready Dockerfile

[→ Backend Documentation](./backend/README.md)

### Frontend

The frontend is based on [LiveKit's agent-starter-react](https://github.com/livekit-examples/agent-starter-react), providing a modern, beautiful UI for interacting with your voice agents.

**Features:**

- Real-time voice interaction with LiveKit Agents
- Camera video streaming support
- Screen sharing capabilities
- Audio visualization and level monitoring
- Light/dark theme switching
- Highly customizable branding and UI

[→ Frontend Documentation](./frontend/README.md)

## Quick Start

### Prerequisites

Make sure you have the following installed:

- Python 3.9+ with [uv](https://docs.astral.sh/uv/) package manager
- Node.js 18+ with pnpm
- [LiveKit CLI](https://docs.livekit.io/home/cli/cli-setup) (optional but recommended)
- [LiveKit Server](https://docs.livekit.io/home/self-hosting/local/) for local development

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd falcon-tdova-nov25-livekit
```

### 2. Backend Setup

```bash
cd backend

# Install dependencies
uv sync

# Copy environment file and configure
cp .env.example .env.local

# Edit .env.local with your credentials:
# - LIVEKIT_URL
# - LIVEKIT_API_KEY
# - LIVEKIT_API_SECRET
# - MURF_API_KEY (for Falcon TTS)
# - GOOGLE_API_KEY (for Gemini LLM)
# - DEEPGRAM_API_KEY (for Deepgram STT)

# Download required models
uv run python src/agent.py download-files
```

For LiveKit Cloud users, you can automatically populate credentials:

```bash
lk cloud auth
lk app env -w -d .env.local
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
pnpm install

# Copy environment file and configure
cp .env.example .env.local

# Edit .env.local with the same LiveKit credentials
```

### 4. Run the Application

#### Install livekit server

```bash
brew install livekit
```

You have two options:

#### Option A: Use the convenience script (runs everything)

```bash
# From the root directory
chmod +x start_app.sh
./start_app.sh
```

This will start:

- LiveKit Server (in dev mode)
- Backend agent (listening for connections)
- Frontend app (at http://localhost:3000)

#### Option B: Run services individually

```bash
# Terminal 1 - LiveKit Server
livekit-server --dev

# Terminal 2 - Backend Agent
cd backend
uv run python src/agent.py dev

# Terminal 3 - Frontend
cd frontend
pnpm dev
```

Then open http://localhost:3000 in your browser!

## Daily Challenge Tasks

Each day, you'll receive a new task that builds upon your voice agent. The tasks will help you:

- Implement different personas and conversation styles
- Add custom tools and capabilities
- Integrate with external APIs
- Build domain-specific agents (customer service, tutoring, etc.)
- Optimize performance and user experience

**Stay tuned for daily task announcements!**

## Documentation & Resources

- [Murf Falcon TTS Documentation](https://murf.ai/api/docs/text-to-speech/streaming)
- [LiveKit Agents Documentation](https://docs.livekit.io/agents)
- [Original Backend Template](https://github.com/livekit-examples/agent-starter-python)
- [Original Frontend Template](https://github.com/livekit-examples/agent-starter-react)

## Testing

The backend includes a comprehensive test suite:

```bash
cd backend
uv run pytest
```

Learn more about testing voice agents in the [LiveKit testing documentation](https://docs.livekit.io/agents/build/testing/).

## Contributing & Community

This is a challenge repository, but we encourage collaboration and knowledge sharing!

- Share your solutions and learnings on GitHub
- Post about your progress on LinkedIn
- Join the [LiveKit Community Slack](https://livekit.io/join-slack)
- Connect with other challenge participants

## License

This project is based on MIT-licensed templates from LiveKit and includes integration with Murf Falcon. See individual LICENSE files in backend and frontend directories for details.

## Have Fun!

Remember, the goal is to learn, experiment, and build amazing voice AI agents. Don't hesitate to be creative and push the boundaries of what's possible with Murf Falcon and LiveKit!

Good luck with the challenge!

---

Built for the AI Voice Agents Challenge by murf.ai

# Day 2 – Coffee Shop Barista Agent
For Day 2, your primary objective is to turn the starter agent into a coffee shop barista that can take voice orders and show a neat text summary.

Primary Goal (Required)
Persona: Turn the agent into a friendly barista for a coffee brand of your choice.
Order state: Maintain a small order state object:
{
  "drinkType": "string",
  "size": "string",
  "milk": "string",
  "extras": ["string"],
  "name": "string"
}
Behavior:
The agent should ask clarifying questions until all fields in the order state are filled.
Once the order is complete, save the order to a JSON file summarizing the order.
Resources:
https://docs.livekit.io/agents/build/tools/
https://docs.livekit.io/agents/build/agents-handoffs/#passing-state
https://docs.livekit.io/agents/build/tasks/
https://github.com/livekit/agents/blob/main/examples/drive-thru/agent.py
Completing the above is enough to finish Day 2.

Advanced Challenge (Optional)
This part is completely optional and only for participants who want an extra challenge:

Build an HTML-based beverage image generation system.
The rendered HTML “drink image” should change according to the order. For example:
If the order is small, show a small cup; if large, show a larger cup.
If the drink has whipped cream, visualize it with a simple HTML shape on top of the cup.
Instead of the beverage image, you can also render an HTML order receipt.
Resources:
https://docs.livekit.io/home/client/data/text-streams/
https://docs.livekit.io/home/client/data/rpc/
