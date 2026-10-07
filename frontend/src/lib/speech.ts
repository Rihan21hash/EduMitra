// Speech Recognition helper for Web Speech API

export interface SpeechListenerOptions {
  locale: string; // "mr-IN", "hi-IN", "en-IN"
  onResult: (transcript: string) => void;
  onError: (error: string) => void;
  onEnd: () => void;
}

export function isSpeechSupported(): boolean {
  if (typeof window === "undefined") return false;
  return Boolean(
    (window as any).SpeechRecognition ||
    (window as any).webkitSpeechRecognition
  );
}

export function startSpeechRecognition(options: SpeechListenerOptions): { stop: () => void } | null {
  if (!isSpeechSupported()) {
    options.onError("Speech recognition not supported in this browser.");
    return null;
  }

  const SpeechClass = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
  const recognition = new SpeechClass();

  recognition.lang = options.locale;
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;
  recognition.continuous = false;

  recognition.onresult = (event: any) => {
    if (event.results && event.results[0] && event.results[0][0]) {
      const transcript = event.results[0][0].transcript;
      options.onResult(transcript);
    }
  };

  recognition.onerror = (event: any) => {
    options.onError(event.error || "Speech error");
  };

  recognition.onend = () => {
    options.onEnd();
  };

  try {
    recognition.start();
  } catch (err: any) {
    options.onError(err.message || "Failed to start microphone");
    return null;
  }

  return {
    stop: () => {
      try {
        recognition.stop();
      } catch (_) {}
    },
  };
}
