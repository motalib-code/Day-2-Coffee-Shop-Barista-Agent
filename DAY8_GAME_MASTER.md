# Day 8 – Voice Game Master (D&D-Style Adventure)

## 🎯 Overview

A voice-powered Game Master (GM) that runs interactive adventures in various settings (Fantasy, Sci-Fi, Zombie Apocalypse). The agent manages the story, tracks player stats and inventory, handles dice rolls, and maintains game state across sessions.

---

## ✨ Features

### Primary Features (MVP)
- ✅ **Interactive Storytelling** - GM describes scenes and reacts to player actions
- ✅ **Multiple Universes** - Supports Fantasy, Cyberpunk, and Zombie settings
- ✅ **Continuity** - Remembers context using chat history and JSON state
- ✅ **Mini-Arc Structure** - Designed for short, satisfying sessions

### Advanced Features
- ✅ **JSON World State** - Tracks Character, Inventory, Health, and Location
- ✅ **Character Sheet UI** - Real-time display of player stats and items in the frontend
- ✅ **Dice Mechanics** - `roll_dice` tool for risky actions with success/failure outcomes
- ✅ **Inventory Management** - Add/remove items via voice commands
- ✅ **Save & Resume** - Persist game state to `day8_saves.json` and load it later

---

## 📁 Files Created

### Backend
```
backend/
├── day8_saves.json           # Saved game states
└── src/
    └── day8_agent.py         # Main GM agent implementation
```

### Frontend
```
frontend/
├── components/app/
│   └── character-sheet.tsx   # React component to display game state
├── hooks/
│   └── useWorldState.ts      # Hook to listen for state updates
└── app/
    └── session-view.tsx      # Updated to include CharacterSheet
```

---

## 🎭 Agent Capabilities

### Storytelling Tools
1. **initialize_universe** - Set up the game setting and character stats
2. **roll_dice** - Handle uncertain outcomes with d20 rolls

### State Management
3. **check_status** - Report HP and stats
4. **check_inventory** - List carried items
5. **update_inventory** - Add/remove items
6. **update_health** - Apply damage or healing

### Persistence
7. **save_game** - Save current progress
8. **load_game** - Restore a previous session

---

## 🚀 Quick Start

### 1. Run the Agent

```bash
cd backend
uv run python src/day8_agent.py dev
```

### 2. Connect to Agent

1. Open browser to: `http://localhost:3000`
2. Join the room when prompted
3. Say "I want to play a Fantasy game" (or Sci-Fi, etc.)
4. The Character Sheet will appear in the top right corner!

---

## 🎮 Example Conversation

**User**: "I want to play a Cyberpunk game."
**GM**: "Initializing Cyberpunk universe... You are Neo, a runner in Night City. You have a Datapad and a Multi-tool. You stand before the neon-lit entrance of the Arasaka Tower. What do you do?"

**User**: "I scan the door for security."
**GM**: "Rolling for perception... [Rolls 18] Success! You spot a hidden laser grid. It's active."

**User**: "I use my Multi-tool to disable it."
**GM**: "Rolling for tech... [Rolls 4] Critical Failure! You trip the alarm. Sirens start blaring. A guard drone approaches!"

**User**: "I run!"

---

## 🔧 Architecture

### Agent Class: `GameMasterAgent`

**State Management:**
- `world_state` dictionary containing:
    - `universe`: Current setting
    - `character`: Name, HP, Stats, Inventory
    - `location`: Current place
    - `history`: Log of events

**Frontend Integration:**
- The agent broadcasts `world_state` via `publish_data` whenever it changes.
- The frontend `useWorldState` hook listens for these updates.
- `CharacterSheet` component renders the data.

---

**Built with:** LiveKit Agents, Murf Falcon TTS (Narrative), Google Gemini 2.5 Flash, Deepgram STT
