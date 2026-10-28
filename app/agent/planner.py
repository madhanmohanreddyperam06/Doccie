"""Autonomous Planner for AI Document Agent.

Independently analyzes natural-language requests to determine:
1. User intent and objective
2. Document type and title
3. Missing information and strategic assumptions
4. Ordered list of execution tasks
"""

import json
import logging
from typing import Any, Dict, List

from app.llm.base import LLMProvider
from app.models.schemas import PlanOutput, TaskDefinition

logger = logging.getLogger(__name__)


class Planner:
    """Autonomous planner that creates a custom execution TODO plan from user request."""

    def __init__(self, llm: LLMProvider) -> None:
        self.llm = llm

    def plan(self, request: str) -> PlanOutput:
        """Create an autonomous task execution plan for the given user request.

        Dynamically determines document type, assumptions, and ordered task sequence.
        """
        logger.info("Autonomous Planner creating plan for request: '%s'", request[:80])

        prompt = f"""You are an autonomous AI planning agent and software architect.
A user has submitted the following document creation request:

"{request}"

Your responsibilities:
1. Determine the exact type of document to produce (e.g. "Project Proposal", "Implementation Plan", "Technical Design Document", "Business Case", "Meeting Minutes", etc.).
2. Generate an authoritative, professional title.
3. Define the core objective.
4. Detect missing, underspecified, or ambiguous details and formulate 3-5 reasonable, realistic ASSUMPTIONS so execution proceeds without needing to halt or ask the user.
5. Create an ordered sequence of 4-7 specific tasks needed to research, structure, generate, and validate the document.
   Each task must have:
   - "id": sequential integer starting from 1
   - "name": concise task title
   - "type": category matching one of ["analysis", "assumptions", "structure", "content", "recommendations", "validation"]
   - "description": clear explanation of what the task accomplishes
   - "status": "pending"

CRITICAL: Return ONLY a valid JSON object matching this schema:
{{
  "document_type": "string",
  "title": "string",
  "objective": "string",
  "assumptions": [
    "string"
  ],
  "tasks": [
    {{
      "id": 1,
      "name": "string",
      "type": "analysis",
      "description": "string",
      "status": "pending"
    }}
  ]
}}
"""
        schema_desc = """{
  "document_type": str,
  "title": str,
  "objective": str,
  "assumptions": list[str],
  "tasks": [{"id": int, "name": str, "type": str, "description": str, "status": "pending"}]
}"""

        try:
            data = self.llm.generate_json(prompt, schema_description=schema_desc)
            if isinstance(data, dict):
                plan_output = PlanOutput(
                    document_type=data.get("document_type", "Project Proposal"),
                    title=data.get("title", "Strategic Document"),
                    objective=data.get("objective", f"Deliver document for: {request}"),
                    assumptions=data.get("assumptions", [
                        "Standard organizational infrastructure is available.",
                        "Initial release will support English with phased expansion."
                    ]),
                    tasks=[
                        TaskDefinition(
                            id=t.get("id", i + 1),
                            name=t.get("name", f"Task {i + 1}"),
                            type=t.get("type", "content"),
                            description=t.get("description", "Execute task."),
                            status="pending",
                        )
                        for i, t in enumerate(data.get("tasks", []))
                    ],
                )
                if plan_output.tasks:
                    logger.info(
                        "Planner generated %d tasks for document type '%s'",
                        len(plan_output.tasks),
                        plan_output.document_type,
                    )
                    return plan_output

        except Exception as err:
            logger.warning("Planner LLM generation error: %s. Constructing contextual plan.", err)

        # Fallback contextual plan if LLM did not return proper schema
        return self._create_contextual_fallback_plan(request)

    def _create_contextual_fallback_plan(self, request: str) -> PlanOutput:
        """Create a contextual plan based on request semantics if LLM parsing failed."""
        lower = request.lower()
        if "college" in lower or "student" in lower or "helpdesk" in lower:
            doc_type = "Implementation Plan"
            title = "College AI Student Helpdesk Implementation Proposal"
            assumptions = [
                "The college has existing digital documents for academic FAQs, admissions, and hostels.",
                "System will leverage open-source models to respect strict budget limitations.",
                "Initial rollout targets a 3-month launch with an English-first interface.",
                "Technical team comprises one lead engineer and two student interns."
            ]
        elif "report" in lower:
            doc_type = "Business Report"
            title = "Comprehensive Business Intelligence Report"
            assumptions = ["Historical data is available for comparative analysis."]
        else:
            doc_type = "Project Proposal"
            title = "AI Solution Implementation Proposal"
            assumptions = [
                "Target stakeholders have authorized preliminary discovery.",
                "Deployment will occur in phased milestones across 10-12 weeks."
            ]

        tasks = [
            TaskDefinition(
                id=1,
                name="Analyze user requirements and constraints",
                type="analysis",
                description="Extract business drivers, audience, and functional boundaries.",
                status="pending",
            ),
            TaskDefinition(
                id=2,
                name="Formulate baseline operational assumptions",
                type="assumptions",
                description="Establish explicit assumptions to resolve ambiguous parameters.",
                status="pending",
            ),
            TaskDefinition(
                id=3,
                name="Design document architecture and sections",
                type="structure",
                description="Determine section hierarchy, data tables, and bullet frameworks.",
                status="pending",
            ),
            TaskDefinition(
                id=4,
                name="Generate comprehensive section content",
                type="content",
                description="Produce in-depth narrative, specifications, and data tables.",
                status="pending",
            ),
            TaskDefinition(
                id=5,
                name="Synthesize strategic recommendations",
                type="recommendations",
                description="Draft actionable governance and adoption guidelines.",
                status="pending",
            ),
            TaskDefinition(
                id=6,
                name="Validate completeness and quality",
                type="validation",
                description="Verify full alignment with original request and assumptions.",
                status="pending",
            ),
        ]

        return PlanOutput(
            document_type=doc_type,
            title=title,
            objective=f"Develop a complete {doc_type} addressing: {request}",
            assumptions=assumptions,
            tasks=tasks,
        )
