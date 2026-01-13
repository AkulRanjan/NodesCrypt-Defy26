"""
Rules Engine with DSL
Provides configurable detection rules with a simple JSON-based DSL.

Features:
- JSON rule format
- Priority-based evaluation
- Rule composition and chaining
- Audit logging of rule changes
"""
import json
import re
import hashlib
from typing import Dict, List, Optional, Callable
from datetime import datetime

class Rule:
    """A single detection rule."""
    
    def __init__(self, rule_dict: dict):
        self.id = rule_dict.get("id", "unknown")
        self.priority = rule_dict.get("priority", 50)
        self.condition = rule_dict.get("condition", "")
        self.action = rule_dict.get("action", "FLAG")
        self.risk_score = rule_dict.get("risk_score", 0.5)
        self.enabled = rule_dict.get("enabled", True)
        self.meta = rule_dict.get("meta", {})
        self.created_at = rule_dict.get("created_at", datetime.utcnow().isoformat())
        
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "priority": self.priority,
            "condition": self.condition,
            "action": self.action,
            "risk_score": self.risk_score,
            "enabled": self.enabled,
            "meta": self.meta,
            "created_at": self.created_at
        }


class RuleEvaluator:
    """Evaluates rule conditions against transaction context."""
    
    def __init__(self):
        self.operators = {
            "==": lambda a, b: a == b,
            "!=": lambda a, b: a != b,
            ">": lambda a, b: float(a) > float(b),
            "<": lambda a, b: float(a) < float(b),
            ">=": lambda a, b: float(a) >= float(b),
            "<=": lambda a, b: float(a) <= float(b),
            "in": lambda a, b: a.lower() in [x.lower() for x in b] if isinstance(b, list) else a.lower() in b.lower(),
            "contains": lambda a, b: b.lower() in a.lower() if isinstance(a, str) else False,
            "startswith": lambda a, b: a.lower().startswith(b.lower()) if isinstance(a, str) else False,
        }
        
    def evaluate(self, condition: str, context: dict) -> bool:
        """
        Evaluate a condition against a context.
        
        Condition format: "field operator value [AND|OR field operator value ...]"
        Examples:
            "to in blacklist"
            "value > 10000"
            "spam_score >= 0.8 AND is_blacklisted == true"
        """
        try:
            # Handle AND/OR logic
            if " AND " in condition:
                parts = condition.split(" AND ")
                return all(self._evaluate_single(p.strip(), context) for p in parts)
            elif " OR " in condition:
                parts = condition.split(" OR ")
                return any(self._evaluate_single(p.strip(), context) for p in parts)
            else:
                return self._evaluate_single(condition, context)
        except Exception as e:
            return False
    
    def _evaluate_single(self, condition: str, context: dict) -> bool:
        """Evaluate a single condition clause."""
        # Parse condition
        for op_str, op_func in sorted(self.operators.items(), key=lambda x: -len(x[0])):
            if f" {op_str} " in condition:
                parts = condition.split(f" {op_str} ", 1)
                if len(parts) == 2:
                    field = parts[0].strip()
                    value_str = parts[1].strip()
                    
                    # Get field value from context
                    field_value = self._get_field_value(field, context)
                    
                    # Parse comparison value
                    if value_str.lower() == "true":
                        compare_value = True
                    elif value_str.lower() == "false":
                        compare_value = False
                    elif value_str == "blacklist":
                        compare_value = context.get("blacklist", set())
                    elif value_str == "whitelist":
                        compare_value = context.get("whitelist", set())
                    else:
                        try:
                            compare_value = float(value_str)
                        except:
                            compare_value = value_str
                    
                    return op_func(field_value, compare_value)
        
        return False
    
    def _get_field_value(self, field: str, context: dict):
        """Get field value from nested context."""
        parts = field.split(".")
        value = context
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return None
        return value


class RulesEngine:
    """
    Main rules engine.
    Manages rules and evaluates them against transactions.
    """
    
    def __init__(self):
        self.rules: List[Rule] = []
        self.evaluator = RuleEvaluator()
        self.audit_log: List[dict] = []
        self._load_default_rules()
        
    def _load_default_rules(self):
        """Load default security rules."""
        default_rules = [
            {
                "id": "block_blacklisted",
                "priority": 100,
                "condition": "is_blacklisted == true",
                "action": "BLOCK",
                "risk_score": 1.0,
                "meta": {"reason": "Address is blacklisted", "category": "blacklist"}
            },
            {
                "id": "high_spam_score",
                "priority": 90,
                "condition": "spam_score >= 0.9",
                "action": "DEPRIORITIZE",
                "risk_score": 0.9,
                "meta": {"reason": "Very high spam score", "category": "spam"}
            },
            {
                "id": "suspicious_approval",
                "priority": 85,
                "condition": "has_approval == true AND value > 0",
                "action": "FLAG",
                "risk_score": 0.7,
                "meta": {"reason": "Suspicious approval with value transfer", "category": "exploit"}
            },
            {
                "id": "large_value_unknown",
                "priority": 80,
                "condition": "value > 100000000000000000000 AND reputation_score < 0.3",
                "action": "FLAG",
                "risk_score": 0.6,
                "meta": {"reason": "Large value from low reputation address", "category": "risk"}
            },
            {
                "id": "whitelisted_pass",
                "priority": 200,
                "condition": "is_whitelisted == true",
                "action": "ALLOW",
                "risk_score": 0.0,
                "meta": {"reason": "Address is whitelisted", "category": "whitelist"}
            }
        ]
        
        for rule_dict in default_rules:
            self.rules.append(Rule(rule_dict))
        
        # Sort by priority (higher first)
        self.rules.sort(key=lambda r: -r.priority)
    
    def add_rule(self, rule_dict: dict, author: str = "system") -> Rule:
        """Add a new rule."""
        rule = Rule(rule_dict)
        self.rules.append(rule)
        self.rules.sort(key=lambda r: -r.priority)
        
        # Audit log
        self.audit_log.append({
            "action": "ADD_RULE",
            "rule_id": rule.id,
            "author": author,
            "timestamp": datetime.utcnow().isoformat(),
            "rule_hash": self._hash_rule(rule)
        })
        
        return rule
    
    def remove_rule(self, rule_id: str, author: str = "system") -> bool:
        """Remove a rule by ID."""
        for i, rule in enumerate(self.rules):
            if rule.id == rule_id:
                removed = self.rules.pop(i)
                
                # Audit log
                self.audit_log.append({
                    "action": "REMOVE_RULE",
                    "rule_id": rule_id,
                    "author": author,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                return True
        return False
    
    def evaluate(self, context: dict) -> Optional[dict]:
        """
        Evaluate all rules against a context.
        Returns the first matching rule result, or None if no rules match.
        """
        for rule in self.rules:
            if not rule.enabled:
                continue
                
            if self.evaluator.evaluate(rule.condition, context):
                return {
                    "rule_id": rule.id,
                    "action": rule.action,
                    "risk_score": rule.risk_score,
                    "reason": rule.meta.get("reason", "Rule matched"),
                    "category": rule.meta.get("category", "unknown"),
                    "priority": rule.priority
                }
        
        return None
    
    def evaluate_all(self, context: dict) -> List[dict]:
        """Evaluate all rules and return all matches."""
        matches = []
        for rule in self.rules:
            if not rule.enabled:
                continue
            if self.evaluator.evaluate(rule.condition, context):
                matches.append({
                    "rule_id": rule.id,
                    "action": rule.action,
                    "risk_score": rule.risk_score,
                    "reason": rule.meta.get("reason", ""),
                    "priority": rule.priority
                })
        return matches
    
    def _hash_rule(self, rule: Rule) -> str:
        """Generate hash of rule for audit."""
        data = json.dumps(rule.to_dict(), sort_keys=True)
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def get_rules(self) -> List[dict]:
        """Get all rules as dicts."""
        return [r.to_dict() for r in self.rules]
    
    def export_rules(self) -> str:
        """Export rules as JSON."""
        return json.dumps(self.get_rules(), indent=2)
    
    def import_rules(self, rules_json: str, author: str = "import"):
        """Import rules from JSON."""
        rules_data = json.loads(rules_json)
        for rule_dict in rules_data:
            self.add_rule(rule_dict, author)


# Singleton instance
_engine = None

def get_engine() -> RulesEngine:
    global _engine
    if _engine is None:
        _engine = RulesEngine()
    return _engine

def evaluate_rules(context: dict) -> Optional[dict]:
    """Convenience function for rule evaluation."""
    return get_engine().evaluate(context)


if __name__ == "__main__":
    print("=" * 60)
    print("[RULES ENGINE] DSL Test")
    print("=" * 60)
    
    engine = RulesEngine()
    
    # Test contexts
    test_contexts = [
        {
            "name": "Blacklisted sender",
            "is_blacklisted": True,
            "spam_score": 0.5,
            "value": 1000
        },
        {
            "name": "High spam score",
            "is_blacklisted": False,
            "spam_score": 0.95,
            "value": 100
        },
        {
            "name": "Whitelisted address",
            "is_whitelisted": True,
            "spam_score": 0.1,
            "value": 10000
        },
        {
            "name": "Normal transaction",
            "is_blacklisted": False,
            "is_whitelisted": False,
            "spam_score": 0.2,
            "value": 500
        }
    ]
    
    for ctx in test_contexts:
        name = ctx.pop("name")
        result = engine.evaluate(ctx)
        print(f"\n{name}:")
        if result:
            print(f"  Rule: {result['rule_id']}")
            print(f"  Action: {result['action']}")
            print(f"  Risk: {result['risk_score']}")
            print(f"  Reason: {result['reason']}")
        else:
            print("  No rules matched")
    
    print(f"\n--- Rules Summary ---")
    print(f"Total rules: {len(engine.rules)}")
    print(f"Audit log entries: {len(engine.audit_log)}")
