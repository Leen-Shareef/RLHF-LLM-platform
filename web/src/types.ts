export type RecordRow = {
    ts: string;
    session_id: string;
    turn: number;
    user: string;
    weak_model: string;
    strong_model: string;
    weak_answer: string;
    strong_answer: string;
    weak_latency_sec: number;
    strong_latency_sec: number;
    memory: { user_name: string | null; preferences: string[] };
    weak_degraded: boolean;
    degrade_turn: number;
  };
  