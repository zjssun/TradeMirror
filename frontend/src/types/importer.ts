export interface MappingCandidate {
  target: string;
  source: string | null;
  confidence: "high" | "medium" | "none";
}

export interface ImportPreview {
  preview_id: string;
  filename: string;
  encoding: string;
  delimiter: string;
  columns: string[];
  mappings: MappingCandidate[];
  sample_rows: Record<string, string>[];
  timezone_hint: string | null;
}

export interface ImportIssue {
  row_number: number;
  message: string;
}

export interface ImportResult {
  batch_id: number;
  total_rows: number;
  imported_rows: number;
  duplicate_rows: number;
  error_rows: number;
  issues: ImportIssue[];
}
