from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Sequence

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
from backend.app.services.memory_service import MemoryService
from domains.banking.data_generator import DEMO_CUSTOMER_ID, generate_demo_data
from domains.banking.prompt import build_system_prompt
from domains.banking.schema import ENTITY_SPECS

ROOT = Path(__file__).resolve().parents[2]


class RadishBankDomain:
    manifest = DomainManifest(
        id="banking",
        description="Radish Bank retail demo: structured accounts plus policy docs.",
        generated_models_module="domains.banking.generated_models",
        generated_models_path="domains/banking/generated_models.py",
        output_dir="output/banking",
        branding=BrandingConfig(
            app_name="Radish Bank",
            subtitle="Customer Care",
            hero_title="Banking Made Easy",
            placeholder_text="Ask about accounts, cards, FDs, insurance, branches, or fee waivers…",
            logo_path="domains/banking/assets/logo.svg",
            demo_steps=[
                "What are my current account balances?",
                "Please remember that I prefer paperless statements and am interested in fixed deposits.",
                "Click Memory",
                "Given what you know about my preferences, what banking products would you recommend for me?",
            ],
            starter_prompts=[
                PromptCard(
                    eyebrow="Context",
                    title="What are my account balances?",
                    prompt="What accounts do I have and what are my current balances?",
                ),
                PromptCard(
                    eyebrow="Context",
                    title="Recent service requests",
                    prompt="Show me my recent service requests",
                ),
                PromptCard(
                    eyebrow="Memory",
                    title="Save banking preferences",
                    prompt="Please remember that I prefer mobile banking and contactless payments",
                ),
                PromptCard(
                    eyebrow="Memory",
                    title="Product recommendations",
                    prompt="What are my banking preferences and savings interests?",
                ),
                PromptCard(
                    eyebrow="Cached",
                    title="Fixed deposit rates",
                    prompt="Tell me about your fixed deposit rates and terms",
                ),
            ],
            theme=ThemeConfig(
                bg="#071a14",
                bg_accent_a="rgba(46, 204, 113, 0.12)",
                bg_accent_b="rgba(241, 196, 15, 0.08)",
                panel="rgba(12, 32, 26, 0.92)",
                panel_strong="rgba(14, 40, 32, 0.97)",
                panel_elevated="rgba(18, 48, 38, 0.95)",
                line="rgba(46, 204, 113, 0.15)",
                line_strong="rgba(241, 196, 15, 0.2)",
                text="#ecf7f2",
                muted="#8fb3a8",
                soft="#cfe8dc",
                accent="#2ecc71",
                user="#0d1f18",
                landing_bg="#F4F7F5",
            ),
        ),
        namespace=NamespaceConfig(
            redis_prefix="banking",
            dataset_meta_key="banking:meta:dataset",
            checkpoint_prefix="banking:checkpoint",
            checkpoint_write_prefix="banking:checkpoint_write",
            redis_instance_name="Radish Bank Redis Cloud",
            surface_name="Radish Bank Context Surface",
            agent_name="Radish Bank Service Agent",
        ),
        rag=RagConfig(
            tool_name="vector_search_bank_documents",
            status_text="Searching Radish Bank policy documents…",
            generating_text="Generating answer…",
            index_name_contains="bankdocument",
            vector_field="content_embedding",
            return_fields=["title", "category", "content", "document_id"],
            num_results=4,
            answer_system_prompt=(
                "You are Radish Bank's policy and product-information assistant. "
                "Answer using only the retrieved bank documents. If they do not cover the question, say so briefly."
            ),
        ),
        identity=IdentityConfig(
            default_id=DEMO_CUSTOMER_ID,
            default_name="Merv Kwok",
            default_email="merv.kwok@example.com",
            id_field="customer_id",
            description=(
                "Returns the signed-in retail customer id, name, and email. "
                "The customer_id is always the full string CUST001 in this demo—copy it exactly into any "
                "filter_*_by_customer_id or similar MCP tool (never shorten to C001). Call before account, card, or balance lookups."
            ),
        ),
        guardrail=GuardrailConfig(
            router_name="banking-guardrails",
            allowed_route_name="allow_list",
            routes=[
                GuardrailRouteConfig(
                    name="allow_list",
                    references=[
                        "Check my savings balance",
                        "What are my account balances?",
                        "Fixed deposit rate FD6",
                        "Waive annual card fee",
                        "Branch hours Tampines",
                        "Auto lobby and branch services",
                        "Accident insurance premium",
                        "Transfer between my accounts",
                        "Hello I need help with my account",
                        "What accounts do I have?",
                        "Early withdrawal penalty fixed deposit",
                        "What FD products are available?",
                        "What is the interest rate?",
                        "I want to invest in a fixed deposit",
                        "How do I open a new account?",
                        "What are the card fee charges?",
                        "Show me my service request history",
                        "Is Bishan a full branch?",
                        "What insurance plans do you offer?",
                        "Place 2000 SGD in the 6-month FD",
                        "Yes",
                        "No",
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
                        "Why is the sky blue?",
                        "Who is the current US president?",
                        "Recipe for chocolate cake",
                        "Capital of Mongolia",
                        "Write me a Python sorting algorithm",
                        "What is the weather tomorrow?",
                        "Tell me a joke",
                        "History of the Roman Empire",
                        "Write a poem about love",
                        "What's the latest news?",
                        "Translate this to Spanish",
                        "Help me debug my code",
                        "What's the meaning of life?",
                        "Play a game with me",
                        "What's the stock market doing?",
                    ],
                    distance_threshold=0.5,
                ),
            ],
        ),
        seed_memories=[
            SeedMemory(
                text="Prefers paperless statements and online banking",
                topics=["banking", "preferences"],
            ),
            SeedMemory(
                text="Interested in fixed deposit products for savings growth",
                topics=["products", "interests"],
            ),
        ],
        seed_langcache=[
            SeedLangCacheEntry(
                prompt="What are your current fixed deposit interest rates?",
                response=(
                    "We currently offer two fixed deposit plans:\n\n"
                    "- **FD6** (6-month term): **2.8% p.a.** — minimum deposit SGD 1,000\n"
                    "- **FD12** (12-month term): **3.1% p.a.** — minimum deposit SGD 1,000\n\n"
                    "Interest is calculated daily and paid at maturity. Early withdrawal forfeits all accrued interest. "
                    "You can open an FD through your account portal or visit any Radish Bank branch."
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
            memory_enabled=bool((runtime_config or {}).get("memory_enabled")),
        )

    def build_answer_verifier_prompt(self, *, runtime_config: dict[str, Any] | None = None) -> str:
        del runtime_config
        return (
            "When the user refers to 'my savings', 'that waiver', or 'the Bishan branch', tie the answer to the "
            "exact account id, request id, or branch id from tool results. Do not invent rates or fees."
        )

    def describe_tool_trace_step(
        self,
        *,
        tool_name: str,
        payload: Any,
        runtime_config: dict[str, Any] | None = None,
    ) -> str | None:
        del payload, runtime_config
        if tool_name == self.manifest.identity.tool_name:
            return "Identify the signed-in Radish Bank customer before account or card lookups."
        if tool_name == "get_current_time":
            return "Compare the current time against service-request timestamps."
        if tool_name == "search_customer_memory":
            return "Search durable customer memory for preferences, past issues, or stored context."
        if tool_name == "remember_customer_detail":
            return "Store a durable customer fact or preference for future conversations."
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
                description="Current UTC time (ISO) for comparing service-request timestamps.",
            ),
            InternalToolDefinition(
                name="dataset_overview",
                description="Counts of Radish Bank demo entities loaded for this surface.",
            ),
        ]
        if (runtime_config or {}).get("memory_enabled"):
            tools.extend(
                [
                    InternalToolDefinition(
                        name="search_customer_memory",
                        description=(
                            "Search durable customer memory for preferences, prior incidents, or facts from previous sessions. "
                            "Use this when the user asks what you remember, refers to preferences, or wants continuity across conversations."
                        ),
                        input_schema={
                            "type": "object",
                            "properties": {
                                "query": {"type": "string", "description": "What to look up in customer memory."},
                                "limit": {"type": "integer", "description": "Optional max number of memories to return.", "default": 5},
                            },
                            "required": ["query"],
                        },
                    ),
                    InternalToolDefinition(
                        name="remember_customer_detail",
                        description=(
                            "Save a durable customer preference or fact into long-term memory. "
                            "Only use this when the user explicitly asks you to remember something or states a lasting preference."
                        ),
                        input_schema={
                            "type": "object",
                            "properties": {
                                "text": {"type": "string", "description": "The exact customer preference or durable fact to remember."},
                                "memory_type": {
                                    "type": "string",
                                    "description": "Memory type: semantic for preferences/facts, episodic for a notable event, message for a verbatim note.",
                                    "default": "semantic",
                                },
                                "topics": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Optional topic tags like banking, preferences, products, insurance.",
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
            raw_id = (os.getenv(identity.id_env_var) or identity.default_id).strip()
            # Demo seed + indexes use CUST001; tolerate common .env typo "C001".
            customer_id = DEMO_CUSTOMER_ID if raw_id.casefold() == "c001" else raw_id
            return {
                identity.id_field: customer_id,
                "name": os.getenv(identity.name_env_var) or identity.default_name,
                "email": os.getenv(identity.email_env_var) or identity.default_email,
            }
        if tool_name == "get_current_time":
            return {"current_time": datetime.now(timezone.utc).isoformat(), "timezone": "UTC"}
        if tool_name == "dataset_overview":
            client = create_redis_client(settings)
            raw = client.execute_command("JSON.GET", self.manifest.namespace.dataset_meta_key, "$")
            if raw:
                data = json.loads(raw)
                return data[0] if isinstance(data, list) else data
            return {"error": "Dataset metadata not found. Run the data loader first."}
        return {"error": f"Unknown tool: {tool_name}"}

    async def aexecute_internal_tool(self, tool_name: str, arguments: dict[str, Any], settings: Any) -> dict[str, Any]:
        if tool_name not in {"search_customer_memory", "remember_customer_detail"}:
            return self.execute_internal_tool(tool_name, arguments, settings)

        identity = self.manifest.identity
        owner_id = os.getenv(identity.id_env_var) or identity.default_id
        memory_service = MemoryService(settings)
        if not memory_service.is_configured():
            return {"error": "Memory service is not configured for this demo."}

        if tool_name == "search_customer_memory":
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
            "customers": len(records.get("Customer", [])),
            "accounts": len(records.get("Account", [])),
            "cards": len(records.get("Card", [])),
            "fixed_deposit_plans": len(records.get("FixedDepositPlan", [])),
            "insurance_plans": len(records.get("InsurancePlan", [])),
            "branches": len(records.get("Branch", [])),
            "branch_hours": len(records.get("BranchHours", [])),
            "product_holdings": len(records.get("ProductHolding", [])),
            "service_requests": len(records.get("ServiceRequest", [])),
            "bank_documents": len(records.get("BankDocument", [])),
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


DOMAIN = RadishBankDomain()
