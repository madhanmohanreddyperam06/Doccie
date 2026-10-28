"""Reflection and Self-Check Module for Autonomous AI Document Agent.

Evaluates generated document content against:
1. Original user request
2. Autonomous task execution plan
3. Document type specifications
4. Formulated assumptions

Executes a single correction cycle if validation does not pass.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from app.agent.tools import ContentGeneratorTool
from app.llm.base import LLMProvider
from app.models.schemas import (
    GeneratedDocumentContent,
    PlanOutput,
    ReflectionResult,
)

logger = logging.getLogger(__name__)


class ReflectionAgent:
    """Evaluates document quality and orchestrates self-correction."""

    def __init__(self, llm: LLMProvider) -> None:
        self.llm = llm

    def evaluate(
        self,
        request: str,
        plan: PlanOutput,
        content: GeneratedDocumentContent,
    ) -> ReflectionResult:
        """Inspect generated content and return structured quality assessment."""
        logger.info("Running reflection self-check on generated content...")

        # Prepare summary of document content for review
        content_summary = {
            "title": content.title,
            "document_type": content.document_type,
            "executive_summary_present": bool(content.executive_summary),
            "assumptions_count": len(content.assumptions),
            "sections": [
                {
                    "heading": s.heading,
                    "has_narrative": bool(s.content),
                    "bullet_count": len(s.bullets),
                    "numbered_count": len(s.numbered),
                    "has_table": bool(s.table_headers and s.table_rows),
                }
                for s in content.sections
            ],
            "recommendations_count": len(content.recommendations),
            "conclusion_present": bool(content.conclusion),
        }

        prompt = f"""You are a principal quality assurance auditor and executive editor.
Evaluate this autonomously generated document against the user's original request and execution plan.

Original User Request:
"{request}"

Planned Document Type: {plan.document_type}
Planned Tasks: {len(plan.tasks)} tasks planned

Document Structure Summary:
{json.dumps(content_summary, indent=2)}

Evaluation Criteria:
1. Does the document directly satisfy the user's primary request?
2. Are all core service pillars / requirements addressed?
3. Are the sections properly developed with concrete details, tables, or lists (not placeholders)?
4. Is there an Executive Summary, clear Assumptions, Recommendations, and Conclusion?

Scoring Guide:
- Score 8-10: Excellent, meets or exceeds all requirements (passed: true).
- Score 1-7: Needs improvements or missing critical sections (passed: false).

CRITICAL: Return ONLY a valid JSON object matching this schema:
{{
  "passed": true,
  "score": 9,
  "issues": [],
  "improvements": []
}}
"""
        schema_desc = '{"passed": bool, "score": int, "issues": list[str], "improvements": list[str]}'

        try:
            data = self.llm.generate_json(prompt, schema_description=schema_desc)
            if isinstance(data, dict):
                score = int(data.get("score", 9))
                passed = bool(data.get("passed", score >= 7))
                issues = [str(i) for i in data.get("issues", [])]
                improvements = [str(imp) for imp in data.get("improvements", [])]

                # Enforce consistency: if score < 7 or has issues, mark passed = False
                if score < 7 and not issues:
                    issues.append("Document requires deeper operational detail.")
                if issues and passed:
                    passed = False

                logger.info("Reflection completed: passed=%s, score=%d", passed, score)
                return ReflectionResult(
                    passed=passed,
                    score=score,
                    issues=issues,
                    improvements=improvements,
                )
        except Exception as err:
            logger.warning("Reflection LLM parse error: %s. Using standard heuristic evaluation.", err)

        # Heuristic fallback check
        return self._heuristic_evaluate(request, content)

    def _heuristic_evaluate(
        self, request: str, content: GeneratedDocumentContent
    ) -> ReflectionResult:
        """Heuristic fallback evaluation based on structural completeness."""
        issues: List[str] = []
        improvements: List[str] = []
        score = 9

        if not content.executive_summary or len(content.executive_summary) < 50:
            issues.append("Executive summary is too brief or missing.")
            improvements.append("Expand executive summary with strategic context.")
            score -= 2

        if len(content.sections) < 2:
            issues.append("Document has fewer than two developed sections.")
            improvements.append("Add structured technical and roadmap sections.")
            score -= 2

        has_table = any(s.table_headers and s.table_rows for s in content.sections)
        if not has_table:
            improvements.append("Include at least one structured metrics or timeline table.")
            score -= 1

        passed = len(issues) == 0 and score >= 7
        return ReflectionResult(
            passed=passed,
            score=max(score, 1),
            issues=issues,
            improvements=improvements,
        )

    def correct_content(
        self,
        content_tool: ContentGeneratorTool,
        request: str,
        plan: PlanOutput,
        content: GeneratedDocumentContent,
        reflection: ReflectionResult,
        requirements: Dict[str, Any],
        structure: List[Dict[str, Any]],
    ) -> GeneratedDocumentContent:
        """Execute one targeted correction cycle to resolve identified issues."""
        logger.info(
            "Executing 1 correction cycle for issues: %s",
            reflection.issues,
        )
        corrected = content_tool.execute(
            request=request,
            document_type=plan.document_type,
            title=plan.title,
            assumptions=plan.assumptions,
            requirements=requirements,
            structure=structure,
            correction_feedback={
                "passed": False,
                "issues": reflection.issues,
                "improvements": reflection.improvements,
            },
        )
        logger.info("Correction cycle completed successfully.")
        return corrected
