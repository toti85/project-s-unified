#!/usr/bin/env python3
"""
AI Evaluation Module
Evaluates prompt drafts based on predefined criteria.
"""

import json
import os
import hashlib
from datetime import datetime
from pathlib import Path

# Evaluation criteria scoring
EVALUATION_CRITERIA = {
    "clarity": {
        "description": "Prompt is unambiguous and clearly stated",
        "weight": 0.25,
        "checks": [
            "prompt contains explicit task definition",
            "output format is specified",
            "constraints are documented"
        ]
    },
    "specificity": {
        "description": "Prompt provides specific guidance and parameters",
        "weight": 0.25,
        "checks": [
            "success criteria are defined",
            "parameters are explicitly listed",
            "quality metrics are quantified"
        ]
    },
    "safety_alignment": {
        "description": "Prompt enforces safe, ethical behavior",
        "weight": 0.20,
        "checks": [
            "safety level is declared",
            "guidelines are provided",
            "limitations are acknowledged"
        ]
    },
    "format_compliance": {
        "description": "Prompt follows JSON schema and naming conventions",
        "weight": 0.15,
        "checks": [
            "JSON is valid",
            "required fields present",
            "naming conventions respected"
        ]
    },
    "reproducibility": {
        "description": "Prompt is deterministic and reproducible",
        "weight": 0.15,
        "checks": [
            "prompt contains version info",
            "parameters are well-defined",
            "output format is consistent"
        ]
    }
}

def compute_hash(content):
    """Compute SHA-256 hash of content."""
    return hashlib.sha256(content.encode()).hexdigest()[:16]

def evaluate_prompt(draft_file):
    """Evaluate a single prompt draft."""
    try:
        with open(draft_file, 'r') as f:
            draft = json.load(f)
        
        evaluation = {
            "draft_id": draft.get("draft_id", "UNKNOWN"),
            "file": os.path.basename(draft_file),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "format_valid": True,
            "criteria_scores": {},
            "overall_score": 0.0,
            "issues": [],
            "recommendations": []
        }
        
        # Format check
        required_fields = ["draft_id", "domain", "prompt", "parameters", "success_criteria", "safety_level"]
        missing = [f for f in required_fields if f not in draft]
        if missing:
            evaluation["format_valid"] = False
            evaluation["issues"].append(f"Missing fields: {', '.join(missing)}")
        
        # Criterion scoring
        for criterion, details in EVALUATION_CRITERIA.items():
            score = 0.0
            passed_checks = 0
            for check in details["checks"]:
                if _check_criterion(criterion, check, draft):
                    passed_checks += 1
            score = (passed_checks / len(details["checks"])) * 100
            evaluation["criteria_scores"][criterion] = round(score, 2)
        
        # Overall score (weighted average)
        overall = sum(
            evaluation["criteria_scores"].get(crit, 0) * EVALUATION_CRITERIA[crit]["weight"]
            for crit in EVALUATION_CRITERIA
        )
        evaluation["overall_score"] = round(overall, 2)
        
        # Pass/fail determination
        evaluation["status"] = "PASS" if evaluation["overall_score"] >= 70 else "FAIL"
        
        # Recommendations
        if evaluation["overall_score"] < 70:
            evaluation["recommendations"].append("Revise prompt to meet minimum quality threshold (70/100)")
        if "prompt" in draft and len(draft["prompt"]) < 100:
            evaluation["recommendations"].append("Expand prompt description for clarity")
        
        return evaluation
    
    except Exception as e:
        return {
            "file": os.path.basename(draft_file),
            "status": "ERROR",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

def _check_criterion(criterion, check, draft):
    """Helper to check if a criterion is met."""
    if criterion == "clarity":
        if check == "prompt contains explicit task definition":
            return "prompt" in draft and len(draft.get("prompt", "")) > 50
        elif check == "output format is specified":
            return "prompt" in draft and ("format" in draft.get("prompt", "").lower() or "output" in draft.get("prompt", "").lower())
        elif check == "constraints are documented":
            return "parameters" in draft
    
    elif criterion == "specificity":
        if check == "success criteria are defined":
            return "success_criteria" in draft and len(draft.get("success_criteria", [])) > 0
        elif check == "parameters are explicitly listed":
            return "parameters" in draft and len(draft.get("parameters", {})) > 0
        elif check == "quality metrics are quantified":
            return any("score" in str(draft).lower() or "metric" in str(draft).lower() for _ in [1])
    
    elif criterion == "safety_alignment":
        if check == "safety level is declared":
            return "safety_level" in draft
        elif check == "guidelines are provided":
            return "prompt" in draft and any(word in draft.get("prompt", "").lower() for word in ["require", "must", "should", "constraint"])
        elif check == "limitations are acknowledged":
            return "notes" in draft or "limitations" in draft.get("prompt", "").lower()
    
    elif criterion == "format_compliance":
        if check == "JSON is valid":
            return True  # Already parsed successfully
        elif check == "required fields present":
            return all(field in draft for field in ["draft_id", "domain", "prompt"])
        elif check == "naming conventions respected":
            return "draft_id" in draft and "_" in draft.get("draft_id", "")
    
    elif criterion == "reproducibility":
        if check == "prompt contains version info":
            return "version" in draft or "created_at" in draft
        elif check == "parameters are well-defined":
            return "parameters" in draft and len(draft.get("parameters", {})) > 0
        elif check == "output format is consistent":
            return "prompt" in draft and ("format" in draft.get("prompt", "").lower() or "output" in draft.get("prompt", "").lower())
    
    return False

def run_evaluation(draft_dir, output_dir):
    """Evaluate all drafts in directory."""
    draft_files = sorted(Path(draft_dir).glob("*.json"))
    
    results = {
        "evaluation_timestamp": datetime.utcnow().isoformat() + "Z",
        "total_drafts": len(draft_files),
        "evaluations": [],
        "summary": {
            "passed": 0,
            "failed": 0,
            "errors": 0,
            "average_score": 0.0
        }
    }
    
    scores = []
    
    for draft_file in draft_files:
        evaluation = evaluate_prompt(str(draft_file))
        results["evaluations"].append(evaluation)
        
        if evaluation.get("status") == "PASS":
            results["summary"]["passed"] += 1
        elif evaluation.get("status") == "FAIL":
            results["summary"]["failed"] += 1
        elif evaluation.get("status") == "ERROR":
            results["summary"]["errors"] += 1
        
        if "overall_score" in evaluation:
            scores.append(evaluation["overall_score"])
    
    if scores:
        results["summary"]["average_score"] = round(sum(scores) / len(scores), 2)
    
    # Write evaluation results
    output_file = os.path.join(output_dir, "evaluation_results.json")
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    return results

if __name__ == "__main__":
    draft_dir = r"C:\ProjectS-Unified\orchestrator_runtime\sandbox\prompt_drafts"
    eval_dir = r"C:\ProjectS-Unified\orchestrator_runtime\sandbox\evaluation_results"
    output_dir = r"C:\ProjectS-Unified\orchestrator_runtime\sandbox\output"
    
    os.makedirs(eval_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    
    results = run_evaluation(draft_dir, eval_dir)
    
    # Print summary
    print("\n=== EVALUATION SUMMARY ===")
    print(f"Total drafts: {results['total_drafts']}")
    print(f"Passed: {results['summary']['passed']}")
    print(f"Failed: {results['summary']['failed']}")
    print(f"Average score: {results['summary']['average_score']}/100")
    print(f"\nResults saved to: {eval_dir}")
