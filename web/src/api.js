const API_BASE = "";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  const text = await response.text();
  const payload = text ? JSON.parse(text) : null;
  if (!response.ok) {
    const detail = payload?.detail || response.statusText;
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return payload;
}

export function getHealth() {
  return request("/api/health");
}

export function sendChat(message, history) {
  return request("/api/chat", {
    method: "POST",
    body: JSON.stringify({ message, history, top_k: 3 }),
  });
}

export function getCases(query = "", limit = 30) {
  const params = new URLSearchParams({ limit: String(limit) });
  if (query.trim()) params.set("q", query.trim());
  return request(`/api/cases?${params}`);
}

export function getResults(limit = 50) {
  return request(`/api/results?limit=${limit}`);
}

export function startRun(limit) {
  return request("/api/runs", {
    method: "POST",
    body: JSON.stringify({ limit }),
  });
}

export function getRun(jobId) {
  return request(`/api/runs/${jobId}`);
}
