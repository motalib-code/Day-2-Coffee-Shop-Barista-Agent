import asyncio
import logging
from unittest.mock import MagicMock, AsyncMock
from src.day8_agent import GameMasterAgent

# Mock LiveKit components
mock_room = MagicMock()
# Mock local_participant and its publish_data method which is async
mock_room.local_participant = MagicMock()
mock_room.local_participant.publish_data = AsyncMock()

mock_context = MagicMock()

async def test_tools():
    agent = GameMasterAgent(room=mock_room)
    
    print("Testing Initialize Universe...")
    res = await agent.initialize_universe(mock_context, universe_type="Cyberpunk Sci-Fi", character_name="Neo")
    print(res)
    assert "Cyberpunk" in res
    assert "Neo" in res
    assert "Datapad" in agent.world_state["character"]["inventory"]
    # Verify broadcast was called
    mock_room.local_participant.publish_data.assert_called()
    
    print("\nTesting Dice Roll...")
    res = await agent.roll_dice(mock_context, sides=20, modifier=5, reason="Hacking")
    print(res)
    assert "Rolled d20" in res
    
    print("\nTesting Inventory...")
    res = await agent.update_inventory(mock_context, item_name="Laser Pistol", action="add")
    print(res)
    assert "Laser Pistol" in agent.world_state["character"]["inventory"]
    
    res = await agent.check_inventory(mock_context)
    print(res)
    assert "Laser Pistol" in res
    
    print("\nTesting Health...")
    res = await agent.update_health(mock_context, amount=-5, reason="Shot")
    print(res)
    assert agent.world_state["character"]["hp"] < agent.world_state["character"]["max_hp"]
    
    print("\nTesting Save Game...")
    res = await agent.save_game(mock_context, save_name="test_save")
    print(res)
    assert "saved successfully" in res
    
    print("\nTesting Load Game...")
    # Modify state to verify load works
    agent.world_state["character"]["hp"] = 0
    res = await agent.load_game(mock_context, save_name="test_save")
    print(res)
    assert agent.world_state["character"]["hp"] > 0
    assert "Laser Pistol" in agent.world_state["character"]["inventory"]
    
    print("\nAll tests passed!")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(test_tools())
