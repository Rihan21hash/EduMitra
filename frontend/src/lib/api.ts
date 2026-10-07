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
  review: {
    id: string;
    correct_index: number;
    explanation: string;
  }[];
}

export interface ProgressResponse {
  total_quizzes: number;
  average_improvement: number;
  topics: {
    topic: string;
    pre_score: number | null;
    post_score: number | null;
    total: number;
    improvement: number | null;
  }[];
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

export const api = {
  async getHealth() {
    const res = await fetch(`${API_BASE_URL}/api/health`);
    return handleResponse<{
      status: string;
      ollama_connected: boolean;
      active_model: string;
      available_models: string[];
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

  async createQuiz(payload: {
    user_id: string;
    response_id: string;
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
