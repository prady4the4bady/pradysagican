"""
F618: Adversarial Loop - Self-Play Tournament System
=====================================================

Competitive agent evaluation through:
- Self-play tournament system
- Head-to-head match tracking
- Dynamic ranking updates
- Adversarial learning from defeats
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum
from datetime import datetime, timezone
import uuid

logger = logging.getLogger(__name__)


class MatchResult(Enum):
    """Outcome of an adversarial match."""
    PLAYER1_WIN = "player1_win"
    PLAYER2_WIN = "player2_win"
    DRAW = "draw"
    ERROR = "error"


@dataclass
class AdversarialMatch:
    """Records a head-to-head match between two agents."""
    match_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    player1_id: str = ""
    player2_id: str = ""
    result: str = MatchResult.DRAW.value
    player1_score: float = 0.0
    player2_score: float = 0.0
    duration_ms: float = 0.0
    moves_count: int = 0
    match_data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    tournament_id: Optional[str] = None

    def get_winner(self) -> Optional[str]:
        """Get winner of the match.

        Returns:
            Winner agent ID or None for draw
        """
        if self.result == MatchResult.PLAYER1_WIN.value:
            return self.player1_id
        elif self.result == MatchResult.PLAYER2_WIN.value:
            return self.player2_id
        return None

    def get_loser(self) -> Optional[str]:
        """Get loser of the match.

        Returns:
            Loser agent ID or None for draw
        """
        winner = self.get_winner()
        if winner == self.player1_id:
            return self.player2_id
        elif winner == self.player2_id:
            return self.player1_id
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert match to dictionary."""
        return {
            "match_id": self.match_id,
            "player1_id": self.player1_id,
            "player2_id": self.player2_id,
            "result": self.result,
            "scores": (self.player1_score, self.player2_score),
            "duration_ms": self.duration_ms,
            "moves_count": self.moves_count,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class AgentRanking:
    """Ranking of an agent in tournament."""
    agent_id: str = ""
    rating: float = 1600.0  # Elo-style rating
    wins: int = 0
    losses: int = 0
    draws: int = 0
    total_matches: int = 0
    win_rate: float = 0.0
    average_score: float = 0.0
    last_match_time: Optional[datetime] = None
    streak: int = 0
    peak_rating: float = 1600.0

    def update_from_match(self, match: AdversarialMatch, is_player1: bool) -> None:
        """Update ranking based on match result.

        Args:
            match: The match result
            is_player1: True if this agent is player1
        """
        self.total_matches += 1
        self.last_match_time = match.timestamp

        my_score = match.player1_score if is_player1 else match.player2_score
        opponent_score = match.player2_score if is_player1 else match.player1_score
        
        self.average_score = (
            (self.average_score * (self.total_matches - 1) + my_score) /
            self.total_matches
        )

        # Update record and streak
        if match.result in (MatchResult.PLAYER1_WIN.value, MatchResult.PLAYER2_WIN.value):
            winner_id = match.get_winner()
            is_winner = winner_id == self.agent_id
            
            if is_winner:
                self.wins += 1
                self.streak = max(self.streak, 0) + 1
            else:
                self.losses += 1
                self.streak = min(self.streak, 0) - 1
        else:
            self.draws += 1
            self.streak = 0

        # Update win rate
        self.win_rate = self.wins / self.total_matches if self.total_matches > 0 else 0.0
        
        # Elo rating update (simplified)
        expected = 1.0 / (1.0 + 10 ** ((opponent_score - my_score) / 400))
        if match.result == MatchResult.DRAW.value:
            score = 0.5
        elif match.get_winner() == self.agent_id:
            score = 1.0
        else:
            score = 0.0

        delta = 32 * (score - expected)
        self.rating += delta
        self.peak_rating = max(self.peak_rating, self.rating)

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary."""
        return {
            "agent_id": self.agent_id,
            "rating": round(self.rating, 1),
            "peak_rating": round(self.peak_rating, 1),
            "record": f"{self.wins}-{self.losses}-{self.draws}",
            "win_rate": round(self.win_rate, 3),
            "average_score": round(self.average_score, 3),
            "total_matches": self.total_matches,
            "current_streak": self.streak,
        }


class Tournament:
    """Self-play tournament system for agent competition."""

    def __init__(self, tournament_id: Optional[str] = None):
        """Initialize tournament.

        Args:
            tournament_id: Optional tournament identifier
        """
        self.tournament_id = tournament_id or str(uuid.uuid4())
        self.matches: List[AdversarialMatch] = []
        self.rankings: Dict[str, AgentRanking] = {}
        self.agent_match_history: Dict[str, List[str]] = {}
        self.created_at = datetime.now(timezone.utc)
        self.current_round = 0
        self.total_rounds = 0

    def register_agent(self, agent_id: str, initial_rating: float = 1600.0) -> None:
        """Register agent for tournament.

        Args:
            agent_id: Agent identifier
            initial_rating: Initial Elo rating
        """
        if agent_id not in self.rankings:
            self.rankings[agent_id] = AgentRanking(
                agent_id=agent_id,
                rating=initial_rating,
                peak_rating=initial_rating
            )
            self.agent_match_history[agent_id] = []
            logger.debug(f"Registered agent {agent_id}")

    def record_match(
        self,
        player1_id: str,
        player2_id: str,
        result: MatchResult,
        player1_score: float,
        player2_score: float,
        duration_ms: float = 0.0,
        moves_count: int = 0,
        match_data: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Record match result and update rankings.

        Args:
            player1_id: First player agent ID
            player2_id: Second player agent ID
            result: Match result
            player1_score: Player 1 score
            player2_score: Player 2 score
            duration_ms: Match duration
            moves_count: Number of moves
            match_data: Additional match data

        Returns:
            Match ID
        """
        # Ensure agents are registered
        self.register_agent(player1_id)
        self.register_agent(player2_id)

        # Create match record
        match = AdversarialMatch(
            player1_id=player1_id,
            player2_id=player2_id,
            result=result.value,
            player1_score=player1_score,
            player2_score=player2_score,
            duration_ms=duration_ms,
            moves_count=moves_count,
            match_data=match_data or {},
            tournament_id=self.tournament_id,
        )

        # Store match
        self.matches.append(match)
        self.agent_match_history[player1_id].append(match.match_id)
        self.agent_match_history[player2_id].append(match.match_id)

        # Update rankings
        self.rankings[player1_id].update_from_match(match, is_player1=True)
        self.rankings[player2_id].update_from_match(match, is_player1=False)

        logger.debug(
            f"Match {match.match_id}: {player1_id} vs {player2_id} -> {result.value}"
        )

        return match.match_id

    def get_standings(self, min_matches: int = 1) -> List[Tuple[str, Dict[str, Any]]]:
        """Get tournament standings.

        Args:
            min_matches: Minimum matches to be included

        Returns:
            List of (agent_id, ranking_summary) tuples, sorted by rating
        """
        standings = [
            (aid, ranking.get_performance_summary())
            for aid, ranking in self.rankings.items()
            if ranking.total_matches >= min_matches
        ]
        
        standings.sort(key=lambda x: x[1]["rating"], reverse=True)
        return standings

    def get_head_to_head(
        self,
        player1_id: str,
        player2_id: str,
    ) -> List[AdversarialMatch]:
        """Get all matches between two players.

        Args:
            player1_id: First player ID
            player2_id: Second player ID

        Returns:
            List of matches between the players
        """
        h2h = [
            m for m in self.matches
            if (m.player1_id == player1_id and m.player2_id == player2_id) or
               (m.player1_id == player2_id and m.player2_id == player1_id)
        ]
        return sorted(h2h, key=lambda m: m.timestamp)

    def get_agent_stats(self, agent_id: str) -> Dict[str, Any]:
        """Get detailed statistics for an agent.

        Args:
            agent_id: Agent identifier

        Returns:
            Detailed statistics dictionary
        """
        if agent_id not in self.rankings:
            return {}

        ranking = self.rankings[agent_id]
        recent_matches = [
            self.matches[mid] for mid in self.agent_match_history[agent_id][-10:]
            if any(m.match_id == mid for m in self.matches)
        ]

        return {
            **ranking.get_performance_summary(),
            "recent_matches": [m.to_dict() for m in recent_matches],
            "match_history_size": len(self.agent_match_history[agent_id]),
        }

    def get_tournament_summary(self) -> Dict[str, Any]:
        """Get tournament summary statistics.

        Returns:
            Tournament statistics
        """
        return {
            "tournament_id": self.tournament_id,
            "created_at": self.created_at.isoformat(),
            "total_matches": len(self.matches),
            "total_agents": len(self.rankings),
            "current_round": self.current_round,
            "total_rounds": self.total_rounds,
            "standings": self.get_standings(),
        }


class TournamentRanking:
    """Multi-tournament ranking aggregator."""

    def __init__(self):
        """Initialize tournament ranking system."""
        self.global_ratings: Dict[str, float] = {}
        self.tournament_results: Dict[str, Dict[str, AgentRanking]] = {}
        self.agent_tournament_count: Dict[str, int] = {}

    def register_tournament(
        self,
        tournament_id: str,
        tournament: Tournament,
    ) -> None:
        """Register tournament results in global ranking.

        Args:
            tournament_id: Tournament identifier
            tournament: Tournament object with results
        """
        self.tournament_results[tournament_id] = dict(tournament.rankings)

        # Update global ratings
        for agent_id, ranking in tournament.rankings.items():
            if agent_id not in self.global_ratings:
                self.global_ratings[agent_id] = 1600.0
                self.agent_tournament_count[agent_id] = 0

            # Update global rating (exponential moving average)
            alpha = 0.7
            self.global_ratings[agent_id] = (
                alpha * ranking.rating +
                (1 - alpha) * self.global_ratings[agent_id]
            )
            self.agent_tournament_count[agent_id] += 1

    def get_global_rankings(self) -> List[Tuple[str, float, int]]:
        """Get global rankings across all tournaments.

        Returns:
            List of (agent_id, global_rating, tournament_count) tuples
        """
        rankings = [
            (aid, rating, self.agent_tournament_count[aid])
            for aid, rating in self.global_ratings.items()
        ]
        rankings.sort(key=lambda x: x[1], reverse=True)
        return rankings

    def get_agent_tournament_history(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get tournament history for an agent.

        Args:
            agent_id: Agent identifier

        Returns:
            List of tournament results
        """
        history = []
        for tournament_id, results in self.tournament_results.items():
            if agent_id in results:
                ranking = results[agent_id]
                history.append({
                    "tournament_id": tournament_id,
                    "rating": ranking.rating,
                    "record": f"{ranking.wins}-{ranking.losses}-{ranking.draws}",
                    "win_rate": ranking.win_rate,
                })
        return sorted(history, key=lambda x: x["tournament_id"])
