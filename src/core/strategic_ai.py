"""
Game-theoretic strategic AI for competitive dynamics.
Nash equilibrium approximation, prisoner's dilemma, tit-for-tat.
No API calls. Pure game theory math.
"""

import math
import random
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
from enum import Enum


class Strategy(Enum):
    COOPERATE = "cooperate"      # Maintain prices, share market
    DEFECT = "defect"            # Undercut, aggressive discount
    TIT_FOR_TAT = "tit_for_tat"  # Mirror opponent's last move
    GRIM_TRIGGER = "grim"        # Cooperate until betrayed, then always defect
    RANDOM = "random"            # Unpredictable
    BULLY = "bully"              # Defect until opponent cooperates, then cooperate


@dataclass
class GameState:
    """State of competitive game"""
    round: int
    my_history: List[str]       # My past actions
    opponent_history: List[str]  # Opponent's past actions
    my_payoff: float
    opponent_payoff: float


class NashEquilibrium:
    """
    Approximate Nash equilibrium for pricing games.
    Uses iterated best response (fictitious play).
    """

    def __init__(self, payoff_matrix: Dict[Tuple[str, str], Tuple[float, float]]):
        self.payoff_matrix = payoff_matrix
        self.best_response_cache: Dict[str, str] = {}

    def best_response(self, opponent_strategy: str) -> str:
        """
        Find my best response to opponent's strategy
        """
        if opponent_strategy in self.best_response_cache:
            return self.best_response_cache[opponent_strategy]

        best_payoff = -float('inf')
        best_action = None

        for my_action in ['cooperate', 'defect']:
            payoff = self.payoff_matrix.get((my_action, opponent_strategy), (0, 0))[0]
            if payoff > best_payoff:
                best_payoff = payoff
                best_action = my_action

        self.best_response_cache[opponent_strategy] = best_action
        return best_action

    def find_equilibrium(self, max_iterations: int = 100) -> Tuple[str, str]:
        """
        Find approximate Nash equilibrium via fictitious play
        """
        # Start with random strategies
        my_strategy = 'cooperate'
        opponent_strategy = 'cooperate'

        for _ in range(max_iterations):
            new_my = self.best_response(opponent_strategy)
            new_opponent = self.best_response(my_strategy)

            if new_my == my_strategy and new_opponent == opponent_strategy:
                return (my_strategy, opponent_strategy)  # Converged

            my_strategy = new_my
            opponent_strategy = new_opponent

        return (my_strategy, opponent_strategy)  # Best approximation


class TitForTatEngine:
    """
    Axelrod's tournament-winning strategy: nice, retaliatory, forgiving, clear.
    """

    def __init__(self, forgiveness_prob: float = 0.1):
        self.forgiveness_prob = forgiveness_prob  # Occasionally forgive defection

    def decide(self, state: GameState) -> str:
        if not state.opponent_history:
            return Strategy.COOPERATE.value  # Start nice

        last_opponent = state.opponent_history[-1]

        if last_opponent == Strategy.COOPERATE.value:
            return Strategy.COOPERATE.value

        # Opponent defected
        if random.random() < self.forgiveness_prob:
            return Strategy.COOPERATE.value  # Forgive

        return Strategy.DEFECT.value  # Retaliate


class PriceWarGame:
    """
    Simulates repeated pricing game between two brands.
    """

    PAYOFF_MATRIX = {
        # (My action, Opponent action) -> (My payoff, Opponent payoff)
        ('cooperate', 'cooperate'): (10, 10),   # Both maintain prices
        ('cooperate', 'defect'): (2, 15),       # I maintain, they undercut
        ('defect', 'cooperate'): (15, 2),       # I undercut, they maintain
        ('defect', 'defect'): (5, 5),           # Both undercut, race to bottom
    }

    def __init__(self, brand_a_strategy: Strategy, brand_b_strategy: Strategy):
        self.strategy_a = brand_a_strategy
        self.strategy_b = brand_b_strategy
        self.history: List[Dict] = []
        self.scores = {'A': 0, 'B': 0}

        # Strategy engines
        self.engines = {
            Strategy.TIT_FOR_TAT: TitForTatEngine(),
            Strategy.GRIM_TRIGGER: None,  # State-based
            Strategy.COOPERATE: None,
            Strategy.DEFECT: None,
            Strategy.RANDOM: None,
            Strategy.BULLY: None
        }

    def play_round(self) -> Dict:
        """Play one round of pricing game"""
        round_num = len(self.history) + 1

        # Get histories
        a_history = [h['a_action'] for h in self.history]
        b_history = [h['b_action'] for h in self.history]

        # Decide actions
        a_state = GameState(round_num, a_history, b_history,
                           self.scores['A'], self.scores['B'])
        b_state = GameState(round_num, b_history, a_history,
                           self.scores['B'], self.scores['A'])

        a_action = self._decide(self.strategy_a, a_state, 'A')
        b_action = self._decide(self.strategy_b, b_state, 'B')

        # Calculate payoffs
        payoff = self.PAYOFF_MATRIX.get((a_action, b_action), (5, 5))

        self.scores['A'] += payoff[0]
        self.scores['B'] += payoff[1]

        result = {
            'round': round_num,
            'a_action': a_action,
            'b_action': b_action,
            'a_payoff': payoff[0],
            'b_payoff': payoff[1],
            'a_cumulative': self.scores['A'],
            'b_cumulative': self.scores['B']
        }

        self.history.append(result)
        return result

    def _decide(self, strategy: Strategy, state: GameState, player: str) -> str:
        """Execute strategy"""
        if strategy == Strategy.COOPERATE:
            return 'cooperate'

        elif strategy == Strategy.DEFECT:
            return 'defect'

        elif strategy == Strategy.TIT_FOR_TAT:
            engine = self.engines[Strategy.TIT_FOR_TAT]
            return engine.decide(state)

        elif strategy == Strategy.GRIM_TRIGGER:
            # Cooperate until opponent defects, then always defect
            if 'defect' in state.opponent_history:
                return 'defect'
            return 'cooperate'

        elif strategy == Strategy.RANDOM:
            return random.choice(['cooperate', 'defect'])

        elif strategy == Strategy.BULLY:
            # Defect until opponent cooperates twice in a row
            if len(state.opponent_history) >= 2:
                if state.opponent_history[-1] == 'cooperate' and \
                   state.opponent_history[-2] == 'cooperate':
                    return 'cooperate'
            return 'defect'

        return 'cooperate'

    def run_tournament(self, rounds: int = 100) -> Dict:
        """Run full tournament between strategies"""
        for _ in range(rounds):
            self.play_round()

        return {
            'strategy_a': self.strategy_a.value,
            'strategy_b': self.strategy_b.value,
            'final_score_a': self.scores['A'],
            'final_score_b': self.scores['B'],
            'winner': 'A' if self.scores['A'] > self.scores['B'] else
                     'B' if self.scores['B'] > self.scores['A'] else 'tie',
            'cooperation_rate': sum(
                1 for h in self.history
                if h['a_action'] == 'cooperate' and h['b_action'] == 'cooperate'
            ) / len(self.history),
            'history': self.history
        }


class MarketEntryGame:
    """
    Should new brand enter market dominated by incumbent?
    Stackelberg competition model.
    """

    def __init__(self, incumbent_capacity: float, market_size: float,
                 entry_cost: float, price_elasticity: float):
        self.incumbent_capacity = incumbent_capacity
        self.market_size = market_size
        self.entry_cost = entry_cost
        self.elasticity = price_elasticity

    def analyze_entry(self, entrant_cost_advantage: float) -> Dict:
        """
        Determine if market entry is profitable
        """
        # Incumbent's optimal quantity (Cournot)
        incumbent_q = self.market_size / 2

        # If entrant enters, total quantity increases, price falls
        total_q = self.market_size * 0.75  # Both produce
        market_price = self.market_size - total_q  # Linear demand

        # Entrant's profit
        entrant_q = total_q - incumbent_q
        entrant_cost = 1 - entrant_cost_advantage  # Lower is better
        entrant_profit = (market_price - entrant_cost) * entrant_q - self.entry_cost

        # Incumbent's profit after entry
        incumbent_profit = (market_price - 1) * incumbent_q

        # Incumbent's profit if no entry (monopoly)
        monopoly_price = self.market_size / 2
        monopoly_profit = (monopoly_price - 1) * incumbent_q

        # Entry deterrence: incumbent may over-invest in capacity
        deterrence_capacity = self.market_size * 0.8  # Threaten to flood market

        return {
            'entrant_profit': entrant_profit,
            'entrant_should_enter': entrant_profit > 0,
            'incumbent_post_entry_profit': incumbent_profit,
            'incumbent_monopoly_profit': monopoly_profit,
            'profit_loss_from_entry': monopoly_profit - incumbent_profit,
            'entry_deterrent_capacity': deterrence_capacity,
            'incumbent_should_deter': monopoly_profit - incumbent_profit > self.entry_cost,
            'recommendation': {
                'entrant': 'Enter' if entrant_profit > 0 else 'Avoid - market too crowded',
                'incumbent': 'Over-invest in capacity to deter' if monopoly_profit - incumbent_profit > self.entry_cost else 'Accommodate entry'
            }
        }
