"""
Skill Check Events System
Provides random events with multiple skill check choices for the player
"""

import random
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from .character import Character
from .item import Item


@dataclass
class SkillCheckChoice:
    """Represents a single skill check option for an event"""
    description: str  # e.g., "Keep an eye out for the goblin. PERCEPTION DC 15"
    skill: str  # e.g., "Perception"
    dc: int  # Difficulty Class
    required_item: Optional[str] = None  # Item name that can help with this check
    item_bonus: int = 0  # Bonus to roll if item is present
    
    def format_description(self) -> str:
        """Format the choice description for display"""
        return f"{self.description} {self.skill.upper()} DC {self.dc}"


@dataclass 
class EventOutcome:
    """Represents the outcome of a skill check event"""
    success_message: str
    failure_message: str
    success_effects: Dict[str, Any]  # Effects applied on success
    failure_effects: Dict[str, Any]  # Effects applied on failure
    

class SkillCheckEvent:
    """A random event that requires skill checks with multiple choices"""
    
    def __init__(self, 
                 name: str,
                 description: str,
                 choices: List[SkillCheckChoice],
                 outcome: EventOutcome,
                 min_level: int = 1,
                 max_level: int = 5,
                 event_type: str = "encounter",
                 rarity_weight: float = 1.0):
        self.name = name
        self.description = description
        self.choices = choices
        self.outcome = outcome
        self.min_level = min_level
        self.max_level = max_level
        self.event_type = event_type
        self.rarity_weight = rarity_weight
        
    def scale_for_level(self, character_level: int) -> 'SkillCheckEvent':
        """Scale the event difficulty based on character level"""
        # Calculate scaling factor
        level_factor = max(0, character_level - 1) * 0.2  # 20% increase per level
        
        # Scale DCs and effects
        scaled_choices = []
        for choice in self.choices:
            scaled_dc = int(choice.dc * (1 + level_factor))
            scaled_choice = SkillCheckChoice(
                description=choice.description,
                skill=choice.skill,
                dc=scaled_dc,
                required_item=choice.required_item,
                item_bonus=choice.item_bonus
            )
            scaled_choices.append(scaled_choice)
            
        # Scale rewards/penalties
        scaled_success_effects = self._scale_effects(self.outcome.success_effects, 1 + level_factor)
        scaled_failure_effects = self._scale_effects(self.outcome.failure_effects, 1 + level_factor)
        
        scaled_outcome = EventOutcome(
            success_message=self.outcome.success_message,
            failure_message=self.outcome.failure_message,
            success_effects=scaled_success_effects,
            failure_effects=scaled_failure_effects
        )
        
        return SkillCheckEvent(
            name=self.name,
            description=self.description,
            choices=scaled_choices,
            outcome=scaled_outcome,
            min_level=self.min_level,
            max_level=self.max_level,
            event_type=self.event_type,
            rarity_weight=self.rarity_weight
        )
        
    def _scale_effects(self, effects: Dict[str, Any], scale_factor: float) -> Dict[str, Any]:
        """Scale numerical effects by the given factor"""
        scaled = effects.copy()
        
        # Scale specific effect types
        if "character_xp_gain" in scaled:
            scaled["character_xp_gain"] = int(scaled["character_xp_gain"] * scale_factor)
        if "character_xp_loss" in scaled:
            scaled["character_xp_loss"] = int(scaled["character_xp_loss"] * scale_factor)
        if "gold_gain" in scaled:
            scaled["gold_gain"] = int(scaled["gold_gain"] * scale_factor)
        if "gold_loss" in scaled:
            scaled["gold_loss"] = int(scaled["gold_loss"] * scale_factor)
        if "item_reward" in scaled and "value" in scaled["item_reward"]:
            scaled["item_reward"]["value"] = int(scaled["item_reward"]["value"] * scale_factor)
            
        return scaled
        
    def to_dict(self) -> dict:
        """Convert event to dictionary for serialization"""
        return {
            "name": self.name,
            "description": self.description,
            "choices": [
                {
                    "description": choice.description,
                    "skill": choice.skill,
                    "dc": choice.dc,
                    "required_item": choice.required_item,
                    "item_bonus": choice.item_bonus
                }
                for choice in self.choices
            ],
            "outcome": {
                "success_message": self.outcome.success_message,
                "failure_message": self.outcome.failure_message,
                "success_effects": self.outcome.success_effects,
                "failure_effects": self.outcome.failure_effects
            },
            "min_level": self.min_level,
            "max_level": self.max_level,
            "event_type": self.event_type,
            "rarity_weight": self.rarity_weight
        }


# Define all skill check events
SKILL_CHECK_EVENTS = [
    # Level 1-2 Events
    SkillCheckEvent(
        name="Goblin Thief",
        description="You encounter a goblin sneaking around outside your shop, eyeing your merchandise with greedy eyes.",
        choices=[
            SkillCheckChoice("Keep an eye out for the goblin.", "Perception", 15),
            SkillCheckChoice("Lay a trap for the goblin.", "Survival", 17, "Rope", 2),
            SkillCheckChoice("Try to follow the goblin without being seen.", "Stealth", 20)
        ],
        outcome=EventOutcome(
            success_message="The goblin runs away in panic, dropping a small pouch!",
            failure_message="The goblin manages to snatch something from your shop display!",
            success_effects={
                "character_xp_gain": 25,
                "gold_gain": 10,
                "item_reward": {"name": "Goblin Trinket", "quantity": 1, "value": 5}
            },
            failure_effects={
                "character_xp_gain": 5,
                "lose_random_item": True,
                "max_value": 30
            }
        ),
        min_level=1,
        max_level=3,
        rarity_weight=1.5
    ),
    
    SkillCheckEvent(
        name="Suspicious Customer",
        description="A hooded figure enters your shop and starts asking unusual questions about your suppliers and security measures.",
        choices=[
            SkillCheckChoice("Try to discern their true intentions.", "Insight", 14),
            SkillCheckChoice("Intimidate them into revealing their purpose.", "Intimidation", 16),
            SkillCheckChoice("Deceive them with false information.", "Deception", 15)
        ],
        outcome=EventOutcome(
            success_message="You successfully handle the situation, and they leave peacefully. You feel more experienced.",
            failure_message="The figure leaves abruptly, and later you notice some items are misplaced.",
            success_effects={
                "character_xp_gain": 30,
                "reputation_gain": 1
            },
            failure_effects={
                "character_xp_gain": 10,
                "reputation_loss": 1,
                "gold_loss": 20
            }
        ),
        min_level=1,
        max_level=3
    ),
    
    SkillCheckEvent(
        name="Street Performer",
        description="A talented street performer sets up outside your shop, drawing a crowd that blocks your entrance.",
        choices=[
            SkillCheckChoice("Politely ask them to move along.", "Persuasion", 13),
            SkillCheckChoice("Join in with your own performance.", "Performance", 15, "Musical Instrument", 3),
            SkillCheckChoice("Study their techniques.", "Investigation", 14)
        ],
        outcome=EventOutcome(
            success_message="The situation resolves favorably, and the crowd becomes interested in your shop!",
            failure_message="The crowd disperses, but not before blocking customers for most of the day.",
            success_effects={
                "character_xp_gain": 20,
                "gold_gain": 25,
                "customer_bonus": 2  # Extra customers for the day
            },
            failure_effects={
                "character_xp_gain": 5,
                "customer_penalty": 2  # Fewer customers for the day
            }
        ),
        min_level=1,
        max_level=2
    ),
    
    # Level 2-3 Events
    SkillCheckEvent(
        name="Magical Mishap",
        description="A novice wizard accidentally drops a glowing potion in your shop, and it begins to smoke ominously!",
        choices=[
            SkillCheckChoice("Quickly identify the potion.", "Arcana", 16),
            SkillCheckChoice("Use your medical knowledge to neutralize it.", "Medicine", 18, "Herbalist Kit", 3),
            SkillCheckChoice("Grab it and throw it outside.", "Athletics", 15)
        ],
        outcome=EventOutcome(
            success_message="You handle the magical emergency expertly! The grateful wizard rewards you.",
            failure_message="The potion explodes in a puff of colored smoke, leaving everything tinted purple for hours.",
            success_effects={
                "character_xp_gain": 40,
                "item_reward": {"name": "Minor Healing Potion", "quantity": 1, "value": 50}
            },
            failure_effects={
                "character_xp_gain": 15,
                "reputation_loss": 1,
                "shop_damage": 30  # Cost to clean/repair
            }
        ),
        min_level=2,
        max_level=4
    ),
    
    SkillCheckEvent(
        name="Noble's Request",
        description="A local noble enters your shop demanding a rare item you don't have in stock, growing increasingly impatient.",
        choices=[
            SkillCheckChoice("Convince them to accept an alternative.", "Persuasion", 17),
            SkillCheckChoice("Recall where you might find such an item.", "History", 16),
            SkillCheckChoice("Bluff about having one on order.", "Deception", 19)
        ],
        outcome=EventOutcome(
            success_message="The noble is satisfied with your solution and promises to spread word of your excellent service!",
            failure_message="The noble storms out, threatening to tell everyone about your 'inadequate' shop.",
            success_effects={
                "character_xp_gain": 50,
                "reputation_gain": 2,
                "gold_gain": 50
            },
            failure_effects={
                "character_xp_gain": 20,
                "reputation_loss": 2
            }
        ),
        min_level=2,
        max_level=4
    ),
    
    # Level 3-4 Events
    SkillCheckEvent(
        name="Guild Inspector",
        description="A merchant guild inspector arrives for a 'routine' inspection, but their demeanor suggests they're looking for violations.",
        choices=[
            SkillCheckChoice("Present your records confidently.", "Persuasion", 18),
            SkillCheckChoice("Notice what they're really after.", "Insight", 19),
            SkillCheckChoice("Discretely hide questionable items.", "Sleight of Hand", 20, "Concealing Cloak", 3)
        ],
        outcome=EventOutcome(
            success_message="The inspector finds everything in order and commends your professionalism!",
            failure_message="The inspector finds several 'violations' and issues a fine.",
            success_effects={
                "character_xp_gain": 60,
                "reputation_gain": 2,
                "guild_standing": 1
            },
            failure_effects={
                "character_xp_gain": 25,
                "gold_loss": 75,
                "reputation_loss": 1
            }
        ),
        min_level=3,
        max_level=5
    ),
    
    SkillCheckEvent(
        name="Rare Creature Sighting",
        description="A rare magical creature is spotted near your shop, and several people are trying to capture it!",
        choices=[
            SkillCheckChoice("Calm the creature with your knowledge.", "Animal Handling", 18),
            SkillCheckChoice("Track where it came from.", "Survival", 17),
            SkillCheckChoice("Study its magical properties.", "Arcana", 19)
        ],
        outcome=EventOutcome(
            success_message="Your expertise helps resolve the situation peacefully, earning you rare materials!",
            failure_message="The creature escapes, but not before causing chaos in the market square.",
            success_effects={
                "character_xp_gain": 70,
                "item_reward": {"name": "Magical Beast Scale", "quantity": 2, "value": 100}
            },
            failure_effects={
                "character_xp_gain": 30,
                "reputation_loss": 1,
                "gold_loss": 40
            }
        ),
        min_level=3,
        max_level=5
    ),
    
    # Level 4-5 Events
    SkillCheckEvent(
        name="Rival Shop Sabotage",
        description="You discover evidence that a rival shop owner is trying to sabotage your business through underhanded means!",
        choices=[
            SkillCheckChoice("Investigate their methods thoroughly.", "Investigation", 20),
            SkillCheckChoice("Confront them directly.", "Intimidation", 21),
            SkillCheckChoice("Set up counter-surveillance.", "Perception", 19, "Spyglass", 4)
        ],
        outcome=EventOutcome(
            success_message="You expose their schemes and they're forced to cease their activities and pay compensation!",
            failure_message="You can't prove anything, and their sabotage continues to hurt your business.",
            success_effects={
                "character_xp_gain": 100,
                "gold_gain": 150,
                "reputation_gain": 3
            },
            failure_effects={
                "character_xp_gain": 40,
                "gold_loss": 100,
                "reputation_loss": 2,
                "ongoing_penalty": {"type": "daily_gold_loss", "amount": 10, "duration": 3}
            }
        ),
        min_level=4,
        max_level=5
    ),
    
    SkillCheckEvent(
        name="Ancient Artifact",
        description="A customer brings in an ancient artifact they found, not knowing its true value or dangerous properties!",
        choices=[
            SkillCheckChoice("Decipher the ancient markings.", "History", 22),
            SkillCheckChoice("Detect its magical properties.", "Arcana", 21),
            SkillCheckChoice("Carefully examine its construction.", "Investigation", 20)
        ],
        outcome=EventOutcome(
            success_message="You successfully identify the artifact and safely handle it, gaining incredible knowledge!",
            failure_message="You trigger a minor curse while examining it, though you learn something in the process.",
            success_effects={
                "character_xp_gain": 150,
                "item_reward": {"name": "Ancient Tome Fragment", "quantity": 1, "value": 200},
                "skill_bonus": {"type": "permanent", "skill": "History", "bonus": 1}
            },
            failure_effects={
                "character_xp_gain": 60,
                "curse": {"type": "minor_curse", "effect": "disadvantage_on_skill", "skill": "Investigation", "duration": 2}
            }
        ),
        min_level=4,
        max_level=5,
        rarity_weight=0.5
    )
]


class SkillCheckEventManager:
    """Manages the triggering and resolution of skill check events"""
    
    def __init__(self, character: Character, game_manager):
        self.character = character
        self.game_manager = game_manager
        self.events = SKILL_CHECK_EVENTS
        self.active_event: Optional[SkillCheckEvent] = None
        self.pending_roll: Optional[Dict[str, Any]] = None
        
    def get_available_events(self) -> List[SkillCheckEvent]:
        """Get events appropriate for character's level"""
        return [
            event for event in self.events
            if event.min_level <= self.character.level <= event.max_level
        ]
        
    def trigger_random_event(self) -> Optional[Dict[str, Any]]:
        """Randomly trigger an event based on weights and return event data"""
        available_events = self.get_available_events()
        if not available_events:
            return None
            
        # Weight-based selection
        weights = [event.rarity_weight for event in available_events]
        selected_event = random.choices(available_events, weights=weights, k=1)[0]
        
        # Scale for character level
        scaled_event = selected_event.scale_for_level(self.character.level)
        self.active_event = scaled_event
        
        # Prepare event data for frontend
        event_data = {
            "name": scaled_event.name,
            "description": scaled_event.description,
            "choices": [
                {
                    "index": i,
                    "description": choice.format_description(),
                    "skill": choice.skill,
                    "dc": choice.dc,
                    "has_item_bonus": choice.required_item and any(
                        item.name == choice.required_item for item in self.character.inventory
                    ),
                    "item_bonus": choice.item_bonus if choice.required_item else 0
                }
                for i, choice in enumerate(scaled_event.choices)
            ]
        }
        
        # Add to journal
        if self.game_manager and hasattr(self.game_manager, 'add_journal_entry'):
            self.game_manager.add_journal_entry(
                action_type="Event Triggered",
                summary=f"Encountered: {scaled_event.name}",
                details={"event": scaled_event.description},
                outcome="Awaiting player choice..."
            )
            
        return event_data
        
    def prepare_skill_check(self, choice_index: int) -> Dict[str, Any]:
        """Prepare a skill check for the given choice"""
        if not self.active_event or choice_index >= len(self.active_event.choices):
            return {"error": "Invalid choice or no active event"}
            
        choice = self.active_event.choices[choice_index]
        
        # Check for item bonus
        has_item = False
        item_bonus = 0
        if choice.required_item:
            has_item = any(item.name == choice.required_item for item in self.character.inventory)
            if has_item:
                item_bonus = choice.item_bonus
                
        # Calculate modifier
        skill_modifier = self.character.get_attribute_score(choice.skill)
        
        # Store pending roll information
        self.pending_roll = {
            "choice_index": choice_index,
            "skill": choice.skill,
            "dc": choice.dc,
            "modifier": skill_modifier,
            "item_bonus": item_bonus,
            "has_item": has_item
        }
        
        return {
            "skill": choice.skill,
            "dc": choice.dc,
            "modifier": skill_modifier,
            "item_bonus": item_bonus,
            "total_modifier": skill_modifier + item_bonus
        }
        
    def resolve_skill_check(self, roll_result: int) -> Dict[str, Any]:
        """Resolve a skill check with the given roll result"""
        if not self.active_event or not self.pending_roll:
            return {"error": "No pending skill check to resolve"}
            
        # Calculate total
        total = roll_result + self.pending_roll["modifier"] + self.pending_roll["item_bonus"]
        success = total >= self.pending_roll["dc"]
        
        # Get outcome
        outcome = self.active_event.outcome
        message = outcome.success_message if success else outcome.failure_message
        effects = outcome.success_effects if success else outcome.failure_effects
        
        # Apply effects
        applied_effects = self._apply_effects(effects)
        
        # Log to journal
        if self.game_manager and hasattr(self.game_manager, 'add_journal_entry'):
            self.game_manager.add_journal_entry(
                action_type="Skill Check",
                summary=f"{self.active_event.name} - {'Success' if success else 'Failure'}",
                details={
                    "skill": self.pending_roll["skill"],
                    "roll": roll_result,
                    "modifier": self.pending_roll["modifier"],
                    "item_bonus": self.pending_roll["item_bonus"],
                    "total": total,
                    "dc": self.pending_roll["dc"],
                    "effects": applied_effects
                },
                outcome=message
            )
            
        # Clear active event and pending roll
        self.active_event = None
        self.pending_roll = None
        
        return {
            "success": success,
            "message": message,
            "roll": roll_result,
            "total": total,
            "dc": self.pending_roll["dc"] if self.pending_roll else 0,
            "effects": applied_effects
        }
        
    def _apply_effects(self, effects: Dict[str, Any]) -> Dict[str, Any]:
        """Apply the effects of an event outcome"""
        applied = {}
        
        # XP effects
        if "character_xp_gain" in effects:
            self.character.award_xp(effects["character_xp_gain"])
            applied["xp_gained"] = effects["character_xp_gain"]
        if "character_xp_loss" in effects:
            self.character.award_xp(-effects["character_xp_loss"])
            applied["xp_lost"] = effects["character_xp_loss"]
            
        # Gold effects
        if "gold_gain" in effects:
            self.character.gold += effects["gold_gain"]
            applied["gold_gained"] = effects["gold_gain"]
        if "gold_loss" in effects:
            amount = min(effects["gold_loss"], self.character.gold)
            self.character.gold -= amount
            applied["gold_lost"] = amount
            
        # Item rewards
        if "item_reward" in effects:
            item_data = effects["item_reward"]
            item = Item(
                name=item_data["name"],
                description=f"Obtained from {self.active_event.name}",
                base_value=item_data.get("value", 10),
                item_type="misc",
                quality="Common",
                quantity=item_data.get("quantity", 1)
            )
            self.character.add_item_to_inventory(item)
            applied["item_gained"] = item_data
            
        # Random item loss
        if "lose_random_item" in effects and effects["lose_random_item"]:
            max_value = effects.get("max_value", 100)
            eligible_items = [
                item for item in self.character.inventory 
                if item.base_value <= max_value and not item.is_magical
            ]
            if eligible_items:
                lost_item = random.choice(eligible_items)
                self.character.remove_specific_item_from_inventory(lost_item)
                applied["item_lost"] = lost_item.name
                
        # Reputation effects (if implemented)
        if "reputation_gain" in effects:
            applied["reputation_gained"] = effects["reputation_gain"]
        if "reputation_loss" in effects:
            applied["reputation_lost"] = effects["reputation_loss"]
            
        # Shop/customer effects (for game manager to handle)
        if "customer_bonus" in effects:
            applied["customer_bonus"] = effects["customer_bonus"]
        if "customer_penalty" in effects:
            applied["customer_penalty"] = effects["customer_penalty"]
        if "shop_damage" in effects:
            self.character.gold = max(0, self.character.gold - effects["shop_damage"])
            applied["shop_damage_cost"] = effects["shop_damage"]
            
        return applied