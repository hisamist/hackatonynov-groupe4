/*
 * TechCorp AI — embeddable chatbot loader.
 *
 * Drop this into any page:
 *   <script src="http://<host>:5050/embed.js"></script>
 *
 * It injects a floating chat bubble (bottom-right). Clicking it opens a panel
 * containing an <iframe> that loads the /widget chat UI from this script's own
 * origin, so it works cross-origin without any extra configuration.
 *
 * Optional data-attributes on the <script> tag:
 *   data-title="..."     panel header title      (default: "Assistant Financier")
 *   data-position="left" bubble corner           (default: right)
 *   data-accent="#hex"   bubble / header accent   (default: #4f8cff)
 */
(function () {
  "use strict";

  if (window.__techcorpChatbotLoaded) return;
  window.__techcorpChatbotLoaded = true;

  // Resolve this script element + its origin.
  var script =
    document.currentScript ||
    (function () {
      var s = document.getElementsByTagName("script");
      return s[s.length - 1];
    })();

  var origin;
  try {
    origin = new URL(script.src, window.location.href).origin;
  } catch (e) {
    origin = window.location.origin;
  }

  var TITLE = script.getAttribute("data-title") || "Assistant Financier";
  var POSITION = script.getAttribute("data-position") === "left" ? "left" : "right";
  var ACCENT = script.getAttribute("data-accent") || "#4f8cff";
  var WIDGET_URL = origin + "/widget";

  var SIDE = POSITION === "left" ? "left: 22px;" : "right: 22px;";

  // ── Styles (scoped via unique ids/classes) ───────────────────────
  var style = document.createElement("style");
  style.textContent =
    "#tcc-launcher{position:fixed;bottom:22px;" + SIDE + "z-index:2147483000;" +
    "width:58px;height:58px;border-radius:50%;border:none;cursor:pointer;" +
    "background:" + ACCENT + ";color:#fff;box-shadow:0 6px 22px rgba(0,0,0,.35);" +
    "display:flex;align-items:center;justify-content:center;" +
    "transition:transform .18s ease, box-shadow .18s ease;}" +
    "#tcc-launcher:hover{transform:scale(1.06);box-shadow:0 8px 26px rgba(0,0,0,.45);}" +
    "#tcc-launcher svg{width:26px;height:26px;}" +
    "#tcc-launcher .tcc-close-icon{display:none;}" +
    "#tcc-launcher.tcc-open .tcc-open-icon{display:none;}" +
    "#tcc-launcher.tcc-open .tcc-close-icon{display:block;}" +
    "#tcc-panel{position:fixed;bottom:92px;" + SIDE + "z-index:2147483000;" +
    "width:380px;max-width:calc(100vw - 32px);height:560px;max-height:calc(100vh - 120px);" +
    "border-radius:16px;overflow:hidden;background:#0c0e14;" +
    "border:1px solid #272b3d;box-shadow:0 16px 50px rgba(0,0,0,.5);" +
    "opacity:0;transform:translateY(12px) scale(.98);pointer-events:none;" +
    "transition:opacity .2s ease, transform .2s ease;}" +
    "#tcc-panel.tcc-open{opacity:1;transform:translateY(0) scale(1);pointer-events:auto;}" +
    "#tcc-panel iframe{width:100%;height:100%;border:none;display:block;background:#0c0e14;}" +
    "@media (max-width:480px){#tcc-panel{width:calc(100vw - 24px);height:calc(100vh - 110px);" + SIDE.replace("22px", "12px") + "}}";
  document.head.appendChild(style);

  // ── Launcher button ──────────────────────────────────────────────
  var launcher = document.createElement("button");
  launcher.id = "tcc-launcher";
  launcher.setAttribute("aria-label", "Ouvrir le chatbot");
  launcher.innerHTML =
    '<svg class="tcc-open-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>' +
    '<svg class="tcc-close-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>';

  // ── Panel (iframe lazy-loaded on first open) ─────────────────────
  var panel = document.createElement("div");
  panel.id = "tcc-panel";
  panel.setAttribute("role", "dialog");
  panel.setAttribute("aria-label", TITLE);

  var iframe = document.createElement("iframe");
  iframe.title = TITLE;
  iframe.setAttribute("loading", "lazy");
  panel.appendChild(iframe);

  var loaded = false;
  var open = false;

  function setOpen(next) {
    open = next;
    if (open && !loaded) {
      iframe.src = WIDGET_URL;
      loaded = true;
    }
    launcher.classList.toggle("tcc-open", open);
    panel.classList.toggle("tcc-open", open);
    launcher.setAttribute("aria-label", open ? "Fermer le chatbot" : "Ouvrir le chatbot");
  }

  launcher.addEventListener("click", function () { setOpen(!open); });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && open) setOpen(false);
  });

  function mount() {
    document.body.appendChild(panel);
    document.body.appendChild(launcher);
  }
  if (document.body) mount();
  else document.addEventListener("DOMContentLoaded", mount);
})();
