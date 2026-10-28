"""Tool definitions for Autonomous AI Document Agent.

Provides modular internal tools for:
- Tool 1: Requirement Analyzer
- Tool 2: Document Structure Generator
- Tool 3: Content Generator
- Tool 4: Document Generator (DOCX)
"""

import abc
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.document.generator import DocxDocumentGenerator
from app.llm.base import LLMProvider
from app.models.schemas import DocumentSection, GeneratedDocumentContent

logger = logging.getLogger(__name__)


class BaseTool(abc.ABC):
    """Abstract base class for all agent tools."""

    name: str
    description: str

    @abc.abstractmethod
    def execute(self, **kwargs: Any) -> Any:
        """Execute the tool with given arguments."""
        raise NotImplementedError


class RequirementAnalyzerTool(BaseTool):
    """Tool 1: Analyzes user request and extracts structured business and functional requirements."""

    name = "requirement_analyzer"
    description = "Analyzes natural-language requests to extract functional requirements, scope, constraints, and target audience."

    def __init__(self, llm: LLMProvider) -> None:
        self.llm = llm

    def execute(self, request: str, assumptions: Optional[List[str]] = None) -> Dict[str, Any]:
        """Analyze request and return structured requirements dictionary."""
        logger.info("Executing RequirementAnalyzerTool for request...")
        assumptions_text = "\n".join(f"- {a}" for a in (assumptions or []))

        prompt = f"""You are an expert enterprise business analyst.
Analyze the following user request and formulate structured requirements for a professional document.

User Request:
"{request}"

Assumptions Made:
{assumptions_text if assumptions_text else "None explicitly specified yet."}

Return a valid JSON object with:
{{
  "core_requirements": ["string", "string"],
  "technical_constraints": ["string", "string"],
  "scope_boundaries": ["string", "string"],
  "target_audience": "string"
}}
"""
        schema_desc = '{"core_requirements": list, "technical_constraints": list, "scope_boundaries": list, "target_audience": str}'
        try:
            result = self.llm.generate_json(prompt, schema_description=schema_desc)
            if isinstance(result, dict):
                return result
            return {"core_requirements": [str(result)], "technical_constraints": [], "target_audience": "Stakeholders"}
        except Exception as e:
            logger.warning("RequirementAnalyzerTool JSON fallback: %s", e)
            return {
                "core_requirements": [request],
                "technical_constraints": ["Ensure fast, budget-conscious delivery"],
                "scope_boundaries": ["Deliver complete initial release"],
                "target_audience": "Project Stakeholders"
            }


class DocumentStructureGeneratorTool(BaseTool):
    """Tool 2: Recommends document sections and layout tailored to document type and requirements."""

    name = "document_structure_generator"
    description = "Designs an optimal section structure for the target document type based on requirements."

    def __init__(self, llm: LLMProvider) -> None:
        self.llm = llm

    def execute(
        self,
        document_type: str,
        requirements: Dict[str, Any],
        title: str,
    ) -> List[Dict[str, Any]]:
        """Determine appropriate sections and layout hierarchy."""
        logger.info("Executing DocumentStructureGeneratorTool for document type: %s", document_type)
        req_json = json.dumps(requirements, indent=2)

        prompt = f"""You are a senior document architect.
Design the optimal section structure for a "{document_type}" titled "{title}".

Requirements Analysis:
{req_json}

Return a valid JSON object with a "sections" array:
{{
  "sections": [
    {{
      "heading": "Section Heading",
      "level": 1,
      "description": "Short explanation of what this section covers",
      "includes_table": true or false,
      "includes_bullets": true or false
    }}
  ]
}}
"""
        schema_desc = '{"sections": [{"heading": str, "level": int, "description": str, "includes_table": bool, "includes_bullets": bool}]}'
        try:
            result = self.llm.generate_json(prompt, schema_description=schema_desc)
            if isinstance(result, dict) and "sections" in result:
                return result["sections"]
            elif isinstance(result, list):
                return result
        except Exception as e:
            logger.warning("DocumentStructureGeneratorTool fallback: %s", e)

        # Fallback standard professional structure
        return [
            {"heading": "1. Project Scope & Service Pillars", "level": 1, "includes_table": True, "includes_bullets": True},
            {"heading": "2. High-Level Technical Architecture", "level": 1, "includes_table": False, "includes_bullets": True},
            {"heading": "3. Phased Implementation Roadmap", "level": 1, "includes_table": True, "includes_bullets": False},
            {"heading": "4. Budget Breakdown & Resource Plan", "level": 1, "includes_table": True, "includes_bullets": False},
        ]


class ContentGeneratorTool(BaseTool):
    """Tool 3: Generates comprehensive, professional document content with narrative, lists, and tables."""

    name = "content_generator"
    description = "Generates complete, publication-grade document content including tables, bullet lists, and narrative."

    def __init__(self, llm: LLMProvider) -> None:
        self.llm = llm

    def execute(
        self,
        request: str,
        document_type: str,
        title: str,
        assumptions: List[str],
        requirements: Dict[str, Any],
        structure: List[Dict[str, Any]],
        correction_feedback: Optional[Dict[str, Any]] = None,
    ) -> GeneratedDocumentContent:
        """Produce full GeneratedDocumentContent."""
        logger.info("Executing ContentGeneratorTool for '%s'...", title)

        correction_text = ""
        if correction_feedback and not correction_feedback.get("passed", True):
            issues = "\n".join(f"- {iss}" for iss in correction_feedback.get("issues", []))
            improvements = "\n".join(f"- {imp}" for imp in correction_feedback.get("improvements", []))
            correction_text = f"""
CORRECTION CYCLE REQUIRED:
A quality check identified the following missing requirements or gaps:
Issues:
{issues}
Required Improvements:
{improvements}
You MUST integrate these missing components directly into the content!
"""

        prompt = f"""You are a principal technical author and executive consultant.
Generate rich, publication-grade content for a {document_type} titled "{title}".

Original User Request:
"{request}"

Assumptions Made:
{json.dumps(assumptions, indent=2)}

Requirements:
{json.dumps(requirements, indent=2)}

Planned Section Structure:
{json.dumps(structure, indent=2)}
{correction_text}

Instructions:
1. Executive Summary: 1-2 thorough, articulate paragraphs.
2. Sections: For each planned section, generate:
   - "heading": section title
   - "level": 1
   - "content": 1-2 detailed, professional paragraphs
   - "bullets": list of 3-4 key points or sub-items (or empty list)
   - "numbered": list of 3-4 chronological steps if applicable (or empty list)
   - "table_headers": 3-4 column titles if this section has tabular data (e.g. milestones, cost, SLAs)
   - "table_rows": 2-4 rows of data matching the headers
3. Recommendations: 3-4 strategic, actionable recommendations.
4. Conclusion: A decisive concluding summary.

Return a valid JSON object matching this structure:
{{
  "title": "{title}",
  "document_type": "{document_type}",
  "subtitle": "Subtitle text",
  "executive_summary": "Thorough executive summary...",
  "assumptions": {json.dumps(assumptions)},
  "sections": [
    {{
      "heading": "Heading Name",
      "level": 1,
      "content": "Paragraph content...",
      "bullets": ["point 1", "point 2"],
      "numbered": [],
      "table_headers": ["Col 1", "Col 2", "Col 3"],
      "table_rows": [["val 1", "val 2", "val 3"], ["val 4", "val 5", "val 6"]]
    }}
  ],
  "recommendations": ["rec 1", "rec 2"],
  "conclusion": "Final concluding remarks..."
}}
"""
        schema_desc = """{
  "title": str, "document_type": str, "subtitle": str, "executive_summary": str,
  "assumptions": list[str], "sections": [{"heading": str, "level": int, "content": str, "bullets": list[str], "numbered": list[str], "table_headers": list[str], "table_rows": list[list[str]]}],
  "recommendations": list[str], "conclusion": str
}"""

        try:
            data = self.llm.generate_json(prompt, schema_description=schema_desc)
            if isinstance(data, dict):
                # Ensure all required fields exist
                return GeneratedDocumentContent(
                    title=data.get("title", title),
                    document_type=data.get("document_type", document_type),
                    subtitle=data.get("subtitle", f"Strategic {document_type}"),
                    executive_summary=data.get("executive_summary", "Executive summary of the proposal."),
                    assumptions=data.get("assumptions", assumptions),
                    sections=[
                        DocumentSection(
                            heading=sec.get("heading", f"Section {i+1}"),
                            level=sec.get("level", 1),
                            content=sec.get("content", ""),
                            bullets=sec.get("bullets", []),
                            numbered=sec.get("numbered", []),
                            table_headers=sec.get("table_headers", []),
                            table_rows=sec.get("table_rows", []),
                        )
                        for i, sec in enumerate(data.get("sections", []))
                    ],
                    recommendations=data.get("recommendations", [
                        "Prioritize stakeholder alignment and bi-weekly milestone reviews.",
                        "Establish continuous monitoring metrics to validate ROI."
                    ]),
                    conclusion=data.get("conclusion", "This initiative delivers significant efficiency gains.")
                )
        except Exception as e:
            logger.error("ContentGeneratorTool failed to parse output: %s", e)

        # Fallback content if generation failed
        return GeneratedDocumentContent(
            title=title,
            document_type=document_type,
            subtitle=f"Prepared for: {request[:50]}",
            executive_summary=f"This document articulates the strategic proposal for {request}. It establishes operational baselines and execution priorities.",
            assumptions=assumptions,
            sections=[
                DocumentSection(
                    heading="1. Operational Requirements & Scope",
                    level=1,
                    content="The project addresses core requirements identified during initial discovery.",
                    bullets=[f"Primary goal: {request}", "Low operating latency", "Secure data privacy controls"],
                    table_headers=["Component", "Target", "Owner"],
                    table_rows=[["Core Module", "Phase 1 Delivery", "Technical Lead"], ["Quality Gate", "Zero Critical Defects", "QA"]]
                )
            ],
            recommendations=["Initiate sprint planning immediately."],
            conclusion="Execution should commence in accordance with the established plan."
        )


class DocumentGeneratorTool(BaseTool):
    """Tool 4: Formats and produces the final Microsoft Word .docx file."""

    name = "document_generator"
    description = "Renders structured content into a polished, presentation-ready Word (.docx) document."

    def __init__(self, doc_generator: Optional[DocxDocumentGenerator] = None) -> None:
        self.doc_generator = doc_generator or DocxDocumentGenerator()

    def execute(self, content: GeneratedDocumentContent) -> Path:
        """Generate and save the .docx file."""
        logger.info("Executing DocumentGeneratorTool to create Word document...")
        return self.doc_generator.generate(content)
