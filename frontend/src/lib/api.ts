const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export interface UserResponse {
  id: string;
  display_name: string;
  preferred_language: string;
  default_level: string;
  created_at: string;
}

export interface QuestionResponse {
  conversation_id: string;
  question_id: string;
  response_id: string;
  detected_language: string;
  intent: string;
  subject: string;
  topic: string;
  level: string;
  exam_marks?: number | null;
  answer: {
    text: string;
    language: string;
  };
  validation: {
    passed: boolean;
    notes: string[];
  };
  meta: {
    model: string;
    latency_ms: number;
    timings: {
      analysis_ms: number;
      generation_ms: number;
      validation_ms: number;
    };
  };
  explain_again_count?: number;
}

export interface ConversationSummary {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface MessageItem {
  question_id: string;
  response_id: string;
  raw_text: string;
  answer_text: string;
  language: string;
  level: string;
  exam_marks?: number | null;
  intent: string;
  subject: string;
  topic: string;
  validation_passed: boolean;
  explain_again_count: number;
  created_at: string;
}

export interface ConversationDetail {
  id: string;
  title: string;
  messages: MessageItem[];
}

export interface QuizQuestionClient {
  id: string;
  prompt: string;
  options: string[];
}

export interface QuizCreateResponse {
  quiz_id: string;
  topic: string;
  phase: string;
  questions: QuizQuestionClient[];
}

export interface QuizSubmitResponse {
  score: number;
  total: number;
  percentage: number;
  improvement_delta?: number | null;
  review: {
    id: string;
    correct_index: number;
    explanation: string;
  }[];
}

export interface TopicProgress {
  topic: string;
  baseline_score?: number | null;
  latest_score?: number | null;
  pre_score: number | null;
  post_score: number | null;
  total: number;
  improvement: number | null;
  attempts_count?: number;
}

export interface ProgressTimelineItem {
  topic: string;
  score: number;
  total: number;
  percentage: number;
  phase: string;
  created_at: string;
}

export interface ProgressResponse {
  total_quizzes: number;
  average_improvement: number;
  questions_asked?: number;
  languages_used?: string[];
  levels_used?: string[];
  satisfaction_pct?: number;
  topics: TopicProgress[];
  timeline?: ProgressTimelineItem[];
}

export interface ResponseVariantItem {
  language: string;
  content: string;
  origin: string;
  created_at?: string;
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errBody = { code: "HTTP_ERROR", message: res.statusText };
    try {
      const data = await res.json();
      if (data.error) errBody = data.error;
    } catch (_) {}
    const err: any = new Error(errBody.message || "Request failed");
    err.code = errBody.code || "INTERNAL";
    throw err;
  }
  return res.json();
}

/**
 * SSE Parser helper for reading StreamingResponse streams.
 */
async function processSSEStream(
  res: Response,
  callbacks: {
    onEvent?: (event: string, data: any) => void;
    onError?: (err: any) => void;
  }
) {
  if (!res.body) return;
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      const parts = buffer.split("\n\n");
      buffer = parts.pop() || "";

      for (const block of parts) {
        if (!block.trim()) continue;
        let eventType = "message";
        let dataStr = "";

        for (const line of block.split("\n")) {
          if (line.startsWith("event:")) {
            eventType = line.replace("event:", "").trim();
          } else if (line.startsWith("data:")) {
            dataStr = line.replace("data:", "").trim();
          }
        }

        if (dataStr) {
          try {
            const parsed = JSON.parse(dataStr);
            callbacks.onEvent?.(eventType, parsed);
          } catch (_) {
            callbacks.onEvent?.(eventType, dataStr);
          }
        }
      }
    }
  } catch (err: any) {
    if (err.name !== "AbortError") {
      callbacks.onError?.(err);
    }
  } finally {
    reader.releaseLock();
  }
}

export const api = {
  async getHealth() {
    const res = await fetch(`${API_BASE_URL}/api/health`);
    return handleResponse<{
      status: string;
      ollama_connected: boolean;
      active_model: string;
      available_models: string[];
      model_loaded?: boolean;
    }>(res);
  },

  async createUser(preferredLanguage: string = "mr", defaultLevel: string = "beginner") {
    const res = await fetch(`${API_BASE_URL}/api/users`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        display_name: "Guest Student",
        preferred_language: preferredLanguage,
        default_level: defaultLevel,
      }),
    });
    return handleResponse<UserResponse>(res);
  },

  async askQuestion(payload: {
    user_id: string;
    conversation_id?: string | null;
    text: string;
    level: string;
    exam_marks?: number | null;
    language_override?: string;
  }) {
    const res = await fetch(`${API_BASE_URL}/api/question`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    return handleResponse<QuestionResponse>(res);
  },

  async askQuestionStream(
    payload: {
      user_id: string;
      conversation_id?: string | null;
      text: string;
      level: string;
      exam_marks?: number | null;
      language_override?: string;
    },
    callbacks: {
      onMeta?: (meta: any) => void;
      onToken?: (token: string) => void;
      onDone?: (data: any) => void;
      onValidation?: (val: any) => void;
      onError?: (err: any) => void;
    },
    signal?: AbortSignal
  ) {
    const res = await fetch(`${API_BASE_URL}/api/question/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal,
    });

    if (!res.ok) {
      let errBody = { message: "Streaming connection failed" };
      try {
        errBody = await res.json();
      } catch (_) {}
      throw new Error(errBody.message || "Failed to start stream");
    }

    await processSSEStream(res, {
      onEvent: (event, data) => {
        if (event === "meta") callbacks.onMeta?.(data);
        else if (event === "token") callbacks.onToken?.(data.token || "");
        else if (event === "done") callbacks.onDone?.(data);
        else if (event === "validation") callbacks.onValidation?.(data);
        else if (event === "error") callbacks.onError?.(data);
      },
      onError: callbacks.onError,
    });
  },

  async simplify(payload: {
    user_id: string;
    response_id: string;
    mode: "simplify" | "explain_again";
  }) {
    const res = await fetch(`${API_BASE_URL}/api/simplify`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    return handleResponse<QuestionResponse>(res);
  },

  async examAnswer(payload: {
    user_id: string;
    conversation_id?: string | null;
    response_id?: string | null;
    text?: string | null;
    marks: number;
    language_override?: string;
  }) {
    const res = await fetch(`${API_BASE_URL}/api/exam-answer`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    return handleResponse<QuestionResponse>(res);
  },

  async followup(payload: {
    user_id: string;
    response_id: string;
    action: "example" | "translate" | "summarize";
    target_language?: string;
  }) {
    const res = await fetch(`${API_BASE_URL}/api/followup`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    return handleResponse<QuestionResponse>(res);
  },

  async getResponseVariants(responseId: string) {
    const res = await fetch(`${API_BASE_URL}/api/response/${responseId}/variants`);
    return handleResponse<{ response_id: string; variants: ResponseVariantItem[] }>(res);
  },

  async getOrCreateVariant(responseId: string, language: string) {
    const res = await fetch(`${API_BASE_URL}/api/response/${responseId}/variant`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ language }),
    });
    return handleResponse<{ response_id: string; language: string; content: string; origin: string }>(res);
  },

  async streamVariant(
    responseId: string,
    language: string,
    callbacks: {
      onToken?: (token: string) => void;
      onDone?: (data: any) => void;
      onError?: (err: any) => void;
    },
    signal?: AbortSignal
  ) {
    const res = await fetch(`${API_BASE_URL}/api/response/${responseId}/variant/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ language }),
      signal,
    });

    await processSSEStream(res, {
      onEvent: (event, data) => {
        if (event === "token") callbacks.onToken?.(data.token || "");
        else if (event === "done") callbacks.onDone?.(data);
        else if (event === "error") callbacks.onError?.(data);
      },
      onError: callbacks.onError,
    });
  },

  async createQuiz(payload: {
    user_id: string;
    response_id?: string | null;
    topic_text?: string | null;
    language?: string;
    num_questions?: number;
    phase?: "pre" | "post";
  }) {
    const res = await fetch(`${API_BASE_URL}/api/quiz`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    return handleResponse<QuizCreateResponse>(res);
  },

  async submitQuiz(quiz_id: string, payload: {
    user_id: string;
    phase: string;
    answers: Record<string, number>;
  }) {
    const res = await fetch(`${API_BASE_URL}/api/quiz/${quiz_id}/submit`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    return handleResponse<QuizSubmitResponse>(res);
  },

  async getProgress(user_id: string) {
    const res = await fetch(`${API_BASE_URL}/api/progress?user_id=${user_id}`);
    return handleResponse<ProgressResponse>(res);
  },

  async getHistory(user_id: string) {
    const res = await fetch(`${API_BASE_URL}/api/history?user_id=${user_id}`);
    return handleResponse<ConversationSummary[]>(res);
  },

  async getConversation(id: string) {
    const res = await fetch(`${API_BASE_URL}/api/conversations/${id}`);
    return handleResponse<ConversationDetail>(res);
  },

  async deleteConversation(id: string) {
    const res = await fetch(`${API_BASE_URL}/api/conversations/${id}`, {
      method: "DELETE",
    });
    return handleResponse<{ success: boolean; id: string }>(res);
  },

  async submitFeedback(payload: { response_id: string; rating: number }) {
    const res = await fetch(`${API_BASE_URL}/api/feedback`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    return handleResponse<{ success: boolean; rating: number }>(res);
  },
};
