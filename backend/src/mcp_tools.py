"""MCP tool integration for external task management and reminders.

This module provides optional MCP integration features. MCP support is only
enabled if the appropriate environment variables and configuration are set.
"""

import logging
import os
from typing import Any

logger = logging.getLogger("mcp_tools")

# Check if MCP integration is enabled
MCP_ENABLED = os.getenv("ENABLE_MCP", "false").lower() == "true"
TODOIST_API_TOKEN = os.getenv("TODOIST_API_TOKEN", "")


def is_mcp_available() -> bool:
    """Check if MCP integration is properly configured."""
    return MCP_ENABLED and bool(TODOIST_API_TOKEN)


async def create_todoist_tasks(goals: list[str]) -> dict[str, Any]:
    """Create Todoist tasks from a list of goals.
    
    Args:
        goals: List of goal descriptions to turn into tasks
    
    Returns:
        dict with keys:
            - success: bool indicating if tasks were created
            - task_count: number of tasks created
            - message: status message
            - task_ids: list of created task IDs (if successful)
    """
    if not is_mcp_available():
        return {
            "success": False,
            "task_count": 0,
            "message": "MCP integration is not enabled. Set ENABLE_MCP=true and configure TODOIST_API_TOKEN.",
            "task_ids": [],
        }
    
    try:
        # Import MCP client here to make it optional
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
        
        # Configure Todoist MCP server
        server_params = StdioServerParameters(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-todoist"],
            env={"TODOIST_API_TOKEN": TODOIST_API_TOKEN},
        )
        
        created_tasks = []
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                # Create a task for each goal
                for goal in goals:
                    result = await session.call_tool(
                        "add_task",
                        arguments={"content": goal}
                    )
                    created_tasks.append(result)
        
        return {
            "success": True,
            "task_count": len(created_tasks),
            "message": f"Created {len(created_tasks)} tasks in Todoist",
            "task_ids": [str(t.get("id", "")) for t in created_tasks],
        }
    
    except ImportError:
        logger.error("MCP package not installed. Install with: uv add mcp")
        return {
            "success": False,
            "task_count": 0,
            "message": "MCP package not installed. Please install it to use this feature.",
            "task_ids": [],
        }
    except Exception as e:
        logger.error(f"Failed to create Todoist tasks: {e}")
        return {
            "success": False,
            "task_count": 0,
            "message": f"Failed to create tasks: {str(e)}",
            "task_ids": [],
        }


async def mark_todoist_task_complete(task_id: str) -> dict[str, Any]:
    """Mark a Todoist task as complete.
    
    Args:
        task_id: The ID of the task to complete
    
    Returns:
        dict with keys:
            - success: bool indicating if task was marked complete
            - message: status message
    """
    if not is_mcp_available():
        return {
            "success": False,
            "message": "MCP integration is not enabled.",
        }
    
    try:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
        
        server_params = StdioServerParameters(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-todoist"],
            env={"TODOIST_API_TOKEN": TODOIST_API_TOKEN},
        )
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                await session.call_tool(
                    "complete_task",
                    arguments={"task_id": task_id}
                )
        
        return {
            "success": True,
            "message": f"Marked task {task_id} as complete",
        }
    
    except Exception as e:
        logger.error(f"Failed to complete task: {e}")
        return {
            "success": False,
            "message": f"Failed to complete task: {str(e)}",
        }


async def create_calendar_reminder(title: str, scheduled_time: str) -> dict[str, Any]:
    """Create a calendar reminder or event.
    
    Note: This is a placeholder - specific implementation depends on which
    calendar MCP server you're using (Google Calendar, Apple Calendar, etc.)
    
    Args:
        title: Title of the reminder/event
        scheduled_time: When to schedule it (ISO format or natural language)
    
    Returns:
        dict with keys:
            - success: bool indicating if reminder was created
            - message: status message
            - event_id: ID of created event (if successful)
    """
    if not is_mcp_available():
        return {
            "success": False,
            "message": "MCP integration is not enabled.",
            "event_id": None,
        }
    
    # This is a placeholder implementation
    # You would implement this based on your calendar MCP server
    logger.warning("Calendar reminder creation is not yet implemented")
    
    return {
        "success": False,
        "message": "Calendar integration is not yet configured. You can manually set a reminder for: " + title,
        "event_id": None,
    }
