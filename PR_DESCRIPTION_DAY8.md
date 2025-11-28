# Day 8: Voice Game Master (D&D-Style Adventure) 🎲

## 📝 Description
This PR implements the Day 8 challenge: a voice-powered Game Master (GM) agent capable of running interactive adventures in multiple settings (Fantasy, Sci-Fi, Zombie Apocalypse).

The agent acts as a Dungeon Master, describing scenes, handling player actions, and managing game state (health, inventory, stats) which is visualized in real-time on the frontend.

## ✨ Features
- **Interactive Storytelling**: GM persona that adapts to the chosen universe.
- **JSON World State**: Tracks character HP, stats, inventory, and location.
- **Real-time Frontend UI**: A new `CharacterSheet` component displays the game state live.
- **Dice Mechanics**: `roll_dice` tool for resolving risky actions.
- **Inventory Management**: Add/remove items via voice.
- **Save/Load System**: Persist game state to JSON.

## 🛠️ Implementation Details
- **Backend**: `day8_agent.py` handles the logic, state management, and tool definitions.
- **Frontend**: Added `CharacterSheet` component and `useWorldState` hook to consume `world_state` broadcasts from the agent.
- **State Sync**: The agent broadcasts the full world state JSON to the frontend whenever it changes.

## 🧪 Testing
- Run the agent: `uv run python src/day8_agent.py dev`
- Run tests: `uv run python test_day8.py`
- Verified:
    - Universe initialization
    - Dice rolling
    - Inventory updates
    - Health updates
    - Save/Load functionality
    - Frontend UI updates

## 📸 Screenshots/Demo
(See `DAY8_GAME_MASTER.md` for details)
