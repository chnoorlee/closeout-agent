import {
  Activity,
  Archive,
  ArrowDownToLine,
  Bot,
  Box,
  Check,
  CheckCircle2,
  CircleDashed,
  Clock3,
  FileCheck2,
  Files,
  Fingerprint,
  Gauge,
  History,
  ListChecks,
  Play,
  RefreshCw,
  Search,
  ShieldCheck,
  Sparkles,
  TriangleAlert,
  Upload,
  Wrench,
  XCircle,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";

import { api } from "./api";
import type { Health, Run, StageStatus, Verdict } from "./types";

const stageIcons = {
  intake: Fingerprint,
  map: ListChecks,
  verify: Search,
  close: Wrench,
  seal: Archive,
};

const verdictIcons = {
  queued: CircleDashed,
  verified: CheckCircle2,
  repaired: Wrench,
  blocked: XCircle,
};

function label(value: string) {
  return value.replaceAll("-", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function relativeTime(value: string) {
  const seconds = Math.max(0, Math.floor((Date.now() - new Date(value).getTime()) / 1000));
  if (seconds < 60) return `${seconds}s ago`;
  const minutes = Math.floor(seconds / 60);
  return minutes < 60 ? `${minutes}m ago` : `${Math.floor(minutes / 60)}h ago`;
}

function StatusMark({ status }: { status: StageStatus }) {
  if (status === "completed") return <Check aria-hidden="true" />;
  if (status === "active") return <RefreshCw aria-hidden="true" className="spin" />;
  if (status === "failed") return <XCircle aria-hidden="true" />;
  return <span className="status-dot" aria-hidden="true" />;
}

function App() {
  const [health, setHealth] = useState<Health | null>(null);
  const [runs, setRuns] = useState<Run[]>([]);
  const [run, setRun] = useState<Run | null>(null);
  const [starting, setStarting] = useState(false);
  const [workspaceFiles, setWorkspaceFiles] = useState<File[]>([]);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const [nextHealth, nextRuns] = await Promise.all([api.health(), api.runs()]);
      setHealth(nextHealth);
      setRuns(nextRuns);
      setRun((current) => current ?? nextRuns[0] ?? null);
      setError(null);
    } catch (nextError) {
      setError(nextError instanceof Error ? nextError.message : "Workspace unavailable");
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (!run || !["queued", "running"].includes(run.status)) return;
    const timer = window.setInterval(() => {
      void api
        .run(run.id)
        .then((nextRun) => {
          setRun(nextRun);
          setRuns((current) => [nextRun, ...current.filter((item) => item.id !== nextRun.id)]);
        })
        .catch((nextError: unknown) => {
          setError(nextError instanceof Error ? nextError.message : "Run update failed");
        });
    }, 400);
    return () => window.clearInterval(timer);
  }, [run]);

  const startRun = async () => {
    setStarting(true);
    setError(null);
    try {
      const nextRun = workspaceFiles.length
        ? await api.startWorkspace(workspaceFiles)
        : await api.startDemo();
      setRun(nextRun);
      setRuns((current) => [nextRun, ...current]);
    } catch (nextError) {
      setError(nextError instanceof Error ? nextError.message : "Run could not start");
    } finally {
      setStarting(false);
    }
  };

  const completion = useMemo(() => {
    if (!run?.stages.length) return 0;
    return Math.round(
      (run.stages.filter((stage) => stage.status === "completed").length / run.stages.length) * 100,
    );
  }, [run]);

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand-row">
          <div className="brand-mark" aria-hidden="true">
            <ShieldCheck />
          </div>
          <div>
            <div className="brand-name">Closeout</div>
            <div className="brand-caption">Delivery operations</div>
          </div>
        </div>

        <nav className="primary-nav" aria-label="Workspace">
          <button type="button" className="nav-item active">
            <Gauge aria-hidden="true" /> Run workspace
          </button>
          <button type="button" className="nav-item" onClick={() => document.querySelector("#ledger")?.scrollIntoView()}>
            <FileCheck2 aria-hidden="true" /> Requirements
          </button>
          <button type="button" className="nav-item" onClick={() => document.querySelector("#activity")?.scrollIntoView()}>
            <Activity aria-hidden="true" /> Activity
          </button>
          <button type="button" className="nav-item" disabled={!run?.bundle_ready}>
            <Box aria-hidden="true" /> Bundles
          </button>
        </nav>

        <div className="history-block">
          <div className="sidebar-label">
            <span>Recent runs</span>
            <History aria-hidden="true" />
          </div>
          <div className="run-history">
            {runs.length ? (
              runs.slice(0, 4).map((item) => (
                <button
                  key={item.id}
                  type="button"
                  className={`history-item ${item.id === run?.id ? "selected" : ""}`}
                  onClick={() => setRun(item)}
                >
                  <span className={`run-light ${item.status}`} aria-hidden="true" />
                  <span>
                    <strong>{item.name.split(" /")[0]}</strong>
                    <small>{relativeTime(item.created_at)}</small>
                  </span>
                </button>
              ))
            ) : (
              <div className="history-empty">No runs yet</div>
            )}
          </div>
        </div>

        <div className="runtime-block">
          <div className="runtime-line">
            <span className={`connection-dot ${health ? "online" : ""}`} />
            {health ? "Runtime connected" : "Connecting"}
          </div>
          <div className="runtime-detail">{health?.model ?? "Gemini 3.5 Flash"}</div>
          <div className="runtime-detail">{health?.framework ?? "Google ADK 2"}</div>
        </div>
      </aside>

      <main className="main-area">
        <header className="topbar">
          <div>
            <div className="eyebrow">Taskmaster / final submission</div>
            <h1>{run?.name ?? "Closeout / Devpost submission"}</h1>
          </div>
          <div className="topbar-actions">
            <span className={`mode-badge ${health?.ai_mode === "live-gemini" ? "live" : "demo"}`}>
              <Bot aria-hidden="true" />
              {health?.ai_mode === "live-gemini" ? "Live Gemini" : "Deterministic demo"}
            </span>
            <button
              type="button"
              className="primary-button"
              onClick={() => void startRun()}
              disabled={starting || run?.status === "running" || run?.status === "queued"}
            >
              {starting || run?.status === "running" || run?.status === "queued" ? (
                <RefreshCw aria-hidden="true" className="spin" />
              ) : (
                <Play aria-hidden="true" />
              )}
              {run?.status === "running" || run?.status === "queued" ? "Running" : "Start closeout"}
            </button>
          </div>
        </header>

        {error ? (
          <div className="error-banner" role="alert">
            <TriangleAlert aria-hidden="true" />
            <span>{error}</span>
            <button type="button" onClick={() => void load()} aria-label="Retry connection" title="Retry connection">
              <RefreshCw aria-hidden="true" />
            </button>
          </div>
        ) : null}

        <section className="stage-band" aria-label="Closeout stages">
          <div className="stage-progress" style={{ "--progress": `${completion}%` } as React.CSSProperties} />
          {(run?.stages ?? [
            { id: "intake", label: "Intake", status: "waiting", summary: "Waiting" },
            { id: "map", label: "Map", status: "waiting", summary: "Waiting" },
            { id: "verify", label: "Verify", status: "waiting", summary: "Waiting" },
            { id: "close", label: "Close", status: "waiting", summary: "Waiting" },
            { id: "seal", label: "Seal", status: "waiting", summary: "Waiting" },
          ] satisfies Array<{ id: string; label: string; status: StageStatus; summary: string }>).map((stage) => {
            const Icon = stageIcons[stage.id as keyof typeof stageIcons] ?? CircleDashed;
            return (
              <div key={stage.id} className={`stage-item ${stage.status}`}>
                <div className="stage-icon">
                  <Icon aria-hidden="true" />
                  <span className="stage-state"><StatusMark status={stage.status} /></span>
                </div>
                <strong>{stage.label}</strong>
                <small>{stage.summary}</small>
              </div>
            );
          })}
        </section>

        {run ? (
          <RunWorkspace run={run} />
        ) : (
          <Preflight files={workspaceFiles} onFiles={setWorkspaceFiles} />
        )}
      </main>
    </div>
  );
}

function Preflight({ files, onFiles }: { files: File[]; onFiles: (files: File[]) => void }) {
  return (
    <div className="preflight-grid">
      <section className="panel preflight-panel">
        <div className="section-heading">
          <div>
            <span className="section-kicker">Ready state</span>
            <h2>Run briefing</h2>
          </div>
          <span className="ready-badge"><CheckCircle2 aria-hidden="true" /> {files.length ? "Inputs ready" : "Fixture ready"}</span>
        </div>
        <dl className="briefing-list">
          <div><dt>Workspace</dt><dd>{files.length ? "Uploaded workspace" : "Closeout / Devpost"}</dd></div>
          <div><dt>Target</dt><dd>Hackathon submission</dd></div>
          <div><dt>Policy</dt><dd>Bounded, reversible actions</dd></div>
          <div><dt>Expected inputs</dt><dd>{files.length ? `${files.length} selected` : "5 demo artifacts"}</dd></div>
        </dl>
        <div className="upload-row">
          <label className="upload-button">
            <Upload aria-hidden="true" /> Add workspace files
            <input
              type="file"
              multiple
              accept=".csv,.json,.md,.mmd,.svg,.txt,.yaml,.yml"
              onChange={(event) => onFiles(Array.from(event.target.files ?? []))}
            />
          </label>
          {files.length ? (
            <span className="file-selection" title={files.map((file) => file.name).join(", ")}>
              {files.map((file) => file.name).join(", ")}
            </span>
          ) : null}
        </div>
        <div className="preflight-note">
          <Sparkles aria-hidden="true" />
          <span>Environment fingerprint and delivery policy are ready.</span>
        </div>
      </section>
      <section className="panel architecture-panel">
        <div className="section-heading">
          <div>
            <span className="section-kicker">Execution topology</span>
            <h2>Agent runtime</h2>
          </div>
        </div>
        <img src="/closeout-system.png" alt="Closeout system architecture" />
      </section>
    </div>
  );
}

function RunWorkspace({ run }: { run: Run }) {
  return (
    <>
      <section className="metrics-band" aria-label="Run metrics">
        <Metric label="Evidence coverage" value={`${run.metrics.evidence_coverage}%`} tone="green" />
        <Metric label="Requirements" value={String(run.metrics.requirements)} />
        <Metric label="Autonomous actions" value={String(run.metrics.autonomous_actions)} tone="blue" />
        <Metric label="Repaired" value={String(run.metrics.repaired)} tone="amber" />
        <Metric label="Blocked" value={String(run.metrics.blocked)} tone={run.metrics.blocked ? "red" : "neutral"} />
      </section>

      <div className="workspace-grid">
        <section className="panel ledger-panel" id="ledger">
          <div className="section-heading">
            <div>
              <span className="section-kicker">Requirement graph</span>
              <h2>Evidence ledger</h2>
            </div>
            <span className="table-count">{run.requirements.length} obligations</span>
          </div>
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Requirement</th>
                  <th>Evidence</th>
                  <th>Confidence</th>
                  <th>Verdict</th>
                </tr>
              </thead>
              <tbody>
                {run.requirements.length ? run.requirements.map((requirement) => (
                  <tr key={requirement.id}>
                    <td data-label="Requirement">
                      <strong>{requirement.title}</strong>
                      <small>{requirement.source}</small>
                    </td>
                    <td data-label="Evidence">
                      <div className="evidence-list">
                        {requirement.evidence.map((item) => <code key={item}>{item}</code>)}
                      </div>
                      {requirement.action ? <small className="action-note">{requirement.action}</small> : null}
                    </td>
                    <td data-label="Confidence"><span className="confidence">{Math.round(requirement.confidence * 100)}%</span></td>
                    <td data-label="Verdict"><VerdictBadge verdict={requirement.verdict} /></td>
                  </tr>
                )) : (
                  <tr><td colSpan={4} className="table-empty">Mapping requirements...</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </section>

        <aside className="panel activity-panel" id="activity">
          <div className="section-heading">
            <div>
              <span className="section-kicker">Audit trace</span>
              <h2>Activity</h2>
            </div>
            <Activity aria-hidden="true" />
          </div>
          <div className="event-list">
            {run.events.length ? [...run.events].reverse().map((event) => (
              <article className="event-item" key={event.id}>
                <span className={`event-mark ${event.status}`}><StatusMark status={event.status} /></span>
                <div>
                  <div className="event-meta"><span>{label(event.stage)}</span><time>{relativeTime(event.created_at)}</time></div>
                  <strong>{event.title}</strong>
                  <p>{event.detail}</p>
                  <code>{event.actor}</code>
                </div>
              </article>
            )) : <div className="activity-empty"><Clock3 aria-hidden="true" /> Awaiting first event</div>}
          </div>
        </aside>
      </div>

      <section className={`bundle-strip ${run.bundle_ready ? "ready" : ""}`}>
        <div className="bundle-icon"><Files aria-hidden="true" /></div>
        <div>
          <span className="section-kicker">Closeout bundle</span>
          <strong>{run.bundle_ready ? "Sealed and reproducible" : "Pending seal stage"}</strong>
          <code>{run.bundle_sha256 ? `SHA-256 ${run.bundle_sha256}` : "Hash unavailable"}</code>
        </div>
        <a
          className={`download-button ${run.bundle_ready ? "" : "disabled"}`}
          href={run.bundle_ready ? api.bundleUrl(run.id) : undefined}
          aria-disabled={!run.bundle_ready}
        >
          <ArrowDownToLine aria-hidden="true" /> Download bundle
        </a>
      </section>
    </>
  );
}

function Metric({ label: metricLabel, value, tone = "neutral" }: { label: string; value: string; tone?: string }) {
  return <div className={`metric ${tone}`}><strong>{value}</strong><span>{metricLabel}</span></div>;
}

function VerdictBadge({ verdict }: { verdict: Verdict }) {
  const Icon = verdictIcons[verdict];
  return <span className={`verdict ${verdict}`}><Icon aria-hidden="true" />{label(verdict)}</span>;
}

export default App;
