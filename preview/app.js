const STORE_KEY = "ember.preview.settings.v1";
const LANGUAGE_KEY = "ember.preview.language.v1";

const pageLabels = {
  api: "gemini",
  voice: "voice",
  behavior: "behavior",
  safety: "safety",
  shortcuts: "shortcuts",
};

const defaults = {
  uiLanguage: "en",
  apiModel: "gemini-3.8-flash",
  responseLanguage: "auto",
  sameLanguage: true,
  conciseReplies: true,
  speakAnswers: true,
  voiceName: "Kore",
  voiceVolume: 80,
  soundsEnabled: true,
  soundVolume: 65,
  standOnWindows: true,
  walkingSpeed: 100,
  characterScale: 70,
  sleepDelay: 10,
  sleepCorner: "bottom-right",
  monitor: "primary",
  rateLimit: 20,
  maxSteps: 12,
  emergencyHotkey: "Ctrl+Alt+S",
  pushToTalk: "",
  autostart: false,
  allowedFolders: ["~/Documents", "~/Downloads"],
  toolTiers: {
    open_app: "auto",
    open_url: "auto",
    list_windows: "auto",
    volume: "auto",
    focus_window: "ask",
    type_text: "ask",
    click_scroll: "ask",
    clipboard: "ask",
    files: "ask",
    shell: "ask",
  },
};

const translations = {
  en: {
    companion: "desktop companion",
    previewMode: "PREVIEW MODE",
    interfaceLanguage: "Interface language",
    closePreview: "Close preview",
    personalize: "MAKE IT YOURS",
    homeTitle: "A little more <em>you.</em>",
    homeDescription: "Choose a part of Ember to shape how your desktop companion works.",
    awake: "Ember is awake",
    readyToTune: "Ready for a little tuning",
    choosePath: "CHOOSE YOUR PATH",
    livePreview: "LIVE PREVIEW",
    gemini: "Gemini & API",
    geminiSub: "Give Ember a voice",
    voice: "Voice & language",
    voiceSub: "Listen, speak, connect",
    behavior: "Movement & rest",
    behaviorSub: "A little desktop life",
    safety: "Permissions & safety",
    safetySub: "You stay in control",
    shortcuts: "Shortcuts & startup",
    shortcutsSub: "Always within reach",
    emberPixelPal: "YOUR PIXEL PAL",
    desktop: "DESKTOP",
    bubbleMessage: "Hey, let's make this feel like home.",
    composerTitle: "Ask Ember",
    composerPlaceholder: "Type a question for Ember…",
    composerHelp: "Click here to type · hold right-click on Ember to record",
    sendQuestion: "Send question",
    microphoneRequesting: "Requesting microphone permission…",
    microphoneRecording: "Recording on this device · release to stop",
    microphonePrivacy: "Audio stays in this browser and is discarded. Nothing is sent to Gemini.",
    microphoneDenied: "Microphone access was blocked. Allow it in your browser, then try again.",
    microphoneUnavailable: "Microphone access is unavailable on this page.",
    recorderUnsupported: "Audio recording is not supported in this browser.",
    recordingCancelled: "Recording cancelled.",
    conversationTitle: "A little chat",
    conversationSubtitle: "Your question, then Ember's reply",
    conversationPreviewNotice: "Preview replies only · Gemini is not connected",
    questionLabel: "You",
    emberReplyLabel: "Ember · sample reply",
    thinkingReply: "Preparing a sample reply…",
    sampleTextReply: "This sample shows how a reply will look. Gemini is not connected in this preview.",
    voiceQuestionLabel: "Voice question · local capture",
    sampleVoiceReply: "The microphone was active locally. This preview does not transcribe speech or connect to Gemini.",
    returnEmber: "Move Ember back and close the chat",
    emberCharacter: "Ember",
    emptyQuestion: "Write a question first, or hold right-click on Ember to record.",
    hoverHint: "Hover over Ember to see what each part can do.",
    yourDesktop: "MADE FOR YOUR DESKTOP",
    previewDisclaimer: "Interactive concept · Changes stay in this browser preview",
    resetPreview: "Reset preview",
    backToEmber: "Back to Ember",
    settings: "SETTINGS",
    localPreview: "Local preview",
    nothingSent: "Nothing is sent or saved to Ember.",
    preferences: "PREFERENCES",
    resetDefaults: "Reset defaults",
    previewOnly: "Preview only — no settings are applied to the desktop app.",
    saveChanges: "Save changes",
    apiEyebrow: "THE BRAIN",
    apiTitle: "A bright spark behind Ember.",
    apiDescription: "Connect a Gemini model and choose how Ember responds. Your key belongs in your system keyring in the real app.",
    connectionTitle: "Gemini connection",
    connectionDescription: "A little intelligence for the moments you need it.",
    apiKey: "Gemini API key",
    apiKeyPlaceholder: "Paste a key to preview this field",
    show: "Show",
    hide: "Hide",
    testConnection: "Test connection",
    noKeyStatus: "No key entered",
    model: "Model",
    modelDescription: "Choose the model used for chat and tools.",
    modelFlash: "Gemini 3.8 Flash · fast, balanced",
    modelLive: "Gemini 3.8 Live · real-time voice",
    modelThinking: "Gemini 3.8 Live · extended thinking",
    responseLanguage: "Response language",
    autoSameLanguage: "Automatic · reply in my language",
    arabic: "Arabic",
    english: "English",
    apiPrivacyTitle: "A safe visual preview",
    apiPrivacyText: "This demo never contacts Google. The API key field is temporary and is never saved in the browser.",
    responseStyleTitle: "How Ember talks",
    responseStyleDescription: "Keep replies useful, warm, and short enough for a speech bubble.",
    sameLanguage: "Reply in the same language",
    sameLanguageHelp: "Understand Egyptian Arabic and English, then match the language you used.",
    conciseReplies: "Keep replies concise",
    conciseRepliesHelp: "Write for a small desktop speech bubble.",
    voiceEyebrow: "THE VOICE",
    voiceTitle: "Hear each other, naturally.",
    voiceDescription: "Shape how Ember listens and speaks. Audio is sent to Google only when you use voice features.",
    spokenAnswersTitle: "Spoken answers",
    spokenAnswersDescription: "Choose how Ember sounds when it replies out loud.",
    speakAnswers: "Speak answers",
    speakAnswersHelp: "Read replies aloud when voice output is enabled.",
    voiceChoice: "Voice",
    voiceKore: "Kore · clear and warm",
    voicePuck: "Puck · bright and playful",
    voiceCharon: "Charon · calm and measured",
    voiceVolume: "Voice volume",
    previewVoice: "Preview voice",
    soundsTitle: "Little sounds",
    soundsDescription: "Short original sounds for movement and reactions.",
    soundsEnabled: "Character sounds",
    soundsEnabledHelp: "Footsteps, listening cues, and sleepy snores.",
    soundVolume: "Sound effects volume",
    languageTitle: "Languages & privacy",
    languageDescription: "English is the interface default. Arabic can be selected in the header.",
    interfaceLanguage: "Interface language",
    speechLanguage: "Spoken language",
    speechAuto: "Auto-detect · Egyptian Arabic + English",
    speechPrivacyTitle: "Your voice stays yours to choose",
    speechPrivacyText: "When you hold to talk, your audio is sent to Google to process your request. Voice playback is also generated by Google. You control when those features are used.",
    behaviorEyebrow: "THE MOVEMENT",
    behaviorTitle: "A little life on your desktop.",
    behaviorDescription: "Tune Ember's pace, where they wander, and when they curl up for a nap.",
    windowWalkingTitle: "Window walking",
    windowWalkingDescription: "Let Ember stroll along the top edge of open windows.",
    standOnWindows: "Stand on open windows",
    standOnWindowsHelp: "Walk on window tops and fall when one moves or closes.",
    movementTitle: "Movement & scale",
    movementDescription: "Keep the motion comfortable for your display.",
    walkingSpeed: "Walking speed",
    characterScale: "Character scale",
    restTitle: "Sleep routine",
    restDescription: "Ember takes a break after a quiet stretch.",
    sleepDelay: "Sleep after",
    minutes: "minutes",
    sleepCorner: "Favorite sleeping corner",
    cornerRight: "Bottom right",
    cornerLeft: "Bottom left",
    cornerTopRight: "Top right",
    cornerTopLeft: "Top left",
    monitor: "Display",
    primaryMonitor: "Primary display",
    behaviorNote: "The character wakes when you move the mouse nearby or click Ember.",
    safetyEyebrow: "THE BOUNDARIES",
    safetyTitle: "Helpful, never out of hand.",
    safetyDescription: "Choose what Ember can do alone, what needs your say-so, and what is never allowed.",
    permissionTitle: "Permission tiers",
    permissionKey: "Permission",
    permissionAuto: "Auto",
    permissionAsk: "Ask first",
    permissionDisabled: "Disabled",
    toolOpenApp: "Open an app or URL",
    toolOpenAppHelp: "Launch apps and visit links",
    toolWindows: "List and focus windows",
    toolWindowsHelp: "See open windows and focus one",
    toolVolume: "Volume and media",
    toolVolumeHelp: "Adjust sound and media playback",
    toolInput: "Typing and pointer",
    toolInputHelp: "Type text, click, scroll, or press keys",
    toolClipboard: "Clipboard access",
    toolClipboardHelp: "Read or write clipboard contents",
    toolFiles: "Files in allowed folders",
    toolFilesHelp: "Create or read files you approve",
    toolShell: "Restricted shell commands",
    toolShellHelp: "Run a command after confirmation",
    toolScreenshots: "Screenshots",
    toolScreenshotsHelp: "Capture the screen only when requested",
    foldersTitle: "Allowed folders",
    foldersDescription: "File actions stay inside these locations.",
    folderPlaceholder: "~/Projects",
    addFolder: "Add folder",
    removeFolder: "Remove folder",
    forbiddenTitle: "Always forbidden",
    forbiddenDescription: "Some actions stay blocked even if someone asks. Confirmation can never override these protections.",
    forbiddenCommands: "sudo · rm -rf · disk formatting · system files · other users' data · password fields · keyring access",
    forbiddenTagDisk: "disk format",
    forbiddenTagSystem: "system files",
    forbiddenTagOthers: "other users",
    forbiddenTagPasswords: "password fields",
    forbiddenTagKeyring: "keyring",
    screenPrivacyTitle: "Screen sharing is always your choice",
    screenPrivacyText: "When you ask Ember to look at your screen, the screenshot is sent to Google for analysis. It is never captured in the background.",
    protectionTitle: "Safety limits",
    protectionDescription: "Put a ceiling on actions and stop them instantly.",
    rateLimit: "Maximum actions per minute",
    maxSteps: "Maximum steps per request",
    stopHotkey: "Emergency stop hotkey",
    shortcutEyebrow: "THE LITTLE CONTROLS",
    shortcutTitle: "Ember, just a key away.",
    shortcutDescription: "Set quick ways to reach Ember, stop an action, and start together when you log in.",
    hotkeysTitle: "Hotkeys",
    hotkeysDescription: "A quick way in, and a quick way out.",
    emergencyHotkey: "Emergency stop",
    emergencyHelp: "Cancels the current action and stops all input.",
    pushToTalk: "Push-to-talk key",
    pushToTalkHelp: "Optional alternative to holding the right mouse button.",
    startTitle: "When your desktop starts",
    startDescription: "Choose how Ember joins your session.",
    autostart: "Start Ember on login",
    autostartHelp: "Open Ember automatically when you log in.",
    keyboardNote: "Your emergency stop remains available even when Ember is listening or thinking.",
    saved: "Preview settings saved in this browser.",
    resetDone: "Preview settings restored to their defaults.",
    closeHint: "Close this tab to leave the preview.",
    keyEmpty: "Enter a sample key to preview the test state.",
    testMock: "Preview only — no request was sent to Google.",
    voiceMock: "Voice preview is visual only in this prototype.",
    folderAdded: "Folder added to this preview.",
    folderExists: "That folder is already in the preview list.",
    folderEmpty: "Enter a folder path first.",
    savedError: "Could not save preview settings in this browser.",
    loadError: "Preview settings could not be read; defaults are shown.",
  },
  ar: {
    companion: "رفيق سطح المكتب",
    previewMode: "نموذج للمعاينة",
    interfaceLanguage: "لغة الواجهة",
    closePreview: "إغلاق المعاينة",
    personalize: "خليه على ذوقك",
    homeTitle: "خلّي Ember <em>شبهك.</em>",
    homeDescription: "اختار جزءًا من Ember عشان تضبط طريقة عمل رفيقك على سطح المكتب.",
    awake: "Ember صاحي",
    readyToTune: "جاهز نضبطه سوا",
    choosePath: "اختار قسمًا",
    livePreview: "معاينة مباشرة",
    gemini: "Gemini وواجهة API",
    geminiSub: "اختار عقل Ember",
    voice: "الصوت واللغة",
    voiceSub: "يسمعك ويرد عليك",
    behavior: "الحركة والراحة",
    behaviorSub: "حياة صغيرة على سطح المكتب",
    safety: "الصلاحيات والأمان",
    safetySub: "أنت المتحكم دائمًا",
    shortcuts: "الاختصارات والتشغيل",
    shortcutsSub: "قريب منك دايمًا",
    emberPixelPal: "صاحبك البكسلي",
    desktop: "سطح المكتب",
    bubbleMessage: "أهلًا! يلا نخلي المكان على ذوقك.",
    composerTitle: "اسأل Ember",
    composerPlaceholder: "اكتب سؤالك لـEmber…",
    composerHelp: "اضغط هنا للكتابة · اضغط مطولًا باليمين على Ember للتسجيل",
    sendQuestion: "إرسال السؤال",
    microphoneRequesting: "جارٍ طلب إذن الميكروفون…",
    microphoneRecording: "تسجيل محلي · ارفع إصبعك للإيقاف",
    microphonePrivacy: "الصوت يظل في المتصفح ويُحذف فورًا؛ لا يُرسل إلى Gemini.",
    microphoneDenied: "تم رفض إذن الميكروفون. اسمح به من المتصفح ثم حاول مرة أخرى.",
    microphoneUnavailable: "الميكروفون غير متاح في هذه الصفحة.",
    recorderUnsupported: "التسجيل الصوتي غير مدعوم في هذا المتصفح.",
    recordingCancelled: "تم إلغاء التسجيل.",
    conversationTitle: "دردشة صغيرة",
    conversationSubtitle: "سؤالك وبعده رد Ember",
    conversationPreviewNotice: "ردود تجريبية فقط · Gemini غير متصل",
    questionLabel: "أنت",
    emberReplyLabel: "Ember · رد تجريبي",
    thinkingReply: "جارٍ تجهيز رد تجريبي…",
    sampleTextReply: "ده رد تجريبي لعرض شكل المحادثة. Gemini مش متصل في المعاينة.",
    voiceQuestionLabel: "سؤال صوتي · تسجيل محلي",
    sampleVoiceReply: "الميكروفون اشتغل محليًا. المعاينة لا تحوّل الكلام لنص ولا تتصل بـGemini.",
    returnEmber: "إرجاع Ember وإغلاق الدردشة",
    emberCharacter: "Ember",
    emptyQuestion: "اكتب سؤالك أولًا، أو اضغط مطولًا باليمين على Ember للتسجيل.",
    hoverHint: "مرّر الماوس على Ember عشان تشوف وظيفة كل جزء.",
    yourDesktop: "متصمم لسطح مكتبك",
    previewDisclaimer: "نموذج تفاعلي · التغييرات تفضل في معاينة المتصفح",
    resetPreview: "إعادة ضبط المعاينة",
    backToEmber: "العودة إلى Ember",
    settings: "الإعدادات",
    localPreview: "معاينة محلية",
    nothingSent: "لا شيء يُرسل أو يُحفظ في Ember.",
    preferences: "التفضيلات",
    resetDefaults: "استعادة الافتراضي",
    previewOnly: "معاينة فقط — لن تُطبّق الإعدادات على تطبيق سطح المكتب.",
    saveChanges: "حفظ التغييرات",
    apiEyebrow: "العقل",
    apiTitle: "الشرارة اللي بتحرّك Ember.",
    apiDescription: "اربط نموذج Gemini واختار طريقة رد Ember. في التطبيق الحقيقي، المفتاح مكانه مخزن مفاتيح النظام.",
    connectionTitle: "اتصال Gemini",
    connectionDescription: "شوية ذكاء يساعدك وقت ما تحتاجه.",
    apiKey: "مفتاح Gemini API",
    apiKeyPlaceholder: "أدخل مفتاحًا تجريبيًا لمعاينة الخانة",
    show: "إظهار",
    hide: "إخفاء",
    testConnection: "اختبار الاتصال",
    noKeyStatus: "لم يُدخل مفتاح",
    model: "النموذج",
    modelDescription: "اختار النموذج المستخدم للمحادثة والأدوات.",
    modelFlash: "Gemini 3.8 Flash · سريع ومتوازن",
    modelLive: "Gemini 3.8 Live · صوت مباشر",
    modelThinking: "Gemini 3.8 Live · تفكير ممتد",
    responseLanguage: "لغة الرد",
    autoSameLanguage: "تلقائي · يرد بنفس لغتي",
    arabic: "العربية",
    english: "الإنجليزية",
    apiPrivacyTitle: "معاينة آمنة",
    apiPrivacyText: "النموذج ده لا يتصل بـGoogle. خانة المفتاح مؤقتة ومش بتتحفظ في المتصفح.",
    responseStyleTitle: "طريقة كلام Ember",
    responseStyleDescription: "خلي الردود مفيدة ولطيفة وقصيرة بما يكفي لفقاعة الكلام.",
    sameLanguage: "الرد بنفس اللغة",
    sameLanguageHelp: "يفهم المصري والإنجليزي، ويرد باللغة اللي استخدمتها.",
    conciseReplies: "ردود مختصرة",
    conciseRepliesHelp: "الرد يناسب فقاعة الكلام الصغيرة على سطح المكتب.",
    voiceEyebrow: "الصوت",
    voiceTitle: "اسمعوا بعض بطبيعية.",
    voiceDescription: "اختار طريقة استماع Ember وكلامه. يُرسل الصوت إلى Google فقط عند استخدام ميزات الصوت.",
    spokenAnswersTitle: "الردود الصوتية",
    spokenAnswersDescription: "اختار صوت Ember لما يرد عليك بصوت مسموع.",
    speakAnswers: "نطق الردود",
    speakAnswersHelp: "قراءة الردود بصوت مسموع عند تفعيل الصوت.",
    voiceChoice: "الصوت",
    voiceKore: "Kore · واضح ودافئ",
    voicePuck: "Puck · مرح وحيوي",
    voiceCharon: "Charon · هادئ ومتزن",
    voiceVolume: "مستوى صوت الرد",
    previewVoice: "معاينة الصوت",
    soundsTitle: "أصوات صغيرة",
    soundsDescription: "أصوات قصيرة أصلية للحركة وردود الفعل.",
    soundsEnabled: "أصوات الشخصية",
    soundsEnabledHelp: "خطوات، وإشارات الاستماع، وشخير النوم.",
    soundVolume: "مستوى المؤثرات",
    languageTitle: "اللغة والخصوصية",
    languageDescription: "الإنجليزية هي الافتراضية للواجهة. اختار العربية من أعلى الصفحة.",
    interfaceLanguage: "لغة الواجهة",
    speechLanguage: "لغة التحدث",
    speechAuto: "اكتشاف تلقائي · مصري وإنجليزي",
    speechPrivacyTitle: "صوتك واختيارك",
    speechPrivacyText: "عند الضغط المطوّل للتحدث، يُرسل صوتك إلى Google لمعالجة طلبك. كما يُنشأ الصوت المنطوق عبر Google. أنت تختار متى تستخدم هذه الميزات.",
    behaviorEyebrow: "الحركة",
    behaviorTitle: "حياة صغيرة على سطح مكتبك.",
    behaviorDescription: "اضبط سرعة Ember وأماكن تجوله وموعد استعداده لقيلولة.",
    windowWalkingTitle: "المشي فوق النوافذ",
    windowWalkingDescription: "خلّي Ember يتمشى فوق الحافة العلوية للنوافذ المفتوحة.",
    standOnWindows: "الوقوف على النوافذ المفتوحة",
    standOnWindowsHelp: "يمشي فوق النوافذ ويقع عند تحريكها أو إغلاقها.",
    movementTitle: "الحركة والحجم",
    movementDescription: "اضبط الحركة بما يناسب شاشتك.",
    walkingSpeed: "سرعة المشي",
    characterScale: "حجم الشخصية",
    restTitle: "روتين النوم",
    restDescription: "Ember بياخد راحة بعد فترة هدوء.",
    sleepDelay: "النوم بعد",
    minutes: "دقائق",
    sleepCorner: "ركن النوم المفضل",
    cornerRight: "أسفل اليمين",
    cornerLeft: "أسفل اليسار",
    cornerTopRight: "أعلى اليمين",
    cornerTopLeft: "أعلى اليسار",
    monitor: "الشاشة",
    primaryMonitor: "الشاشة الرئيسية",
    behaviorNote: "Ember يصحى لما تقرّب بالماوس أو تضغط عليه.",
    safetyEyebrow: "الحدود",
    safetyTitle: "يساعدك، من غير ما يخرج عن سيطرتك.",
    safetyDescription: "حدد ما يمكن لـEmber فعله تلقائيًا، وما يحتاج موافقتك، وما هو ممنوع دائمًا.",
    permissionTitle: "مستويات الصلاحيات",
    permissionKey: "الصلاحية",
    permissionAuto: "تلقائي",
    permissionAsk: "اسألني أولًا",
    permissionDisabled: "معطّل",
    toolOpenApp: "فتح تطبيق أو رابط",
    toolOpenAppHelp: "تشغيل تطبيقات وفتح روابط",
    toolWindows: "عرض النوافذ وتفعيلها",
    toolWindowsHelp: "معرفة النوافذ المفتوحة وتفعيل إحداها",
    toolVolume: "الصوت والوسائط",
    toolVolumeHelp: "ضبط مستوى الصوت وتشغيل الوسائط",
    toolInput: "الكتابة والماوس",
    toolInputHelp: "كتابة نص أو نقر أو تمرير أو ضغط مفاتيح",
    toolClipboard: "الوصول إلى الحافظة",
    toolClipboardHelp: "قراءة محتوى الحافظة أو الكتابة إليها",
    toolFiles: "ملفات المجلدات المسموحة",
    toolFilesHelp: "إنشاء أو قراءة الملفات بعد موافقتك",
    toolShell: "أوامر طرفية مقيّدة",
    toolShellHelp: "تشغيل أمر بعد التأكيد",
    toolScreenshots: "لقطات الشاشة",
    toolScreenshotsHelp: "التقاط الشاشة عند طلبك فقط",
    foldersTitle: "المجلدات المسموحة",
    foldersDescription: "عمليات الملفات تفضل داخل المجلدات دي.",
    folderPlaceholder: "~/Projects",
    addFolder: "إضافة مجلد",
    removeFolder: "حذف المجلد",
    forbiddenTitle: "ممنوع دائمًا",
    forbiddenDescription: "في حاجات تفضل محظورة حتى لو طُلبت. التأكيد لا يتجاوز وسائل الحماية دي.",
    forbiddenCommands: "sudo · rm -rf · تهيئة الأقراص · ملفات النظام · بيانات الآخرين · خانات كلمات المرور · الوصول لمخزن المفاتيح",
    forbiddenTagDisk: "تهيئة الأقراص",
    forbiddenTagSystem: "ملفات النظام",
    forbiddenTagOthers: "بيانات الآخرين",
    forbiddenTagPasswords: "خانات كلمات المرور",
    forbiddenTagKeyring: "مخزن المفاتيح",
    screenPrivacyTitle: "مشاركة الشاشة باختيارك دائمًا",
    screenPrivacyText: "عندما تطلب من Ember النظر إلى شاشتك، تُرسل لقطة الشاشة إلى Google لتحليلها. لا تُلتقط في الخلفية.",
    protectionTitle: "حدود الأمان",
    protectionDescription: "ضع حدًا لعدد الإجراءات وأوقفها فورًا.",
    rateLimit: "أقصى إجراءات في الدقيقة",
    maxSteps: "أقصى خطوات في الطلب",
    stopHotkey: "اختصار الإيقاف الطارئ",
    shortcutEyebrow: "التحكم السريع",
    shortcutTitle: "Ember، على بُعد ضغطة.",
    shortcutDescription: "اختار طريقة سريعة للوصول إلى Ember وإيقاف إجراء وبدء العمل عند تسجيل الدخول.",
    hotkeysTitle: "الاختصارات",
    hotkeysDescription: "دخول سريع، وخروج أسرع.",
    emergencyHotkey: "الإيقاف الطارئ",
    emergencyHelp: "يلغي الإجراء الحالي ويوقف كل الإدخال.",
    pushToTalk: "زر التحدث",
    pushToTalkHelp: "اختياري كبديل للضغط المطوّل بزر الماوس اليمين.",
    startTitle: "عند تشغيل سطح المكتب",
    startDescription: "اختار موعد ظهور Ember في جلستك.",
    autostart: "تشغيل Ember عند تسجيل الدخول",
    autostartHelp: "فتح Ember تلقائيًا عند تسجيل دخولك.",
    keyboardNote: "اختصار الإيقاف الطارئ متاح حتى أثناء استماع Ember أو تفكيره.",
    saved: "حُفظت إعدادات المعاينة في المتصفح.",
    resetDone: "أُعيدت إعدادات المعاينة إلى القيم الافتراضية.",
    closeHint: "أغلق علامة التبويب للخروج من المعاينة.",
    keyEmpty: "أدخل مفتاحًا تجريبيًا لمعاينة حالة الاختبار.",
    testMock: "معاينة فقط — لم يُرسل أي طلب إلى Google.",
    voiceMock: "معاينة الصوت شكلية فقط في النموذج ده.",
    folderAdded: "أُضيف المجلد إلى المعاينة.",
    folderExists: "المجلد موجود بالفعل في قائمة المعاينة.",
    folderEmpty: "أدخل مسار مجلد أولًا.",
    savedError: "تعذر حفظ إعدادات المعاينة في المتصفح.",
    loadError: "تعذرت قراءة إعدادات المعاينة؛ تُعرض القيم الافتراضية.",
  },
};

const toolDefinitions = [
  ["toolOpenApp", "toolOpenAppHelp", "open_app", "auto"],
  ["toolWindows", "toolWindowsHelp", "list_windows", "auto"],
  ["toolVolume", "toolVolumeHelp", "volume", "auto"],
  ["toolInput", "toolInputHelp", "type_text", "ask"],
  ["toolClipboard", "toolClipboardHelp", "clipboard", "ask"],
  ["toolFiles", "toolFilesHelp", "files", "ask"],
  ["toolShell", "toolShellHelp", "shell", "ask"],
  ["toolScreenshots", "toolScreenshotsHelp", "screenshots", "ask"],
];

let currentLanguage = "en";
let currentPage = "api";
let toastTimer;
let conversationTurns = [];
let recordingHoldTimer = 0;
let recordingPointerId = null;
let recordingRequestId = 0;
let recordingState = "idle";
let recordingStream = null;
let recordingRecorder = null;
let characterTravelId = 0;

const homeView = document.querySelector("#home-view");
const settingsView = document.querySelector("#settings-view");
const settingsContent = document.querySelector("#settings-content");
const travelingEmber = document.querySelector("#traveling-ember");
const toast = document.querySelector("#toast");
const characterWrap = document.querySelector("#character-wrap");
const characterSvg = document.querySelector("#character-wrap .ember-character");
const characterEyes = characterSvg.querySelector(".character-eyes");
const voiceComposer = document.querySelector("#voice-composer");
const voiceQuestion = document.querySelector("#voice-question");
const voiceStatus = document.querySelector("#voice-status");
const conversationWindow = document.querySelector("#conversation-window");
const conversationMessages = document.querySelector("#conversation-messages");
const chatScrim = document.querySelector("#chat-scrim");
const orbitStage = document.querySelector("#orbit-stage");
const orbitLines = orbitStage.querySelector(".orbit-lines");
const connectorDefinitions = [
  { page: "api", anchor: "bottom", target: { x: 190, y: 100 } },
  { page: "voice", anchor: "right", target: { x: 108, y: 141 } },
  { page: "shortcuts", anchor: "left", target: { x: 272, y: 141 } },
  { page: "behavior", anchor: "top-right", target: { x: 142, y: 212 } },
  { page: "safety", anchor: "top-left", target: { x: 238, y: 212 } },
];
const gaze = {
  x: 0,
  y: 0,
  velocityX: 0,
  velocityY: 0,
  targetX: 0,
  targetY: 0,
  frame: 0,
  lastTime: 0,
};
let pointerPosition = null;
let connectorFrame = 0;

function readStoredState() {
  try {
    const raw = localStorage.getItem(STORE_KEY);
    if (!raw) return structuredClone(defaults);
    return { ...structuredClone(defaults), ...JSON.parse(raw) };
  } catch {
    showToast(translations[currentLanguage].loadError);
    return structuredClone(defaults);
  }
}

function showToast(message) {
  toast.textContent = message;
  toast.classList.add("visible");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove("visible"), 2600);
}

function text(key) {
  return translations[currentLanguage][key] ?? translations.en[key] ?? key;
}

function applyLanguage() {
  document.documentElement.lang = currentLanguage;
  document.documentElement.dir = currentLanguage === "ar" ? "rtl" : "ltr";
  document.querySelector("#language-select").value = currentLanguage;
  document.querySelectorAll("[data-i18n]").forEach((element) => {
    const value = text(element.dataset.i18n);
    if (value.includes("<em>")) element.innerHTML = value;
    else element.textContent = value;
  });
  document.querySelectorAll("[data-i18n-aria]").forEach((element) => {
    element.setAttribute("aria-label", text(element.dataset.i18nAria));
    element.setAttribute("title", text(element.dataset.i18nAria));
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach((element) => {
    element.setAttribute("placeholder", text(element.dataset.i18nPlaceholder));
  });
  document.querySelectorAll("[data-i18n-title]").forEach((element) => {
    element.setAttribute("title", text(element.dataset.i18nTitle));
  });
  const crumb = document.querySelector("#section-crumb");
  if (crumb) crumb.textContent = text(pageLabels[currentPage]);
  const status = document.querySelector("#api-key-status");
  if (status && !status.dataset.state) status.lastChild.textContent = text("noKeyStatus");
  const showKeyButton = document.querySelector("#show-key");
  if (showKeyButton) {
    const keyInput = document.querySelector("#api-key");
    showKeyButton.textContent = keyInput.type === "password" ? text("show") : text("hide");
  }
  scheduleOrbitConnectorUpdate();
}

function cardHeading(icon, titleKey, descriptionKey) {
  return `<div class="card-heading"><div><h2 data-i18n="${titleKey}">${text(titleKey)}</h2><p data-i18n="${descriptionKey}">${text(descriptionKey)}</p></div><span class="card-icon" aria-hidden="true">${icon}</span></div>`;
}

function card(titleKey, descriptionKey, content, icon, wide = false) {
  return `<article class="setting-card${wide ? " full-width" : ""}">${cardHeading(icon, titleKey, descriptionKey)}${content}</article>`;
}

function selectOptions(items, selected) {
  return items.map(([value, labelKey, literal]) => {
    const label = literal ?? text(labelKey);
    return `<option value="${value}"${value === selected ? " selected" : ""}${labelKey ? ` data-i18n="${labelKey}"` : ""}>${label}</option>`;
  }).join("");
}

function fieldSelect(labelKey, setting, items, selected, hintKey = "") {
  return `<label class="field"><span class="field-label" data-i18n="${labelKey}">${text(labelKey)}</span><select class="field-select" data-setting="${setting}">${selectOptions(items, selected)}</select>${hintKey ? `<span class="field-hint" data-i18n="${hintKey}">${text(hintKey)}</span>` : ""}</label>`;
}

function toggle(setting, titleKey, helpKey, checked) {
  return `<div class="setting-row"><span><strong data-i18n="${titleKey}">${text(titleKey)}</strong><small data-i18n="${helpKey}">${text(helpKey)}</small></span><button class="switch-control switch" type="button" role="switch" aria-checked="${checked}" aria-label="${text(titleKey)}" data-setting="${setting}"></button></div>`;
}

function rangeField(setting, labelKey, value, min, max, suffix) {
  const shown = `${value}${suffix}`;
  return `<label class="field"><span class="field-label" data-i18n="${labelKey}">${text(labelKey)}</span><span class="range-field"><input type="range" min="${min}" max="${max}" value="${value}" data-setting="${setting}" aria-label="${text(labelKey)}"><output class="range-value">${shown}</output></span></label>`;
}

function sectionHeader(index, eyebrowKey, titleKey, descriptionKey) {
  return `<header class="section-heading"><span class="eyebrow"><span class="eyebrow-line"></span><span>${String(index).padStart(2, "0")}</span><span data-i18n="${eyebrowKey}">${text(eyebrowKey)}</span></span><h1 id="section-title" data-i18n="${titleKey}">${text(titleKey)}</h1><p data-i18n="${descriptionKey}">${text(descriptionKey)}</p></header>`;
}

function privacyCallout(titleKey, descriptionKey) {
  return `<div class="privacy-callout"><span class="callout-mark" aria-hidden="true">◇</span><span><strong data-i18n="${titleKey}">${text(titleKey)}</strong> <span data-i18n="${descriptionKey}">${text(descriptionKey)}</span></span></div>`;
}

function apiPage(state) {
  const models = [
    ["gemini-3.8-flash", "modelFlash"],
    ["gemini-3.8-live", "modelLive"],
    ["gemini-3.8-live-extended-thinking", "modelThinking"],
  ];
  const languages = [
    ["auto", "autoSameLanguage"],
    ["ar", "arabic"],
    ["en", "english"],
  ];
  const connection = `<label class="field"><span class="field-label" data-i18n="apiKey">${text("apiKey")}</span><span class="input-row"><input id="api-key" class="field-input" type="password" autocomplete="off" dir="ltr" data-sensitive placeholder="${text("apiKeyPlaceholder")}" data-i18n-placeholder="apiKeyPlaceholder"><button id="show-key" class="tiny-button" type="button">${text("show")}</button><button id="test-connection" class="primary-button" type="button" data-i18n="testConnection">${text("testConnection")}</button></span><span id="api-key-status" class="status-line"><i class="status-mark"></i><span>${text("noKeyStatus")}</span></span></label><div class="form-stack">${fieldSelect("model", "apiModel", models.map(([value, key]) => [value, key]), state.apiModel, "modelDescription")}${fieldSelect("responseLanguage", "responseLanguage", languages, state.responseLanguage)}</div>`;
  const response = `${toggle("sameLanguage", "sameLanguage", "sameLanguageHelp", true)}${toggle("conciseReplies", "conciseReplies", "conciseRepliesHelp", true)}`;
  settingsContent.innerHTML = `${sectionHeader(1, "apiEyebrow", "apiTitle", "apiDescription")}<div class="content-grid">${card("connectionTitle", "connectionDescription", connection, "✳")}${card("responseStyleTitle", "responseStyleDescription", `<div class="setting-list">${response}</div>`, "◌")}<article class="setting-card full-width">${privacyCallout("apiPrivacyTitle", "apiPrivacyText")}</article></div>`;
}

function voicePage(state) {
  const voices = [
    ["Kore", "voiceKore"],
    ["Puck", "voicePuck"],
    ["Charon", "voiceCharon"],
  ];
  const voiceContent = `<div class="setting-list">${toggle("speakAnswers", "speakAnswers", "speakAnswersHelp", state.speakAnswers)}</div><div class="form-stack">${fieldSelect("voiceChoice", "voiceName", voices.map(([value, key]) => [value, key]), state.voiceName)}${rangeField("voiceVolume", "voiceVolume", state.voiceVolume, 0, 100, "%")}<button id="preview-voice" class="secondary-button" type="button" data-i18n="previewVoice">${text("previewVoice")}</button></div>`;
  const soundContent = `<div class="setting-list">${toggle("soundsEnabled", "soundsEnabled", "soundsEnabledHelp", state.soundsEnabled)}</div>${rangeField("soundVolume", "soundVolume", state.soundVolume, 0, 100, "%")}`;
  const privacy = `<div class="form-stack">${fieldSelect("interfaceLanguage", "uiLanguage", [["en", "english"], ["ar", "arabic"]], currentLanguage)}${fieldSelect("speechLanguage", "speechLanguage", [["auto", "speechAuto"]], "auto")}</div>${privacyCallout("speechPrivacyTitle", "speechPrivacyText")}`;
  settingsContent.innerHTML = `${sectionHeader(2, "voiceEyebrow", "voiceTitle", "voiceDescription")}<div class="content-grid">${card("spokenAnswersTitle", "spokenAnswersDescription", voiceContent, "◖")}${card("soundsTitle", "soundsDescription", soundContent, "∿")}${card("languageTitle", "languageDescription", privacy, "文", true)}</div>`;
}

function behaviorPage(state) {
  const walking = `<div class="setting-list">${toggle("standOnWindows", "standOnWindows", "standOnWindowsHelp", state.standOnWindows)}</div>`;
  const movement = `${rangeField("walkingSpeed", "walkingSpeed", state.walkingSpeed, 30, 180, "%")}${rangeField("characterScale", "characterScale", state.characterScale, 40, 120, "%")}`;
  const corners = [
    ["bottom-right", "cornerRight"],
    ["bottom-left", "cornerLeft"],
    ["top-right", "cornerTopRight"],
    ["top-left", "cornerTopLeft"],
  ];
  const rest = `<div class="form-stack">${rangeField("sleepDelay", "sleepDelay", state.sleepDelay, 1, 60, ` ${text("minutes")}`)}${fieldSelect("sleepCorner", "sleepCorner", corners, state.sleepCorner)}${fieldSelect("monitor", "monitor", [["primary", "primaryMonitor"]], state.monitor)}</div><div class="privacy-callout"><span class="callout-mark" aria-hidden="true">✳</span><span data-i18n="behaviorNote">${text("behaviorNote")}</span></div>`;
  settingsContent.innerHTML = `${sectionHeader(3, "behaviorEyebrow", "behaviorTitle", "behaviorDescription")}<div class="content-grid">${card("windowWalkingTitle", "windowWalkingDescription", walking, "⌑")}${card("movementTitle", "movementDescription", movement, "↔")}${card("restTitle", "restDescription", rest, "☾", true)}</div>`;
}

function toolRows(state) {
  const options = [
    ["auto", "permissionAuto"],
    ["ask", "permissionAsk"],
    ["disabled", "permissionDisabled"],
  ];
  return toolDefinitions.map(([titleKey, helpKey, toolKey, fallback]) => {
    const tier = state.toolTiers?.[toolKey] ?? fallback;
    return `<div class="tool-row"><span><strong data-i18n="${titleKey}">${text(titleKey)}</strong><small data-i18n="${helpKey}">${text(helpKey)}</small></span><select class="field-select" aria-label="${text(titleKey)}" data-tool-tier="${toolKey}">${selectOptions(options, tier)}</select></div>`;
  }).join("");
}

function folderRows(folders) {
  const rows = folders.map((folder, index) => `<li><span aria-hidden="true">⌁</span><code dir="ltr">${escapeHtml(folder)}</code><button type="button" data-remove-folder="${index}" aria-label="${text("removeFolder")}" title="${text("removeFolder")}">×</button></li>`).join("");
  return `<ul class="folder-list" id="folder-list">${rows}</ul>`;
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (character) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  })[character]);
}

function safetyPage(state) {
  const folders = folderRows(state.allowedFolders);
  const limits = `${rangeField("rateLimit", "rateLimit", state.rateLimit, 1, 60, "")}${rangeField("maxSteps", "maxSteps", state.maxSteps, 1, 30, "")}`;
  const forbidden = `<div class="forbidden-box"><p data-i18n="forbiddenCommands">${text("forbiddenCommands")}</p><div class="forbidden-tags"><span>sudo</span><span>rm -rf</span><span data-i18n="forbiddenTagDisk">${text("forbiddenTagDisk")}</span><span data-i18n="forbiddenTagSystem">${text("forbiddenTagSystem")}</span><span data-i18n="forbiddenTagOthers">${text("forbiddenTagOthers")}</span><span data-i18n="forbiddenTagPasswords">${text("forbiddenTagPasswords")}</span><span data-i18n="forbiddenTagKeyring">${text("forbiddenTagKeyring")}</span></div></div>`;
  const folderContent = `<p class="field-hint" data-i18n="foldersDescription">${text("foldersDescription")}</p>${folders}<div class="folder-add"><input id="folder-entry" class="field-input" type="text" dir="ltr" placeholder="${text("folderPlaceholder")}" data-i18n-placeholder="folderPlaceholder"><button id="add-folder" class="tiny-button" type="button" data-i18n="addFolder">${text("addFolder")}</button></div>`;
  const privacy = `<article class="setting-card full-width">${privacyCallout("screenPrivacyTitle", "screenPrivacyText")}</article>`;
  settingsContent.innerHTML = `${sectionHeader(4, "safetyEyebrow", "safetyTitle", "safetyDescription")}<div class="content-grid">${card("permissionTitle", "permissionKey", `<div class="tool-list">${toolRows(state)}</div>`, "◇", true)}${card("foldersTitle", "foldersDescription", folderContent, "⌂")}${card("forbiddenTitle", "forbiddenDescription", forbidden, "⊘")}${card("protectionTitle", "protectionDescription", limits, "⟲", true)}${privacy}</div>`;
}

function shortcutsPage(state) {
  const hotkeys = `<label class="field"><span class="field-label" data-i18n="emergencyHotkey">${text("emergencyHotkey")}</span><input class="field-input" type="text" dir="ltr" data-setting="emergencyHotkey" value="${escapeHtml(state.emergencyHotkey)}"><span class="field-hint" data-i18n="emergencyHelp">${text("emergencyHelp")}</span></label><label class="field"><span class="field-label" data-i18n="pushToTalk">${text("pushToTalk")}</span><input class="field-input" type="text" dir="ltr" data-setting="pushToTalk" value="${escapeHtml(state.pushToTalk)}" placeholder="Optional"></label><p class="field-hint" data-i18n="pushToTalkHelp">${text("pushToTalkHelp")}</p>`;
  const startup = `<div class="setting-list">${toggle("autostart", "autostart", "autostartHelp", state.autostart)}</div>`;
  const limit = `<label class="field"><span class="field-label" data-i18n="rateLimit">${text("rateLimit")}</span><input class="field-input" type="number" min="1" max="60" data-setting="rateLimit" value="${state.rateLimit}"></label><label class="field"><span class="field-label" data-i18n="maxSteps">${text("maxSteps")}</span><input class="field-input" type="number" min="1" max="30" data-setting="maxSteps" value="${state.maxSteps}"></label>`;
  settingsContent.innerHTML = `${sectionHeader(5, "shortcutEyebrow", "shortcutTitle", "shortcutDescription")}<div class="content-grid">${card("hotkeysTitle", "hotkeysDescription", `<div class="form-stack">${hotkeys}</div>`, "⌘")}${card("startTitle", "startDescription", startup, "◉")}${card("protectionTitle", "protectionDescription", limit, "⟲")}<article class="setting-card full-width">${privacyCallout("keyboardNote", "emergencyHelp")}</article></div>`;
}

function renderPage(page, state = readStoredState()) {
  currentPage = page;
  const renderers = {
    api: apiPage,
    voice: voicePage,
    behavior: behaviorPage,
    safety: safetyPage,
    shortcuts: shortcutsPage,
  };
  renderers[page](state);
  document.querySelectorAll(".section-nav [data-page]").forEach((button) => {
    if (button.dataset.page === page) button.setAttribute("aria-current", "page");
    else button.removeAttribute("aria-current");
  });
  document.querySelector("#section-crumb").textContent = text(pageLabels[page]);
  applyLanguage();
}

function collectSettings() {
  const next = { ...draftSettings };
  settingsContent.querySelectorAll("[data-setting]").forEach((control) => {
    if (control.classList.contains("switch")) {
      next[control.dataset.setting] = control.getAttribute("aria-checked") === "true";
    } else if (control.type === "range" || control.type === "number") {
      next[control.dataset.setting] = Number(control.value);
    } else {
      next[control.dataset.setting] = control.value;
    }
  });
  const tiers = { ...next.toolTiers };
  settingsContent.querySelectorAll("[data-tool-tier]").forEach((control) => {
    tiers[control.dataset.toolTier] = control.value;
  });
  next.toolTiers = tiers;
  const folders = settingsContent.querySelector("#folder-list");
  if (folders) {
    next.allowedFolders = [...folders.querySelectorAll("code")].map((item) => item.textContent);
  }
  return next;
}

function saveSettings() {
  try {
    draftSettings = collectSettings();
    localStorage.setItem(STORE_KEY, JSON.stringify(draftSettings));
    document.querySelector("#save-feedback").textContent = text("saved");
    showToast(text("saved"));
  } catch {
    document.querySelector("#save-feedback").textContent = text("savedError");
    showToast(text("savedError"));
  }
}

function pageTransitionPoint(element) {
  const bounds = element.getBoundingClientRect();
  return {
    x: bounds.left + bounds.width / 2,
    y: bounds.top + bounds.height / 2,
  };
}

function characterScale(element) {
  return element.getBoundingClientRect().width / 380;
}

function makeTravelingEmber(svg, point, scale) {
  travelingEmber.replaceChildren(svg.cloneNode(true));
  travelingEmber.style.display = "block";
  travelingEmber.style.left = `${point.x}px`;
  travelingEmber.style.top = `${point.y}px`;
  travelingEmber.style.transform = `translate(-50%, -50%) scale(${scale})`;
  return travelingEmber;
}

function flyCharacter(start, end, startScale, endScale, arc = -52, parkAtEnd = false) {
  const source = document.querySelector(".character-wrap .ember-character");
  if (!source) return Promise.resolve();
  const travelId = ++characterTravelId;
  travelingEmber.getAnimations().forEach((animation) => animation.cancel());
  travelingEmber.classList.remove("is-chat-parked", "is-recording");
  travelingEmber.setAttribute("aria-hidden", "true");
  travelingEmber.removeAttribute("role");
  travelingEmber.removeAttribute("aria-label");
  travelingEmber.tabIndex = -1;
  const overlay = makeTravelingEmber(source, start, startScale);
  const animation = overlay.animate([
    {
      left: `${start.x}px`,
      top: `${start.y}px`,
      transform: `translate(-50%, -50%) scale(${startScale}) rotate(-6deg)`,
      offset: 0,
    },
    {
      left: `${(start.x + end.x) / 2}px`,
      top: `${(start.y + end.y) / 2 + arc}px`,
      transform: `translate(-50%, -50%) scale(${Math.max(startScale, endScale) * 1.07}) rotate(4deg)`,
      offset: 0.56,
    },
    {
      left: `${end.x}px`,
      top: `${end.y}px`,
      transform: `translate(-50%, -50%) scale(${endScale}) rotate(0deg)`,
      offset: 1,
    },
  ], {
    duration: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? 0 : 680,
    easing: "cubic-bezier(0.2, 0.82, 0.22, 1)",
    fill: "forwards",
  });
  return animation.finished.catch(() => undefined).then(() => {
    if (travelId !== characterTravelId) return;
    if (parkAtEnd) {
      overlay.style.left = `${end.x}px`;
      overlay.style.top = `${end.y}px`;
      overlay.style.transform = `translate(-50%, -50%) scale(${endScale})`;
      overlay.classList.add("is-chat-parked");
      overlay.setAttribute("aria-hidden", "false");
      overlay.setAttribute("role", "button");
      overlay.setAttribute("aria-label", text("emberCharacter"));
      overlay.tabIndex = 0;
      return;
    }
    overlay.classList.remove("is-chat-parked", "is-recording");
    overlay.style.display = "none";
    overlay.setAttribute("aria-hidden", "true");
    overlay.tabIndex = -1;
  });
}

function companionPosition() {
  const header = document.querySelector(".topbar");
  const scale = clamp(window.innerWidth / 3200, 0.31, 0.42);
  const headerBottom = header?.getBoundingClientRect().bottom ?? 74;
  return {
    point: {
      x: window.innerWidth - Math.max(74, 190 * scale / 2 + 16),
      y: headerBottom + 125 * scale / 2 + 14,
    },
    scale,
  };
}

function setComposerStatus(messageKey = "", error = false) {
  voiceStatus.textContent = messageKey ? text(messageKey) : "";
  voiceComposer.classList.toggle("is-error", error);
}

function positionVoiceComposer(anchor) {
  const bounds = anchor.getBoundingClientRect();
  const composerWidth = voiceComposer.getBoundingClientRect().width;
  const parked = anchor === travelingEmber;
  let left = parked
    ? bounds.left - composerWidth - 18
    : bounds.left + bounds.width * 0.56;
  let top = parked
    ? bounds.bottom + 12
    : bounds.top + bounds.height * 0.05;
  left = clamp(left, 16, window.innerWidth - composerWidth - 16);
  const composerHeight = voiceComposer.getBoundingClientRect().height;
  top = clamp(top, 84, window.innerHeight - composerHeight - 16);
  voiceComposer.style.left = `${left}px`;
  voiceComposer.style.top = `${top}px`;
}

function openVoiceComposer(anchor = characterWrap) {
  if (!settingsView.hidden) return;
  voiceComposer.hidden = false;
  voiceComposer.classList.remove("is-error", "is-recording");
  setComposerStatus();
  positionVoiceComposer(anchor);
}

function stopMicrophone() {
  if (recordingRecorder?.state === "recording") recordingRecorder.stop();
  recordingRecorder = null;
  recordingStream?.getTracks().forEach((track) => track.stop());
  recordingStream = null;
  characterWrap.classList.remove("is-recording");
  travelingEmber.classList.remove("is-recording");
  voiceComposer.classList.remove("is-recording");
}

function closeVoiceComposer(cancelRecording = true) {
  if (cancelRecording && recordingState !== "idle") {
    recordingRequestId += 1;
    stopMicrophone();
    recordingState = "idle";
  }
  if (recordingHoldTimer) {
    clearTimeout(recordingHoldTimer);
    recordingHoldTimer = 0;
  }
  recordingPointerId = null;
  voiceComposer.hidden = true;
  voiceComposer.classList.remove("is-error", "is-recording");
  setComposerStatus();
}

function renderConversation() {
  conversationMessages.replaceChildren();
  for (const turn of conversationTurns) {
    const item = document.createElement("li");
    item.className = "conversation-turn";

    const question = document.createElement("article");
    question.className = "conversation-message is-question";
    const questionLabel = document.createElement("span");
    questionLabel.className = "conversation-message-label";
    questionLabel.textContent = text("questionLabel");
    const questionText = document.createElement("p");
    questionText.className = "conversation-message-text";
    questionText.dir = "auto";
    questionText.textContent = turn.question;
    question.append(questionLabel, questionText);

    const answer = document.createElement("article");
    answer.className = `conversation-message is-answer${turn.pending ? " is-pending" : ""}`;
    const answerLabel = document.createElement("span");
    answerLabel.className = "conversation-message-label";
    answerLabel.textContent = text("emberReplyLabel");
    const answerText = document.createElement("p");
    answerText.className = "conversation-message-text";
    answerText.dir = "auto";
    answerText.textContent = turn.pending ? text("thinkingReply") : turn.answer;
    answer.append(answerLabel, answerText);
    item.append(question, answer);
    conversationMessages.append(item);
  }
  conversationMessages.scrollTop = conversationMessages.scrollHeight;
}

function appendConversationTurn(question, kind = "text") {
  const turn = {
    question,
    answer: "",
    answerKey: kind === "voice" ? "sampleVoiceReply" : "sampleTextReply",
    pending: true,
  };
  conversationTurns.push(turn);
  renderConversation();
  openConversation();
  window.setTimeout(() => {
    turn.pending = false;
    turn.answer = text(turn.answerKey);
    renderConversation();
  }, 760);
}

function openConversation() {
  if (!conversationWindow.hidden) return;
  const start = pageTransitionPoint(characterSvg);
  const startScale = characterScale(characterSvg);
  const destination = companionPosition();
  conversationWindow.hidden = false;
  chatScrim.hidden = false;
  homeView.classList.add("chat-active");
  characterWrap.classList.add("chat-away");
  document.body.classList.add("chat-open");
  void flyCharacter(
    start,
    destination.point,
    startScale,
    destination.scale,
    -48,
    true,
  );
  conversationWindow.focus({ preventScroll: true });
}

function closeConversation() {
  if (conversationWindow.hidden) return;
  closeVoiceComposer();
  const bounds = travelingEmber.style.display === "block"
    ? travelingEmber.getBoundingClientRect()
    : null;
  const start = bounds
    ? { x: bounds.left + bounds.width / 2, y: bounds.top + bounds.height / 2 }
    : pageTransitionPoint(characterSvg);
  const startScale = bounds ? bounds.width / 380 : characterScale(characterSvg);
  const end = pageTransitionPoint(characterSvg);
  const endScale = characterScale(characterSvg);
  conversationWindow.hidden = true;
  chatScrim.hidden = true;
  homeView.classList.remove("chat-active");
  document.body.classList.remove("chat-open");
  void flyCharacter(start, end, startScale, endScale, -58).then(() => {
    if (!conversationWindow.hidden) return;
    characterWrap.classList.remove("chat-away");
    characterWrap.focus({ preventScroll: true });
  });
}

function submitVoiceQuestion() {
  const question = voiceQuestion.value.trim();
  if (!question) {
    setComposerStatus("emptyQuestion", true);
    voiceQuestion.focus();
    return;
  }
  voiceQuestion.value = "";
  closeVoiceComposer(false);
  appendConversationTurn(question);
}

async function beginLocalRecording(requestId) {
  if (typeof MediaRecorder === "undefined") {
    recordingState = "idle";
    recordingPointerId = null;
    setComposerStatus("recorderUnsupported", true);
    return;
  }
  if (!navigator.mediaDevices?.getUserMedia) {
    recordingState = "idle";
    recordingPointerId = null;
    setComposerStatus("microphoneUnavailable", true);
    return;
  }
  recordingState = "requesting";
  setComposerStatus("microphoneRequesting");
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    if (requestId !== recordingRequestId || recordingPointerId === null) {
      stream.getTracks().forEach((track) => track.stop());
      return;
    }
    recordingStream = stream;
    recordingRecorder = new MediaRecorder(stream);
    recordingRecorder.start();
    recordingState = "recording";
    voiceComposer.classList.add("is-recording");
    characterWrap.classList.add("is-recording");
    if (travelingEmber.classList.contains("is-chat-parked")) {
      travelingEmber.classList.add("is-recording");
    }
    setComposerStatus("microphoneRecording");
  } catch (error) {
    recordingState = "idle";
    recordingPointerId = null;
    stopMicrophone();
    const message = error?.name === "NotAllowedError" || error?.name === "PermissionDeniedError"
      ? "microphoneDenied"
      : "microphoneUnavailable";
    setComposerStatus(message, true);
  }
}

function handleEmberPointerDown(event) {
  if (
    event.button !== 2
    || voiceComposer.hidden
    || recordingPointerId !== null
    || !event.target.closest("#character-wrap, #traveling-ember.is-chat-parked")
  ) return;
  event.preventDefault();
  recordingPointerId = event.pointerId;
  const requestId = ++recordingRequestId;
  recordingHoldTimer = window.setTimeout(() => {
    recordingHoldTimer = 0;
    if (recordingPointerId === event.pointerId) {
      void beginLocalRecording(requestId);
    }
  }, 350);
}

function finishEmberPointer(event, cancelled = false) {
  if ((!cancelled && event.button !== 2) || event.pointerId !== recordingPointerId) return;
  if (recordingHoldTimer) {
    clearTimeout(recordingHoldTimer);
    recordingHoldTimer = 0;
  }
  const hadRecording = recordingState === "recording";
  const awaitingPermission = recordingState === "requesting";
  recordingPointerId = null;
  if (awaitingPermission) recordingRequestId += 1;
  if (hadRecording) {
    stopMicrophone();
    recordingState = "idle";
    if (cancelled) {
      setComposerStatus("recordingCancelled");
      return;
    }
    closeVoiceComposer(false);
    appendConversationTurn(text("voiceQuestionLabel"), "voice");
  } else if (awaitingPermission || cancelled) {
    recordingState = "idle";
    stopMicrophone();
    setComposerStatus("recordingCancelled");
  }
}

async function openSection(page) {
  if (!pageLabels[page]) return;
  if (homeView.hidden) {
    draftSettings = collectSettings();
    renderPage(page, draftSettings);
    return;
  }
  const source = document.querySelector("#character-wrap");
  const sourceSvg = source.querySelector(".ember-character");
  const avatarSvg = document.querySelector(".avatar-back .avatar-ring svg");
  const start = pageTransitionPoint(sourceSvg);
  homeView.hidden = true;
  settingsView.hidden = false;
  scheduleOrbitConnectorUpdate();
  centerGaze();
  renderPage(page, draftSettings);
  const end = pageTransitionPoint(avatarSvg);
  await flyCharacter(
    start,
    end,
    characterScale(sourceSvg),
    characterScale(avatarSvg),
    -35,
  );
}

async function returnHome() {
  if (homeView.hidden) {
    const avatar = document.querySelector(".avatar-back .avatar-ring");
    const avatarSvg = avatar.querySelector("svg");
    const start = pageTransitionPoint(avatarSvg);
    settingsView.hidden = true;
    homeView.hidden = false;
    scheduleOrbitConnectorUpdate();
    const homeCharacter = document.querySelector("#character-wrap");
    const homeSvg = homeCharacter.querySelector(".ember-character");
    const target = pageTransitionPoint(homeSvg);
    if (pointerPosition) {
      moveGazeTowardPointer(pointerPosition);
    }
    await flyCharacter(
      start,
      target,
      characterScale(avatarSvg),
      characterScale(homeSvg),
      -78,
    );
    return;
  }
  homeView.hidden = false;
}

function addFolder() {
  const field = settingsContent.querySelector("#folder-entry");
  const list = settingsContent.querySelector("#folder-list");
  const folder = field.value.trim();
  if (!folder) {
    showToast(text("folderEmpty"));
    field.focus();
    return;
  }
  const existing = [...list.querySelectorAll("code")].map((item) => item.textContent);
  if (existing.includes(folder)) {
    showToast(text("folderExists"));
    field.select();
    return;
  }
  const next = [...existing, folder];
  const wrapper = document.createElement("div");
  wrapper.innerHTML = folderRows(next);
  list.replaceWith(wrapper.firstElementChild);
  field.value = "";
  showToast(text("folderAdded"));
}

function resetPreview() {
  try {
    localStorage.removeItem(STORE_KEY);
    localStorage.removeItem(LANGUAGE_KEY);
    draftSettings = structuredClone(defaults);
    currentLanguage = "en";
    document.querySelector("#save-feedback").textContent = "";
    applyLanguage();
    if (!settingsView.hidden) renderPage(currentPage, draftSettings);
    showToast(text("resetDone"));
  } catch {
    showToast(text("savedError"));
  }
}

function setLanguage(language) {
  if (!settingsView.hidden) draftSettings = collectSettings();
  currentLanguage = language === "ar" ? "ar" : "en";
  draftSettings.uiLanguage = currentLanguage;
  try {
    localStorage.setItem(LANGUAGE_KEY, currentLanguage);
  } catch {
    showToast(text("savedError"));
  }
  applyLanguage();
  if (!settingsView.hidden) renderPage(currentPage, draftSettings);
}

function updateRangeOutput(range) {
  const output = range.closest(".range-field").querySelector("output");
  const suffix = range.dataset.setting === "sleepDelay"
    ? ` ${text("minutes")}`
    : ["walkingSpeed", "characterScale", "voiceVolume", "soundVolume"].includes(range.dataset.setting)
      ? "%"
      : "";
  output.value = `${range.value}${suffix}`;
  output.textContent = output.value;
}

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

function getConnectorAnchor(rect, direction) {
  const inset = 18;
  if (direction === "bottom") {
    return { x: rect.left + rect.width / 2, y: rect.bottom };
  }
  if (direction === "right") {
    return { x: rect.right, y: rect.top + rect.height / 2 };
  }
  if (direction === "left") {
    return { x: rect.left, y: rect.top + rect.height / 2 };
  }
  if (direction === "top-right") {
    return { x: rect.right - inset, y: rect.top };
  }
  return { x: rect.left + inset, y: rect.top };
}

function updateOrbitConnectors() {
  connectorFrame = 0;
  if (homeView.hidden) return;

  const stageRect = orbitStage.getBoundingClientRect();
  if (!stageRect.width || !stageRect.height) return;
  orbitLines.setAttribute("viewBox", `0 0 ${stageRect.width} ${stageRect.height}`);

  for (const { page, anchor, target: targetPoint } of connectorDefinitions) {
    const cardClass = page === "api" ? "gemini" : page;
    const card = orbitStage.querySelector(`.orbit-${cardClass}`);
    const path = orbitLines.querySelector(`[data-connector="${page}"]`);
    const dot = orbitLines.querySelector(`[data-connector-dot="${page}"]`);
    if (!card || !path || !dot) continue;

    const cardRect = card.getBoundingClientRect();
    const start = getConnectorAnchor(cardRect, anchor);
    const svgPoint = characterSvg.createSVGPoint();
    svgPoint.x = targetPoint.x;
    svgPoint.y = targetPoint.y;
    const screenTarget = svgPoint.matrixTransform(characterSvg.getScreenCTM());
    const target = {
      x: screenTarget.x,
      y: screenTarget.y,
    };
    const startX = start.x - stageRect.left;
    const startY = start.y - stageRect.top;
    const targetX = target.x - stageRect.left;
    const targetY = target.y - stageRect.top;
    const deltaX = targetX - startX;
    const deltaY = targetY - startY;

    path.setAttribute(
      "d",
      `M ${startX} ${startY} C ${startX + deltaX * 0.36} ${startY + deltaY * 0.12}, ${targetX - deltaX * 0.28} ${targetY - deltaY * 0.18}, ${targetX} ${targetY}`,
    );
    dot.setAttribute("cx", targetX.toFixed(2));
    dot.setAttribute("cy", targetY.toFixed(2));
  }
}

function scheduleOrbitConnectorUpdate() {
  if (connectorFrame) return;
  connectorFrame = requestAnimationFrame(updateOrbitConnectors);
}

function moveGazeTowardPointer(event) {
  pointerPosition = { clientX: event.clientX, clientY: event.clientY };
  if (homeView.hidden) {
    gaze.targetX = 0;
    gaze.targetY = 0;
  } else {
    const point = characterSvg.createSVGPoint();
    point.x = event.clientX;
    point.y = event.clientY;
    const svgPoint = point.matrixTransform(characterSvg.getScreenCTM().inverse());
    gaze.targetX = clamp((svgPoint.x - 190) * 0.035, -4.5, 4.5);
    gaze.targetY = clamp((svgPoint.y - 156) * 0.035, -3.5, 3.5);
  }
  scheduleGazeAnimation();
}

function centerGaze() {
  gaze.targetX = 0;
  gaze.targetY = 0;
  scheduleGazeAnimation();
}

function scheduleGazeAnimation() {
  if (!gaze.frame) {
    gaze.lastTime = 0;
    gaze.frame = requestAnimationFrame(animateGaze);
  }
}

function animateGaze(now) {
  const dt = gaze.lastTime ? Math.min((now - gaze.lastTime) / 1000, 0.05) : 0;
  gaze.lastTime = now;
  const stiffness = 260;
  const damping = 0.82;
  const dampingCoefficient = 2 * Math.sqrt(stiffness) * damping;
  gaze.velocityX += (
    stiffness * (gaze.targetX - gaze.x) - dampingCoefficient * gaze.velocityX
  ) * dt;
  gaze.velocityY += (
    stiffness * (gaze.targetY - gaze.y) - dampingCoefficient * gaze.velocityY
  ) * dt;
  gaze.x += gaze.velocityX * dt;
  gaze.y += gaze.velocityY * dt;
  characterEyes.setAttribute(
    "transform",
    `translate(${gaze.x.toFixed(2)} ${gaze.y.toFixed(2)})`,
  );

  const settled = Math.abs(gaze.targetX - gaze.x) < 0.01
    && Math.abs(gaze.targetY - gaze.y) < 0.01
    && Math.abs(gaze.velocityX) < 0.02
    && Math.abs(gaze.velocityY) < 0.02;
  if (settled) {
    gaze.x = gaze.targetX;
    gaze.y = gaze.targetY;
    gaze.velocityX = 0;
    gaze.velocityY = 0;
    characterEyes.setAttribute(
      "transform",
      `translate(${gaze.x.toFixed(2)} ${gaze.y.toFixed(2)})`,
    );
    gaze.frame = 0;
    gaze.lastTime = 0;
    return;
  }
  gaze.frame = requestAnimationFrame(animateGaze);
}

document.addEventListener("pointermove", moveGazeTowardPointer, { passive: true });
window.addEventListener("resize", scheduleOrbitConnectorUpdate, { passive: true });
new ResizeObserver(scheduleOrbitConnectorUpdate).observe(orbitStage);
document.fonts.ready.then(scheduleOrbitConnectorUpdate);

document.addEventListener("contextmenu", (event) => {
  const character = event.target.closest(
    "#character-wrap, #traveling-ember.is-chat-parked",
  );
  if (!character) return;
  event.preventDefault();
  if (voiceComposer.hidden) {
    openVoiceComposer(character.id === "character-wrap" ? characterWrap : travelingEmber);
  }
});

document.addEventListener("pointerdown", handleEmberPointerDown, true);
document.addEventListener("pointerup", finishEmberPointer, true);
document.addEventListener(
  "pointercancel",
  (event) => finishEmberPointer(event, true),
  true,
);

characterWrap.addEventListener("keydown", (event) => {
  if (
    event.target === characterWrap
    && (event.key === "Enter" || event.key === " " || event.key === "ContextMenu")
  ) {
    event.preventDefault();
    openVoiceComposer(characterWrap);
  }
});

travelingEmber.addEventListener("keydown", (event) => {
  if (
    travelingEmber.classList.contains("is-chat-parked")
    && (event.key === "Enter" || event.key === " " || event.key === "ContextMenu")
  ) {
    event.preventDefault();
    openVoiceComposer(travelingEmber);
  }
});

voiceComposer.addEventListener("click", (event) => {
  if (!event.target.closest("button, textarea")) voiceQuestion.focus();
});
voiceQuestion.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey && !event.isComposing) {
    event.preventDefault();
    submitVoiceQuestion();
  } else if (event.key === "Escape") {
    event.preventDefault();
    closeVoiceComposer();
  }
});

chatScrim.addEventListener("click", closeConversation);
document.querySelector("#conversation-return").addEventListener("click", closeConversation);
conversationWindow.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    event.preventDefault();
    closeConversation();
  } else if (event.key === "Tab") {
    event.preventDefault();
    document.querySelector("#conversation-return").focus();
  }
});
window.addEventListener("resize", () => {
  if (travelingEmber.classList.contains("is-chat-parked")) {
    const destination = companionPosition();
    travelingEmber.style.left = `${destination.point.x}px`;
    travelingEmber.style.top = `${destination.point.y}px`;
    travelingEmber.style.transform = `translate(-50%, -50%) scale(${destination.scale})`;
  }
  if (!voiceComposer.hidden) {
    positionVoiceComposer(
      travelingEmber.classList.contains("is-chat-parked") ? travelingEmber : characterWrap,
    );
  }
}, { passive: true });

document.addEventListener("click", (event) => {
  if (event.target.closest("#voice-composer")) {
    if (!event.target.closest("button, textarea")) voiceQuestion.focus();
    if (!event.target.closest("#send-question")) return;
  }
  if (event.target.closest("#send-question")) {
    submitVoiceQuestion();
    return;
  }
  if (event.target.closest("#conversation-window")) return;
  const pageButton = event.target.closest("[data-page]");
  if (pageButton) {
    event.preventDefault();
    openSection(pageButton.dataset.page);
    return;
  }
  if (event.target.closest("[data-home]")) {
    event.preventDefault();
    returnHome();
    return;
  }
  if (event.target.closest("[data-reset]")) {
    resetPreview();
    return;
  }
  if (event.target.closest("#save-button")) {
    saveSettings();
    return;
  }
  if (event.target.closest("#show-key")) {
    const input = settingsContent.querySelector("#api-key");
    input.type = input.type === "password" ? "text" : "password";
    event.target.closest("#show-key").textContent = input.type === "password" ? text("show") : text("hide");
    return;
  }
  if (event.target.closest("#test-connection")) {
    const input = settingsContent.querySelector("#api-key");
    const status = settingsContent.querySelector("#api-key-status");
    status.dataset.state = input.value.trim() ? "success" : "error";
    status.lastChild.textContent = input.value.trim() ? text("testMock") : text("keyEmpty");
    return;
  }
  if (event.target.closest("#preview-voice")) {
    showToast(text("voiceMock"));
    return;
  }
  if (event.target.closest("#add-folder")) {
    addFolder();
    return;
  }
  const removeFolderButton = event.target.closest("[data-remove-folder]");
  if (removeFolderButton) {
    const folders = [...settingsContent.querySelectorAll("#folder-list code")]
      .map((item) => item.textContent)
      .filter((_folder, index) => index !== Number(removeFolderButton.dataset.removeFolder));
    const wrapper = document.createElement("div");
    wrapper.innerHTML = folderRows(folders);
    settingsContent.querySelector("#folder-list").replaceWith(wrapper.firstElementChild);
    return;
  }
  const switchControl = event.target.closest(".switch");
  if (switchControl) {
    const checked = switchControl.getAttribute("aria-checked") === "true";
    switchControl.setAttribute("aria-checked", String(!checked));
    return;
  }
  if (event.target.closest(".close-button")) {
    showToast(text("closeHint"));
  }
});

document.addEventListener("input", (event) => {
  if (event.target.matches('input[type="range"]')) updateRangeOutput(event.target);
});

document.querySelector("#language-select").addEventListener("change", (event) => {
  setLanguage(event.target.value);
});

settingsContent.addEventListener("change", (event) => {
  if (event.target.dataset.setting === "uiLanguage") setLanguage(event.target.value);
});

settingsContent.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && event.target.id === "folder-entry") {
    event.preventDefault();
    addFolder();
  }
});

let draftSettings = readStoredState();

try {
  const savedLanguage = localStorage.getItem(LANGUAGE_KEY);
  currentLanguage = savedLanguage === "ar" || (!savedLanguage && draftSettings.uiLanguage === "ar") ? "ar" : "en";
  draftSettings.uiLanguage = currentLanguage;
} catch {
  currentLanguage = "en";
}
applyLanguage();
