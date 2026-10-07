// Dev-time validator for content.js
import * as contentModule from "@/content";

export function validateContent() {
  if (process.env.NODE_ENV === "production") return;

  const errors: string[] = [];

  function checkObject(obj: any, path: string) {
    if (!obj || typeof obj !== "object") return;

    // Check if this looks like a trilingual string object
    const keys = Object.keys(obj);
    const hasAnyLang = keys.includes("en") || keys.includes("hi") || keys.includes("mr");
    const isLangObject = hasAnyLang && keys.every(k => ["en", "hi", "mr"].includes(k));

    if (isLangObject) {
      // If all lang values are arrays (e.g. exampleQuestions), recurse — don't check as strings
      const allArrays = ["en", "hi", "mr"].every(l => Array.isArray(obj[l]));
      if (allArrays) {
        for (const [k, v] of Object.entries(obj)) {
          checkObject(v, `${path}.${k}`);
        }
        return;
      }
      for (const lang of ["en", "hi", "mr"]) {
        if (typeof obj[lang] !== "string") {
          errors.push(`Missing '${lang}' in content key: ${path}`);
        } else if (obj[lang].trim() === "" && !path.includes("role")) {
          // Allow empty only for explicitly optional fields like role
          errors.push(`Empty string for '${lang}' in content key: ${path}`);
        }
      }
      return;
    }

    // Recurse into nested properties/arrays
    for (const [k, v] of Object.entries(obj)) {
      if (typeof v === "object" && v !== null) {
        checkObject(v, path ? `${path}.${k}` : k);
      }
    }
  }

  checkObject(contentModule, "content");

  if (errors.length > 0) {
    console.warn("⚠️ EduMitra content.js validation warnings:", errors);
  } else {
    console.info("✅ EduMitra content.js validated: all trilingual strings complete.");
  }
}
