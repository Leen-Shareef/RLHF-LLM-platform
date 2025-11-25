import React, { useState } from "react";
import { startSession, sendTurn, fetchState } from "./api";
import TurnRow from "./components/TurnRow";
import { RecordRow } from "./types";


export default function App() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [systemPrompt, setSystemPrompt] = useState("");
  const [input, setInput] = useState("");
  const [rows, setRows] = useState<RecordRow[]>([]);
  const [turn, setTurn] = useState(0);
  const [degradeTurn, setDegradeTurn] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);

  const start = async () => {
    setLoading(true);
    try {
      const res = await startSession(systemPrompt || undefined);
      setSessionId(res.session_id);
      setDegradeTurn(res.degrade_turn);
      setRows([]);
      setTurn(0);
    } finally {
      setLoading(false);
    }
  };

  const send = async () => {
    if (!sessionId || !input.trim()) return;
    if (turn >= 5) return alert("Five turns completed.");
    setLoading(true);
    try {
      const rec = await sendTurn(sessionId, input.trim());
      setRows((r) => [...r, rec]);
      setTurn(rec.turn);
      setInput("");
    } finally {
      setLoading(false);
    }
  };

  const dump = async () => {
    if (!sessionId) return;
    const s = await fetchState(sessionId);
    const blob = new Blob([JSON.stringify(s, null, 2)], { type: "application/json" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `state-${sessionId}.json`;
    a.click();
  };

  return (
    <div className="wrap">
      <header>
        <h1>Two-Model Live Runner</h1>
        <div className="sub">White/Clean · Side-by-Side (Weak | Strong) · Local API</div>
      </header>

      {!sessionId ? (
        <div className="card">
          <label className="lbl">System Prompt (applies to all 5 turns)</label>
          <textarea
            placeholder="You are a helpful assistant. Always answer concisely and correctly..."
            value={systemPrompt}
            onChange={(e) => setSystemPrompt(e.target.value)}
          />
          <button onClick={start} disabled={loading}>
            {loading ? "Starting..." : "Start Session"}
          </button>
        </div>
      ) : (
        <>
          <div className="bar">
            <div>Session: <code>{sessionId}</code></div>
            <div>Turn: {turn}/5</div>
            <div>Weak temp boosted on turn: {degradeTurn}</div>
            <div className="spacer" />
            <button onClick={dump}>Download JSON</button>
          </div>

          <div className="card">
            <label className="lbl">Your message</label>
            <input
              type="text"
              placeholder="Type your message…"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && send()}
            />
            <button onClick={send} disabled={loading || turn >= 5 || !input.trim()}>
              {loading ? "Sending..." : turn >= 5 ? "Done (5/5)" : "Send Turn"}
            </button>
          </div>

          <div className="list">
            {rows.map((r) => <TurnRow key={r.turn} row={r} />)}
          </div>
        </>
      )}
    </div>
  );
}
