import type { AgentMode, DomainConfig, PromptCard } from "../types";
import { ComposerBar } from "./ComposerBar";

function EyebrowIcon({ eyebrow }: { eyebrow: string }) {
  const size = 12;
  const props = { width: size, height: size, viewBox: "0 0 16 16", fill: "none", stroke: "currentColor", strokeWidth: "1.5", strokeLinecap: "round" as const, strokeLinejoin: "round" as const };
  switch (eyebrow) {
    case "Context":
      return <svg {...props}><circle cx="4" cy="4" r="2" /><circle cx="12" cy="4" r="2" /><circle cx="8" cy="12" r="2" /><path d="M5.5 5.5L7 10.5M10.5 5.5L9 10.5" /></svg>;
    case "Memory":
      return <svg {...props}><path d="M8 2C5 2 3 4 3 6.5c0 1.5.8 2.8 2 3.5v2.5a.5.5 0 00.5.5h5a.5.5 0 00.5-.5V10c1.2-.7 2-2 2-3.5C13 4 11 2 8 2z" /><path d="M6 14h4" /></svg>;
    case "Cached":
      return <svg {...props}><path d="M9 2L5 9h3l-1 5 4-7H8l1-5z" /></svg>;
    case "Search":
      return <svg {...props}><circle cx="7" cy="7" r="4" /><path d="M10 10l3.5 3.5" /></svg>;
    default:
      return null;
  }
}

type EmptyStateProps = {
  domain: DomainConfig;
  input: string;
  onInputChange: (value: string) => void;
  onSubmit: () => void;
  isLoading: boolean;
  mode: AgentMode;
  onModeChange: (mode: AgentMode) => void;
  starterPrompts: PromptCard[];
  onPrefill: (prompt: string) => void;
  showRealtimeMode: boolean;
};

export function EmptyState({
  domain,
  input,
  onInputChange,
  onSubmit,
  isLoading,
  mode,
  onModeChange,
  starterPrompts,
  onPrefill,
  showRealtimeMode,
}: EmptyStateProps) {
  return (
    <div className="empty-state">
      <div className="mode-toggle">
        <button
          className={`mode-toggle-option ${mode === "simple_rag" ? "active" : ""}`}
          onClick={() => onModeChange("simple_rag")}
          type="button"
        >
          Simple RAG
        </button>
        {showRealtimeMode && (
          <button
            className={`mode-toggle-option context ${mode === "context_surfaces" ? "active" : ""}`}
            onClick={() => onModeChange("context_surfaces")}
            type="button"
          >
            Real-time Context
          </button>
        )}
      </div>

      <h1 className="empty-state-title">
        {domain?.hero_title ?? "How can we help?"}
      </h1>

      <ComposerBar
        input={input}
        onInputChange={onInputChange}
        onSubmit={onSubmit}
        isLoading={isLoading}
        placeholder={
          domain?.placeholder_text ??
          "Ask about your order, delivery status, or policies..."
        }
        variant="hero"
      />

      {starterPrompts.length > 0 && (() => {
        const groups = new Map<string, PromptCard[]>();
        for (const p of starterPrompts) {
          const key = p.eyebrow || "Other";
          if (!groups.has(key)) groups.set(key, []);
          groups.get(key)!.push(p);
        }
        return (
          <div className="starter-strip">
            {[...groups.entries()].map(([eyebrow, cards]) => (
              <div key={eyebrow} className="starter-group">
                <span className="starter-group-label">
                  <EyebrowIcon eyebrow={eyebrow} />
                </span>
                <div className="starter-chips">
                  {cards.map((p) => (
                    <button
                      key={p.title}
                      className="starter-chip"
                      onClick={() => onPrefill(p.prompt)}
                      type="button"
                    >
                      {p.title}
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>
        );
      })()}
    </div>
  );
}
