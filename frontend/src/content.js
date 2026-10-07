// frontend/src/content.js
// ---------------------------------------------------------------------------
// EduMitra — single source of truth for ALL editable content.
// Edit, save, and the app hot-reloads. No other file should contain visible text.
// Language keys: en = English, hi = Hindi, mr = Marathi.
// Every text object MUST have all three keys.
// ---------------------------------------------------------------------------

// Turn unfinished features on/off without touching code.
export const featureFlags = {
  voiceInput: true,
  examMode: true,
  quiz: true,
  progress: true,
  streaming: false,
};

export const site = {
  name: { en: "EduMitra", hi: "एडुमित्र", mr: "एडुमित्र" },
  fullName: {
    en: "EduMitra: Multilingual Academic Support System",
    hi: "एडुमित्र: बहुभाषी शैक्षणिक सहायता प्रणाली",
    mr: "एडुमित्र: बहुभाषिक शैक्षणिक सहाय्य प्रणाली",
  },
  tagline: {
    en: "Learn in your language. Understand at your level.",
    hi: "अपनी भाषा में सीखें। अपने स्तर पर समझें।",
    mr: "तुमच्या भाषेत शिका. तुमच्या पातळीवर समजून घ्या.",
  },
  event: { en: "AARAMBH · WCE-Hackathon 2026", hi: "AARAMBH · WCE-Hackathon 2026", mr: "AARAMBH · WCE-Hackathon 2026" },
  institution: {
    en: "Walchand College of Engineering, Sangli",
    hi: "वालचंद कॉलेज ऑफ इंजीनियरिंग, सांगली",
    mr: "वालचंद अभियांत्रिकी महाविद्यालय, सांगली",
  },
};

export const nav = {
  chat: { en: "Chat", hi: "चैट", mr: "चॅट" },
  progress: { en: "Progress", hi: "प्रगति", mr: "प्रगती" },
  tutor: { en: "Tutor", hi: "शिक्षक", mr: "मार्गदर्शक" },
  history: { en: "History", hi: "इतिहास", mr: "इतिहास" },
};

// Hex colors. The root layout injects these as CSS variables.
export const theme = {
  brand: "#6B2B3A",
  accent: "#D8A23C",
  surface: "#F6F0F0",
  text: "#222222",
  border: "#E4D8D8",
};

export const languages = [
  { id: "mr", nativeName: "मराठी", englishName: "Marathi", speechLocale: "mr-IN" },
  { id: "hi", nativeName: "हिंदी", englishName: "Hindi", speechLocale: "hi-IN" },
  { id: "en", nativeName: "English", englishName: "English", speechLocale: "en-IN" },
];

export const levels = [
  {
    id: "beginner",
    label: { en: "Beginner", hi: "शुरुआती", mr: "सुरुवातीचा" },
    description: {
      en: "Simple words and one everyday example.",
      hi: "सरल शब्द और एक रोज़मर्रा का उदाहरण।",
      mr: "सोपे शब्द आणि एक रोजचे उदाहरण.",
    },
  },
  {
    id: "intermediate",
    label: { en: "Intermediate", hi: "मध्यम", mr: "मध्यम" },
    description: {
      en: "Textbook terms with a clear explanation.",
      hi: "पाठ्यपुस्तक की शब्दावली के साथ स्पष्ट व्याख्या।",
      mr: "पाठ्यपुस्तकातील संज्ञांसह स्पष्ट स्पष्टीकरण.",
    },
  },
  {
    id: "advanced",
    label: { en: "Advanced", hi: "उन्नत", mr: "प्रगत" },
    description: {
      en: "Precise reasoning, edge cases, and applications.",
      hi: "सटीक तर्क, विशेष स्थितियाँ और अनुप्रयोग।",
      mr: "अचूक तर्क, विशेष प्रसंग आणि उपयोजने.",
    },
  },
  {
    id: "exam",
    label: { en: "Exam", hi: "परीक्षा", mr: "परीक्षा" },
    description: {
      en: "Answers formatted for 2, 5, 7 or 10 marks.",
      hi: "2, 5, 7 या 10 अंकों के प्रारूप में उत्तर।",
      mr: "2, 5, 7 किंवा 10 गुणांच्या स्वरूपात उत्तर.",
    },
  },
];

export const examMarks = [
  { marks: 2, label: { en: "2 Marks", hi: "2 अंक", mr: "२ गुण" } },
  { marks: 5, label: { en: "5 Marks", hi: "5 अंक", mr: "५ गुण" } },
  { marks: 7, label: { en: "7 Marks", hi: "7 अंक", mr: "७ गुण" } },
  { marks: 10, label: { en: "10 Marks", hi: "10 अंक", mr: "१० गुण" } },
];

export const subjects = {
  Physics: { en: "Physics", hi: "भौतिक विज्ञान", mr: "भौतिकशास्त्र" },
  Chemistry: { en: "Chemistry", hi: "रसायन विज्ञान", mr: "रसायनशास्त्र" },
  Mathematics: { en: "Mathematics", hi: "गणित", mr: "गणित" },
  Biology: { en: "Biology", hi: "जीव विज्ञान", mr: "जीवशास्त्र" },
  "Computer Science": { en: "Computer Science", hi: "कंप्यूटर साइंस", mr: "संगणक शास्त्र" },
  "Electrical Engineering": { en: "Electrical Engg", hi: "इलेक्ट्रिकल इंजीनियरिंग", mr: "विद्युत अभियांत्रिकी" },
  "General Science": { en: "General Science", hi: "सामान्य विज्ञान", mr: "सामान्य विज्ञान" },
  Other: { en: "Other", hi: "अन्य", mr: "इतर" },
};

export const landing = {
  heroTitle: {
    en: "Learn in your language. Understand at your level.",
    hi: "अपनी भाषा में सीखें। अपने स्तर पर समझें।",
    mr: "तुमच्या भाषेत शिका. तुमच्या पातळीवर समजून घ्या.",
  },
  heroSubtitle: {
    en: "Multilingual academic tutor for Marathi, Hindi, and English that preserves true conceptual meaning and adapts explanations from school basics to exam scoring.",
    hi: "मराठी, हिंदी और अंग्रेजी के लिए एक बहुभाषी शैक्षणिक शिक्षक, जो अवधारणा के वास्तविक अर्थ को बनाए रखता है और स्कूल से परीक्षा तक स्तर अनुकूलित करता है।",
    mr: "मराठी, हिंदी आणि इंग्रजीसाठी एक बहुभाषिक शैक्षणिक मार्गदर्शक, जो मूळ संकल्पनांचा अर्थ जपत शालेय स्तरापासून परीक्षेपर्यंत अनुकूल स्पष्टीकरण देतो.",
  },
  startLearning: {
    en: "Start Learning Now",
    hi: "अब सीखना शुरू करें",
    mr: "आता शिकणे सुरू करा",
  },
  viewProgress: {
    en: "View Progress",
    hi: "प्रगति देखें",
    mr: "प्रगती पहा",
  },
  howItWorksTitle: {
    en: "How EduMitra Works",
    hi: "एडुमित्र कैसे काम करता है",
    mr: "एडुमित्र कसे कार्य करते",
  },
  howItWorksSubtitle: {
    en: "A 5-step meaning-preserving pedagogical pipeline built for regional learners.",
    hi: "क्षेत्रीय शिक्षार्थियों के लिए बनाया गया 5-चरणीय अर्थ-संरक्षक शैक्षणिक पाइपलाइन।",
    mr: "स्थानिक भाषांतील विद्यार्थ्यांसाठी विकसित केलेली ५-टप्प्यांची अर्थ-संरक्षक शैक्षणिक पद्धत.",
  },
  steps: [
    {
      step: 1,
      title: { en: "Ask", hi: "पूछें", mr: "विचारा" },
      desc: {
        en: "Ask academic questions in Marathi, Hindi, English, or mixed natural phrasing.",
        hi: "मराठी, हिंदी, अंग्रेजी या मिश्रित प्राकृतिक भाषा में शैक्षणिक प्रश्न पूछें।",
        mr: "मराठी, हिंदी, इंग्रजी किंवा मिश्र बोलीभाषेत शैक्षणिक प्रश्न विचारा.",
      },
    },
    {
      step: 2,
      title: { en: "Understand", hi: "समझें", mr: "समजा" },
      desc: {
        en: "Detects language, subject, topic, and extracts canonical core intent without losing technical terms.",
        hi: "भाषा, विषय और मुख्य शैक्षणिक आशय को तकनीकी शब्दावली खोए बिना पहचानता है।",
        mr: "तांत्रिक संज्ञा न गमावता भाषा, विषय आणि मुख्य संकल्पनात्मक उद्देश ओळखतो.",
      },
    },
    {
      step: 3,
      title: { en: "Adapt", hi: "अनुकूलित करें", mr: "पातळी जुळवा" },
      desc: {
        en: "Dynamically matches Beginner, Intermediate, Advanced, or Exam structure.",
        hi: "शुरुआती, मध्यम, उन्नत या परीक्षा प्रारूप के अनुसार स्वतः अनुकूलित होता है।",
        mr: "सुरुवातीची, मध्यम, प्रगत किंवा परीक्षा पद्धतीनुसार जुळवून घेतो.",
      },
    },
    {
      step: 4,
      title: { en: "Explain", hi: "समझाएँ", mr: "स्पष्टीकरण" },
      desc: {
        en: "Delivers explanations in the student's language preserving formulas and brackets on first mention.",
        hi: "विद्यार्थी की भाषा में सूत्र और कोष्ठक में मानक शब्द सुरक्षित रखते हुए उत्तर देता है।",
        mr: "सूत्रे आणि वैज्ञानिक संज्ञा कंसात ठेवत विद्यार्थ्याच्या मातृभाषेत स्पष्टीकरण देतो.",
      },
    },
    {
      step: 5,
      title: { en: "Check", hi: "जाँचें", mr: "पडताळा" },
      desc: {
        en: "Reinforces learning with diagnostic quizzes and instant Simplify / Explain-again actions.",
        hi: "नैदानिक क्विज़ और सरल करें / पुनः समझाएँ विकल्पों के साथ समझ की पुष्टि करें।",
        mr: "सराव क्विझ आणि सोपे करा / पुन्हा समजावा पर्यायांद्वारे ज्ञानाची खात्री करा.",
      },
    },
  ],
  featuresTitle: {
    en: "Engineered for Academic Rigor",
    hi: "शैक्षणिक गुणवत्ता के लिए विशेष रूप से निर्मित",
    mr: "शैक्षणिक गुणवत्तेसाठी सखोल रचलेले",
  },
  features: [
    {
      title: { en: "Zero Meaning Loss", hi: "अर्थ की संपूर्ण सुरक्षा", mr: "अचूक संकल्पनात्मक अर्थ" },
      desc: {
        en: "Avoids naive word-by-word translation; maps conceptual intent preserving textbook terminology.",
        hi: "सीधे शब्दशः अनुवाद से बचता है; पाठ्यपुस्तक की शब्दावली को सुरक्षित रखता है।",
        mr: "शब्दशः भाषांतर टाळून पाठ्यपुस्तकातील नेमक्या वैज्ञानिक संज्ञा जपल्या जातात.",
      },
    },
    {
      title: { en: "Level-Adaptive Depth", hi: "स्तर-अनुकूल गहराई", mr: "पातळीनुसार सखोलता" },
      desc: {
        en: "Switch between real-world analogies for beginners and rigorous derivations for advanced learners.",
        hi: "शुरुआती छात्रों के लिए रोजमर्रा के उदाहरण और उन्नत छात्रों के लिए गणितीय व्युत्पत्ति।",
        mr: "सुरुवातीच्या विद्यार्थ्यांसाठी रोजची उदाहरणे तर प्रगत विद्यार्थ्यांसाठी सखोल सिद्धता.",
      },
    },
    {
      title: { en: "Exam Marks Mode", hi: "परीक्षा अंक प्रारूप", mr: "परीक्षेतील गुण पद्धती" },
      desc: {
        en: "Structured specifically for 2, 5, 7, and 10 marks with the headings and bullet points examiners seek.",
        hi: "परीक्षकों द्वारा अपेक्षित शीर्षक और बिंदुओं के साथ 2, 5, 7 और 10 अंकों के लिए विशेष प्रारूप।",
        mr: "परीक्षेत अपेक्षेनुसार शीर्षक व मुद्द्यांसह २, ५, ७ आणि १० गुणांचे अचूक उत्तर प्रारूप.",
      },
    },
    {
      title: { en: "Self-Verification Pipeline", hi: "स्व-सत्यापन पाइपलाइन", mr: "स्वयं-तपासणी प्रणाली" },
      desc: {
        en: "Response validator checks formulas, numbers, and glossary terminology on every answer.",
        hi: "प्रत्येक उत्तर पर सूत्र, संख्या और शब्दावली की स्वतः शुद्धता जाँचता है।",
        mr: "प्रत्येक उत्तरावर सूत्रे, संख्या आणि परिभाषा अचूक असल्याची खात्री केली जाते.",
      },
    },
    {
      title: { en: "Private & Local-First", hi: "सुरक्षित और स्थानीय", mr: "स्थानिक व सुरक्षित" },
      desc: {
        en: "Runs 100% locally with open LLMs via Ollama. No paid API keys, no data leaves your device.",
        hi: "ओलामा के माध्यम से 100% स्थानीय। कोई शुल्क नहीं, कोई डेटा बाहर नहीं जाता।",
        mr: "स्थानिक संगणकावर ऑलामाद्वारे चालते. कोणताही खर्च नाही, माहिती गोपनीय राहते.",
      },
    },
    {
      title: { en: "Pre & Post Assessment", hi: "पूर्व एवं पश्चात् मूल्यांकन", mr: "पूर्व व नंतरचे मूल्यांकन" },
      desc: {
        en: "Measures actual understanding improvement with topic-aligned diagnostic quizzes.",
        hi: "विषय-आधारित क्विज़ के साथ वास्तविक समझ में सुधार को मापता है।",
        mr: "संकल्पना समजल्याची खात्री करण्यासाठी पूर्व व नंतर क्विझद्वारे प्रगती मोजली जाते.",
      },
    },
  ],
  impactTitle: {
    en: "Measurable Learning Impact",
    hi: "मापने योग्य सीखने का प्रभाव",
    mr: "मोजता येण्याजोगा शैक्षणिक प्रभाव",
  },
  impacts: [
    {
      stat: "100%",
      label: { en: "Local & Zero Cost", hi: "स्थानीय और निःशुल्क", mr: "स्थानिक व विनामूल्य" },
      sub: { en: "Runs offline on student laptops", hi: "लैपटॉप पर स्थानीय रूप से चलता है", mr: "विद्यार्थ्यांच्या लॅपटॉपवर चालते" },
    },
    {
      stat: "3+",
      label: { en: "Languages Supported", hi: "समर्थित भाषाएँ", mr: "समर्थित भाषा" },
      sub: { en: "Marathi, Hindi, English & mixed", hi: "मराठी, हिंदी, अंग्रेजी और मिश्रित", mr: "मराठी, हिंदी, इंग्रजी व मिश्र" },
    },
    {
      stat: "4",
      label: { en: "Adaptive Levels", hi: "अनुकूलित स्तर", mr: "अनुकूलन पातळ्या" },
      sub: { en: "Beginner, Intermediate, Advanced, Exam", hi: "शुरुआती, मध्यम, उन्नत, परीक्षा", mr: "सुरुवातीचा, मध्यम, प्रगत, परीक्षा" },
    },
  ],
};

export const chat = {
  placeholder: {
    en: "Ask a question in Marathi, Hindi or English…",
    hi: "मराठी, हिंदी या अंग्रेज़ी में प्रश्न पूछें…",
    mr: "मराठी, हिंदी किंवा इंग्रजीत प्रश्न विचारा…",
  },
  emptyTitle: {
    en: "What would you like to understand today?",
    hi: "आज आप क्या समझना चाहते हैं?",
    mr: "आज तुम्हाला काय समजून घ्यायचे आहे?",
  },
  emptySubtitle: {
    en: "Choose an example question below or type your own concept in your preferred language.",
    hi: "नीचे दिए गए उदाहरण प्रश्नों में से चुनें या अपनी पसंदीदा भाषा में प्रश्न लिखें।",
    mr: "खालीलपैकी एक उदाहरण प्रश्न निवडा किंवा तुमच्या भाषेत नवीन प्रश्न विचारा.",
  },
  send: { en: "Send", hi: "भेजें", mr: "पाठवा" },
  thinking: { en: "Thinking…", hi: "सोच रहे हैं…", mr: "विचार करत आहे…" },
  newChat: { en: "New chat", hi: "नई चैट", mr: "नवीन चॅट" },
  history: { en: "History", hi: "इतिहास", mr: "इतिहास" },
  noHistory: { en: "No saved chats yet", hi: "अभी कोई बातचीत नहीं है", mr: "अद्याप कोणतीही चॅट नाही" },
  verifyNotice: {
    en: "Please verify this answer with your textbook.",
    hi: "कृपया इस उत्तर को अपनी पाठ्यपुस्तक से जाँच लें।",
    mr: "कृपया हे उत्तर तुमच्या पाठ्यपुस्तकाशी पडताळून पाहा.",
  },
  autoLanguage: { en: "Auto Detect", hi: "स्वतः पहचानें", mr: "आपोआप ओळखा" },
  marksLabel: { en: "Marks:", hi: "अंक:", mr: "गुण:" },
  levelLabel: { en: "Level:", hi: "स्तर:", mr: "पातळी:" },
  clearChat: { en: "Clear", hi: "साफ़ करें", mr: "साफ करा" },
  voiceListening: { en: "Listening… Speak your question", hi: "सुन रहे हैं… अपना प्रश्न बोलें", mr: "ऐकत आहे… तुमचा प्रश्न बोला" },
  voiceUnsupported: { en: "Voice input not supported in this browser", hi: "इस ब्राउज़र में आवाज़ इनपुट समर्थित नहीं है", mr: "या ब्राउझरमध्ये व्हॉइस इनपुट समर्थित नाही" },
  charsRemaining: { en: "characters", hi: "अक्षर", mr: "अक्षरे" },
  deleteConfirm: { en: "Delete this chat?", hi: "क्या यह चैट हटाना चाहते हैं?", mr: "ही चॅट हटवायची आहे का?" },
  uiLanguage: { en: "Interface Language", hi: "इंटरफ़ेस भाषा", mr: "इंटरफेस भाषा" },
};

export const exampleQuestions = {
  mr: [
    "न्यूटनचा पहिला नियम काय आहे?",
    "Photosynthesis म्हणजे काय?",
    "ओहमचा नियम स्पष्ट करा आणि V = IR चे महत्त्व सांगा.",
    "जडत्व म्हणजे काय? दैनंदिन जीवनातील एक उदाहरण द्या.",
  ],
  hi: [
    "न्यूटन का पहला नियम क्या है?",
    "ओम का नियम समझाइए और इसका सूत्र क्या है?",
    "प्रकाश संश्लेषण की क्रिया कैसे होती है?",
    "जड़त्व का नियम 5 अंक के लिए लिखिए।",
  ],
  en: [
    "What is Newton's first law of motion?",
    "Explain Ohm's law with an example.",
    "Explain the process and significance of photosynthesis.",
    "What is the difference between an atom and a molecule?",
  ],
};

export const followUps = {
  simplify: { en: "Simplify", hi: "सरल करें", mr: "सोपे करा" },
  explainAgain: { en: "Explain again", hi: "फिर से समझाएँ", mr: "पुन्हा समजावा" },
  example: { en: "Give an example", hi: "उदाहरण दें", mr: "उदाहरण द्या" },
  translate: { en: "Translate", hi: "अनुवाद करें", mr: "भाषांतर करा" },
  summarize: { en: "Summarize", hi: "सारांश दें", mr: "सारांश द्या" },
  quiz: { en: "Quiz me", hi: "क्विज़ दें", mr: "मला क्विझ द्या" },
  helpful: { en: "Helpful", hi: "मददगार", mr: "उपयुक्त" },
  notHelpful: { en: "Not helpful", hi: "मददगार नहीं", mr: "अनुपयुक्त" },
  copied: { en: "Copied!", hi: "कॉपी किया गया!", mr: "कॉपी केले!" },
  copy: { en: "Copy", hi: "कॉपी करें", mr: "कॉपी करा" },
};

export const quiz = {
  title: { en: "Comprehension Check", hi: "समझ की जाँच", mr: "आकलन चाचणी" },
  subtitle: {
    en: "Test your understanding of the concept explained above.",
    hi: "ऊपर समझाए गए विषय की अपनी समझ की जाँच करें।",
    mr: "वरील संकल्पना किती समजली हे तपासण्यासाठी ही चाचणी सोडवा.",
  },
  submit: { en: "Submit Answers", hi: "उत्तर जमा करें", mr: "उत्तरे सबमिट करा" },
  submitting: { en: "Checking…", hi: "जाँच रहे हैं…", mr: "तपासत आहे…" },
  yourScore: { en: "Your Score", hi: "आपका स्कोर", mr: "तुमचा गुण" },
  excellent: { en: "Excellent understanding!", hi: "शानदार समझ!", mr: "उत्कृष्ट समज!" },
  good: { en: "Good effort! Review the explanations below.", hi: "अच्छा प्रयास! नीचे दिए गए स्पष्टीकरण देखें।", mr: "चांगला प्रयत्न! खालील स्पष्टीकरणे पहा." },
  needsReview: { en: "Review needed. Try 'Explain again' in chat.", hi: "पुनरावलोकन आवश्यक है। 'फिर से समझाएँ' का प्रयास करें।", mr: "अधिक सरावाची गरज आहे. चॅटमध्ये 'पुन्हा समजावा' वापरून पहा." },
  backToChat: { en: "Back to Chat", hi: "चैट पर वापस जाएँ", mr: "चॅटकडे परत जा" },
  retake: { en: "Retake Quiz", hi: "पुनः क्विज़ दें", mr: "पुन्हा चाचणी द्या" },
  preQuizBadge: { en: "Diagnostic Pre-Quiz", hi: "नैदानिक पूर्व-क्विज़", mr: "निदान पूर्व-चाचणी" },
  postQuizBadge: { en: "Concept Post-Quiz", hi: "अवधारणा पश्चात्-क्विज़", mr: "संकल्पना पश्चात-चाचणी" },
};

export const progress = {
  title: { en: "Learning Progress & Impact", hi: "सीखने की प्रगति और प्रभाव", mr: "शिकण्याची प्रगती व प्रभाव" },
  subtitle: {
    en: "Tracking your understanding before and after AI-guided explanations.",
    hi: "एआई मार्गदर्शन के पहले और बाद में आपकी समझ के सुधार का विश्लेषण।",
    mr: "मार्गदर्शनापूर्वी आणि नंतरच्या ज्ञानातील सुधारणेचा आलेख.",
  },
  improvementMetric: {
    en: "Average Understanding Gain",
    hi: "औसत समझ में सुधार",
    mr: "सरासरी आकलन सुधारणा",
  },
  quizzesTaken: {
    en: "Total Quizzes Completed",
    hi: "कुल पूर्ण क्विज़",
    mr: "पूर्ण केलेल्या चाचण्या",
  },
  topicBreakdown: {
    en: "Topic-wise Mastery",
    hi: "विषयवार प्रवीणता",
    mr: "विषयनिहाय प्रभुत्व",
  },
  noData: {
    en: "No quiz attempts recorded yet. Take a quiz after an explanation to track progress!",
    hi: "अभी कोई क्विज़ रिकॉर्ड नहीं है। प्रगति ट्रैक करने के लिए उत्तर के बाद क्विज़ लें!",
    mr: "अद्याप चाचणीचा कोणताही डेटा नाही. प्रगती पाहण्यासाठी उत्तरांनंतर क्विझ सोडवा!",
  },
  preScore: { en: "Pre-Score", hi: "पूर्व अंक", mr: "पूर्व गुण" },
  postScore: { en: "Post-Score", hi: "पश्चात् अंक", mr: "नंतरचे गुण" },
  gain: { en: "Gain", hi: "वृद्धि", mr: "वाढ" },
  loading: { en: "Loading progress records…", hi: "प्रगति रिकॉर्ड लोड हो रहे हैं…", mr: "प्रगती तपशील लोड होत आहेत…" },
  goToChat: { en: "Go to Tutor Chat", hi: "शिक्षक चैट पर जाएँ", mr: "मार्गदर्शक चॅटकडे जा" },
};

export const errors = {
  modelUnavailable: {
    en: "The AI model is not available right now. Please ensure Ollama is running and try again.",
    hi: "AI मॉडल अभी उपलब्ध नहीं है। कृपया सुनिश्चित करें कि ओलामा चल रहा है और फिर से प्रयास करें।",
    mr: "AI मॉडेल सध्या उपलब्ध नाही. कृपया ओलामा सुरू असल्याची खात्री करा आणि पुन्हा प्रयत्न करा.",
  },
  timeout: {
    en: "The request timed out. The local model took too long to respond. Please try again.",
    hi: "अनुरोध समय समाप्त हो गया। स्थानीय मॉडल ने उत्तर देने में बहुत समय लिया। पुनः प्रयास करें।",
    mr: "विनंतीची वेळ संपली. स्थानिक मॉडेलने उत्तर देण्यास वेळ घेतला. कृपया पुन्हा प्रयत्न करा.",
  },
  network: {
    en: "Unable to connect to the backend server. Please check your network connection.",
    hi: "बैकएंड सर्वर से कनेक्ट करने में असमर्थ। कृपया कनेक्शन जांचें।",
    mr: "बॅकएंड सर्व्हरशी संपर्क साधता आला नाही. कृपया नेटवर्क कनेक्शन तपासा.",
  },
  emptyInput: {
    en: "Please enter a question before sending.",
    hi: "कृपया भेजने से पहले कोई प्रश्न लिखें।",
    mr: "कृपया पाठवण्यापूर्वी प्रश्न टाइप करा.",
  },
  tooLong: {
    en: "Question exceeds the maximum allowed length (1000 characters).",
    hi: "प्रश्न अधिकतम अनुमत लंबाई (1000 वर्ण) से अधिक है।",
    mr: "प्रश्न कमाल मर्यादा (१००० अक्षरे) ओलांडत आहे.",
  },
  validationFailed: {
    en: "This answer could not be fully verified against the academic validator. Please review carefully.",
    hi: "इस उत्तर को शैक्षणिक सत्यापनकर्ता द्वारा पूरी तरह से जाँचा नहीं जा सका। कृपया ध्यान से पढ़ें।",
    mr: "हे उत्तर शैक्षणिक तपासणीनुसार पूर्णपणे पडताळता आले नाही. कृपया काळजीपूर्वक वाचा.",
  },
  generic: {
    en: "An unexpected error occurred. Please try again.",
    hi: "एक अनपेक्षित त्रुटि हुई। कृपया पुनः प्रयास करें।",
    mr: "अनपेक्षित त्रुटी आली. कृपया पुन्हा प्रयत्न करा.",
  },
  retry: {
    en: "Retry",
    hi: "पुनः प्रयास करें",
    mr: "पुन्हा प्रयत्न करा",
  },
};

export const limits = {
  maxQuestionChars: 1000,
  historyPageSize: 20,
  quizQuestionCount: 3,
};

export const team = {
  name: "The Penguins",
  members: [
    { name: "Atharva", role: { en: "Team Lead & ML Architect", hi: "टीम लीड एवं एमएल वास्तुकार", mr: "संघ प्रमुख व एमएल रचनाकार" } },
    { name: "Rihan", role: { en: "Full-Stack & Systems Engineer", hi: "फुल-स्टैक एवं सिस्टम इंजीनियर", mr: "फुल-स्टॅक व सिस्टम्स अभियंता" } },
    { name: "Ashutosh", role: { en: "NLP Pipeline & Prompt Engineer", hi: "एनएलपी पाइपलाइन एवं प्रॉम्प्ट इंजीनियर", mr: "एनएलपी पाइपलाइन व प्रॉम्प्ट अभियंता" } },
    { name: "Sonal", role: { en: "Frontend & UI/UX Specialist", hi: "फ्रंटएंड एवं यूआई/यूएक्स विशेषज्ञ", mr: "फ्रंटएंड व यूआय/युएक्स तज्ज्ञ" } },
  ],
};

export const links = {
  github: "https://github.com/the-penguins/edumitra",
  hackathon: "https://walchandsangli.ac.in",
  documentation: "https://github.com/the-penguins/edumitra#readme",
};

export const footer = {
  copyright: {
    en: "© 2026 EduMitra · Built by The Penguins for AARAMBH · WCE-Hackathon 2026",
    hi: "© 2026 एडुमित्र · आरम्भ WCE-हैकथॉन 2026 हेतु द पेंगुइन्स द्वारा निर्मित",
    mr: "© २०२६ एडुमित्र · आरंभा WCE-हॅकेथॉन २०२६ साठी 'द पेंग्विन्स' द्वारे निर्मित",
  },
  poweredBy: {
    en: "Powered by Walchand College of Engineering, Sangli",
    hi: "वालचंद कॉलेज ऑफ इंजीनियरिंग, सांगली द्वारा समर्थित",
    mr: "वालचंद अभियांत्रिकी महाविद्यालय, सांगली यांच्या सौजन्याने",
  },
};
