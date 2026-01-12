(async function () {

  /*************************
   * CONFIG
   *************************/

  console.log(document.currentScript);
  const script = document.currentScript;
  if (!script) {
    throw new Error("chat-widget must be loaded via a <script> tag");
  }

  console.log("Script Hit");

  const scriptUrl = new URL(script.src);

  console.log(scriptUrl)


  const FASTAPI_BASE_URL = scriptUrl.origin + scriptUrl.pathname.replace(/\/chat-widget\/chat-widget\.js$/, "");
    console.log(scriptUrl.origin)
    console.log(scriptUrl.pathname)


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
      console.log("Chat page data hydrated:", pageData);
    });
  }

  /*************************
   * CONTEXT (FROM SCRIPT TAG)
   *************************/


  // function renderMarkdown(text) {
  //   const rawHtml = marked.parse(text || "");
  //   return DOMPurify.sanitize(rawHtml);
  // }

  // const pageContext = {
  //   title: script.getAttribute("data-page-title"),
  //   slug: script.getAttribute("data-page-slug")
  // };

  function getPageContext() {
    return {
      title: document.title || "Untitled Page",
      url: window.location.href,
    };
  }

  // console.log(pageContext)

  let userContext = {};

  /*************************
   * UI STYLES
   *************************/
  const style = document.createElement("style");
  style.innerHTML = `
    #bdc-chat-launcher {
      position: fixed;
      bottom: 24px;
      right: 24px;
      width: 56px;
      height: 56px;
      border-radius: 50%;
      background: #2563eb;
      color: white;
      font-size: 24px;
      border: none;
      cursor: pointer;
      box-shadow: 0 10px 25px rgba(0,0,0,0.2);
      z-index: 9999;
    }

    #bdc-chat-widget {
      position: fixed;
      bottom: 90px;
      right: 24px;
      width: 360px;
      height: 480px;
      background: #fff;
      border-radius: 12px;
      box-shadow: 0 20px 40px rgba(0,0,0,0.2);
      display: none;
      flex-direction: column;
      font-family: system-ui, -apple-system, sans-serif;
      z-index: 9999;
      overflow: hidden;
    }

    #bdc-chat-header {
      background: #2563eb;
      color: white;
      padding: 14px;
      font-weight: 600;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    #bdc-chat-messages {
      flex: 1;
      padding: 12px;
      overflow-y: auto;
      background: #f9fafb;
    }

    .bdc-msg {
      margin-bottom: 10px;
      max-width: 80%;
      padding: 10px 12px;
      border-radius: 12px;
      font-size: 14px;
      line-height: 1.4;
    }

    .bdc-user {
      background: #2563eb;
      color: white;
      margin-left: auto;
      border-bottom-right-radius: 4px;
    }

    .bdc-bot {
      background: #e5e7eb;
      color: #111;
      margin-right: auto;
      border-bottom-left-radius: 4px;
    }

    .bdc-actions {
  display: flex;
  gap: 8px;
  margin-top: 8px;
  flex-wrap: wrap;
}

.bdc-action-btn {
  background: #f3f4f6;
  border: 1px solid #d1d5db;
  color: #111827;
  font-size: 12px;
  padding: 6px 10px;
  border-radius: 999px;
  cursor: pointer;
}

.bdc-action-btn:hover {
  background: #e5e7eb;
}


#bdc-typing {
  background: rgba(255, 0, 0, 0.2)
  display: none;
  align-items: center;
  gap: 6px;
  padding: 10px 12px;
}

#bdc-typing span {
  width: 6px;
  height: 6px;
  background: #6b7280;
  border-radius: 50%;
  display: inline-block;
  animation: typing-bounce 1.2s infinite ease-in-out;
}

#bdc-typing span:nth-child(1) { animation-delay: 0s; }
#bdc-typing span:nth-child(2) { animation-delay: .15s; }
#bdc-typing span:nth-child(3) { animation-delay: .3s; }

@keyframes typing-bounce {
  0%, 80%, 100% { transform: scale(0); opacity: .3; }
  40% { transform: scale(1); opacity: 1; }
}


    #bdc-chat-input {
      display: flex;
      border-top: 1px solid #e5e7eb;
    }

    #bdc-chat-input input {
      flex: 1;
      border: none;
      padding: 12px;
      font-size: 14px;
      outline: none;
    }

    #bdc-chat-input button {
      background: #2563eb;
      color: white;
      border: none;
      padding: 0 16px;
      cursor: pointer;
    }
  `;
  document.head.appendChild(style);

  /*************************
   * UI ELEMENTS
   *************************/
  const launcher = document.createElement("button");
  launcher.id = "bdc-chat-launcher";
  launcher.innerText = "💬";



  const widget = document.createElement("div");
  widget.id = "bdc-chat-widget";
  widget.innerHTML = `
    <div id="bdc-chat-header">
      <span>Blue Data Assistant</span>
      <span id="bdc-chat-close" style="cursor:pointer;">✕</span>
    </div>
    <div id="bdc-chat-messages"></div>
    <div id="bdc-chat-input">
      <input type="text" placeholder="Ask something..." />
      <button>Send</button>
    </div>
  `;

  document.body.appendChild(launcher);
  document.body.appendChild(widget);

  const messagesEl = widget.querySelector("#bdc-chat-messages");
  const inputEl = widget.querySelector("input");
  const sendBtn = widget.querySelector("button");

  // const style = document.createElement("style");
  //   style.innerHTML = `
  //   /* chat widget base styles */
  // `;
  //   document.head.appendChild(style);
  /*************************
   * UI HELPERS
   *************************/

  function addBotMessageWithActions(text, actions = [], courses = []) {
    const wrapper = document.createElement("div");
    wrapper.className = "bdc-msg bdc-bot";

    // Speech
    const speechDiv = document.createElement("div");
    speechDiv.innerText = text;
    // speechDiv.innerHTML = renderMarkdown(text);
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
        console.error("Non-JSON response:", text);
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
  // typingEl.style.display = "none";
  typingEl.className = "bdc-msg bdc-bot";
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
    sendBtn.style.opacity = "0.6";
    sendBtn.style.cursor = "not-allowed";
    sendBtn.blur();
    inputEl.disabled = true;
  }

  function enableInput() {
    sendBtn.disabled = false;
    sendBtn.style.opacity = "1";
    sendBtn.style.cursor = "pointer";
    inputEl.disabled = false;
    inputEl.focus();
  }


  /*************************
   * Handle Actions
  *************************/

  async function handleAction(act, e) {
    e.stopImmediatePropagation();
    console.log(`Actions Clicked: ${JSON.stringify(act)}`);
    let actionType = act?.type;
    let course = act?.course || {};
    let courseSlug = course?.slug || "";
    let courseId = course?.id || "";
    let courseTitle = course?.title || "";
    console.log(`Action Type: ${actionType}, Course Slug: ${courseSlug}, Course ID: ${courseId}`)

    switch (actionType) {
      case "details":
        console.log("Visit details page of given course");
        console.log(`Redirecsted to course with slug : ${courseSlug}`)
        window.location.href = `${REDIRECT_PAGE_URL}/${courseSlug}`
        break;

      case "interest":
        console.log("Increment Interest count for particular course");
        COURSE_INTEREST_API = `${API_BASE}/course/${courseSlug}/mark_interest`;
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


        // console.log(`User interested in course: ${courseTitle} (ID: ${courseId}, Slug: ${courseSlug})`);
        // let user_evt = {
        //   action: "showing interest in course",
        //   course: {
        //     id: courseId,
        //     slug: courseSlug,
        //     title: courseTitle
        //   }
        // };

        // console.log("Event Payload:", user_evt);
        // await sendAgentEvent(user_evt);


        break;

      case "alternative":
        console.log("Show alternative of particular course");
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




  // async function sendAgentEvent(evt_payload) {
  //   console.log("Sending agent event:", evt_payload);
  //   if (isProcessing) return;

  //   isProcessing = true;
  //   disableInput();
  //   showTyping();


  //   try {
  //     const res = await fetch(CHAT_API, {
  //       method: "POST",
  //       headers: {
  //         "Content-Type": "application/json",
  //         "ngrok-skip-browser-warning": "true"
  //       },
  //       body: JSON.stringify({
  //         session_id: sessionId,
  //         message: "", // no user text
  //         context: {
  //           page_context: getPageContext(),
  //           user_context: evt_payload
  //         }
  //       })
  //     });

  //     const data = await res.json();
  //     hideTyping();

  //     addBotMessageWithActions(
  //       data.reply?.speech || "",
  //       data.reply?.actions || []
  //     );

  //   } finally {
  //     isProcessing = false;
  //     enableInput();
  //     userContext = {}
  //   }
  // }


  /*************************
   * EVENTS
   *************************/

  launcher.onclick = async () => {
    if (!isChatWidgetOpen) {
      widget.style.display = "flex";
      launcher.style.display = "block";
      isChatWidgetOpen = true;

      // Clear messages only
      messagesEl.innerHTML = "";

      await loadHistory();

      widget.querySelector("#bdc-chat-close").onclick = (e) => {
        e.stopPropagation();
        widget.style.display = "none";
        isChatWidgetOpen = false;
      };
    }
    else {
      widget.style.display = "none";
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