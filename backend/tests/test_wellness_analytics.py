"""Tests for wellness analytics functions."""

import json
from datetime import datetime, timedelta

import pytest

from wellness_analytics import (
    calculate_goal_completion_rate,
    calculate_mood_trend,
    filter_recent_sessions,
    generate_weekly_insights,
    get_common_stressors,
)


def create_sample_session(days_ago=0, mood="good", energy="medium", goals=None, stressors=None):
    """Helper to create a sample wellness session."""
    date = datetime.now() - timedelta(days=days_ago)
    return {
        "date": date.isoformat(),
        "mood": mood,
        "energy": energy,
        "goals": goals or [],
        "stressors": stressors or [],
        "summary": f"Test session from {days_ago} days ago",
    }


class TestFilterRecentSessions:
    def test_empty_history(self):
        result = filter_recent_sessions([], days=7)
        assert result == []

    def test_filters_by_days(self):
        history = [
            create_sample_session(days_ago=3),
            create_sample_session(days_ago=10),
            create_sample_session(days_ago=1),
        ]
        result = filter_recent_sessions(history, days=7)
        assert len(result) == 2

    def test_includes_all_recent(self):
        history = [
            create_sample_session(days_ago=i) for i in range(5)
        ]
        result = filter_recent_sessions(history, days=7)
        assert len(result) == 5


class TestCalculateMoodTrend:
    def test_empty_history(self):
        result = calculate_mood_trend([])
        assert result["recent_sessions"] == 0
        assert "No recent check-ins" in result["trend_summary"]

    def test_consistent_mood(self):
        history = [
            create_sample_session(days_ago=i, mood="great") for i in range(3)
        ]
        result = calculate_mood_trend(history, days=7)
        assert result["recent_sessions"] == 3
        assert "consistently great" in result["trend_summary"]

    def test_varied_moods(self):
        history = [
            create_sample_session(days_ago=0, mood="good"),
            create_sample_session(days_ago=1, mood="tired"),
            create_sample_session(days_ago=2, mood="stressed"),
        ]
        result = calculate_mood_trend(history, days=7)
        assert result["recent_sessions"] == 3
        assert len(result["moods"]) == 3

    def test_mood_counts(self):
        history = [
            create_sample_session(days_ago=0, mood="good"),
            create_sample_session(days_ago=1, mood="good"),
            create_sample_session(days_ago=2, mood="tired"),
        ]
        result = calculate_mood_trend(history, days=7)
        assert result["mood_counts"]["good"] == 2
        assert result["mood_counts"]["tired"] == 1


class TestCalculateGoalCompletionRate:
    def test_empty_history(self):
        result = calculate_goal_completion_rate([])
        assert result["total_goals_set"] == 0
        assert "No recent check-ins" in result["summary"]

    def test_no_goals_set(self):
        history = [
            create_sample_session(days_ago=i, goals=[]) for i in range(3)
        ]
        result = calculate_goal_completion_rate(history, days=7)
        assert result["total_goals_set"] == 0
        assert result["sessions_with_goals"] == 0

    def test_consistent_goal_setting(self):
        history = [
            create_sample_session(days_ago=i, goals=["goal1", "goal2"]) 
            for i in range(3)
        ]
        result = calculate_goal_completion_rate(history, days=7)
        assert result["total_goals_set"] == 6
        assert result["sessions_with_goals"] == 3
        assert "all 3 recent check-ins" in result["summary"].lower()

    def test_partial_goal_setting(self):
        history = [
            create_sample_session(days_ago=0, goals=["goal1"]),
            create_sample_session(days_ago=1, goals=[]),
            create_sample_session(days_ago=2, goals=["goal2", "goal3"]),
        ]
        result = calculate_goal_completion_rate(history, days=7)
        assert result["total_goals_set"] == 3
        assert result["sessions_with_goals"] == 2


class TestGenerateWeeklyInsights:
    def test_empty_history(self):
        result = generate_weekly_insights([])
        assert "don't have any recent check-ins" in result.lower()

    def test_single_session(self):
        history = [
            create_sample_session(days_ago=0, mood="good", goals=["goal1"])
        ]
        result = generate_weekly_insights(history)
        assert "one check-in" in result.lower()

    def test_multiple_sessions(self):
        history = [
            create_sample_session(
                days_ago=i,
                mood="good" if i % 2 == 0 else "tired",
                energy="high" if i < 2 else "low",
                goals=["goal1", "goal2"]
            )
            for i in range(5)
        ]
        result = generate_weekly_insights(history)
        assert "5 times" in result.lower() or "5" in result
        assert len(result) > 50  # Should be a comprehensive summary


class TestGetCommonStressors:
    def test_no_stressors(self):
        history = [
            create_sample_session(days_ago=i, stressors=[]) for i in range(3)
        ]
        result = get_common_stressors(history)
        assert len(result["stressors"]) == 0
        assert "haven't mentioned" in result["summary"].lower()

    def test_single_stressor(self):
        history = [
            create_sample_session(days_ago=i, stressors=["work"]) for i in range(3)
        ]
        result = get_common_stressors(history)
        assert "work" in result["stressors"]
        assert result["stressor_counts"]["work"] == 3

    def test_multiple_stressors(self):
        history = [
            create_sample_session(days_ago=0, stressors=["work", "sleep"]),
            create_sample_session(days_ago=1, stressors=["work"]),
            create_sample_session(days_ago=2, stressors=["sleep", "health"]),
        ]
        result = get_common_stressors(history)
        assert result["stressor_counts"]["work"] == 2
        assert result["stressor_counts"]["sleep"] == 2
        assert result["stressor_counts"]["health"] == 1
