export interface PipelineStatus {
  preprocessing: boolean;
  paddleocr_success: boolean;
  trocr_success: boolean;
  fusion_applied: boolean;
  vision_used: boolean;
  ocr_execution_mode?: "local";
}

export interface ExtractionResponse {
  id: string;
  filename: string;
  extracted_text: string;
  user_prompt: string;
  ai_response: Record<string, unknown> | unknown[];
  created_at: string;
  ocr_execution_mode?: "local";
  pipeline?: PipelineStatus;
  fusion_context?: string;
  paddleocr_output?: Record<string, unknown>;
  trocr_output?: Record<string, unknown>;
}

export type JsonValue =
  | string
  | number
  | boolean
  | null
  | JsonValue[]
  | { [key: string]: JsonValue };
