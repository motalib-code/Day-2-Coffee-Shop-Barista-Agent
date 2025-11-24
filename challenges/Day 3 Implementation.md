# Day 3 Implementation - Health & Wellness Voice Companion

## Overview
This implementation creates a supportive health and wellness voice companion that:
- Conducts daily check-ins about mood, energy, and goals
- Provides grounded, realistic advice
- Persists data to JSON for context-aware conversations
- References past sessions to build continuity

## Key Features

### 1. Context-Aware Greetings
The agent loads past check-ins from `wellness_log.json` and personalizes its greeting:
```python
def _generate_instructions(self) -> str:
    # Adds context from last session if available
    if self.history:
        last_session = self.history[-1]
        context_note = f"\n\nContext from last check-in ({last_session.get('date', 'recent')}):\n"
```

### 2. Structured Conversation Flow
The agent follows a clear flow:
1. **Greeting** - References past sessions
2. **Mood & Energy Check** - "How are you feeling today?"
3. **Daily Goals** - "What are 1-3 things you'd like to get done?"
4. **Simple Advice** - Practical, grounded suggestions
5. **Recap** - Summarize and confirm before saving

### 3. JSON Persistence
Data is stored in `wellness_log.json` with this schema:
```json
{
  "date": "2025-11-24T21:24:13+05:30",
  "mood": "good",
  "energy": "medium",
  "stressors": ["deadline", "sleep"],
  "goals": ["finish report", "take a walk", "call friend"],
  "summary": "User feeling good but stressed about deadline"
}
```

### 4. Function Tool: save_log
The agent uses a function tool to persist check-ins:
```python
@function_tool
async def save_log(
    self, 
    context: RunContext,
    mood: str,
    energy: str,
    goals: list[str],
    stressors: str = "",
    summary: str = ""
):
```

## File Structure

### Modified Files
- **[RENAMED]** `backend/src/agent.py` → `backend/src/day2_agent.py`
  - Preserved the Coffee Shop Barista agent

### New Files
- **[NEW]** `backend/src/agent.py`
  - WellnessCompanion agent implementation
  - Loads and saves `wellness_log.json`
  - Provides context-aware conversations

- **[NEW]** `backend/wellness_log.json` (created on first run)
  - Stores all check-in history

## How to Use

### Start the Agent
```bash
cd backend
uv run python src/agent.py
```

### Voice Interaction Example
**Agent**: "Hi! Last time we talked, you mentioned feeling low on energy. How does today compare?"

**User**: "I'm feeling better today, more energized."

**Agent**: "That's great to hear! What's your energy like on a scale - would you say high, medium, or low?"

**User**: "I'd say medium to high."

**Agent**: "Awesome. What are 1-3 things you'd like to get done today?"

**User**: "I want to finish my project report, go for a run, and call my mom."

**Agent**: "Those sound like solid goals. For the project report, it might help to break it into smaller chunks - maybe start with just the outline. And scheduling that run earlier in the day could help maintain your energy. Does that sound right?"

**User**: "Yes, that sounds good."

**Agent**: "Perfect! So to recap: You're feeling medium to high energy today, and your main goals are finishing the project report, going for a run, and calling your mom. Does this sound right?"

**User**: "Yes, that's correct."

**Agent**: *[Calls save_log tool]* "Session saved! Take care, and I'll check in with you next time."

## Technical Details

### Agent Initialization
- Loads history **before** calling `super().__init__()` to personalize instructions
- Dynamically generates instructions based on past sessions

### Error Handling
- Gracefully handles missing or corrupted JSON files
- Logs errors but continues operation

### Voice Pipeline
- **STT**: Deepgram Nova-3
- **LLM**: Google Gemini 2.5 Flash
- **TTS**: Murf (Matthew voice, Conversation style)
- **Turn Detection**: Multilingual Model

## Next Steps (Optional Advanced Goals)

### Advanced Goal 1: MCP Integration
- Connect to Notion/Todoist/Zapier MCP servers
- Allow agent to create tasks from goals
- Example: "Turn these into Todoist tasks"

### Advanced Goal 2: Weekly Reflection
- Add weekly summary function
- Analyze mood trends over time
- Provide insights: "Your energy has been trending up this week"

### Advanced Goal 3: Follow-up Reminders
- Use MCP to create calendar events
- Example: "Set a reminder for my run at 6 PM"

## Implementation Notes

### Design Decisions
1. **Single Function Tool**: Used one `save_log` tool instead of multiple update tools for simplicity
2. **Dynamic Instructions**: Generated instructions with context to keep the agent's memory fresh
3. **Grounded Advice**: Emphasized in instructions to avoid medical claims
4. **Conversational Tone**: Kept responses natural for voice interaction

### Differences from Day 2
- Day 2 (Coffee Shop) used multiple tools (`update_drink_type`, `update_size`, etc.)
- Day 3 uses a single tool (`save_log`) called at the end
- Day 2 had visual HTML updates; Day 3 focuses on conversation flow
- Day 3 leverages history for context awareness

## Verification Checklist
- [ ] Agent starts without errors
- [ ] Agent references past sessions in greeting
- [ ] Agent asks about mood and energy
- [ ] Agent asks about daily goals
- [ ] Agent provides practical advice
- [ ] Agent recaps before saving
- [ ] `wellness_log.json` is created and updated
- [ ] Subsequent sessions load and reference past data
