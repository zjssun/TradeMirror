export interface EngineRuntime {
  baseUrl: string;
  token: string;
}

export interface HealthResponse {
  status: "healthy";
  engine_version: string;
  database: "ready";
  server_time: string;
}
