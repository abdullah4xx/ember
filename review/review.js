const ember = document.querySelector("#desktop-ember");
const bubble = document.querySelector("#ask-bubble");
const question = document.querySelector("#ask-question");
const form = document.querySelector("#ask-form");
const status = document.querySelector("#ask-status");
const desktop = document.querySelector(".desktop");
const voiceMeter = document.querySelector("#voice-meter");
const voiceBars = [...voiceMeter.querySelectorAll("i")];
const eyes = document.querySelector("#desktop-ember-eyes");
const chatWindow = document.querySelector(".chat-window");
const browserPreview = document.querySelector("#browser-preview");
const browserClose = document.querySelector("#browser-close");
const chromeDockItem = document.querySelector("#chrome-dock-item");
const browserTabTitle = document.querySelector(".browser-tab-title");
const browserAddressText = document.querySelector("#browser-address-text");
const browserPreviewStatus = document.querySelector("#browser-preview-status");
const browserQuery = document.querySelector("#browser-query");
const typingCaret = document.querySelector("#typing-caret");
const searchResults = document.querySelector("#search-results");
const searchResultsCount = document.querySelector("#search-results-count");
const searchResultSource = document.querySelector(".search-result-source");
const searchResultTitle = document.querySelector("#search-result-title");
const searchResultDescription = document.querySelector("#search-result-description");
const chatUserMessage = document.querySelector("#chat-user-message");
const chatTitle = document.querySelector("#chat-title");
const chatSubtitle = document.querySelector("#chat-subtitle");
const chatPreviewLabel = document.querySelector("#chat-preview-label");
const chatThread = document.querySelector("#chat-thread");
const chatUserLabel = document.querySelector("#chat-user-label");
const chatEmberLabel = document.querySelector("#chat-ember-label");
const chatEmberReply = document.querySelector("#chat-ember-reply");
const chatInputLabel = document.querySelector("#chat-input-label");
const chatComposerHint = document.querySelector("#chat-composer-hint");
const chatOnline = document.querySelector("#chat-online");
const chatOnlineLabel = document.querySelector("#chat-online-label");
const chatClose = document.querySelector("#chat-close");
const chatForm = document.querySelector("#chat-form");
const chatInput = document.querySelector("#chat-input");
const chatSend = document.querySelector("#chat-send");
const chatStatus = document.querySelector("#chat-status");
const chatDate = document.querySelector("#chat-date");
const conversationCopy = {
  en: {
    windowLabel: "Ember conversation preview",
    title: "Ember",
    subtitle: "Here whenever you need a hand",
    online: "Preview mode",
    preview: "Local preview · Gemini is not connected",
    thread: "Conversation",
    date: "Today",
    you: "You",
    replyLabel: "Ember",
    sampleReply: "I’m here to help you take things one step at a time. This is a sample reply; Gemini isn’t connected in this preview.",
    voiceQuestion: "Voice question · local capture",
    voiceReply: "The microphone was active locally. This preview does not transcribe speech or connect to Gemini.",
    close: "Close conversation",
    inputLabel: "Write a message to Ember",
    placeholder: "Ask Ember anything…",
    send: "Send message",
    hint: "Enter to send · Shift+Enter for a new line",
    thinking: "Ember is preparing a preview reply…",
    empty: "Write a message first.",
    demoReply: "This is a local preview, so Gemini isn’t connected yet. Your message stays on this page.",
    webPreviewStatus: "Animation preview · nothing is sent to a website",
    searchPreview: "Search preview",
    searchPreviewReady: "Preview results · no external search was performed",
    browserClose: "Close website preview",
    webTaskDone: "Chrome animation preview · no external site was opened.",
    webProgress: "Ember is heading to Chrome to start the search…",
    browserLabel: "Chrome website preview",
    searchSource: "Ember · interactive preview",
  },
  ar: {
    windowLabel: "معاينة محادثة Ember",
    title: "Ember",
    subtitle: "أنا هنا أساعدك وقت ما تحتاج",
    online: "وضع المعاينة",
    preview: "معاينة محلية · Gemini غير متصل",
    thread: "المحادثة",
    date: "اليوم",
    you: "أنت",
    replyLabel: "Ember",
    sampleReply: "أنا هنا أساعدك تاخد الأمور خطوة بخطوة. ده رد تجريبي؛ Gemini مش متصل في المعاينة.",
    voiceQuestion: "سؤال صوتي · تسجيل محلي",
    voiceReply: "الميكروفون اشتغل محليًا. المعاينة لا تحوّل الكلام لنص ولا تتصل بـGemini.",
    close: "إغلاق المحادثة",
    inputLabel: "اكتب رسالة إلى Ember",
    placeholder: "اسأل Ember أي حاجة…",
    send: "إرسال الرسالة",
    hint: "Enter للإرسال · Shift+Enter لسطر جديد",
    thinking: "Ember بيجهز رد المعاينة…",
    empty: "اكتب رسالة الأول.",
    demoReply: "دي معاينة محلية، عشان كده Gemini مش متصل. رسالتك بتفضل على الصفحة دي.",
    webPreviewStatus: "معاينة للحركة · مش بنبعت حاجة لأي موقع",
    searchPreview: "معاينة بحث",
    searchPreviewReady: "نتائج تجريبية · لم يُجرَ بحث حقيقي على الإنترنت",
    browserClose: "إغلاق معاينة الموقع",
    webTaskDone: "حركة Chrome تجريبية · لم يُفتح موقع خارجي.",
    webProgress: "Ember رايح لأيقونة Chrome عشان يبدأ البحث…",
    browserLabel: "معاينة موقع في Chrome",
    searchSource: "Ember · معاينة تفاعلية",
  },
};
const sleepDelay = 30 * 1000;
const wakeRadius = 125;

let holdTimer = 0;
let heldPointerId = null;
let recordingRequestId = 0;
let recordingStream = null;
let audioContext = null;
let analyser = null;
let audioFrame = 0;
let recordingState = "idle";
let dragTimer = 0;
let dragPointerId = null;
let dragOrigin = null;
let dragTarget = null;
let dragCurrent = null;
let dragFrame = 0;
let dragLastTime = 0;
let dragReleased = false;
let gazeTarget = { x: 0, y: 0 };
let gazeCurrent = { x: 0, y: 0 };
let gazeFrame = 0;
let gazeLastTime = 0;
let lastPointerPosition = null;
let sleepTimer = 0;
let wakeAudioContext = null;
let wakeChimePending = false;
let sleepArrivalAnimation = null;
let chatArrivalAnimation = null;
let chatReturnAnimation = null;
let chatReturnState = null;
let chatReplyPending = false;
let websiteTaskSequence = 0;
let websiteTaskActive = false;
let websiteReturnState = null;
let websiteCharacterAnimation = null;
let preferredConversationLanguage = navigator.language?.toLowerCase().startsWith("ar")
  ? "ar"
  : "en";

function scheduleSleep() {
  if (sleepTimer) clearTimeout(sleepTimer);
  if (ember.classList.contains("is-sleeping")) return;
  sleepTimer = window.setTimeout(enterSleep, sleepDelay);
}

function enterSleep() {
  sleepTimer = 0;
  if (
    ember.classList.contains("is-sleeping")
    || !bubble.hidden
    || !chatWindow.hidden
    || recordingState !== "idle"
    || dragPointerId !== null
  ) return;
  const bounds = ember.getBoundingClientRect();
  const desktopBounds = desktop.getBoundingClientRect();
  const maxLeft = Math.max(0, desktop.clientWidth - bounds.width);
  const edgeInset = Math.min(16, maxLeft / 2);
  const maxRandomLeft = maxLeft - edgeInset;
  const chatRight = chatWindow.hidden
    ? edgeInset
    : chatWindow.getBoundingClientRect().right - desktopBounds.left + 16;
  const clearMinLeft = Math.max(edgeInset, chatRight);
  const minLeft = clearMinLeft <= maxRandomLeft ? clearMinLeft : edgeInset;
  const left = minLeft + Math.random() * (maxRandomLeft - minLeft);
  const top = 32 - bounds.height * 0.144;
  const startLeft = bounds.left - desktopBounds.left;
  const startTop = bounds.top - desktopBounds.top;

  ember.style.left = `${left}px`;
  ember.style.top = `${top}px`;
  ember.style.right = "auto";
  ember.style.bottom = "auto";
  ember.classList.add("is-sleeping");
  ember.setAttribute("aria-label", "Ember is asleep. Move the pointer near Ember to wake him.");

  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  sleepArrivalAnimation = ember.animate(
    [
      { transform: `translate(${startLeft - left}px, ${startTop - top}px)` },
      { transform: "translate(0, 0)" },
    ],
    { duration: 950, easing: "cubic-bezier(0.16, 1, 0.3, 1)" },
  );
  sleepArrivalAnimation.onfinish = () => {
    sleepArrivalAnimation = null;
  };
}

async function playWakeChime() {
  const AudioContextClass = window.AudioContext;
  if (!AudioContextClass) return;
  if (navigator.userActivation && !navigator.userActivation.hasBeenActive) {
    wakeChimePending = true;
    return;
  }
  try {
    if (!wakeAudioContext || wakeAudioContext.state === "closed") {
      wakeAudioContext = new AudioContextClass();
    }
    const context = wakeAudioContext;
    if (context.state === "suspended") await context.resume();
    const start = context.currentTime + 0.02;
    [660, 880].forEach((frequency, index) => {
      const oscillator = context.createOscillator();
      const gain = context.createGain();
      const noteStart = start + index * 0.13;
      oscillator.type = "sine";
      oscillator.frequency.setValueAtTime(frequency, noteStart);
      gain.gain.setValueAtTime(0.0001, noteStart);
      gain.gain.exponentialRampToValueAtTime(0.045, noteStart + 0.035);
      gain.gain.exponentialRampToValueAtTime(0.0001, noteStart + 0.24);
      oscillator.connect(gain);
      gain.connect(context.destination);
      oscillator.start(noteStart);
      oscillator.stop(noteStart + 0.25);
    });
    wakeChimePending = false;
    window.setTimeout(() => {
      if (context.state === "running") {
        void context.suspend().catch(() => {
          if (!bubble.hidden) status.textContent = "The wake sound could not stop cleanly.";
        });
      }
    }, 700);
  } catch {
    wakeChimePending = true;
    if (!bubble.hidden) status.textContent = "The wake sound was blocked by the browser.";
  }
}

function wakeEmber() {
  if (!ember.classList.contains("is-sleeping")) return;
  if (sleepArrivalAnimation) {
    const bounds = ember.getBoundingClientRect();
    const desktopBounds = desktop.getBoundingClientRect();
    ember.style.left = `${bounds.left - desktopBounds.left}px`;
    ember.style.top = `${bounds.top - desktopBounds.top}px`;
    sleepArrivalAnimation.cancel();
    sleepArrivalAnimation = null;
  }
  ember.classList.remove("is-sleeping");
  ember.classList.add("is-awake-hanging", "is-waking");
  ember.setAttribute("aria-label", "Ember is awake and still hanging upside down. Hold and drag to move him.");
  void playWakeChime();
  scheduleSleep();
}

function handlePointerProximity(event) {
  const bounds = ember.getBoundingClientRect();
  const nearestX = Math.max(bounds.left, Math.min(event.clientX, bounds.right));
  const nearestY = Math.max(bounds.top, Math.min(event.clientY, bounds.bottom));
  if (Math.hypot(event.clientX - nearestX, event.clientY - nearestY) > wakeRadius) return;
  wakeEmber();
  scheduleSleep();
}

function finishWakeAnimation(event) {
  if (event.animationName === "ember-eyes-open") {
    ember.classList.remove("is-waking");
  }
}

document.addEventListener("pointerdown", () => {
  if (wakeChimePending) void playWakeChime();
}, { capture: true });

scheduleSleep();

function positionBubble() {
  const characterBounds = ember.getBoundingClientRect();
  const desktopBounds = desktop.getBoundingClientRect();
  const bubbleWidth = bubble.offsetWidth;
  const bubbleHeight = bubble.offsetHeight;
  const headTop = characterBounds.top + characterBounds.height * 0.4;
  const centerX = characterBounds.left + characterBounds.width / 2;
  const left = Math.max(
    16,
    Math.min(centerX - bubbleWidth / 2, window.innerWidth - bubbleWidth - 16),
  );
  const top = Math.max(44, headTop - bubbleHeight - 10);

  bubble.style.left = `${left - desktopBounds.left}px`;
  bubble.style.top = `${top - desktopBounds.top}px`;
  bubble.style.setProperty("--tail-x", `${centerX - left}px`);
}

function setGazeTarget(x, y) {
  const bounds = ember.getBoundingClientRect();
  const scale = bounds.width / 380;
  if (!scale) return;
  gazeTarget = {
    x: Math.max(-5, Math.min(5, (x - (bounds.left + bounds.width / 2)) / scale * 0.14)),
    y: Math.max(-4, Math.min(4, (y - (bounds.top + bounds.height * 0.53)) / scale * 0.1)),
  };
  if (!gazeFrame) {
    gazeLastTime = 0;
    gazeFrame = requestAnimationFrame(animateGaze);
  }
}

function updateGazeTarget(event) {
  lastPointerPosition = { x: event.clientX, y: event.clientY };
  setGazeTarget(event.clientX, event.clientY);
  handlePointerProximity(event);
}

function animateGaze(time) {
  const delta = gazeLastTime ? Math.min(time - gazeLastTime, 48) : 16;
  gazeLastTime = time;
  const amount = 1 - Math.exp(-delta / 115);
  gazeCurrent.x += (gazeTarget.x - gazeCurrent.x) * amount;
  gazeCurrent.y += (gazeTarget.y - gazeCurrent.y) * amount;
  eyes.setAttribute(
    "transform",
    `translate(${gazeCurrent.x.toFixed(2)} ${gazeCurrent.y.toFixed(2)})`,
  );
  if (
    Math.abs(gazeTarget.x - gazeCurrent.x) < 0.025
    && Math.abs(gazeTarget.y - gazeCurrent.y) < 0.025
  ) {
    gazeCurrent = { ...gazeTarget };
    eyes.setAttribute("transform", `translate(${gazeCurrent.x.toFixed(2)} ${gazeCurrent.y.toFixed(2)})`);
    gazeFrame = 0;
    gazeLastTime = 0;
    return;
  }
  gazeFrame = requestAnimationFrame(animateGaze);
}

function openBubble() {
  bubble.hidden = false;
  status.textContent = "";
  positionBubble();
  question.focus();
}

function detectConversationLanguage(message) {
  const arabicLetters = message.match(/[\u0621-\u064a\u066e-\u06d3\u0750-\u077f\u08a0-\u08ff]/giu) ?? [];
  const latinLetters = message.match(/[a-z]/gi) ?? [];
  if (arabicLetters.length > latinLetters.length) return "ar";
  if (latinLetters.length > arabicLetters.length) return "en";
  if (arabicLetters.length && latinLetters.length) {
    const firstArabic = message.search(/[\u0621-\u064a\u066e-\u06d3\u0750-\u077f\u08a0-\u08ff]/iu);
    const firstLatin = message.search(/[a-z]/i);
    return firstArabic < firstLatin ? "ar" : "en";
  }
  return arabicLetters.length ? "ar" : preferredConversationLanguage;
}

function parseWebsiteSearchRequest(message) {
  const searchMatch = message.match(
    /(?:ابحث(?:ي|وا|لي)?(?:\s+عن)?|دور(?:ي)?\s+على|search(?:\s+for)?|look\s+up)\s+(.+)$/iu,
  );
  const asksToOpen = /(?:افتح|افتحلي|روح|ادخل|اذهب|open|visit|go\s+to)/iu.test(message);
  if (!asksToOpen && !searchMatch) return null;

  const hostMatch = message.match(
    /(?:https?:\/\/)?(?:www\.)?([a-z0-9-]+(?:\.[a-z]{2,})+)/iu,
  );
  const host = hostMatch?.[1]?.toLowerCase() ?? "";
  const query = (searchMatch?.[1] ?? host ?? message)
    .trim()
    .replace(/[.!؟?،,]+$/u, "");
  return {
    host,
    query: query || message.trim(),
  };
}

function delay(milliseconds) {
  return new Promise((resolve) => window.setTimeout(resolve, milliseconds));
}

function revealBrowserPreview(request) {
  const language = preferredConversationLanguage;
  const copy = conversationCopy[language];
  browserPreview.hidden = false;
  browserPreview.setAttribute("aria-label", copy.browserLabel);
  browserClose.setAttribute("aria-label", copy.browserClose);
  browserClose.title = copy.browserClose;
  browserPreview.classList.remove("is-entering", "is-typing", "has-search-helper");
  void browserPreview.offsetWidth;
  browserPreview.classList.add("is-entering");
  browserTabTitle.textContent = request.host
    ? `${request.host} · preview`
    : copy.searchPreview;
  browserAddressText.textContent = request.host
    ? `${request.host}/search · preview`
    : "preview.local/search";
  browserPreviewStatus.textContent = copy.webPreviewStatus;
  browserQuery.value = "";
  searchResults.hidden = true;
  searchResultsCount.textContent = copy.searchPreviewReady;
  searchResultSource.textContent = copy.searchSource;
  searchResultTitle.textContent = request.query;
  searchResultDescription.textContent = language === "ar"
    ? "هذه نتيجة توضيحية داخل المعاينة فقط. لم يتم فتح موقع خارجي أو تنفيذ بحث حقيقي."
    : "This is an illustrative result in the preview only. No external website was opened and no live search was performed.";
}

function saveWebsiteReturnState() {
  return {
    className: ember.className,
    style: {
      left: ember.style.left,
      top: ember.style.top,
      right: ember.style.right,
      bottom: ember.style.bottom,
      width: ember.style.width,
    },
  };
}

function setInlineStyle(element, property, value) {
  if (value) element.style.setProperty(property, value);
  else element.style.removeProperty(property);
}

async function moveWebsiteCharacter(target, { duration, jump = false } = {}) {
  const currentBounds = ember.getBoundingClientRect();
  const desktopBounds = desktop.getBoundingClientRect();
  const dx = currentBounds.left - desktopBounds.left - target.left
    + (currentBounds.width - target.width) / 2;
  const dy = currentBounds.top - desktopBounds.top - target.top
    + (currentBounds.height - target.height) / 2;
  const ratio = currentBounds.width / target.width;
  ember.style.left = `${target.left}px`;
  ember.style.top = `${target.top}px`;
  ember.style.right = "auto";
  ember.style.bottom = "auto";
  ember.style.width = `${target.width}px`;
  ember.classList.add("is-web-task");
  ember.classList.toggle("is-web-jumping", jump);
  ember.classList.toggle("is-web-traveling", !jump);
  const frames = [
    { transform: `translate(${dx}px, ${dy}px) scale(${ratio})` },
  ];
  if (jump) {
    frames.push({
      transform: `translate(${dx * 0.55}px, ${dy - 30}px) scale(1)`,
    });
  }
  frames.push({ transform: "translate(0, 0) scale(1)" });
  const animation = ember.animate(frames, {
    duration,
    easing: jump ? "cubic-bezier(0.2, 0.75, 0.25, 1)" : "cubic-bezier(0.16, 1, 0.3, 1)",
    fill: "both",
  });
  websiteCharacterAnimation = animation;
  await animation.finished.catch(() => {});
  if (websiteCharacterAnimation !== animation) return;
  animation.cancel();
  websiteCharacterAnimation = null;
  ember.classList.remove("is-web-traveling", "is-web-jumping");
}

async function runWebsitePreview(request) {
  if (websiteReturnState) {
    closeWebsitePreview();
    await delay(window.matchMedia("(prefers-reduced-motion: reduce)").matches ? 1 : 560);
  }
  const sequence = ++websiteTaskSequence;
  websiteTaskActive = true;
  websiteReturnState = saveWebsiteReturnState();
  chatStatus.textContent = conversationCopy[preferredConversationLanguage].webProgress;
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const desktopBounds = desktop.getBoundingClientRect();
  const dockBounds = chromeDockItem.getBoundingClientRect();
  const targetWidth = Math.min(126, Math.max(88, desktop.clientWidth * 0.105));
  const targetHeight = targetWidth * 250 / 380;
  const dockTop = dockBounds.top - desktopBounds.top - targetHeight + 8;
  const dockCenter = dockBounds.left - desktopBounds.left + dockBounds.width / 2;
  const approachLeft = Math.max(
    12,
    Math.min(
      dockCenter - targetWidth * 1.55,
      desktop.clientWidth - targetWidth - 12,
    ),
  );
  ember.classList.remove(
    "is-sleeping",
    "is-awake-hanging",
    "is-waking",
    "is-chat-seated",
    "is-chat-traveling",
    "is-chat-returning",
  );
  await moveWebsiteCharacter({
    left: approachLeft,
    top: Math.max(42, dockTop),
    width: targetWidth,
    height: targetHeight,
  }, { duration: reducedMotion ? 1 : 620 });
  if (sequence !== websiteTaskSequence) return;
  await moveWebsiteCharacter({
    left: dockCenter - targetWidth / 2,
    top: Math.max(42, dockTop),
    width: targetWidth,
    height: targetHeight,
  }, { duration: reducedMotion ? 1 : 360, jump: true });
  if (sequence !== websiteTaskSequence) return;
  chromeDockItem.classList.add("is-launching", "is-running");
  window.setTimeout(() => chromeDockItem.classList.remove("is-launching"), 260);
  revealBrowserPreview(request);
  await delay(reducedMotion ? 1 : 460);
  if (sequence !== websiteTaskSequence) return;
  browserPreview.classList.add("has-search-helper");
  const searchBounds = browserPreview
    .querySelector(".browser-search-box")
    .getBoundingClientRect();
  const desktopAfterOpen = desktop.getBoundingClientRect();
  const helperWidth = Math.min(144, Math.max(84, desktop.clientWidth * 0.12));
  const helperHeight = helperWidth * 250 / 380;
  const helperTop = searchBounds.top - desktopAfterOpen.top
    + (searchBounds.height - helperHeight) / 2;
  const helperLeft = Math.max(
    8,
    Math.min(
      searchBounds.right - desktopAfterOpen.left + 8,
      desktop.clientWidth - helperWidth - 8,
    ),
  );
  await moveWebsiteCharacter({
    left: helperLeft,
    top: Math.max(40, Math.min(helperTop, desktop.clientHeight - helperHeight - 66)),
    width: helperWidth,
    height: helperHeight,
  }, { duration: reducedMotion ? 1 : 620 });
  if (sequence !== websiteTaskSequence) return;
  ember.classList.add("is-web-typing");

  browserPreview.classList.add("is-typing");
  const characters = Array.from(request.query);
  for (const character of characters) {
    if (sequence !== websiteTaskSequence) return;
    browserQuery.value += character;
    await delay(reducedMotion ? 1 : 38);
  }
  if (sequence !== websiteTaskSequence) return;
  browserPreview.classList.remove("is-typing", "is-entering");
  searchResults.hidden = false;
  ember.classList.remove("is-web-typing");
  chatStatus.textContent = conversationCopy[preferredConversationLanguage].webTaskDone;
  chatReplyPending = false;
  websiteTaskActive = false;
  updateChatComposer();
}

function closeWebsitePreview() {
  websiteTaskSequence += 1;
  websiteTaskActive = false;
  browserPreview.hidden = true;
  browserPreview.classList.remove("is-entering", "is-typing", "has-search-helper");
  chromeDockItem.classList.remove("is-launching", "is-running");
  ember.classList.remove(
    "is-web-task",
    "is-web-typing",
    "is-web-traveling",
    "is-web-jumping",
  );

  const returnState = websiteReturnState;
  websiteReturnState = null;
  if (websiteCharacterAnimation) {
    websiteCharacterAnimation.cancel();
    websiteCharacterAnimation = null;
  }
  if (!returnState) {
    chatReplyPending = false;
    updateChatComposer();
    return;
  }

  const currentBounds = ember.getBoundingClientRect();
  const desktopBounds = desktop.getBoundingClientRect();
  Object.entries(returnState.style).forEach(([property, value]) => {
    setInlineStyle(ember, property, value);
  });
  ember.className = returnState.className;
  const destinationBounds = ember.getBoundingClientRect();

  ember.style.left = `${currentBounds.left - desktopBounds.left}px`;
  ember.style.top = `${currentBounds.top - desktopBounds.top}px`;
  ember.style.right = "auto";
  ember.style.bottom = "auto";
  ember.style.width = `${currentBounds.width}px`;
  const ratio = destinationBounds.width / Math.max(1, currentBounds.width);
  const dx = destinationBounds.left - currentBounds.left
    + (destinationBounds.width - currentBounds.width) / 2;
  const dy = destinationBounds.top - currentBounds.top
    + (destinationBounds.height - currentBounds.height) / 2;
  const returnAnimation = ember.animate(
    [
      { transform: "translate(0, 0) scale(1)" },
      { transform: `translate(${dx}px, ${dy}px) scale(${ratio})` },
    ],
    {
      duration: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? 1 : 500,
      easing: "cubic-bezier(0.4, 0, 1, 1)",
      fill: "both",
    },
  );
  returnAnimation.onfinish = () => {
    returnAnimation.cancel();
    Object.entries(returnState.style).forEach(([property, value]) => {
      setInlineStyle(ember, property, value);
    });
    chatReplyPending = false;
    updateChatComposer();
  };
}

function setConversationChrome(language) {
  const copy = conversationCopy[language];
  chatWindow.lang = language;
  chatWindow.dir = language === "ar" ? "rtl" : "ltr";
  chatWindow.setAttribute("aria-label", copy.windowLabel);
  chatTitle.textContent = copy.title;
  chatSubtitle.textContent = copy.subtitle;
  chatPreviewLabel.textContent = copy.preview;
  chatThread.setAttribute("aria-label", copy.thread);
  chatDate.textContent = copy.date;
  chatUserLabel.textContent = copy.you;
  chatEmberLabel.textContent = copy.replyLabel;
  chatOnline.setAttribute("aria-label", copy.online);
  chatOnlineLabel.textContent = copy.online;
  chatClose.setAttribute("aria-label", copy.close);
  chatClose.title = copy.close;
  chatInputLabel.textContent = copy.inputLabel;
  chatInput.placeholder = copy.placeholder;
  chatSend.setAttribute("aria-label", copy.send);
  chatSend.title = copy.send;
  chatComposerHint.textContent = copy.hint;
  chatStatus.textContent = "";
}

function setConversationLanguage(language, message, kind) {
  const copy = conversationCopy[language];
  setConversationChrome(language);
  chatUserMessage.textContent = kind === "voice" ? copy.voiceQuestion : message;
  chatUserMessage.dir = "auto";
  chatEmberReply.textContent = kind === "voice" ? copy.voiceReply : copy.sampleReply;
  chatEmberReply.dir = "auto";
}

function appendChatMessage(kind, text) {
  const copy = conversationCopy[preferredConversationLanguage];
  const article = document.createElement("article");
  article.className = `chat-message chat-message-${kind}`;
  const sender = document.createElement("p");
  sender.className = "chat-sender";
  sender.textContent = kind === "user" ? copy.you : copy.replyLabel;
  const bubbleText = document.createElement("p");
  bubbleText.className = "chat-bubble";
  bubbleText.dir = "auto";
  bubbleText.textContent = text;
  article.append(sender, bubbleText);
  chatThread.append(article);
  chatThread.scrollTop = chatThread.scrollHeight;
}

function updateChatComposer() {
  chatSend.disabled = chatReplyPending || !chatInput.value.trim();
  chatInput.style.height = "auto";
  const height = Math.min(chatInput.scrollHeight, 136);
  chatInput.style.height = `${height}px`;
  chatInput.style.overflowY = chatInput.scrollHeight > 136 ? "auto" : "hidden";
}

function submitChatMessage(event) {
  event.preventDefault();
  if (chatReplyPending) return;
  const message = chatInput.value.trim();
  if (!message) {
    chatStatus.textContent = conversationCopy[preferredConversationLanguage].empty;
    chatInput.focus();
    return;
  }

  preferredConversationLanguage = detectConversationLanguage(message);
  setConversationChrome(preferredConversationLanguage);
  appendChatMessage("user", message);
  const websiteRequest = parseWebsiteSearchRequest(message);
  chatInput.value = "";
  chatReplyPending = true;
  updateChatComposer();
  if (websiteRequest) {
    void runWebsitePreview(websiteRequest);
    return;
  }
  chatStatus.textContent =
    conversationCopy[preferredConversationLanguage].thinking;
  window.setTimeout(() => {
    appendChatMessage(
      "ember",
      conversationCopy[preferredConversationLanguage].demoReply,
    );
    chatReplyPending = false;
    chatStatus.textContent = "";
    updateChatComposer();
    chatInput.focus();
  }, 480);
}

function closeBubble() {
  cancelRecordingIntent();
  stopRecording(false);
  bubble.hidden = true;
  scheduleSleep();
}

function stopChatArrivalAtCurrentPosition() {
  if (!chatArrivalAnimation) return;
  const bounds = ember.getBoundingClientRect();
  const desktopBounds = desktop.getBoundingClientRect();
  chatArrivalAnimation.cancel();
  chatArrivalAnimation = null;
  ember.style.left = `${bounds.left - desktopBounds.left}px`;
  ember.style.top = `${bounds.top - desktopBounds.top}px`;
  ember.style.width = `${bounds.width}px`;
  ember.style.right = "auto";
  ember.style.bottom = "auto";
  ember.classList.remove("is-chat-traveling");
  ember.classList.add("is-chat-seated");
}

function moveEmberToChatWindow() {
  if (ember.classList.contains("is-chat-seated")) return;
  const bounds = ember.getBoundingClientRect();
  const desktopBounds = desktop.getBoundingClientRect();
  const chatBounds = chatWindow.getBoundingClientRect();
  chatReturnState = {
    left: ember.style.left,
    top: ember.style.top,
    right: ember.style.right,
    bottom: ember.style.bottom,
    width: ember.style.width,
    position: {
      left: bounds.left - desktopBounds.left,
      top: bounds.top - desktopBounds.top,
      width: bounds.width,
    },
    wasHanging: ember.classList.contains("is-awake-hanging"),
  };
  const start = {
    left: bounds.left - desktopBounds.left,
    top: bounds.top - desktopBounds.top,
    width: bounds.width,
  };
  const targetWidth = Math.min(112, start.width);
  const targetHeight = targetWidth * 250 / 380;
  const target = {
    left: Math.max(
      0,
      Math.min(
        chatBounds.left - desktopBounds.left
          + chatBounds.width * 0.57
          - targetWidth / 2,
        desktop.clientWidth - targetWidth,
      ),
    ),
    top: Math.max(34, chatBounds.top - desktopBounds.top - targetHeight * 0.72),
    width: targetWidth,
  };

  ember.style.left = `${start.left}px`;
  ember.style.top = `${start.top}px`;
  ember.style.width = `${start.width}px`;
  ember.style.right = "auto";
  ember.style.bottom = "auto";
  ember.classList.remove("is-awake-hanging", "is-waking", "is-sleeping");
  ember.classList.add("is-chat-traveling");
  const animation = ember.animate(
    [
      { left: `${start.left}px`, top: `${start.top}px`, width: `${start.width}px` },
      { left: `${target.left}px`, top: `${target.top}px`, width: `${target.width}px` },
    ],
    {
      duration: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? 1 : 1180,
      easing: "cubic-bezier(0.16, 1, 0.3, 1)",
    },
  );
  chatArrivalAnimation = animation;
  animation.onfinish = () => {
    if (chatArrivalAnimation !== animation) return;
    ember.style.left = `${target.left}px`;
    ember.style.top = `${target.top}px`;
    ember.style.width = `${target.width}px`;
    chatArrivalAnimation = null;
    animation.cancel();
    ember.classList.remove("is-chat-traveling");
    ember.classList.add("is-chat-seated");
    setGazeTarget(
      chatBounds.left + chatBounds.width * 0.68,
      chatBounds.top + chatBounds.height * 0.46,
    );
  };
}

function restoreEmberFromChat() {
  const returnState = chatReturnState;
  chatWindow.hidden = true;
  if (!returnState) {
    scheduleSleep();
    return;
  }
  if (chatReturnAnimation) {
    chatReturnAnimation.cancel();
    chatReturnAnimation = null;
  }

  const bounds = ember.getBoundingClientRect();
  const desktopBounds = desktop.getBoundingClientRect();
  const start = {
    left: bounds.left - desktopBounds.left,
    top: bounds.top - desktopBounds.top,
    width: bounds.width,
  };
  const target = returnState.position;
  ember.style.left = `${start.left}px`;
  ember.style.top = `${start.top}px`;
  ember.style.width = `${start.width}px`;
  ember.style.right = "auto";
  ember.style.bottom = "auto";
  ember.classList.remove("is-chat-seated");
  ember.classList.add("is-chat-returning");

  const animation = ember.animate(
    [
      { left: `${start.left}px`, top: `${start.top}px`, width: `${start.width}px` },
      { left: `${target.left}px`, top: `${target.top}px`, width: `${target.width}px` },
    ],
    {
      duration: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? 1 : 800,
      easing: "cubic-bezier(0.16, 1, 0.3, 1)",
    },
  );
  chatReturnAnimation = animation;
  animation.onfinish = () => {
    if (chatReturnAnimation !== animation) return;
    [
      ["left", returnState.left],
      ["top", returnState.top],
      ["right", returnState.right],
      ["bottom", returnState.bottom],
      ["width", returnState.width],
    ].forEach(([property, value]) => {
      if (value) ember.style.setProperty(property, value);
      else ember.style.removeProperty(property);
    });
    ember.classList.remove("is-chat-returning");
    if (returnState.wasHanging) ember.classList.add("is-awake-hanging");
    chatReturnAnimation = null;
    chatReturnState = null;
    animation.cancel();
    scheduleSleep();
  };
}

function openConversation(message, kind = "text") {
  const firstOpen = chatWindow.hidden;
  const language = kind === "voice"
    ? preferredConversationLanguage
    : detectConversationLanguage(message);
  preferredConversationLanguage = language;
  setConversationLanguage(language, message, kind);
  chatWindow.hidden = false;
  bubble.hidden = true;
  question.value = "";
  status.textContent = "";
  chatInput.value = "";
  chatReplyPending = false;
  chatStatus.textContent = "";
  updateChatComposer();
  chatInput.focus({ preventScroll: true });
  const websiteRequest = kind === "text"
    ? parseWebsiteSearchRequest(message)
    : null;
  if (websiteRequest) {
    chatReplyPending = true;
    updateChatComposer();
    void runWebsitePreview(websiteRequest);
  } else if (firstOpen) {
    moveEmberToChatWindow();
  }
  scheduleSleep();
}

function resetVoiceMeter() {
  voiceMeter.hidden = true;
  voiceMeter.classList.remove("is-active");
  voiceBars.forEach((bar) => {
    bar.style.transform = "scaleY(0.13)";
  });
}

function cancelRecordingIntent() {
  if (holdTimer) {
    clearTimeout(holdTimer);
    holdTimer = 0;
  }
  if (recordingState === "requesting") {
    recordingRequestId += 1;
    recordingState = "idle";
  }
  heldPointerId = null;
}

function stopRecording(showStatus = true) {
  if (audioFrame) {
    cancelAnimationFrame(audioFrame);
    audioFrame = 0;
  }
  if (recordingStream) {
    recordingStream.getTracks().forEach((track) => track.stop());
    recordingStream = null;
  }
  if (audioContext) {
    void audioContext.close();
    audioContext = null;
  }
  analyser = null;
  recordingState = "idle";
  resetVoiceMeter();
  question.hidden = false;
  if (showStatus) {
    status.textContent = "Preview only — your voice was not sent.";
  }
}

async function beginRecording(pointerId, requestId) {
  if (!navigator.mediaDevices?.getUserMedia) {
    recordingState = "idle";
    status.textContent = "Microphone access is unavailable in this browser.";
    return;
  }
  recordingState = "requesting";
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    if (
      requestId !== recordingRequestId
      || heldPointerId !== pointerId
      || bubble.hidden
    ) {
      stream.getTracks().forEach((track) => track.stop());
      recordingState = "idle";
      return;
    }
    recordingStream = stream;
    audioContext = new AudioContext();
    const source = audioContext.createMediaStreamSource(stream);
    analyser = audioContext.createAnalyser();
    analyser.fftSize = 128;
    source.connect(analyser);
    recordingState = "recording";
    question.hidden = true;
    voiceMeter.hidden = false;
    voiceMeter.classList.add("is-active");
    status.textContent = "";
    positionBubble();
    animateVoiceMeter();
  } catch (error) {
    stopRecording(false);
    status.textContent = error?.name === "NotAllowedError"
      ? "Microphone permission was denied."
      : "Could not access the microphone.";
  }
}

function animateVoiceMeter() {
  if (!analyser || recordingState !== "recording") return;
  const samples = new Uint8Array(analyser.frequencyBinCount);
  analyser.getByteFrequencyData(samples);
  voiceBars.forEach((bar, index) => {
    const sampleIndex = Math.floor(index * samples.length / voiceBars.length);
    const amplitude = samples[sampleIndex] / 255;
    const scale = 0.13 + amplitude * 0.87;
    bar.style.transform = `scaleY(${scale})`;
  });
  audioFrame = requestAnimationFrame(animateVoiceMeter);
}

ember.addEventListener("contextmenu", (event) => {
  event.preventDefault();
  wakeEmber();
  scheduleSleep();
  openBubble();
});

ember.addEventListener("keydown", (event) => {
  if (event.key === "Enter" || event.key === " ") {
    event.preventDefault();
    wakeEmber();
    scheduleSleep();
    openBubble();
  }
});

document.addEventListener("pointermove", updateGazeTarget, { passive: true });

form.addEventListener("submit", (event) => {
  event.preventDefault();
  if (recordingState === "recording") return;
  const message = question.value.trim();
  if (!message) {
    status.textContent = "Write a question first.";
    question.focus();
    return;
  }
  openConversation(message);
});

chatForm.addEventListener("submit", submitChatMessage);
chatInput.addEventListener("input", updateChatComposer);
chatInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey && !event.isComposing) {
    event.preventDefault();
    chatForm.requestSubmit();
  }
});
function closeConversationPreview() {
  if (!browserPreview.hidden) {
    closeWebsitePreview();
    window.setTimeout(
      () => {
        restoreEmberFromChat();
        ember.focus();
      },
      window.matchMedia("(prefers-reduced-motion: reduce)").matches ? 0 : 520,
    );
    return;
  }
  restoreEmberFromChat();
  ember.focus();
}

chatClose.addEventListener("click", closeConversationPreview);
browserClose.addEventListener("click", closeWebsitePreview);

document.addEventListener("pointerdown", (event) => {
  if (
    event.button !== 0
    || !ember.contains(event.target)
    || dragPointerId !== null
  ) return;
  wakeEmber();
  scheduleSleep();
  stopChatArrivalAtCurrentPosition();
  event.preventDefault();
  const bounds = ember.getBoundingClientRect();
  const desktopBounds = desktop.getBoundingClientRect();
  dragPointerId = event.pointerId;
  dragReleased = false;
  dragOrigin = {
    offsetX: event.clientX - bounds.left,
    offsetY: event.clientY - bounds.top,
    desktopLeft: desktopBounds.left,
    desktopTop: desktopBounds.top,
    width: bounds.width,
    height: bounds.height,
  };
  dragCurrent = {
    left: bounds.left - desktopBounds.left,
    top: bounds.top - desktopBounds.top,
  };
  dragTarget = { ...dragCurrent };
  dragTimer = window.setTimeout(() => {
    dragTimer = 0;
    if (dragPointerId !== event.pointerId || !dragOrigin) return;
    if (ember.classList.contains("is-chat-seated")) {
      const scale = 266 / dragOrigin.width;
      dragOrigin.offsetX *= scale;
      dragOrigin.offsetY *= scale;
      dragOrigin.width = 266;
      dragOrigin.height *= scale;
      ember.style.width = `${dragOrigin.width}px`;
      ember.classList.remove("is-chat-seated");
    }
    ember.style.left = `${dragCurrent.left}px`;
    ember.style.top = `${dragCurrent.top}px`;
    ember.style.right = "auto";
    ember.style.bottom = "auto";
    ember.classList.remove("is-awake-hanging");
    ember.setAttribute("aria-label", "Ember, your desktop companion. Right-click to ask a question.");
    ember.classList.add("is-dragging");
    if (ember.setPointerCapture) ember.setPointerCapture(event.pointerId);
    dragLastTime = 0;
    dragFrame = requestAnimationFrame(animateCharacterDrag);
  }, 320);
});

function animateCharacterDrag(time) {
  if (!dragCurrent || !dragTarget) {
    dragFrame = 0;
    return;
  }
  const delta = dragLastTime ? Math.min(time - dragLastTime, 48) : 16;
  dragLastTime = time;
  const amount = 1 - Math.exp(-delta / 52);
  dragCurrent.left += (dragTarget.left - dragCurrent.left) * amount;
  dragCurrent.top += (dragTarget.top - dragCurrent.top) * amount;
  ember.style.left = `${dragCurrent.left}px`;
  ember.style.top = `${dragCurrent.top}px`;
  if (lastPointerPosition) {
    setGazeTarget(lastPointerPosition.x, lastPointerPosition.y);
  }
  const movementX = dragTarget.left - dragCurrent.left;
  const tilt = Math.max(-4, Math.min(4, movementX * 0.08));
  ember.style.setProperty("--drag-tilt", `${tilt}deg`);
  if (!bubble.hidden) positionBubble();

  const remaining = Math.hypot(
    dragTarget.left - dragCurrent.left,
    dragTarget.top - dragCurrent.top,
  );
  if (dragReleased && remaining < 0.35) {
    ember.style.left = `${dragTarget.left}px`;
    ember.style.top = `${dragTarget.top}px`;
    ember.style.setProperty("--drag-tilt", "0deg");
    ember.classList.remove("is-dragging");
    ember.classList.add("is-settling");
    dragCurrent = null;
    dragTarget = null;
    dragFrame = 0;
    dragLastTime = 0;
    return;
  }
  dragFrame = requestAnimationFrame(animateCharacterDrag);
}

document.addEventListener("pointermove", (event) => {
  if (
    event.pointerId !== dragPointerId
    || !dragOrigin
    || dragTimer
    || !ember.classList.contains("is-dragging")
  ) return;
  const maxLeft = Math.max(0, desktop.clientWidth - dragOrigin.width);
  const maxTop = Math.max(0, desktop.clientHeight - dragOrigin.height);
  const left = Math.max(
    0,
    Math.min(event.clientX - dragOrigin.desktopLeft - dragOrigin.offsetX, maxLeft),
  );
  const top = Math.max(
    0,
    Math.min(event.clientY - dragOrigin.desktopTop - dragOrigin.offsetY, maxTop),
  );
  dragTarget = { left, top };
});

function finishCharacterDrag(event) {
  if (event.pointerId !== dragPointerId) return;
  const dragWasPending = Boolean(dragTimer);
  if (dragWasPending) {
    clearTimeout(dragTimer);
    dragTimer = 0;
  }
  if (ember.hasPointerCapture?.(event.pointerId)) {
    ember.releasePointerCapture(event.pointerId);
  }
  if (dragWasPending) {
    ember.classList.remove("is-dragging");
    dragCurrent = null;
    dragTarget = null;
    dragReleased = false;
    if (!chatWindow.hidden && chatReturnState) {
      restoreEmberFromChat();
    }
  } else if (ember.classList.contains("is-dragging")) {
    dragReleased = true;
    if (!dragFrame) dragFrame = requestAnimationFrame(animateCharacterDrag);
  }
  dragPointerId = null;
  dragOrigin = null;
  scheduleSleep();
}

document.addEventListener("pointerup", finishCharacterDrag);
document.addEventListener("pointercancel", finishCharacterDrag);
ember.addEventListener("animationend", (event) => {
  if (event.animationName === "ember-land") {
    ember.classList.remove("is-settling");
    ember.style.removeProperty("--drag-tilt");
  }
});

document.addEventListener("pointerdown", (event) => {
  if (
    event.button !== 2
    || bubble.hidden
    || !ember.contains(event.target)
    || recordingState !== "idle"
  ) return;
  heldPointerId = event.pointerId;
  const requestId = ++recordingRequestId;
  holdTimer = window.setTimeout(() => {
    holdTimer = 0;
    if (heldPointerId === event.pointerId) {
      void beginRecording(event.pointerId, requestId);
    }
  }, 350);
});

function finishPointerHold(event) {
  if (event.pointerId !== heldPointerId) return;
  if (holdTimer) {
    clearTimeout(holdTimer);
    holdTimer = 0;
  }
  heldPointerId = null;
  if (recordingState === "recording") {
    stopRecording();
    openConversation("", "voice");
  } else if (recordingState === "requesting") {
    recordingRequestId += 1;
    recordingState = "idle";
  }
}

document.addEventListener("pointerup", finishPointerHold);
document.addEventListener("pointercancel", finishPointerHold);

document.addEventListener("pointerdown", (event) => {
  if (
    !bubble.hidden
    && recordingState === "idle"
    && !bubble.contains(event.target)
    && !ember.contains(event.target)
  ) {
    closeBubble();
  }
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && !chatWindow.hidden) {
    if (!browserPreview.hidden) {
      closeWebsitePreview();
      return;
    }
    closeConversationPreview();
    return;
  }
  if (event.key === "Escape" && !bubble.hidden) {
    stopRecording(false);
    closeBubble();
    ember.focus();
  }
});

window.addEventListener("resize", () => {
  if (ember.classList.contains("is-sleeping")) enterSleep();
  if (!bubble.hidden) positionBubble();
});

ember.addEventListener("animationend", finishWakeAnimation);
document.addEventListener("keydown", scheduleSleep);
document.addEventListener("pointerdown", handlePointerProximity, { passive: true });
