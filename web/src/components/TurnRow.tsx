import React from "react";
import { RecordRow } from "../types";

export default function TurnRow({ row }: { row: RecordRow }) {
  return (
    <div className="turn">
      <div className="turn-header">
        <div className="pill">Turn {row.turn}</div>
        {row.weak_degraded && <div className="pill warning">weak temp↑</div>}
        <div className="user">{row.user}</div>
      </div>
      <div className="cols">
        <div className="col">
          <div className="col-title">Weak</div>
          <div className="answer">{row.weak_answer}</div>
          <div className="meta">model: {row.weak_model} · {row.weak_latency_sec}s</div>
        </div>
        <div className="col">
          <div className="col-title strong">Strong</div>
          <div className="answer">{row.strong_answer}</div>
          <div className="meta">model: {row.strong_model} · {row.strong_latency_sec}s</div>
        </div>
      </div>
    </div>
  );
}




