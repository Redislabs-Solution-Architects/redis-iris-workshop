# Add a New Workshop Domain

You are adding a new industry vertical to the Redis Iris Workshop. The user will provide:
- **Source domain** in the demos repo at `/Users/yusuf.bahadur/Repos/iris/redis-iris-demos/domains/<demo-domain>/`
- **Workshop domain key** (the slug used in the workshop, e.g. `banking`, `retail`, `healthcare`)
- **Display name** for the guide tab (e.g. "Banking", "Retail", "Healthcare")

If the user only provides one name, ask them to confirm the workshop domain key and display name.

## Important Rules

- Exercise stubs MUST return `None` (or `pass` for context_retriever). NEVER commit filled-in solutions as stubs.
- No hyphens in prose text in the guide. Code/config values keep hyphens.
- No "AI speak" (avoid: leverage, harness, empower, cutting-edge). Direct, confident, human tone.
- Short text in the guide. Scannable, not walls of text.
- All guide pages get `hide: [toc]` frontmatter.
- Match the existing design language exactly. Do not invent new patterns.

---

## Step 0: Read the Source Domain

Read these files from the demos repo to understand the domain:

```
/Users/yusuf.bahadur/Repos/iris/redis-iris-demos/domains/<demo-domain>/domain.py
/Users/yusuf.bahadur/Repos/iris/redis-iris-demos/domains/<demo-domain>/schema.py
/Users/yusuf.bahadur/Repos/iris/redis-iris-demos/domains/<demo-domain>/prompt.py
/Users/yusuf.bahadur/Repos/iris/redis-iris-demos/domains/<demo-domain>/data_generator.py
```

Extract and note:
- `app_name`, `subtitle`, `hero_title`, `placeholder_text`
- `starter_prompts` (all PromptCard objects with eyebrow/title/prompt)
- `seed_memories` (text + topics for each)
- `seed_langcache` (prompt + response for each)
- `rag.return_fields`, `rag.num_results`, `rag.index_name_contains`, `rag.tool_name`
- `identity.default_id`, `identity.default_name`
- `guardrail` route names, references, and thresholds
- All entity names from `schema.py` ENTITY_SPECS
- The redis key template pattern (e.g. `reddash_customer:{customer_id}`)
- The vector-bearing entity (the one with `content_embedding`)
- Entity count
- `namespace` config (redis_prefix, surface_name, agent_name, etc.)
- Theme colors

---

## Step 1: Workshop Codebase Files

All paths below are relative to `/Users/yusuf.bahadur/Repos/iris/workshops/redis-iris-workshop/`.

### 1A. Copy the domain directory

Copy the entire `domains/<demo-domain>/` from the demos repo to `domains/<workshop-key>/` in the workshop repo:

```
domains/<workshop-key>/
  __init__.py
  domain.py
  schema.py
  prompt.py
  data_generator.py
  generated_models.py
  assets/logo.svg
```

Then update `domain.py` to change:
- `id` field to the workshop domain key (e.g. `"banking"` not `"radish-bank"`)
- `output_dir` to `"output/<workshop-key>"`
- `generated_models_module` to match the workshop directory name
- `generated_models_path` to match
- `logo_path` to `"domains/<workshop-key>/assets/logo.svg"`
- `redis_prefix` in `NamespaceConfig` to match the workshop key
- `dataset_meta_key`, `checkpoint_prefix`, `checkpoint_write_prefix` to use workshop key
- `guardrail.router_name` to use workshop key (e.g. `"banking-guardrails"`)
- `seed_langcache` attributes domain to workshop key
- All other branding/content stays the same as the demos repo

**Import path differences (demos vs workshop):**
- Demos: `from backend.app.memory_service import MemoryService`
  Workshop: `from backend.app.services.memory_service import MemoryService`
- Demos: `from domains.<demo-domain>.* import ...`
  Workshop: `from domains.<workshop-key>.* import ...`

**validate() method:** The demos repo may use `validate_entity_specs()` from `domain_schema`. The workshop uses inline validation (see `domains/banking/domain.py` for the pattern with `seen_classes`/`seen_files` sets). Match the workshop pattern.

If the directory name has a hyphen (e.g. `digital-native`), the domain.py must use `_load_local_module()` with `importlib.util` instead of direct imports. Copy the pattern from `domains/digital-native/domain.py`. If no hyphen, use normal imports like `domains/banking/domain.py`.

**Keep redis key templates in `schema.py` and `generated_models.py` as-is** — they use the demos prefix (e.g. `rmobile_customer:{customer_id}`) and must match the pre-generated output data. The `redis_prefix` in NamespaceConfig is separate from entity key templates.

### 1B. Create exercise stubs

Create `exercises/<workshop-key>/` with these files:

**`__init__.py`** — empty file

**`vector_search.py`** — COPY VERBATIM from any existing domain (e.g. `exercises/digital-native/vector_search.py`). This file is identical across all domains.

**`context_retriever.py`** — COPY VERBATIM from any existing domain. Always just `pass`.

**`langcache.py`** — COPY VERBATIM from any existing domain. Always `return None`.

**`semantic_router.py`** — CUSTOMIZE. Copy the structure from an existing domain but change:
- Route names to match `domain.py` guardrail config (e.g. `"banking"` / `"off_topic"` or `"allow_list"` / `"deny_list"`)
- Reference phrases to match the domain's theme (use 5-8 from the domain's guardrail `references` for the allowed route, 3-5 for the deny route)
- Comments to say "Add 2-3 more <domain-theme> queries" and "Add 2-3 more off-topic queries"
- Distance thresholds to match guardrail config

**`agent_memory.py`** — CUSTOMIZE only the namespace in the docstring comment. Change `"<workshop-key>-demo"`. Everything else is identical.

### 1C. Create exercise solutions

Create `exercises/<workshop-key>/solutions/` with:

**`__init__.py`** — empty file

**`vector_search.py`** — COPY VERBATIM from any existing domain. Uses `rag_config.num_results`.

**`context_retriever.py`** — COPY VERBATIM. Just `pass`.

**`langcache.py`** — COPY VERBATIM. Returns `{"prompt": prompt, "similarityThreshold": 0.82, "searchStrategies": ["semantic"]}`.

**`semantic_router.py`** — CUSTOMIZE. Must include the full reference lists from `domain.py`'s guardrail config. The solution has MORE references than the stub (stub has starter examples, solution has the complete set).

**`agent_memory.py`** — CUSTOMIZE namespace to `"<workshop-key>-demo"`. Everything else is identical to other domains.

### 1D. Output data

**Preferred:** Copy pre-generated data from the demos repo if it exists:
```bash
cp /Users/yusuf.bahadur/Repos/iris/redis-iris-demos/output/<demo-domain>/*.jsonl output/<workshop-key>/
```

This avoids needing an OpenAI API key for embedding generation. Check that `output/<demo-domain>/` exists in the demos repo first.

**Alternative:** Generate fresh data (requires `OPENAI_API_KEY` in `.env`):
```bash
make generate-data DOMAIN=<workshop-key>
```

### 1E. Generated models

**Preferred:** Copy from the demos repo (already correct since schema.py key templates are unchanged):
```bash
cp /Users/yusuf.bahadur/Repos/iris/redis-iris-demos/domains/<demo-domain>/generated_models.py domains/<workshop-key>/generated_models.py
```

**Alternative:** Regenerate from schema:
```bash
make generate-models DOMAIN=<workshop-key>
```

Also update `data_generator.py`: change `OUTPUT_DIR = ROOT / "output" / "<demo-domain>"` to `ROOT / "output" / "<workshop-key>"`.

### 1F. Frontend backgrounds

Create `frontend/public/backgrounds/<workshop-key>/left.svg` and `right.svg`.

Check the demos repo at `frontend/public/backgrounds/<demo-domain>/`. If found, copy both SVGs. If not, copy from an existing workshop domain as a placeholder and tell the user they need custom SVGs.

### 1G. Screenshot for the guide

The guide needs a screenshot at:
```
/Users/yusuf.bahadur/Repos/iris/workshops/redis-iris-workshop-guide/docs/images/Demo_<AppName>.png
```

Check if one exists in `/Users/yusuf.bahadur/Repos/iris/redis-iris-demos/docs/screenshots/`. If not, tell the user they need to take one after the app runs.

---

## Step 2: Workshop Guide Pages

All paths below are relative to `/Users/yusuf.bahadur/Repos/iris/workshops/redis-iris-workshop-guide/`.

Create `docs/<workshop-key>/` with 8 markdown files. Every file gets this frontmatter:

```yaml
---
hide:
  - toc
---
```

### 2A. `index.md` — Welcome/Start page

Use this exact template. Replace placeholders with domain-specific values.

```markdown
---
hide:
  - toc
---

<div class="welcome-page" markdown>

# <Display Name> Workshop

<p class="welcome-tagline"><ONE_SENTENCE: "Build a <role> that <what it does> using <key capabilities>."></p>

<img src="../images/Demo_<AppName>.png" alt="<AppName>" class="domain-screenshot" />

## How it works

Work through each module in the sidebar. You'll add document search, query routing, live data retrieval, response caching, and persistent memory to your agent.

</div>
```

The tagline should be one sentence, domain-specific, describing what the learner builds. Look at existing domains for tone:
- Digital Native: "Build a food delivery support agent that answers customer questions using live order data, cached responses, and persistent memory."
- Banking: "Build a customer care agent that looks up accounts, cards, and deposits while keeping track of each customer's preferences."

### 2B. `setup.md`

Use this exact template. Customize the marked fields.

```markdown
---
hide:
  - toc
---

# Setup

Get your environment running in 6 steps.

[:material-github: Workshop Repository](https://github.com/Redislabs-Solution-Architects/redis-iris-workshop){ target=_blank }

---

## 1. Clone and install

\```bash
git clone https://github.com/Redislabs-Solution-Architects/redis-iris-workshop.git
cd redis-iris-workshop
make install
\```

## 2. Create a Redis Cloud database

1. Go to [cloud.redis.io](https://redis.io/try-free/) and sign up or log in.
2. Click **New database** and select **Try 30 MB for Free**.

    ![Free tier](../images/free_database.png)

3. Name it (e.g. `iris-workshop`) and click **Create**.
4. Click **Connect**, choose **Python**, and copy your **host**, **port**, and **password**.

    ![Connect](../images/connect_database.png)

## 3. Configure environment

\```bash
cp .env.example .env
\```

Fill in your credentials:

\```env
DEMO_DOMAIN=<WORKSHOP_KEY>
OPENAI_API_KEY=<from your instructor — check Announcements>
REDIS_HOST=<your host>
REDIS_PORT=<your port>
REDIS_PASSWORD=<your password>
\```

## 4. Seed data

\```bash
make seed-data
\```

This loads <DOCUMENT_TYPE_DESCRIPTION> with vector embeddings into your Redis database.

## 5. Start the app

\```bash
make dev
\```

## 6. Verify

Open [localhost:3040](http://localhost:3040).

- [ ] You see the **<APP_NAME>** landing page
- [ ] **Simple RAG** is the only mode available
- [ ] Typing a question returns nothing (expected — Vector Search is next)
```

Customize:
- `DEMO_DOMAIN=<WORKSHOP_KEY>`
- `<DOCUMENT_TYPE_DESCRIPTION>` — e.g. "policy documents", "bank policy and product documents", "medical policies and guidelines"
- `<APP_NAME>` — the branding app_name from domain.py

### 2C. `vector-search.md`

Use this exact template. Customize the marked fields.

```markdown
---
hide:
  - toc
---

# Module 1: Vector Search

<INTRO_SENTENCE: one sentence about why vector search matters for this domain. Example: "Without grounding in real data, LLMs hallucinate confidently. Vector search lets your agent retrieve actual policy documents from Redis by meaning, not just keywords, so every answer is backed by source material.">

---

## Exercise

**Open** `exercises/<WORKSHOP_KEY>/vector_search.py`. You will write ~5 lines in `SimpleRAGService` .

### `create_vector_query(embedding, rag_config)`

This method builds a `VectorQuery` — the object that tells Redis how to search your document vectors and what to send back.

| Parameter | What it means | What to pass |
|-----------|---------------|--------------|
| `vector` | The user's question as an embedding. Redis compares this against all stored document vectors using cosine similarity. | `embedding` |
| `vector_field_name` | Which field in your documents contains the embedding vectors. | `rag_config.vector_field` |
| `return_fields` | Which fields to return from matching documents (title, content, etc.). | `rag_config.return_fields` |
| `num_results` | How many documents to retrieve. More results = more context but weaker matches. | `rag_config.num_results` |

Return a `VectorQuery(...)` instance.

??? success "Show solution"
    \```python
    def create_vector_query(self, embedding, rag_config):
        return VectorQuery(
            vector=embedding,
            vector_field_name=rag_config.vector_field,
            return_fields=rag_config.return_fields,
            num_results=rag_config.num_results,
        )
    \```

---

## Verify

Stop the running server (`Ctrl+C` in the terminal), then restart with `make dev`. Open [localhost:3040](http://localhost:3040).

- [ ] Ask: **"<VERIFY_QUESTION>"**
- [ ] View the **Activity Panel** — you see RAG retrieval results with document titles

---

## Try this

- Change `num_results` to `1`, refresh, and ask the same question. Notice how the response changes with less information.
```

Customize:
- `<WORKSHOP_KEY>` in the file path
- `<INTRO_SENTENCE>` — domain-appropriate
- `<VERIFY_QUESTION>` — a question that works against the seeded policy/document data. Pick something that matches a document in `output/<workshop-key>/policies.jsonl` (or equivalent vector-bearing entity JSONL).

### 2D. `semantic-router.md`

Use this exact template. Read an existing domain's semantic-router.md (e.g. `docs/digital-native/semantic-router.md`) for the complete structure, then customize:

- File path to `exercises/<WORKSHOP_KEY>/semantic_router.py`
- Route names matching the domain's guardrail config
- The code snippet showing the stub's starter references (copy from the actual stub you created)
- Hint text about what domain-relevant and off-topic queries look like
- Verify questions: one that should pass the guardrail, one that should be blocked
- The `.env` snippet showing `GUARDRAIL_ENABLED=true`

### 2E. `context-retriever.md`

This is the longest guide page. Read an existing domain's version (e.g. `docs/banking/context-retriever.md`) for the complete structure. This page has NO code exercise — it walks through Redis Cloud console setup.

Customize:
- Comparison table questions (Vector Search vs Context Retriever column) — use domain-specific examples
- Service name in the cloud console
- Key template (e.g. `radish_bank_customer:{customer_id}`)
- Entity name for the walkthrough (usually the primary entity like Customer or Patient)
- Entity count and entity list
- Tool examples in the "auto generated MCP tools" description
- `make setup-surface` and `make load-data` commands (these are the same across domains)
- Try-it questions — MUST match starter_prompts from domain.py that have eyebrow "Context Retriever" or "Context"
- The intro text should be exactly: "Vector search finds documents. But questions like \"<DOMAIN_SPECIFIC_QUESTION>\" need live data that changes constantly. [Context Retriever](https://redis.io/context-retriever/) connects your agent directly to that data."

### 2F. `langcache.md`

Read an existing domain's version for the complete structure. Customize:

- File path to `exercises/<WORKSHOP_KEY>/langcache.py`
- Cloud setup instructions (LangCache service name, cache name)
- The seeded entry description — must match `seed_langcache` from domain.py
- The `make seed-langcache` command (same across domains)
- Env vars: `LANGCACHE_HOST`, `LANGCACHE_CACHE_ID`, `LANGCACHE_API_KEY`
- Verify question — must be the exact seeded prompt from `seed_langcache`
- Try-it questions — one that's a cache hit (similar to seeded), one that's a miss
- The exercise and solution code are IDENTICAL across domains (no customization needed in the code blocks)

### 2G. `agent-memory.md`

Read an existing domain's version for the complete structure. Customize:

- File path to `exercises/<WORKSHOP_KEY>/agent_memory.py`
- Cloud setup instructions (Agent Memory service name, store name)
- The `namespace` value in the solution code block: `"<workshop-key>-demo"`
- Seeded memory descriptions — must match `seed_memories` from domain.py
- The `make seed-memories` command (same across domains)
- Env vars: `MEMORY_API_BASE_URL`, `MEMORY_STORE_ID`, `MEMORY_API_KEY`
- Verify/try-it questions — MUST match starter_prompts with eyebrow "Memory" or "Agent Memory"

### 2H. `congratulations.md`

COPY VERBATIM from any existing domain. This file is identical across all domains:

```markdown
---
hide:
  - toc
---

# Done!

You built a complete agent powered by **Redis Iris**.

| Module | What you added |
|--------|---------------|
| **Vector Search** | Search documents by meaning |
| **Semantic Router** | Block off topic queries before the LLM |
| **Context Retriever** | Query live data with auto generated tools |
| **LangCache** | Cache answers for instant responses |
| **Agent Memory** | Remember users across conversations |

---

## Keep going

- [Redis Iris docs](https://redis.io/docs/latest/develop/ai/context-engine/)
- [LangCache](https://redis.io/langcache/)
- [Context Retriever](https://redis.io/context-retriever/)
- [Agent Memory](https://redis.io/docs/latest/operate/rc/context-engine/agent-memory/)
- [RedisVL](https://redis.io/docs/latest/integrate/redisvl/)
- [Redis Cloud](https://redis.io/cloud/)

Questions? Find your instructor or check [Announcements](../announcements.md).
```

---

## Step 3: Update Existing Files

### 3A. `mkdocs.yml`

Add the new domain to the `nav:` section, BEFORE the `Announcements` entry:

```yaml
  - <Display Name>:
    - Start: <workshop-key>/index.md
    - "0. Setup": <workshop-key>/setup.md
    - "1. Vector Search": <workshop-key>/vector-search.md
    - "2. Semantic Router": <workshop-key>/semantic-router.md
    - "3. Context Retriever": <workshop-key>/context-retriever.md
    - "4. LangCache": <workshop-key>/langcache.md
    - "5. Agent Memory": <workshop-key>/agent-memory.md
    - "Done!": <workshop-key>/congratulations.md
```

### 3B. `docs/index.md` — Add domain card

Add a new card inside the `<div class="domain-grid">` section. Follow the existing pattern:

```html
<div class="domain-card" markdown>
### <Display Name>

<One-line description, e.g. "Food delivery support agent">

[Start ->](<workshop-key>/index.md)
</div>
```

### 3C. Workshop `README.md`

Add the new domain to the "Pick a vertical" table:

```markdown
| <Display Name> | <Agent description> | `<workshop-key>` |
```

---

## Step 4: Verify

Run these checks:

1. **Exercise stubs are clean:**
```bash
grep -r "return None" exercises/<workshop-key>/*.py
# Should see: vector_search.py, langcache.py, agent_memory.py
grep -r "pass" exercises/<workshop-key>/context_retriever.py
# Should see: pass
```

2. **Solutions exist and differ from stubs:**
```bash
diff exercises/<workshop-key>/semantic_router.py exercises/<workshop-key>/solutions/semantic_router.py
diff exercises/<workshop-key>/agent_memory.py exercises/<workshop-key>/solutions/agent_memory.py
```

3. **Guide builds cleanly:**
```bash
cd /Users/yusuf.bahadur/Repos/iris/workshops/redis-iris-workshop-guide
mkdocs build --strict
```

4. **Data seeds successfully:**
```bash
DEMO_DOMAIN=<workshop-key> make seed-data
```

5. **App starts:**
```bash
DEMO_DOMAIN=<workshop-key> make dev
```

---

## Step 5: Tell the user what's left

After completing all steps, tell the user:

1. Whether you found/copied background SVGs or if they need to create them
2. Whether you found/copied a screenshot or if they need to take one
3. Remind them to run `make generate-data` and `make generate-models` if you couldn't
4. Remind them to test the full flow: seed data, start app, try each module's verify questions
5. List the starter_prompts you used as verify/try-it questions in the guide so they can confirm they work with the seeded data
