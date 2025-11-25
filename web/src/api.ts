const API_BASE = "http://localhost:5057";

export async function startSession(system_prompt?: string) {
  const res = await fetch(`${API_BASE}/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ system_prompt }),
  });
  if (!res.ok) throw new Error(`Start failed: ${res.status}`);
  return res.json() as Promise<{ session_id: string; degrade_turn: number }>;
}

export async function sendTurn(session_id: string, user: string) {
  const res = await fetch(`${API_BASE}/turn`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id, user }),
  });
  if (!res.ok) throw new Error(`Turn failed: ${res.status}`);
  return res.json();
}

export async function fetchState(session_id: string) {
  const res = await fetch(`${API_BASE}/state/${session_id}`);
  if (!res.ok) throw new Error(`State failed: ${res.status}`);
  return res.json();
}
