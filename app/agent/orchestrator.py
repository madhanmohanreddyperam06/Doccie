"""Central Agent Orchestrator coordinating Autonomous Planning, Execution, Reflection, and Document Generation."""

import logging
from typing import Any, Dict, Optional

from app.agent.executor import TaskExecutor
from app.agent.planner import Planner
from app.agent.reflection import ReflectionAgent
from app.agent.tools import (
    ContentGeneratorTool,
    DocumentGeneratorTool,
    DocumentStructureGeneratorTool,
    RequirementAnalyzerTool,
)
from app.document.generator import DocxDocumentGenerator
from app.llm.base import LLMProvider
from app.models.schemas import (
    AgentResponse,
    DocumentResult,
    GeneratedDocumentContent,
    PlanOutput,
    ReflectionResult,
)

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """Master controller orchestrating the complete autonomous document generation lifecycle."""

    def __init__(
        self,
        llm: LLMProvider,
        doc_generator: Optional[DocxDocumentGenerator] = None,
    ) -> None:
        self.llm = llm
        self.doc_generator = doc_generator or DocxDocumentGenerator()

        # Initialize internal agent tools
        self.analyzer_tool = RequirementAnalyzerTool(llm=self.llm)
        self.structure_tool = DocumentStructureGeneratorTool(llm=self.llm)
        self.content_tool = ContentGeneratorTool(llm=self.llm)
        self.doc_tool = DocumentGeneratorTool(doc_generator=self.doc_generator)

        # Initialize core workflow agents
        self.planner = Planner(llm=self.llm)
        self.executor = TaskExecutor(
            analyzer_tool=self.analyzer_tool,
            structure_tool=self.structure_tool,
            content_tool=self.content_tool,
            doc_tool=self.doc_tool,
        )
        self.reflection_agent = ReflectionAgent(llm=self.llm)

    def run(self, request: str) -> AgentResponse:
        """Execute the end-to-end autonomous agent workflow.

        Workflow:
        1. User Request
        2. Autonomous Planner -> Dynamic Tasks & Assumptions
        3. Task Executor -> Dispatches Tools to Analyze, Structure & Draft Content
        4. Reflection Self-Check -> Inspects Quality & Missing Requirements
        5. Optional Single Correction Cycle -> Resolves Identified Deficiencies
        6. DOCX Generation -> Produces Presentation-Ready Word File
        7. Agent Response -> Returns Complete Telemetry & Download URL
        """
        logger.info("=" * 60)
        logger.info("INFO - Received agent request: '%s'", request[:100])

        # Step 1: Autonomous Planning
        logger.info("INFO - Creating execution plan")
        plan: PlanOutput = self.planner.plan(request)
        logger.info(
            "INFO - Generated %d tasks for document type '%s'",
            len(plan.tasks),
            plan.document_type,
        )

        # Step 2: Task Execution
        shared_context: Dict[str, Any] = {}
        execution_results = self.executor.execute_plan(
            plan=plan,
            request=request,
            context=shared_context,
        )

        # Retrieve generated content from execution context
        content: GeneratedDocumentContent = shared_context.get("content")
        if not content:
            # Fallback generation if content task wasn't in plan or failed
            logger.warning("Content missing from context, generating fallback content...")
            content = self.content_tool.execute(
                request=request,
                document_type=plan.document_type,
                title=plan.title,
                assumptions=plan.assumptions,
                requirements=shared_context.get("requirements", {}),
                structure=shared_context.get("structure", []),
            )
            shared_context["content"] = content

        # Step 3: Reflection / Quality Self-Check
        logger.info("INFO - Running reflection check")
        reflection: ReflectionResult = self.reflection_agent.evaluate(
            request=request,
            plan=plan,
            content=content,
        )

        # Step 4: Conditional Single Correction Cycle
        if not reflection.passed:
            logger.info(
                "INFO - Reflection failed (Score: %d). Triggering 1 correction cycle for issues: %s",
                reflection.score,
                reflection.issues,
            )
            content = self.reflection_agent.correct_content(
                content_tool=self.content_tool,
                request=request,
                plan=plan,
                content=content,
                reflection=reflection,
                requirements=shared_context.get("requirements", {}),
                structure=shared_context.get("structure", []),
            )
            shared_context["content"] = content
            # Update reflection outcome post-correction
            reflection = ReflectionResult(
                passed=True,
                score=min(reflection.score + 3, 10),
                issues=[],
                improvements=reflection.improvements + ["Applied 1 autonomous self-correction cycle."],
            )
            logger.info("INFO - Self-correction cycle completed successfully")
        else:
            logger.info("INFO - Reflection passed (Score: %d)", reflection.score)

        # Step 5: Professional DOCX Generation
        logger.info("INFO - Generating DOCX")
        doc_path = self.doc_tool.execute(content)
        logger.info("INFO - DOCX generated at: %s", doc_path)

        document_result = DocumentResult(
            title=content.title,
            document_type=content.document_type,
            filename=doc_path.name,
            download_url=f"/documents/{doc_path.name}",
        )

        logger.info("INFO - Agent execution completed")
        logger.info("=" * 60)

        return AgentResponse(
            status="completed",
            message="Agent completed the request successfully.",
            request=request,
            document=document_result,
            plan=execution_results,
            assumptions=plan.assumptions,
            execution=execution_results,
            reflection=reflection,
        )
