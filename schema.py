RE_RANK_SCHEMA = {
  "type": "object",
  "properties": {
    "results": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "_id": {
            "type": ["string", "object"],
            "description": "Document ID"
          },
          "ranking_score": {
            "type": "integer",
            "minimum": 0,
            "maximum": 100,
            "description": "Score 0-100"
          },
          "detailed_reason_for_ranking": {
            "type": "string",
            "description": "Explanation for score"
          }
        },
        "required": ["_id", "ranking_score", "detailed_reason_for_ranking"],
        "additionalProperties": False
      }
    }
  },
  "required": ["results"],
  "additionalProperties": False
}

ENHANCED_RE_RANK_SCHEMA = {
    "type": "object",
    "properties": {
        "results": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "_id": {
                        "type": ["string", "object"],
                        "description": "Document ID"
                    },
                    "ranking_score": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 100,
                        "description": "Score 0-100"
                    },
                    "hard_constraints_passed": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of hard constraints that passed"
                    },
                    "hard_constraints_failed": {
                        "type": "array", 
                        "items": {"type": "string"},
                        "description": "List of hard constraints that failed"
                    },
                    "detailed_reason_for_ranking": {
                        "type": "string",
                        "description": "Explanation for score including constraint verification"
                    }
                },
                "required": ["_id", "ranking_score", "hard_constraints_passed", "hard_constraints_failed", "detailed_reason_for_ranking"],
                "additionalProperties": False
            }
        }
    },
    "required": ["results"],
    "additionalProperties": False
}
