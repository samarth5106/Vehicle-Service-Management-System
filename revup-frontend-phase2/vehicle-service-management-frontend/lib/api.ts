const API_URL = "https://revup-backend-vfuh.onrender.com";

export class ApiError extends Error {
  fields: Record<string, string>;
  constructor(message: string, fields: Record<string, string> = {}) { super(message); this.fields = fields; }
}

export async function api<T = any>(path: string, options?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, { ...options, headers: { "Content-Type": "application/json", ...(options?.headers || {}) }, cache: "no-store" });
  } catch {
    throw new ApiError("Cannot reach the server. Is the backend running on port 5000?");
  }
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new ApiError(data.error || "Request failed", data.fields || {});
  return data as T;
}
