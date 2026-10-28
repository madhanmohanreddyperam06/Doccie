"""Mock LLM Provider for deterministic offline testing and verification."""

import json
import logging
from typing import Optional

from app.llm.base import LLMProvider

logger = logging.getLogger(__name__)


class MockLLMProvider(LLMProvider):
    """Deterministic, high-quality Mock LLM provider for unit tests and offline demos."""

    def generate(self, prompt: str, system: Optional[str] = None) -> str:
        """Inspect prompt keywords and return contextual, structured output."""
        lower_prompt = prompt.lower()

        # 1. Planner request: returns a structured JSON plan with tasks and assumptions
        if "planning agent" in lower_prompt or "autonomous planner" in lower_prompt or "creating plan for request" in lower_prompt:
            if "helpdesk" in lower_prompt or "college" in lower_prompt:
                return json.dumps({
                    "document_type": "Implementation Plan",
                    "title": "College AI Student Helpdesk Implementation Proposal",
                    "objective": "Design and deploy a scalable, budget-conscious AI-powered student helpdesk within a three-month timeline.",
                    "assumptions": [
                        "The college provides existing academic FAQs, admission guidelines, and hostel manuals in digital format.",
                        "Initial deployment will use an on-premise or cloud-hosted open-source LLM to keep recurring API costs minimal.",
                        "Initial release will support English with Phase 2 adding regional languages.",
                        "Implementation team comprises one senior engineer, one part-time systems admin, and two student interns.",
                        "System will be deployed in a lightweight containerized environment."
                    ],
                    "tasks": [
                        {
                            "id": 1,
                            "name": "Analyze college requirements and constraints",
                            "type": "analysis",
                            "description": "Assess academic, admission, hostel, and technical support scope alongside the 3-month timeline and budget limits.",
                            "status": "pending"
                        },
                        {
                            "id": 2,
                            "name": "Formulate strategic system assumptions",
                            "type": "assumptions",
                            "description": "Document architectural, staffing, and budget assumptions to resolve missing specifications.",
                            "status": "pending"
                        },
                        {
                            "id": 3,
                            "name": "Define document architecture and sections",
                            "type": "structure",
                            "description": "Establish a professional document layout covering executive summary, architecture, 3-month roadmap, and budget.",
                            "status": "pending"
                        },
                        {
                            "id": 4,
                            "name": "Generate core implementation content",
                            "type": "content",
                            "description": "Draft in-depth technical design, phased deployment milestones, and operational workflows.",
                            "status": "pending"
                        },
                        {
                            "id": 5,
                            "name": "Synthesize recommendations and risk mitigation",
                            "type": "recommendations",
                            "description": "Outline actionable recommendations for sustainability, data privacy, and student adoption.",
                            "status": "pending"
                        },
                        {
                            "id": 6,
                            "name": "Perform quality and completeness check",
                            "type": "validation",
                            "description": "Verify coverage of all college domains and ensure all budget constraints are addressed.",
                            "status": "pending"
                        }
                    ]
                })
            else:
                # Default / Chatbot proposal plan
                return json.dumps({
                    "document_type": "Project Proposal",
                    "title": "AI Customer Support Chatbot Implementation Proposal",
                    "objective": "Deliver an intelligent, 24/7 automated customer support chatbot to increase resolution rates and reduce operational support costs.",
                    "assumptions": [
                        "The organization maintains an existing searchable customer support knowledge base and ticketing system.",
                        "Initial launch focuses on web chat widget with CRM integration.",
                        "The platform will support English at launch, with multi-lingual support in subsequent releases.",
                        "Target initial containment rate is 65% for tier-1 repetitive inquiries."
                    ],
                    "tasks": [
                        {
                            "id": 1,
                            "name": "Analyze business objectives and user needs",
                            "type": "analysis",
                            "description": "Evaluate current support ticket volume, pain points, and customer satisfaction targets.",
                            "status": "pending"
                        },
                        {
                            "id": 2,
                            "name": "Establish baseline assumptions and scope",
                            "type": "assumptions",
                            "description": "Record foundational operational assumptions and project boundaries.",
                            "status": "pending"
                        },
                        {
                            "id": 3,
                            "name": "Design document outline and section hierarchy",
                            "type": "structure",
                            "description": "Structure sections from Executive Summary to Solution Architecture, Implementation Roadmap, and ROI.",
                            "status": "pending"
                        },
                        {
                            "id": 4,
                            "name": "Generate detailed technical and operational content",
                            "type": "content",
                            "description": "Produce thorough narrative, system architecture details, and SLA metrics.",
                            "status": "pending"
                        },
                        {
                            "id": 5,
                            "name": "Compile strategic recommendations and next steps",
                            "type": "recommendations",
                            "description": "Provide governance, change management, and phased rollout guidelines.",
                            "status": "pending"
                        },
                        {
                            "id": 6,
                            "name": "Validate document completeness and clarity",
                            "type": "validation",
                            "description": "Review consistency between objectives, scope, and technical deliverables.",
                            "status": "pending"
                        }
                    ]
                })

        # 2. Reflection request
        if "reflection" in lower_prompt or "self-check" in lower_prompt or "evaluate" in lower_prompt:
            # Check if this is an intentionally failing prompt or check for missing timeline
            if "must fail" in lower_prompt:
                return json.dumps({
                    "passed": False,
                    "score": 6,
                    "issues": ["Implementation timeline lacks specific phase deliverables."],
                    "improvements": ["Add a detailed 3-phase delivery schedule."]
                })
            return json.dumps({
                "passed": True,
                "score": 9,
                "issues": [],
                "improvements": ["Consider including post-launch SLA monitoring metrics."]
            })

        # 3. Requirement Analyzer Tool output
        if ("enterprise business analyst" in lower_prompt or "formulate structured requirements" in lower_prompt) and "publication-grade" not in lower_prompt:
            return json.dumps({
                "core_requirements": [
                    "Automated 24/7 query handling and resolution",
                    "Seamless escalation to human agents for complex issues",
                    "Integration with existing organizational knowledge repositories",
                    "Audit logging and conversational analytics reporting"
                ],
                "technical_constraints": [
                    "Scalable low-latency response times (< 1.5s)",
                    "Data privacy and student/customer confidentiality compliance",
                    "Budget-conscious infrastructure deployment"
                ],
                "target_audience": "End users, institutional stakeholders, and system administrators"
            })

        # 4. Document Structure Tool output
        if ("senior document architect" in lower_prompt or "design the optimal section structure" in lower_prompt or "optimal section structure" in lower_prompt) and "publication-grade" not in lower_prompt:
            return json.dumps({
                "sections": [
                    {
                        "heading": "1. Operational Scope & Service Pillars",
                        "level": 1,
                        "description": "Comprehensive scope of services and coverage.",
                        "includes_table": True,
                        "includes_bullets": True
                    },
                    {
                        "heading": "2. Proposed System Architecture",
                        "level": 1,
                        "description": "Technical design, model integration, and workflows.",
                        "includes_table": False,
                        "includes_bullets": True
                    },
                    {
                        "heading": "3. Phased Implementation Roadmap",
                        "level": 1,
                        "description": "Chronological milestones and deliverables.",
                        "includes_table": True,
                        "includes_bullets": True
                    },
                    {
                        "heading": "4. Budget Breakdown & Cost Analysis",
                        "level": 1,
                        "description": "Cost items, infrastructure, and resource requirements.",
                        "includes_table": True,
                        "includes_bullets": False
                    }
                ]
            })

        # 5. Content Generator Tool output
        if "principal technical author" in lower_prompt or "publication-grade" in lower_prompt or "rich, publication-grade" in lower_prompt or "content generator" in lower_prompt:

            if "college" in lower_prompt or "student helpdesk" in lower_prompt:
                return json.dumps({
                    "title": "College AI Student Helpdesk Implementation Proposal",
                    "document_type": "Implementation Plan",
                    "subtitle": "A Pragmatic, Budget-Conscious 3-Month Implementation Strategy",
                    "executive_summary": "This proposal outlines an autonomous, scalable AI-driven student helpdesk for higher education institutions. Designed specifically to launch within three months under disciplined budget constraints, the platform consolidates academic FAQs, admission procedures, hostel regulations, and essential technical support into an intuitive 24/7 conversational interface. By combining open-source local LLM inference with modern vector search, the college achieves institutional data sovereignty, immediate student responsiveness, and low operating costs.",
                    "assumptions": [
                        "Institutional knowledge bases (academic calendar, hostel guidelines, admission forms) are accessible in digital formats (PDF/DOCX/HTML).",
                        "On-premise hardware or low-cost cloud instances will be utilized to avoid recurring per-token commercial API costs.",
                        "Initial launch focuses on English-language interactions, with regional multi-language capability scheduled for Phase 2.",
                        "A dedicated internal project team (one faculty lead, one engineer, and two student technical assistants) drives the rollout."
                    ],
                    "sections": [
                        {
                            "heading": "1. Project Scope & Core Service Pillars",
                            "level": 1,
                            "content": "The AI Student Helpdesk addresses the primary query domains that overburden administrative and academic departments during peak semesters. The system is partitioned into four functional pillars to ensure dedicated coverage and straightforward knowledge updating.",
                            "bullets": [
                                "Academic FAQs: Course schedules, examination guidelines, grading criteria, and credit transfer procedures.",
                                "Admissions: Program eligibility, application timelines, required document checklists, and fee payment instructions.",
                                "Hostel & Facilities: Room allocation guidelines, mess timings, curfew policies, and campus maintenance ticketing.",
                                "Basic Technical Support: WiFi network onboarding, student portal password resets, and LMS troubleshooting."
                            ],
                            "numbered": [],
                            "table_headers": ["Service Pillar", "Target Resolution Time", "Knowledge Source", "Escalation Route"],
                            "table_rows": [
                                ["Academic Inquiries", "< 2 seconds", "College Academic Handbook", "Department Academic Advisors"],
                                ["Admission Support", "< 2 seconds", "Admissions Prospectus 2026", "Central Admissions Office"],
                                ["Hostel Affairs", "< 2 seconds", "Hostel Rules & Mess Charter", "Warden & Facilities Desk"],
                                ["IT & Campus Tech", "< 3 seconds", "IT Knowledge Base & FAQs", "College IT Helpdesk Ticket"]
                            ]
                        },
                        {
                            "heading": "2. High-Level Technical Architecture",
                            "level": 1,
                            "content": "To strictly adhere to budgetary limits while providing responsive student experiences, the architecture utilizes a Retrieval-Augmented Generation (RAG) framework powered by local or private cloud LLM inference.",
                            "bullets": [
                                "Ingestion Layer: Automated parser extracting text chunks from campus documents and indexing them into a vector repository.",
                                "Retrieval Layer: Semantic similarity search returning top-ranked relevant context snippets in under 200ms.",
                                "Generation Layer: Compact, instruction-tuned LLM producing grounded, safe answers strictly from verified institutional sources.",
                                "Client Layer: Responsive mobile-first web widget integrated directly into the student intranet and portal."
                            ],
                            "numbered": [],
                            "table_headers": [],
                            "table_rows": []
                        },
                        {
                            "heading": "3. Three-Month Implementation Roadmap",
                            "level": 1,
                            "content": "A disciplined 12-week schedule divided into three concentrated 4-week phases ensures on-time campus delivery before the upcoming semester commences.",
                            "bullets": [],
                            "numbered": [
                                "Phase 1 (Weeks 1-4): Requirements gathering, institutional data curation, vector indexing pipeline setup, and model evaluation.",
                                "Phase 2 (Weeks 5-8): System integration, student portal web widget development, guardrail implementation, and administrative dashboard.",
                                "Phase 3 (Weeks 9-12): Pilot testing with 200 student beta users, feedback refinement, staff training, and full campus launch."
                            ],
                            "table_headers": ["Milestone", "Timeline", "Key Deliverables", "Status Gate"],
                            "table_rows": [
                                ["Foundation & Setup", "Weeks 1 - 4", "Data repository curated, vector index constructed", "Data Accuracy > 95%"],
                                ["Integration & UI", "Weeks 5 - 8", "Web widget, API gateway, admin dashboard", "Response Latency < 1.5s"],
                                ["Pilot & Launch", "Weeks 9 - 12", "Student beta trial, feedback triage, production launch", "Student CSAT > 85%"]
                            ]
                        },
                        {
                            "heading": "4. Budget Breakdown & Cost Analysis",
                            "level": 1,
                            "content": "By leveraging open-source technologies and internal college resources, capital and operating expenditures are reduced by over 80% compared to proprietary commercial customer support suites.",
                            "bullets": [],
                            "numbered": [],
                            "table_headers": ["Cost Item", "Estimated Cost ($)", "Notes & Cost Saving Strategy"],
                            "table_rows": [
                                ["Compute Infrastructure", "$350 / month", "Single cloud GPU / CPU instance running quantized model"],
                                ["Vector Database", "$0 (Open Source)", "Locally embedded vector store (ChromaDB / Faiss)"],
                                ["Software & Licensing", "$0 (Open Source)", "FastAPI, Python, open-source RAG stack"],
                                ["Student Intern Stipends", "$1,200 total", "Two student development assistants (10 hrs/week)"],
                                ["Contingency & Reserves", "$500 total", "Buffer for cloud bandwidth and domain certifications"]
                            ]
                        }
                    ],
                    "recommendations": [
                        "Establish a bi-weekly institutional content review committee to keep FAQs current.",
                        "Implement automated fallback alerts when confidence scores fall below threshold.",
                        "Collect anonymous student query feedback thumbs up/down to continuously train the retriever."
                    ],
                    "conclusion": "The proposed AI Student Helpdesk delivers an innovative, affordable, and high-impact digital transformation for the college. With a disciplined three-month execution roadmap and minimal recurring overhead, the institution will achieve substantial administrative efficiency while dramatically improving student satisfaction."
                })
            else:
                return json.dumps({
                    "title": "AI Customer Support Chatbot Implementation Proposal",
                    "document_type": "Project Proposal",
                    "subtitle": "Transforming Customer Experience Through Intelligent Automation",
                    "executive_summary": "This proposal presents a comprehensive engineering and operational roadmap to deploy an enterprise-grade AI customer support chatbot. Designed to resolve up to 70% of tier-1 inquiries autonomously, the solution accelerates inquiry resolution, eliminates customer wait times, and empowers human support agents to focus on complex, high-value customer interactions.",
                    "assumptions": [
                        "The company has an existing digital repository of support knowledge base articles, refund policies, and user manuals.",
                        "Initial rollout will interface directly with the web e-commerce storefront.",
                        "All customer interactions will be logged securely in compliance with standard consumer privacy standards.",
                        "Human agent escalation protocols will be supported via webhooks into the existing ticketing platform."
                    ],
                    "sections": [
                        {
                            "heading": "1. Business Case & Expected Impact",
                            "level": 1,
                            "content": "Modern customer support demands instantaneous, 24/7 responsiveness. By introducing an intelligent conversational agent, the business captures immediate operational gains across resolution speed, customer satisfaction, and support cost containment.",
                            "bullets": [
                                "Resolution Speed: Average first-response time dropped from 18 minutes to under 2 seconds.",
                                "Cost Efficiency: Cost-per-ticket reduced by an estimated 55% over a 12-month period.",
                                "Agent Satisfaction: Routine inquiries handled automatically, eliminating agent burnout.",
                                "Omnichannel Readiness: Architecture designed for subsequent WhatsApp and mobile app expansion."
                            ],
                            "numbered": [],
                            "table_headers": ["Performance Metric", "Current Baseline", "Target with AI Chatbot", "Projected Improvement"],
                            "table_rows": [
                                ["First Response Time", "18 minutes", "< 2 seconds", "99% faster"],
                                ["Tier-1 Autonomous Resolution", "0%", "65% - 70%", "Complete tier-1 coverage"],
                                ["Customer CSAT Score", "3.6 / 5.0", "4.5 / 5.0", "+25% increase"],
                                ["24/7 Availability", "Limited / Business Hours", "Uninterrupted 24/7", "Continuous availability"]
                            ]
                        },
                        {
                            "heading": "2. System Architecture & Conversational Flow",
                            "level": 1,
                            "content": "The architecture incorporates state-of-the-art semantic search paired with guarded LLM response generation to ensure grounded, hallucination-free assistance.",
                            "bullets": [
                                "Dialogue Management: Contextual session tracking preserving user intent across multi-turn queries.",
                                "Knowledge Grounding: Real-time RAG context retrieval ensuring answers reflect current policies.",
                                "Guardrails & Safety: Automated input sanitization and PII redaction filters protecting customer data.",
                                "Agent Handoff: Seamless ticket generation and contextual history handover when human intervention is required."
                            ],
                            "numbered": [],
                            "table_headers": [],
                            "table_rows": []
                        },
                        {
                            "heading": "3. Phased Implementation Roadmap",
                            "level": 1,
                            "content": "The implementation spans four structured phases across 10 weeks, ensuring thorough testing, telemetry verification, and agent training prior to public launch.",
                            "bullets": [],
                            "numbered": [
                                "Sprint 1-2: Architecture design, knowledge base audit, and API integration specifications.",
                                "Sprint 3-5: Conversational agent training, RAG pipeline setup, and custom web chat UI integration.",
                                "Sprint 6-7: Internal testing, security audit, safety guardrail calibration, and support team training.",
                                "Sprint 8-10: Staged public rollout (20% traffic ramping to 100%), real-time analytics monitoring, and hypercare."
                            ],
                            "table_headers": ["Phase", "Duration", "Core Milestones", "Success Criteria"],
                            "table_rows": [
                                ["Discovery & Prep", "2 Weeks", "Knowledge base export, API contracts", "Data coverage sign-off"],
                                ["Core Build", "3 Weeks", "RAG pipeline, chat widget, webhook triggers", "Retrieval accuracy > 90%"],
                                ["Testing & Guardrails", "2 Weeks", "Safety testing, red-teaming, agent training", "Zero safety violations"],
                                ["Deployment & Scale", "3 Weeks", "Gradual traffic rollout, telemetry monitoring", "CSAT > 4.2 in pilot group"]
                            ]
                        }
                    ],
                    "recommendations": [
                        "Prioritize weekly retraining of the knowledge base based on unresolved customer queries.",
                        "Establish clear human escalation pathways for sensitive billing and cancellation requests.",
                        "Track customer sentiment trends via continuous dashboard analytics."
                    ],
                    "conclusion": "Implementing this autonomous AI customer support solution positions the organization at the forefront of digital customer experience. With rapid deployment, measurable ROI, and enhanced operational scalability, the initiative delivers substantial long-term value."
                })

        # Fallback generic text
        return "Task completed successfully with all required details."
