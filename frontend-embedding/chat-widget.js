(async function () {

  /*************************
   * CONFIG
   *************************/

  const script = document.currentScript;
  if (!script) {
    throw new Error("chat-widget must be loaded via a <script> tag");
  }


  const scriptUrl = new URL(script.src);
  const FASTAPI_BASE_URL = scriptUrl.origin + scriptUrl.pathname.replace(/\/chat-widget\/chat-widget\.js$/, "");


  const CHAT_API = `${FASTAPI_BASE_URL}/agent/chat/v2/with_history`;
  const HISTORY_API = `${FASTAPI_BASE_URL}/agent/chat/history`;

  const SESSION_KEY = "bdc_chat_session_id";
  const REDIRECT_PAGE_URL = `https://blue-academy-rust.vercel.app/courses`


  let isChatWidgetOpen = false
  let isProcessing = false;


  const pageTitle = document.title

  /*************************
   * SESSION
   *************************/
  function getSessionId() {
    let id = sessionStorage.getItem(SESSION_KEY)
    if (!id) {
      id = crypto.randomUUID();
      sessionStorage.setItem(SESSION_KEY, id);
    }
    return id;
  }

  const sessionId = getSessionId();

  /*************************
   * Page Data Preload)
   *************************/

  function getPreloadedPageData() {
    const payload = window.__BDC_PAGE_PAYLOAD__;
    if (!payload || payload.status !== "ready") return null;

    return {
      type: payload.type,
      payload: payload.data
    };
  }


  let pageData = getPreloadedPageData();

  if (!pageData) {
    window.addEventListener("BDC_PAGE_DATA_READY", () => {
      pageData = getPreloadedPageData();
    });
  }

  /*************************
   * CONTEXT
   *************************/
  function getPageContext() {
    return {
      title: document.title || "Untitled Page",
      url: window.location.href,
    };
  }

  let userContext = {};

  /*************************
   * UI STYLES (REDESIGNED)
   *************************/
  const style = document.createElement("style");
  style.innerHTML = `
    /* --- FONTS & RESET --- */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');

    #bdc-chat-widget * {
      box-sizing: border-box;
    }

    /* --- LAUNCHER --- */
    #bdc-chat-launcher {
      position: fixed;
      bottom: 18px;
      right: 24px;
      width: 46px;
      height: 46px;
      border-radius: 50%;
      background: #155dfc;
      color: white;
      font-size: 28px;
      border: none;
      cursor: pointer;
      box-shadow: 0 8px 24px rgba(37, 99, 235, 0.45);
      z-index: 99999;
      transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 0.3s ease;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    #bdc-chat-launcher:hover {
      transform: scale(1.1);
      box-shadow: 0 12px 28px rgba(37, 99, 235, 0.55);
      background: #1447e6
    }

    /* --- WIDGET CONTAINER --- */
    #bdc-chat-widget {
      position: fixed;
      bottom: 100px;
      right: 24px;
      width: 380px;
      height: 550px;
      max-height: 80vh;
      background: #ffffff;
      border-radius: 20px;
      box-shadow: 0 20px 60px rgba(0,0,0,0.15), 0 0 0 1px rgba(0,0,0,0.05);
      display: none; /* Toggled via JS */
      flex-direction: column;
      font-family: 'Inter', system-ui, -apple-system, sans-serif;
      z-index: 99999;
      overflow: hidden;
      animation: bdc-slide-up 0.4s cubic-bezier(0.16, 1, 0.3, 1);
    }

    @keyframes bdc-slide-up {
      from { opacity: 0; transform: translateY(20px) scale(0.95); }
      to { opacity: 1; transform: translateY(0) scale(1); }
    }

    /* --- HEADER --- */
    #bdc-chat-header {
      background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
      color: white;
      padding: 18px 20px;
      font-weight: 600;
      font-size: 16px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 1px solid rgba(255,255,255,0.1);
      box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }

    #bdc-chat-close {
      opacity: 0.8;
      transition: opacity 0.2s;
      font-size: 18px;
    }
    #bdc-chat-close:hover { opacity: 1; }

    /* --- MESSAGES AREA --- */
    #bdc-chat-messages {
      flex: 1;
      padding: 20px;
      overflow-y: auto;
      background: #f8fafc;
      scrollbar-width: thin;
      scrollbar-color: #cbd5e1 transparent;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }

    #bdc-chat-messages::-webkit-scrollbar {
      width: 6px;
    }
    #bdc-chat-messages::-webkit-scrollbar-thumb {
      background-color: #cbd5e1;
      border-radius: 10px;
    }

    /* --- BUBBLES --- */
    .bdc-msg {
      max-width: 85%;
      padding: 12px 16px;
      border-radius: 18px;
      font-size: 14px;
      line-height: 1.5;
      position: relative;
      word-wrap: break-word;
      animation: bdc-msg-pop 0.3s ease-out;
    }

    @keyframes bdc-msg-pop {
      from { opacity: 0; transform: translateY(10px); }
      to { opacity: 1; transform: translateY(0); }
    }

    .bdc-user {
      background: #2563eb;
      color: white;
      align-self: flex-end; /* Modern Flex alignment */
      border-bottom-right-radius: 4px;
      box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2);
    }

    .bdc-bot {
      background: #ffffff;
      color: #1e293b;
      align-self: flex-start; /* Modern Flex alignment */
      border-bottom-left-radius: 4px;
      border: 1px solid #e2e8f0;
      box-shadow: 0 2px 5px rgba(0,0,0,0.03);
    }

    /* --- ACTIONS --- */
    .bdc-actions {
      display: flex;
      gap: 8px;
      margin-top: 10px;
      flex-wrap: wrap;
    }

    .bdc-action-btn {
      background: #ffffff;
      border: 1px solid #bfdbfe;
      color: #2563eb;
      font-size: 12px;
      font-weight: 500;
      padding: 8px 14px;
      border-radius: 999px;
      cursor: pointer;
      transition: all 0.2s ease;
    }

    .bdc-action-btn:hover {
      background: #eff6ff;
      border-color: #2563eb;
      transform: translateY(-1px);
      box-shadow: 0 2px 8px rgba(37, 99, 235, 0.15);
    }

    /* --- TYPING INDICATOR --- */
    #bdc-typing {
      background: transparent;
      border: none;
      box-shadow: none;
      padding: 0;
      margin-left: 10px;
      display: none;
      align-items: center;
      gap: 4px;
      align-self: flex-start;
    }

    #bdc-typing span {
      width: 8px;
      height: 8px;
      background: #94a3b8;
      border-radius: 50%;
      display: inline-block;
      animation: typing-bounce 1.4s infinite ease-in-out both;
    }

    #bdc-typing span:nth-child(1) { animation-delay: -0.32s; }
    #bdc-typing span:nth-child(2) { animation-delay: -0.16s; }

    @keyframes typing-bounce {
      0%, 80%, 100% { transform: scale(0); }
      40% { transform: scale(1); }
    }

    /* --- INPUT AREA --- */
    #bdc-chat-input {
      display: flex;
      border-top: 1px solid #e2e8f0;
      padding: 12px;
      background: #ffffff;
      align-items: center;
      gap: 8px;
    }

    #bdc-chat-input input {
      flex: 1;
      border: 1px solid #e2e8f0;
      border-radius: 24px;
      padding: 12px 16px;
      font-size: 14px;
      outline: none;
      background: #f8fafc;
      transition: border-color 0.2s;
    }

    #bdc-chat-input input:focus {
      border-color: #2563eb;
      background: #fff;
    }

    #bdc-chat-input button {
      background: #2563eb;
      color: white;
      border: none;
      padding: 10px 18px;
      border-radius: 24px;
      cursor: pointer;
      font-weight: 600;
      font-size: 13px;
      transition: background 0.2s;
    }

    #bdc-chat-input button:hover {
      background: #1d4ed8;
    }

    #bdc-chat-input button:disabled {
      background: #94a3b8;
      cursor: not-allowed;
    }
  `;
  document.head.appendChild(style);

  /*************************
   * UI ELEMENTS
   *************************/
  const launcher = document.createElement("button");
  launcher.id = "bdc-chat-launcher";
  // Changed icon to a cleaner SVG look or simple emoji
  launcher.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>`;


  const widget = document.createElement("div");
  widget.id = "bdc-chat-widget";
  widget.innerHTML = `
    <div id="bdc-chat-header">
      <div style="display:flex; align-items:center; gap:8px;">
        <span>Blue Academy</span>
      </div>
      <span id="bdc-chat-close">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
      </span>
    </div>
    <div id="bdc-chat-messages"></div>
    <div id="bdc-chat-input">
      <input type="text" placeholder="Type your message..." />
      <button>Send</button>
    </div>
  `;

  document.body.appendChild(launcher);
  document.body.appendChild(widget);

  const messagesEl = widget.querySelector("#bdc-chat-messages");
  const inputEl = widget.querySelector("input");
  const sendBtn = widget.querySelector("button");


  /*************************
   * UI HELPERS
   *************************/

  function addBotMessageWithActions(text, actions = [], courses = []) {
    const wrapper = document.createElement("div");
    wrapper.className = "bdc-msg bdc-bot";

    // Speech
    const speechDiv = document.createElement("div");
    speechDiv.innerText = text;
    wrapper.appendChild(speechDiv);

    // Actions
    if (actions.length > 0) {
      const actionsDiv = document.createElement("div");
      actionsDiv.className = "bdc-actions";

      actions.forEach(act => {
        const btn = document.createElement("button");
        btn.className = "bdc-action-btn";
        btn.innerText = act.label;

        // No-op for now
        btn.onclick = (e) => {
          e.stopImmediatePropagation()
          e.stopPropagation();
          handleAction(act, e);
        };

        actionsDiv.appendChild(btn);
      });

      wrapper.appendChild(actionsDiv);
    }

    messagesEl.appendChild(wrapper);
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }


  function addMessage(text, type) {
    const div = document.createElement("div");
    div.className = `bdc-msg ${type}`;
    div.innerText = text;
    messagesEl.appendChild(div);
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  /*************************
   * FETCH HISTORY
   *************************/
  async function loadHistory() {
    try {
      const res = await fetch(`${HISTORY_API}/${sessionId}`, {
        headers: {
          "ngrok-skip-browser-warning": "true"
        }
      }
      );

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }

      const contentType = res.headers.get("content-type");

      if (!contentType || !contentType.includes("application/json")) {
        const text = await res.text();
        throw new Error("History API did not return JSON");
      }

      const data = await res.json();

      if (!Array.isArray(data.history)) return;

      data.history.forEach(item => {
        if (item.role === "user") {
          addMessage(item.content, "bdc-user");
        } else {
          addBotMessageWithActions(
            normalizeMessage(item.content),
            item.content?.actions || []
          );
        }
      });
    } catch (err) {
      console.error("History load failed:", err);
    }
  }


  function normalizeMessage(content) {
    if (typeof content === "string") return content;
    if (content?.speech) return content.speech;
    if (content?.text) return content.text;
    return "";
  }

  /*************************
   * SEND MESSAGE
   *************************/

  const typingEl = document.createElement("div");
  typingEl.id = "bdc-typing";
  typingEl.className = "bdc-msg bdc-bot"; // Ensures it keeps bot styling inheritance if needed, though overridden by ID
  typingEl.innerHTML = `<span></span><span></span><span></span>`;

  function showTyping() {
    if (!typingEl.parentNode) {
      messagesEl.appendChild(typingEl);
    }
    typingEl.style.display = "flex";
    typingEl.scrollIntoView({ block: "end" });
  }

  function hideTyping() {
    if (typingEl.parentNode) {
      typingEl.remove();
    }
  }


  /*************************
   * Button Handler
  *************************/
  function disableInput() {
    sendBtn.disabled = true;
    inputEl.disabled = true;
  }

  function enableInput() {
    sendBtn.disabled = false;
    inputEl.disabled = false;
    inputEl.focus();
  }


  /*************************
   * Handle Actions
  *************************/

  async function handleAction(act, e) {
    e.stopImmediatePropagation();
    let actionType = act?.type;
    let course = act?.course || {};
    let courseSlug = course?.slug || "";
    let courseId = course?.id || "";
    let courseTitle = course?.title || "";
    switch (actionType) {
      case "details":
        window.location.href = `${REDIRECT_PAGE_URL}/${courseSlug}`
        break;

      case "interest":
        COURSE_INTEREST_API = `${FASTAPI_BASE_URL}/internal/mark_user_interested/${courseSlug}`;
        await fetch(COURSE_INTEREST_API, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          }
        });
        inputEl.value = `I am interested in "${courseTitle}"`
        userContext.action = `Showing interest in particular course`
        userContext.course = {
          id: courseId,
          slug: courseSlug,
          title: courseTitle
        }
        await sendMessage();
        break;
    }
  }



  async function sendMessage() {
    if (isProcessing) return;

    const text = inputEl.value.trim();
    if (!text) return;

    isProcessing = true;
    inputEl.value = "";
    disableInput();
    addMessage(text, "bdc-user");
    showTyping();

    const start = Date.now();

    let payload = {
      message: text,
      session_id: sessionId,
      context: {
        page_context: getPageContext(),
        user_context: userContext
      }
    }

    try {
      const res = await fetch(CHAT_API, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "ngrok-skip-browser-warning": "true"
        },
        body: JSON.stringify(payload)
      });

      if (res.status === 409) {
        hideTyping();
        addMessage("Please wait, I’m still responding.", "bdc-bot");
        return;
      }

      const data = await res.json();

      // Optional UX delay
      const elapsed = Date.now() - start;
      if (elapsed < 600) {
        await new Promise(r => setTimeout(r, 600 - elapsed));
      }

      // 3. Remove typing
      hideTyping();

      // 4. Bot response
      const replyText =
        data.reply?.speech ||
        data.reply?.text ||
        "Sorry, I couldn't understand that.";

      addBotMessageWithActions(
        replyText,
        data.reply?.actions || [],
        data.reply?.courses || []
      );

    } catch (err) {
      hideTyping();
      addMessage("Something went wrong.", "bdc-bot");

    } finally {
      // 🔓 ALWAYS unlock
      isProcessing = false;
      enableInput();
    }
  }


  /*************************
   * EVENTS
   *************************/

  launcher.onclick = async () => {
    if (!isChatWidgetOpen) {
      widget.style.display = "flex";
      launcher.style.display = "none"; // Hide launcher when open for cleaner look, or keep "block" if you prefer
      isChatWidgetOpen = true;

      // Clear messages only
      messagesEl.innerHTML = "";

      await loadHistory();

      widget.querySelector("#bdc-chat-close").onclick = (e) => {
        e.stopPropagation();
        widget.style.display = "none";
        launcher.style.display = "flex"; // Bring back launcher
        isChatWidgetOpen = false;
      };
    }
    else {
      widget.style.display = "none";
      launcher.style.display = "flex";
      isChatWidgetOpen = false;
    }

  };


  sendBtn.onclick = sendMessage;

  inputEl.addEventListener("keydown", e => {
    if (e.key === "Enter") {
      e.preventDefault();
      if (!isProcessing) sendMessage();
    };
  });

})();