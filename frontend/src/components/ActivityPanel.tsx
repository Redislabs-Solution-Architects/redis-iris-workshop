import { useState } from "react";
import type {
  AgentMode,
  ChatMessage,
  MemoryDashboardState,
  RedisContextView,
  ToolDefinition,
} from "../types";
import {
  mergeToolEvents,
  toolDisplayName,
  toolKindLabel,

  memoryEventText,
  generateToolDescription,
  extractEntity,
} from "../utils";

type ActivityPanelProps = {
  allMessages: ChatMessage[];
  isOpen: boolean;
  onClose: () => void;
  contextView: RedisContextView;
  onContextViewChange: (view: RedisContextView) => void;
  memoryData: MemoryDashboardState;
  memoryLoading: boolean;
  onRefreshMemory: () => void;
  onLoadContext: () => void;
  toolsData: ToolDefinition[];
  toolsLoading: boolean;
  mode: AgentMode;
};

function ChevronIcon({ open, className }: { open: boolean; className?: string }) {
  return (
    <svg
      className={`section-chevron ${open ? "open" : ""} ${className ?? ""}`}
      width="16"
      height="16"
      viewBox="0 0 16 16"
      fill="none"
    >
      <path d="M6 4L10 8L6 12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}


function ToolRow({
  name,
  durationMs,
  callPayload,
  resultPayload,
  isComplete,
}: {
  name: string;
  kind?: string;
  durationMs?: number;
  callPayload?: Record<string, unknown>;
  resultPayload?: Record<string, unknown>;
  isComplete: boolean;
}) {
  const [expanded, setExpanded] = useState(false);
  const isDemoBlocked = resultPayload?.demo_blocked === true;
  const statusClass = isDemoBlocked ? "blocked" : isComplete ? "done" : "running";
  return (
    <div className="activity-tool-row">
      <button
        className="activity-tool-summary"
        onClick={() => setExpanded(!expanded)}
        type="button"
      >
        <span className={`activity-tool-status ${statusClass}`}>
          {isDemoBlocked ? (
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
              <circle cx="7" cy="7" r="6" stroke="currentColor" strokeWidth="1.3" />
              <path d="M7 4.5V7.5" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
              <circle cx="7" cy="9.5" r="0.6" fill="currentColor" />
            </svg>
          ) : isComplete ? (
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
              <circle cx="7" cy="7" r="6" stroke="currentColor" strokeWidth="1.3" />
              <path d="M4 7L6 9L10 5" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          ) : (
            <span className="activity-tool-spinner" />
          )}
        </span>
        <span className="activity-tool-name">{toolDisplayName(name)}</span>
        {durationMs !== undefined && (
          <span className="timing-badge" title="Includes SDK round-trip">{durationMs}ms</span>
        )}
        <svg
          className={`activity-tool-chevron ${expanded ? "open" : ""}`}
          width="12"
          height="12"
          viewBox="0 0 12 12"
          fill="none"
        >
          <path d="M3 5L6 8L9 5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </button>
      {isDemoBlocked && (
        <div className="demo-notice">Demo mode — identified as long-term but not stored</div>
      )}
      {expanded && (
        <div className="activity-tool-detail">
          {callPayload && (
            <div className="activity-tool-section">
              <div className="activity-tool-section-label">Input</div>
              <pre>{JSON.stringify(callPayload, null, 2)}</pre>
            </div>
          )}
          {resultPayload && (
            <div className="activity-tool-section">
              <div className="activity-tool-section-label">Result</div>
              <pre>{JSON.stringify(resultPayload, null, 2)}</pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function ActivityView({ allMessages, mode }: { allMessages: ChatMessage[]; mode: AgentMode }) {
  const latestAssistant = [...allMessages]
    .reverse()
    .find((m) => m.role === "assistant");
  if (!latestAssistant) {
    return <div className="activity-empty">Send a message to see Redis in action.</div>;
  }

  const merged = mergeToolEvents(latestAssistant.toolEvents);
  const isRag = mode === "simple_rag";

  if (isRag) {
    const ragGuardrailTools = merged.filter((t) => t.toolKind === "guardrail");
    const ragSearchTools = merged.filter((t) => t.toolKind !== "guardrail");
    const ragGuardrailAllowed = ragGuardrailTools.every(
      (t) => !t.resultPayload || (t.resultPayload as Record<string, unknown>).allowed !== false
    );
    return (
      <div className="activity-content">
        {ragGuardrailTools.length > 0 && (
          <section className="activity-section">
            <div className="activity-section-header">
              <span className="activity-section-title">Semantic Routing</span>
              <span className="activity-section-count">
                {ragGuardrailAllowed ? "Allowed" : "Blocked"}
              </span>
            </div>
            {ragGuardrailTools.map((tool, i) => (
              <ToolRow
                key={`guard-${i}`}
                name={tool.toolName}
                durationMs={tool.durationMs}
                callPayload={tool.callPayload}
                resultPayload={tool.resultPayload}
                isComplete={tool.resultPayload !== undefined}
              />
            ))}
          </section>
        )}
        {ragSearchTools.length > 0 ? (
          <section className="activity-section">
            <div className="activity-section-header">
              <span className="activity-section-title">Vector Search</span>
              <span className="activity-section-count">
                {ragSearchTools.length} call{ragSearchTools.length !== 1 ? "s" : ""}
              </span>
            </div>
            {ragSearchTools.map((tool, i) => (
              <ToolRow
                key={`tool-${i}`}
                name={tool.toolName}
                kind="vector_search"
                durationMs={tool.durationMs}
                callPayload={tool.callPayload}
                resultPayload={tool.resultPayload}
                isComplete={tool.resultPayload !== undefined}
              />
            ))}
          </section>
        ) : (
          !ragGuardrailTools.length && <div className="activity-empty">Waiting for vector search...</div>
        )}
        <div className="panel-footer-badge">Powered by Redis Vector Search</div>
      </div>
    );
  }

  const guardrailTools = merged.filter((t) => t.toolKind === "guardrail");
  const cacheTools = merged.filter((t) => t.toolKind === "langcache");
  const memoryTools = merged.filter((t) => t.toolKind === "memory");
  const otherTools = merged.filter((t) => t.toolKind !== "memory" && t.toolKind !== "langcache" && t.toolKind !== "guardrail");

  const cacheHit = cacheTools.some(
    (t) => t.resultPayload && (t.resultPayload as Record<string, unknown>).hit === true
  );

  const guardrailAllowed = guardrailTools.every(
    (t) => !t.resultPayload || (t.resultPayload as Record<string, unknown>).allowed !== false
  );

  return (
    <div className="activity-content">
      {guardrailTools.length > 0 && (
        <section className="activity-section">
          <div className="activity-section-header">
            <span className="activity-section-title">Semantic Routing</span>
            <span className="activity-section-count">
              {guardrailAllowed ? "Allowed" : "Blocked"}
            </span>
          </div>
          {guardrailTools.map((tool, i) => (
            <ToolRow
              key={`guard-${i}`}
              name={tool.toolName}
              durationMs={tool.durationMs}
              callPayload={tool.callPayload}
              resultPayload={tool.resultPayload}
              isComplete={tool.resultPayload !== undefined}
            />
          ))}
        </section>
      )}

      {cacheTools.length > 0 && (
        <section className="activity-section">
          <div className="activity-section-header">
            <span className="activity-section-title">LangCache</span>
            <span className="activity-section-count">
              {cacheHit ? "Hit" : "Miss"}
            </span>
          </div>
          {cacheTools.map((tool, i) => (
            <ToolRow
              key={`cache-${i}`}
              name={tool.toolName}
              kind="LangCache"
              durationMs={tool.durationMs}
              callPayload={tool.callPayload}
              resultPayload={tool.resultPayload}
              isComplete={tool.resultPayload !== undefined}
            />
          ))}
        </section>
      )}

      {memoryTools.length > 0 && (
        <section className="activity-section">
          <div className="activity-section-header">
            <span className="activity-section-title">Agent Memory</span>
            <span className="activity-section-count">{memoryTools.length}</span>
          </div>
          {memoryTools.map((tool, i) => (
            <ToolRow
              key={`mem-${i}`}
              name={tool.toolName}
              kind={toolKindLabel(tool.toolKind)}
              durationMs={tool.durationMs}
              callPayload={tool.callPayload}
              resultPayload={tool.resultPayload}
              isComplete={tool.resultPayload !== undefined}
            />
          ))}
        </section>
      )}

      {otherTools.length > 0 && (
        <section className="activity-section">
          <div className="activity-section-header">
            <span className="activity-section-title">Context Retriever</span>
            <span className="activity-section-count">
              {otherTools.length} call{otherTools.length !== 1 ? "s" : ""}
            </span>
          </div>
          {otherTools.map((tool, i) => (
            <ToolRow
              key={`tool-${i}`}
              name={tool.toolName}
              kind={toolKindLabel(tool.toolKind)}
              durationMs={tool.durationMs}
              callPayload={tool.callPayload}
              resultPayload={tool.resultPayload}
              isComplete={tool.resultPayload !== undefined}
            />
          ))}
        </section>
      )}

      {guardrailTools.length === 0 && cacheTools.length === 0 && memoryTools.length === 0 && otherTools.length === 0 && (
        <div className="activity-empty">Waiting for tool calls...</div>
      )}
    </div>
  );
}


const CACHED_ENTRIES = [
  {
    question: "What's your refund policy for late deliveries?",
    snippet: "If your order arrives more than 15 minutes late, you're eligible for a 20% credit...",
  },
];


/* ─── Expandable card used in conversation All Context ─── */

function ExpandableCard({
  title,
  summary,
  badge,
  children,
  rightAction,
  expandLabel = "View details",
}: {
  title: string;
  summary: React.ReactNode;
  badge?: React.ReactNode;
  children?: React.ReactNode;
  rightAction?: React.ReactNode;
  expandLabel?: string;
}) {
  const [open, setOpen] = useState(false);
  const hasDetail = !!children;

  return (
    <div className={`context-card ${open ? "open" : ""}`}>
      <div
        className="context-card-header"
        onClick={() => hasDetail && setOpen(!open)}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); hasDetail && setOpen(!open); } }}
        style={{ cursor: hasDetail ? "pointer" : "default" }}
      >
        <span className="context-card-title">{title}</span>
        {badge && <span className="context-card-badge">{badge}</span>}
        {rightAction && (
          <span className="context-card-action" onClick={(e) => e.stopPropagation()}>
            {rightAction}
          </span>
        )}
        {hasDetail && <ChevronIcon open={open} className="context-card-chevron" />}
      </div>
      <div className="context-card-summary">{summary}</div>
      {hasDetail && !open && (
        <button
          className="context-card-expand-hint"
          onClick={() => setOpen(true)}
          type="button"
        >
          <span>{expandLabel}</span>
          <svg width="10" height="10" viewBox="0 0 12 12" fill="none">
            <path d="M3 5L6 8L9 5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </button>
      )}
      {hasDetail && (
        <div className={`context-card-detail ${open ? "open" : ""}`}>
          <div className="context-card-detail-inner">
            <div className="context-card-detail-content">{children}</div>
            <button
              className="context-card-collapse-hint"
              onClick={() => setOpen(false)}
              type="button"
            >
              <span>Collapse</span>
              <svg width="10" height="10" viewBox="0 0 12 12" fill="none">
                <path d="M3 8L6 5L9 8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

/* ─── Conversation detail panel: All Context ─── */

function RedisContextContent({
  memoryData,
  memoryLoading,
  onRefreshMemory,
  toolsData,
  toolsLoading,
  mode,
}: {
  memoryData: MemoryDashboardState;
  memoryLoading: boolean;
  onRefreshMemory: () => void;
  toolsData: ToolDefinition[];
  toolsLoading: boolean;
  mode: AgentMode;
}) {
  const mcpTools = toolsData.filter((t) => t.kind === "mcp_tool");
  const entityCount = new Set(mcpTools.map((t) => extractEntity(t.name))).size;

  const grouped = new Map<string, ToolDefinition[]>();
  for (const tool of mcpTools) {
    const entity = extractEntity(tool.name);
    const list = grouped.get(entity) ?? [];
    list.push(tool);
    grouped.set(entity, list);
  }
  const entityGroups = [...grouped.entries()].sort(([a], [b]) => a.localeCompare(b));

  const longTermCount = memoryData?.long_term?.length ?? 0;
  const shortTermCount = memoryData?.short_term?.length ?? 0;

  return (
    <div className="redis-context-content">
      {/* ── LangCache ── */}
      <ExpandableCard
        title="LangCache"
        summary={
          <>
            <div className="overview-stat">
              <span className="overview-stat-value overview-stat-value--sm">{CACHED_ENTRIES.length}</span>
              <span className="overview-stat-label">cached response{CACHED_ENTRIES.length !== 1 ? "s" : ""}</span>
            </div>
            <div className="overview-preview">
              {CACHED_ENTRIES.map((e, i) => (
                <div key={i} className="overview-preview-item">
                  {e.question}
                  <span className="cache-origin">
                    <svg width="10" height="10" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                      <circle cx="8" cy="8" r="6.5" />
                      <path d="M8 4.5V8L10.5 9.5" />
                    </svg>
                    Asked 8 hours ago in Austin, TX
                  </span>
                </div>
              ))}
            </div>
          </>
        }
      />

      {/* ── Agent Memory ── */}
      <ExpandableCard
        title="Agent Memory"
        rightAction={
          <button
            className="panel-refresh-btn"
            onClick={onRefreshMemory}
            disabled={memoryLoading}
            type="button"
            title="Refresh"
          >
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
              <path d="M11.5 7A4.5 4.5 0 11 7 2.5" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
              <path d="M7 1L9 3L7 5" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </button>
        }
        summary={
          memoryLoading && !memoryData ? (
            <div className="overview-stat-label">Loading...</div>
          ) : (
            <>
              <div className="overview-stat-row">
                <div className="overview-stat">
                  <span className="overview-stat-value overview-stat-value--sm">{longTermCount}</span>
                  <span className="overview-stat-label">long-term</span>
                </div>
                <div className="overview-stat">
                  <span className="overview-stat-value overview-stat-value--sm">{shortTermCount}</span>
                  <span className="overview-stat-label">working</span>
                </div>
              </div>
              {longTermCount > 0 && (
                <div className="overview-preview">
                  {memoryData!.long_term.slice(0, 2).map((m, i) => (
                    <div key={i} className="overview-preview-item">
                      {String(m.text ?? "").slice(0, 60)}{String(m.text ?? "").length > 60 ? "..." : ""}
                    </div>
                  ))}
                </div>
              )}
            </>
          )
        }
        expandLabel="View working memory"
      >
        {shortTermCount > 0 && (
          <>
            <div className="panel-mem-sublabel">Working Memory</div>
            <div className="panel-mem-list">
              {memoryData!.short_term.map((event, i) => {
                const role = String(event.role ?? "event").toLowerCase();
                const roleLabel = role === "user" ? "Customer" : role === "assistant" ? "Agent" : role;
                const raw = memoryEventText(event).replace(/\*\*/g, "");
                const text = raw.length > 120 ? raw.slice(0, 120).replace(/\s+\S*$/, "") + "..." : raw;
                return (
                  <div key={`se-${i}`} className="panel-mem-card">
                    <div className="panel-mem-session-role">{roleLabel}</div>
                    <div className="panel-mem-text">{text}</div>
                  </div>
                );
              })}
            </div>
          </>
        )}
      </ExpandableCard>

      {/* ── Context Retriever ── */}
      <ExpandableCard
        title="Context Retriever"
        summary={
          toolsLoading ? (
            <div className="overview-stat-label">Loading...</div>
          ) : (
            <div className="overview-stat-row">
              <div className="overview-stat">
                <span className="overview-stat-value overview-stat-value--sm">{mcpTools.length}</span>
                <span className="overview-stat-label">tools</span>
              </div>
              <div className="overview-stat">
                <span className="overview-stat-value overview-stat-value--sm">{entityCount}</span>
                <span className="overview-stat-label">entities</span>
              </div>
            </div>
          )
        }
        expandLabel="View all tools & entities"
      >
        {mcpTools.length > 0 && (
          <div className="panel-tools-grouped">
            {entityGroups.map(([entity, tools]) => (
              <div key={entity} className="panel-entity-group">
                <div className="panel-entity-header">{entity}</div>
                {tools.map((tool) => (
                  <div key={tool.name} className="panel-tool-item">
                    <div className="panel-tool-desc">{generateToolDescription(tool.name)}</div>
                    <div className="panel-tool-name">{tool.name}</div>
                  </div>
                ))}
              </div>
            ))}
          </div>
        )}
      </ExpandableCard>

      {/* ── Data Sources ── */}
      <ExpandableCard
        title="Data Sources"
        badge={<span className="overview-card-badge">RDI</span>}
        summary={
          <div className="overview-sources">
            {["PostgreSQL", "MongoDB", "MySQL"].map((name) => (
              <div key={name} className="overview-source">
                <span className="overview-source-dot" />
                <span>{name}</span>
              </div>
            ))}
          </div>
        }
      />

      <div className="panel-footer-badge">Powered by {mode === "simple_rag" ? "Redis Vector Search" : "Redis Iris"}</div>
    </div>
  );
}

export function ActivityPanel({
  allMessages,
  isOpen,
  onClose,
  contextView,
  onContextViewChange,
  memoryData,
  memoryLoading,
  onRefreshMemory,
  onLoadContext,
  toolsData,
  toolsLoading,
  mode,
}: ActivityPanelProps) {
  const hasMessages = allMessages.length > 0;
  const isRag = mode === "simple_rag";
  const showOverview = !hasMessages && !isRag;

  function handleSwitchToContext() {
    onLoadContext();
    onContextViewChange("redis-context");
  }

  return (
    <aside className={`activity-panel ${isOpen ? "open" : ""}`}>
      <div className="activity-panel-header">
        <div className="activity-panel-title">
          <img src="/RedisLogo.png" alt="" className="panel-title-logo" />
          {isRag ? (
            <span>Redis Vector Search</span>
          ) : (
            <span>Redis Iris</span>
          )}
        </div>
        <button
          className="activity-panel-close"
          onClick={onClose}
          type="button"
          aria-label="Close"
        >
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path d="M4 4L12 12M12 4L4 12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
          </svg>
        </button>
      </div>

      {hasMessages && !isRag && (
        <div className="panel-tab-bar">
          <button
            className={`panel-tab ${contextView === "activity" ? "active" : ""}`}
            onClick={() => onContextViewChange("activity")}
            type="button"
          >
            Activity
          </button>
          <button
            className={`panel-tab ${contextView === "redis-context" ? "active" : ""}`}
            onClick={handleSwitchToContext}
            type="button"
          >
            All Context
          </button>
        </div>
      )}

      <div className="activity-panel-body">
        {showOverview ? (
          <RedisContextContent
            memoryData={memoryData}
            memoryLoading={memoryLoading}
            onRefreshMemory={onRefreshMemory}
            toolsData={toolsData}
            toolsLoading={toolsLoading}
            mode={mode}
          />
        ) : isRag ? (
          <ActivityView allMessages={allMessages} mode={mode} />
        ) : (
          <>
            {contextView === "activity" && (
              <ActivityView allMessages={allMessages} mode={mode} />
            )}
            {contextView === "redis-context" && (
              <RedisContextContent
                memoryData={memoryData}
                memoryLoading={memoryLoading}
                onRefreshMemory={onRefreshMemory}
                toolsData={toolsData}
                toolsLoading={toolsLoading}
                mode={mode}
              />
            )}
          </>
        )}
      </div>
    </aside>
  );
}
