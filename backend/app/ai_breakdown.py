import anthropic
import os
from typing import Dict
from . import models

class AIBreakDownService:
    """
    Generates human-readable fight analysis using Claud AI
    """

    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")

        self.client = anthropic.Anthropic(api_key=api_key)
        
    def generate_breakdown(self, fighter_a: models.Fighter, 
                            fighter_b: models.Fighter, prediction: Dict) -> str:
        """
        Generate an analyst-style fight breakdown.
        """

        # Build the context for Claude
        prompt = self._build_prompt(fighter_a, fighter_b, prediction)

        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=1000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return message.content[0].text
        
        except Exception as e:
            return f"Error generating breakdown: {str(e)}"
        
    def _build_prompt(self, fighter_a: models.Fighter, 
                        fighter_b: models.Fighter, prediction: Dict) -> str:
        """
        Build a detailed prompt for Claude with all relevant fight data.
        """

        deltas = prediction['deltas']
        stats_a = fighter_a.stats
        stats_b = fighter_b.stats

        prompt = f"""You are a professional UFC analyst. Generate a compelling fight breakdown for this matchup:

        **{fighter_a.name}** "{fighter_a.nickname or ''}" vs **{fighter_b.name}** "{fighter_b.nickname or ''}"

        **FIGHTER A: {fighter_a.name}**
        - Record: {fighter_a.wins}-{fighter_a.losses}-{fighter_a.draws}
        - Weight Class: {fighter_a.weight_class}
        - Height: {fighter_a.height_cm}cm | Reach: {fighter_a.reach_cm}cm
        - Stance: {fighter_a.stance}
        - Striking: {stats_a.sig_strikes_landed_per_min:.2f} SL/min, {stats_a.striking_accuracy:.0f}% accuracy, {stats_a.striking_defense:.0f}% defense
        - Grappling: {stats_a.takedown_avg_per_fight:.2f} TD/fight, {stats_a.takedown_accuracy:.0f}% TD accuracy, {stats_a.takedown_defense:.0f}% TD defense

        **FIGHTER B: {fighter_b.name}**
        - Record: {fighter_b.wins}-{fighter_b.losses}-{fighter_b.draws}
        - Weight Class: {fighter_b.weight_class}
        - Height: {fighter_b.height_cm}cm | Reach: {fighter_b.reach_cm}cm
        - Stance: {fighter_b.stance}
        - Striking: {stats_b.sig_strikes_landed_per_min:.2f} SL/min, {stats_b.striking_accuracy:.0f}% accuracy, {stats_b.striking_defense:.0f}% defense
        - Grappling: {stats_b.takedown_avg_per_fight:.2f} TD/fight, {stats_b.takedown_accuracy:.0f}% TD accuracy, {stats_b.takedown_defense:.0f}% TD defense

        **KEY STATISTICAL ADVANTAGES:**
        - Reach difference: {deltas['reach_diff_cm']:+.1f}cm (favors {fighter_a.name if deltas['reach_diff_cm'] > 0 else fighter_b.name})
        - Striking output: {deltas['striking_output_diff']:+.2f} SL/min (favors {fighter_a.name if deltas['striking_output_diff'] > 0 else fighter_b.name})
        - Striking defense: {deltas['striking_defense_diff']:+.1f}% (favors {fighter_a.name if deltas['striking_defense_diff'] > 0 else fighter_b.name})
        - Takedown offense: {deltas['takedown_offense_diff']:+.2f} TD/fight (favors {fighter_a.name if deltas['takedown_offense_diff'] > 0 else fighter_b.name})
        - Takedown defense: {deltas['takedown_defense_diff']:+.1f}% (favors {fighter_a.name if deltas['takedown_defense_diff'] > 0 else fighter_b.name})

        **MODEL PREDICTION:**
        - {fighter_a.name}: {prediction['fighter_a_win_probability']*100:.1f}% win probability
        - {fighter_b.name}: {prediction['fighter_b_win_probability']*100:.1f}% win probability
        - Confidence: {prediction['confidence']}

        Write a 250-300 word analyst breakdown covering:
        1. **Opening Hook**: Start with the most compelling narrative angle of this matchup
        2. **Key Advantages**: Highlight 2-3 critical statistical edges for each fighter
        3. **Win Conditions**: Explain how each fighter is most likely to win
        4. **X-Factors**: Mention stylistic elements, physical attributes, or intangibles that could swing the fight
        5. **Prediction Summary**: Brief conclusion that ties to the model's prediction

        Write in the style of a professional MMA analyst - authoritative, analytical, but engaging. Use specific stats to support your points. Avoid clichés."""

        return prompt

    def generate_quick_summary(self, fighter_a: models.Fighter, 
                                fighter_b: models.Fighter, prediction: Dict) -> Dict[str, str]:
        """
        Generate quick one-liner summaries for each fighters path to victory
        """

        deltas = prediction['deltas']

        # Determine fighter A's best path
        fighter_a_path = self._determine_win_path(deltas, is_fighter_a=True)
        fighter_b_path = self._determine_win_path(deltas, is_fighter_a=False)
    
        return {
            "fighter_a_win_condition": fighter_a_path,
            "fighter_b_win_condition": fighter_b_path
        }
    
    def _determine_win_path(self, deltas: Dict, is_fighter_a: bool) -> str:
        """ 
        Determine the most likely win condition based on statistical advantages.
        """

        multiplier = 1 if is_fighter_a else -1

        # Calculate advantage scores
        striking_advantage = (
        deltas['striking_output_diff'] + 
        deltas['striking_defense_diff'] * 0.5 +
        deltas['striking_accuracy_diff'] * 0.3
        ) * multiplier
    
        grappling_advantage = (
            deltas['takedown_offense_diff'] * 2 +
            deltas['takedown_defense_diff'] * 0.5
        ) * multiplier

        # Determine primary path to victory
        if grappling_advantage > 5:
            return "Control the fight with takedowns and top position"
        elif grappling_advantage < -5:
            return "Keep the fight standing and avoid the clinch"
        elif striking_advantage > 3:
            return "Pressure forward with volume striking and superior defense"
        elif striking_advantage < -3:
            return "Counter-strike and capitalize on defensive lapses"
        elif deltas['reach_diff_cm'] * multiplier > 7:
            return "Utilize reach advantage to control distance and pick shots"
        else:
            return "Mix striking and grappling to keep opponent guessing"