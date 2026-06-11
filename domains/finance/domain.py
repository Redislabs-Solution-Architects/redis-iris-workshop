from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Sequence

from backend.app.services.memory_service import MemoryService
from backend.app.core.domain_contract import (
    BrandingConfig,
    DomainManifest,
    GeneratedDataset,
    GuardrailConfig,
    GuardrailRouteConfig,
    IdentityConfig,
    InternalToolDefinition,
    NamespaceConfig,
    PromptCard,
    RagConfig,
    SeedLangCacheEntry,
    SeedMemory,
    ThemeConfig,
)
from backend.app.core.domain_schema import EntitySpec
from backend.app.redis_connection import create_redis_client
from domains.finance.data_generator import generate_demo_data
from domains.finance.prompt import build_system_prompt
from domains.finance.schema import ENTITY_SPECS

ROOT = Path(__file__).resolve().parents[2]


class FinanceResearcherDomain:
    manifest = DomainManifest(
        id="finance",
        description=(
            "Finance research demo domain for watchlist analysis across filings, earnings materials, "
            "metrics, prices, and normalized update events."
        ),
        generated_models_module="domains.finance.generated_models",
        generated_models_path="domains/finance/generated_models.py",
        output_dir="output/finance",
        branding=BrandingConfig(
            app_name="ShiftIQ",
            subtitle="Market shifts, made clear.",
            hero_title="Finance Research Assistant",
            placeholder_text="Compare companies, documents, metrics, or recent events...",
            logo_path="domains/finance/assets/logo.svg",
            demo_steps=[
                "Compare the latest gross profit trends for NVIDIA, AMD, and Broadcom",
                "Remember that I focus on semiconductor stocks and prefer quarterly earnings data",
                "Click Memory",
                "Given what you know about my research focus, what should I look at next across my watchlist?",
            ],
            starter_prompts=[
                PromptCard(
                    eyebrow="Context",
                    title="Walk me through Oracle",
                    prompt="Walk me through Oracle's latest quarter using both the filing and the structured metrics.",
                ),
                PromptCard(
                    eyebrow="Memory",
                    title="Save research preferences",
                    prompt="Please remember that I prefer visual comparisons with charts when analyzing multi-company trends.",
                ),
                PromptCard(
                    eyebrow="Memory",
                    title="Coverage and preferences",
                    prompt="What is my semiconductor coverage and analysis preferences?",
                ),
                PromptCard(
                    eyebrow="Cached",
                    title="Gross profit trends",
                    prompt="Compare the latest gross profit trends for NVIDIA, AMD, and Broadcom",
                ),
            ],
            theme=ThemeConfig(
                bg="#081018",
                bg_accent_a="rgba(39, 145, 255, 0.18)",
                bg_accent_b="rgba(51, 214, 164, 0.10)",
                panel="rgba(12, 19, 29, 0.90)",
                panel_strong="rgba(9, 15, 24, 0.96)",
                panel_elevated="rgba(16, 26, 38, 0.94)",
                line="rgba(75, 173, 255, 0.14)",
                line_strong="rgba(75, 173, 255, 0.25)",
                text="#eef4fb",
                muted="#9fb0c2",
                soft="#d2deeb",
                accent="#6fd3ff",
                user="#13263a",
                landing_bg="#F3F4F1",
            ),
        ),
        namespace=NamespaceConfig(
            redis_prefix="finance",
            dataset_meta_key="finance:meta:dataset",
            checkpoint_prefix="finance:checkpoint",
            checkpoint_write_prefix="finance:checkpoint_write",
            redis_instance_name="Finance Researcher Redis Cloud",
            surface_name="Finance Researcher Surface",
            agent_name="Finance Researcher Agent",
        ),
        rag=RagConfig(
            tool_name="vector_search_research_chunks",
            status_text="Searching research chunks...",
            generating_text="Generating answer...",
            index_name_contains="researchchunk",
            vector_field="content_embedding",
            return_fields=["company_id", "ticker", "document_id", "section_heading", "page_label", "chunk_text"],
            num_results=3,
            answer_system_prompt=(
                "Answer using only the provided research chunks and structured finance records. "
                "Separate facts from narrative evidence, name the company and period explicitly, and say when the "
                "available data does not support a claim."
            ),
        ),
        identity=IdentityConfig(
            id_field="analyst_id",
            default_id="ANALYST_DEMO_001",
            default_name="Morgan Lee",
            default_email="morgan.lee@example.com",
            description=(
                "Returns the signed-in analyst profile used for the finance demo, including the active "
                "watchlist context."
            ),
        ),
        guardrail=GuardrailConfig(
            router_name="shiftiq-guardrails",
            allowed_route_name="allow_list",
            routes=[
                GuardrailRouteConfig(
                    name="allow_list",
                    references=[
                        "Compare the latest NVIDIA and AMD filings",
                        "What changed in Broadcom's earnings this quarter?",
                        "Show me NVDA gross profit trends",
                        "Pull the SEC filing for Microsoft",
                        "How does Oracle's revenue compare to its peers?",
                        "What's the operating margin trend for AMD?",
                        "Walk me through Intel's latest quarterly earnings",
                        "What's new on my watchlist?",
                        "Compare stock price trends for NVDA and AVGO",
                        "Show me the revenue breakdown for Meta",
                        "What did management say about AI revenue in the latest filing?",
                        "How has diluted EPS trended for Tesla over the past year?",
                        "Filter coverage events for Qualcomm",
                        "Update my watchlist research notes",
                        "What are the key differences between NVIDIA and AMD this quarter?",
                        "Show me Micron's net income trend",
                        "Which semiconductor company had the best gross profit growth?",
                        "Summarize the latest Amazon earnings document",
                        "Compare sector fundamentals across my watchlist",
                        "What's the latest filing date for Alphabet?",
                        "Yes",
                        "No",
                        "Tell me more",
                        "Go ahead",
                        "Sure",
                        "Thanks",
                        "Hello",
                        "Can you help me?",
                    ],
                    distance_threshold=0.7,
                ),
                GuardrailRouteConfig(
                    name="deny_list",
                    references=[
                        "What's the weather like today?",
                        "Tell me a joke",
                        "Write me a Python script",
                        "Help me with a cooking recipe",
                        "Who won the game last night?",
                        "Should I buy this stock?",
                        "Give me crypto trading tips",
                        "What's the best savings account rate?",
                        "Help me with my personal budget",
                        "Explain quantum physics",
                        "Translate this to French",
                        "Write a poem",
                        "What's the capital of Japan?",
                        "Generate an image of a chart",
                        "How do I fix my car?",
                    ],
                    distance_threshold=0.5,
                ),
            ],
        ),
        seed_memories=[
            SeedMemory(
                text="Focuses on semiconductor sector — NVDA, AMD, AVGO are primary coverage",
                topics=["watchlist", "preferences"],
            ),
            SeedMemory(
                text="Prefers quarterly earnings over annual filings for recent momentum analysis",
                topics=["research", "methodology"],
            ),
        ],
        seed_langcache=[
            SeedLangCacheEntry(
                prompt="Compare the latest gross profit trends for NVIDIA, AMD, and Broadcom",
                response=(
                    "Based on the most recent quarterly filings:\n\n"
                    "- **NVIDIA (NVDA)**: Gross profit continues to accelerate, driven by AI accelerator demand. "
                    "Quarter-over-quarter growth remains the strongest among semiconductor peers.\n"
                    "- **AMD**: Gross profit has been relatively flat, reflecting competitive pressure in both CPU "
                    "and GPU segments.\n"
                    "- **Broadcom (AVGO)**: Steady gross profit growth driven by infrastructure and networking demand.\n\n"
                    "For detailed numbers, I can pull the exact quarterly metrics from the research database."
                ),
                attributes={},
            ),
        ],
    )

    def get_entity_specs(self) -> tuple[EntitySpec, ...]:
        return ENTITY_SPECS

    def get_runtime_config(self, settings: Any) -> dict[str, Any]:
        memory_service = MemoryService(settings)
        return {
            "memory_enabled": memory_service.is_configured(),
        }

    def build_system_prompt(
        self,
        *,
        mcp_tools: Sequence[dict[str, Any]],
        runtime_config: dict[str, Any] | None = None,
    ) -> str:
        return build_system_prompt(
            mcp_tools=mcp_tools,
            runtime_config=runtime_config,
            memory_enabled=bool((runtime_config or {}).get("memory_enabled")),
        )

    def build_answer_verifier_prompt(self, *, runtime_config: dict[str, Any] | None = None) -> str:
        del runtime_config
        return (
            "When the user says 'it', 'that quarter', or 'recent', resolve the exact company, ticker, document, and "
            "period before answering. Keep structured metrics separate from narrative evidence unless both are "
            "explicitly tied to the same company and period."
        )

    def describe_tool_trace_step(
        self,
        *,
        tool_name: str,
        payload: Any,
        runtime_config: dict[str, Any] | None = None,
    ) -> str | None:
        del runtime_config
        detail = ""
        if isinstance(payload, dict):
            for key in ("query", "text", "ticker", "company_id", "document_id"):
                value = payload.get(key)
                if value:
                    detail = str(value)
                    break

        if tool_name == self.manifest.identity.tool_name:
            return "Identify the signed-in analyst and use their watchlist as the default research context."
        if tool_name == "get_current_time":
            return "Anchor comparisons to the current market and filing calendar."
        if tool_name == "dataset_overview":
            return "Inspect the current research dataset coverage before answering."
        if tool_name == "vector_search_research_chunks":
            return f"Search the research corpus for narrative evidence: {detail or 'research query'}."
        if tool_name == "search_analyst_memory":
            return "Search durable analyst memory for research preferences, coverage focus, or stored context."
        if tool_name == "remember_analyst_preference":
            return "Store a durable analyst preference or research note for future sessions."
        return None

    def get_internal_tool_definitions(
        self,
        *,
        runtime_config: dict[str, Any] | None = None,
    ) -> Sequence[InternalToolDefinition]:
        tools: list[InternalToolDefinition] = [
            InternalToolDefinition(
                name=self.manifest.identity.tool_name,
                description=self.manifest.identity.description,
            ),
            InternalToolDefinition(
                name="get_current_time",
                description="Returns the current UTC date and time in ISO 8601 format for recency and period comparisons.",
            ),
            InternalToolDefinition(
                name="dataset_overview",
                description=(
                    "Returns a summary of the finance dataset, including company, document, chunk, metric, "
                    "price, and event counts."
                ),
            ),
        ]
        if (runtime_config or {}).get("memory_enabled"):
            tools.extend(
                [
                    InternalToolDefinition(
                        name="search_analyst_memory",
                        description=(
                            "Search durable analyst memory for research preferences, coverage focus, methodology notes, "
                            "or facts from previous sessions. Use this when the user asks what you remember, refers to "
                            "preferences, or wants continuity across conversations."
                        ),
                        input_schema={
                            "type": "object",
                            "properties": {
                                "query": {"type": "string", "description": "What to look up in analyst memory."},
                                "limit": {"type": "integer", "description": "Optional max number of memories to return.", "default": 5},
                            },
                            "required": ["query"],
                        },
                    ),
                    InternalToolDefinition(
                        name="remember_analyst_preference",
                        description=(
                            "Save a durable analyst preference or research note into long-term memory. "
                            "Only use this when the user explicitly asks you to remember something or states a lasting preference."
                        ),
                        input_schema={
                            "type": "object",
                            "properties": {
                                "text": {"type": "string", "description": "The exact analyst preference or research note to remember."},
                                "memory_type": {
                                    "type": "string",
                                    "description": "Memory type: semantic for preferences/facts, episodic for a notable event, message for a verbatim note.",
                                    "default": "semantic",
                                },
                                "topics": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Optional topic tags like watchlist, research, methodology, sector, preferences.",
                                },
                            },
                            "required": ["text"],
                        },
                    ),
                ]
            )
        return tuple(tools)

    def execute_internal_tool(self, tool_name: str, arguments: dict[str, Any], settings: Any) -> dict[str, Any]:
        from datetime import datetime, timezone

        if tool_name == self.manifest.identity.tool_name:
            identity = self.manifest.identity
            return {
                identity.id_field: os.getenv(identity.id_env_var) or identity.default_id,
                "name": os.getenv(identity.name_env_var) or identity.default_name,
                "email": os.getenv(identity.email_env_var) or identity.default_email,
            }
        if tool_name == "get_current_time":
            now = datetime.now(timezone.utc)
            return {"current_time": now.isoformat(), "timezone": "UTC"}
        if tool_name == "dataset_overview":
            client = create_redis_client(settings)
            raw = client.execute_command("JSON.GET", self.manifest.namespace.dataset_meta_key, "$")
            if raw:
                data = json.loads(raw)
                return data[0] if isinstance(data, list) else data
            return {"error": "Dataset metadata not found. Run the data loader first."}
        return {"error": f"Unknown tool: {tool_name}"}

    async def aexecute_internal_tool(self, tool_name: str, arguments: dict[str, Any], settings: Any) -> dict[str, Any]:
        if tool_name not in {"search_analyst_memory", "remember_analyst_preference"}:
            return self.execute_internal_tool(tool_name, arguments, settings)

        identity = self.manifest.identity
        owner_id = os.getenv(identity.id_env_var) or identity.default_id
        memory_service = MemoryService(settings)
        if not memory_service.is_configured():
            return {"error": "Memory service is not configured for this demo."}

        if tool_name == "search_analyst_memory":
            query = str(arguments.get("query", "")).strip()
            if not query:
                return {"error": "query is required"}
            limit = arguments.get("limit")
            memories = await memory_service.asearch_long_term_memory(
                text=query,
                owner_id=owner_id,
                limit=int(limit) if limit is not None else None,
            )
            return {
                "owner_id": owner_id,
                "query": query,
                "memory_count": len(memories),
                "memories": [
                    {
                        "id": memory.get("id"),
                        "text": memory.get("text"),
                        "memory_type": memory.get("memoryType"),
                        "topics": memory.get("topics", []),
                        "session_id": memory.get("sessionId"),
                        "created_at": memory.get("createdAt"),
                    }
                    for memory in memories
                ],
            }

        # remember_analyst_preference
        text = str(arguments.get("text", "")).strip()
        if not text:
            return {"error": "text is required"}
        memory_type = str(arguments.get("memory_type", "semantic")).strip() or "semantic"
        if memory_type not in {"semantic", "episodic", "message"}:
            memory_type = "semantic"
        topics = arguments.get("topics") or []
        if not isinstance(topics, list):
            topics = []
        return {
            "owner_id": owner_id,
            "saved_text": text,
            "memory_type": memory_type,
            "topics": [str(t).strip() for t in topics if str(t).strip()],
            "demo_blocked": True,
            "response": {"acknowledged": True},
        }

    def write_dataset_meta(self, *, settings: Any, records: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
        summary = {
            "analyst_profiles": len(records.get("AnalystProfile", [])),
            "companies": len(records.get("Company", [])),
            "research_documents": len(records.get("ResearchDocument", [])),
            "research_chunks": len(records.get("ResearchChunk", [])),
            "financial_metric_points": len(records.get("FinancialMetricPoint", [])),
            "price_bars": len(records.get("PriceBar", [])),
            "coverage_events": len(records.get("CoverageEvent", [])),
        }
        client = create_redis_client(settings)
        client.delete(self.manifest.namespace.dataset_meta_key)
        client.execute_command(
            "JSON.SET",
            self.manifest.namespace.dataset_meta_key,
            "$",
            json.dumps(summary, ensure_ascii=False),
        )
        return summary

    def generate_demo_data(
        self,
        *,
        output_dir: Path,
        seed: int | None = None,
        update_env_file: bool = False,
    ) -> GeneratedDataset:
        return generate_demo_data(output_dir=output_dir, seed=seed, update_env_file=update_env_file)

    def validate(self) -> list[str]:
        errors: list[str] = []
        seen_classes: set[str] = set()
        seen_files: set[str] = set()
        for spec in self.get_entity_specs():
            if spec.class_name in seen_classes:
                errors.append(f"Duplicate entity class name: {spec.class_name}")
            if spec.file_name in seen_files:
                errors.append(f"Duplicate entity file name: {spec.file_name}")
            seen_classes.add(spec.class_name)
            seen_files.add(spec.file_name)
        if not (ROOT / self.manifest.branding.logo_path).exists():
            errors.append(f"Logo file not found: {self.manifest.branding.logo_path}")
        if not self.manifest.branding.starter_prompts:
            errors.append("Branding must define at least one starter prompt")
        return errors


DOMAIN = FinanceResearcherDomain()
