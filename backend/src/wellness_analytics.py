"""Wellness analytics utilities for analyzing check-in history."""

import logging
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger("wellness_analytics")


def parse_date(date_str: str) -> datetime:
    """Parse ISO format date string to datetime object."""
    try:
        return datetime.fromisoformat(date_str)
    except (ValueError, TypeError):
        logger.warning(f"Could not parse date: {date_str}")
        return datetime.now()


def filter_recent_sessions(history: list[dict[str, Any]], days: int = 7) -> list[dict[str, Any]]:
    """Filter sessions from the last N days."""
    if not history:
        return []
    
    cutoff_date = datetime.now() - timedelta(days=days)
    recent_sessions = []
    
    for session in history:
        session_date = parse_date(session.get("date", ""))
        if session_date >= cutoff_date:
            recent_sessions.append(session)
    
    return recent_sessions


def calculate_mood_trend(history: list[dict[str, Any]], days: int = 7) -> dict[str, Any]:
    """Analyze mood trends over the last N days.
    
    Returns:
        dict with keys:
            - recent_sessions: number of sessions analyzed
            - moods: list of reported moods
            - trend_summary: natural language summary
            - average_energy: if energy was tracked
    """
    recent = filter_recent_sessions(history, days)
    
    if not recent:
        return {
            "recent_sessions": 0,
            "moods": [],
            "trend_summary": "No recent check-ins to analyze.",
            "average_energy": None,
        }
    
    moods = [s.get("mood", "").lower() for s in recent if s.get("mood")]
    energies = [s.get("energy", "").lower() for s in recent if s.get("energy")]
    
    # Count mood frequencies
    mood_counts = {}
    for mood in moods:
        mood_counts[mood] = mood_counts.get(mood, 0) + 1
    
    # Generate natural language summary
    if not moods:
        trend_summary = f"You've had {len(recent)} check-ins recently, but mood wasn't recorded."
    else:
        most_common_mood = max(mood_counts, key=mood_counts.get)
        if len(set(moods)) == 1:
            trend_summary = f"Your mood has been consistently {moods[0]} over the last {days} days."
        elif mood_counts[most_common_mood] > len(moods) // 2:
            trend_summary = f"You've mostly been feeling {most_common_mood} lately, with {mood_counts[most_common_mood]} out of {len(moods)} check-ins."
        else:
            trend_summary = f"Your mood has been varied - {', '.join(set(moods))} - over the last {days} days."
    
    return {
        "recent_sessions": len(recent),
        "moods": moods,
        "mood_counts": mood_counts,
        "trend_summary": trend_summary,
        "energies": energies,
    }


def calculate_goal_completion_rate(history: list[dict[str, Any]], days: int = 7) -> dict[str, Any]:
    """Track goal setting and completion patterns.
    
    Note: This is a basic heuristic since we don't explicitly track completion.
    We assume consistent check-ins indicate follow-through.
    
    Returns:
        dict with keys:
            - total_goals_set: total number of goals across all sessions
            - average_goals_per_day: average goals per session
            - goal_frequency: how often goals were set
            - summary: natural language summary
    """
    recent = filter_recent_sessions(history, days)
    
    if not recent:
        return {
            "total_goals_set": 0,
            "average_goals_per_day": 0,
            "goal_frequency": "No recent data",
            "summary": "No recent check-ins to analyze.",
        }
    
    total_goals = 0
    sessions_with_goals = 0
    
    for session in recent:
        goals = session.get("goals", [])
        if goals:
            total_goals += len(goals)
            sessions_with_goals += 1
    
    avg_goals = total_goals / len(recent) if recent else 0
    goal_percentage = (sessions_with_goals / len(recent) * 100) if recent else 0
    
    # Generate summary
    if sessions_with_goals == 0:
        summary = f"You've had {len(recent)} check-ins but haven't set specific goals."
    elif sessions_with_goals == len(recent):
        summary = f"Great consistency! You've set goals in all {len(recent)} recent check-ins, averaging {avg_goals:.1f} goals per session."
    else:
        summary = f"You set goals in {sessions_with_goals} out of {len(recent)} check-ins ({goal_percentage:.0f}%), averaging {avg_goals:.1f} goals when you do."
    
    return {
        "total_goals_set": total_goals,
        "sessions_with_goals": sessions_with_goals,
        "average_goals_per_day": round(avg_goals, 1),
        "goal_frequency": f"{goal_percentage:.0f}% of sessions",
        "summary": summary,
    }


def generate_weekly_insights(history: list[dict[str, Any]]) -> str:
    """Generate a comprehensive weekly summary combining mood and goal data.
    
    Returns:
        Natural language summary suitable for voice output.
    """
    mood_analysis = calculate_mood_trend(history, days=7)
    goal_analysis = calculate_goal_completion_rate(history, days=7)
    
    if mood_analysis["recent_sessions"] == 0:
        return "I don't have any recent check-ins to summarize. Let's do one now!"
    
    # Build comprehensive summary
    insights = []
    
    # Session frequency
    session_count = mood_analysis["recent_sessions"]
    if session_count == 1:
        insights.append("We've had one check-in this week.")
    else:
        insights.append(f"We've checked in {session_count} times this week.")
    
    # Mood trend
    insights.append(mood_analysis["trend_summary"])
    
    # Energy trend (if available)
    if mood_analysis.get("energies"):
        energies = mood_analysis["energies"]
        if "high" in energies or "energetic" in energies:
            insights.append("Your energy has been good lately.")
        elif all(e in ["low", "tired", "exhausted"] for e in energies):
            insights.append("Your energy has been on the lower side. Make sure you're getting enough rest.")
    
    # Goal setting
    insights.append(goal_analysis["summary"])
    
    # Encouraging note
    if goal_analysis["sessions_with_goals"] > 0:
        insights.append("Keep up the good work setting intentions for yourself!")
    
    return " ".join(insights)


def get_common_stressors(history: list[dict[str, Any]], days: int = 7) -> dict[str, Any]:
    """Identify common stressors from recent sessions.
    
    Returns:
        dict with keys:
            - stressors: list of unique stressors
            - stressor_counts: frequency of each stressor
            - summary: natural language summary
    """
    recent = filter_recent_sessions(history, days)
    
    all_stressors = []
    for session in recent:
        stressors = session.get("stressors", [])
        if isinstance(stressors, list):
            all_stressors.extend(stressors)
    
    if not all_stressors:
        return {
            "stressors": [],
            "stressor_counts": {},
            "summary": "You haven't mentioned any specific stressors recently.",
        }
    
    # Count frequencies
    stressor_counts = {}
    for stressor in all_stressors:
        stressor_counts[stressor] = stressor_counts.get(stressor, 0) + 1
    
    # Sort by frequency
    sorted_stressors = sorted(stressor_counts.items(), key=lambda x: x[1], reverse=True)
    
    if len(sorted_stressors) == 1:
        summary = f"The main thing stressing you out has been {sorted_stressors[0][0]}."
    else:
        top_two = [s[0] for s in sorted_stressors[:2]]
        summary = f"Your main stressors have been {top_two[0]} and {top_two[1]}."
    
    return {
        "stressors": list(stressor_counts.keys()),
        "stressor_counts": stressor_counts,
        "summary": summary,
    }
