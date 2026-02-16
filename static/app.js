// SnackStopper Frontend

const VAPID_PUBLIC_KEY = document.querySelector('meta[name="vapid-key"]')?.content || "";

// --- Navigation ---
function showPage(page) {
  document.querySelectorAll(".page").forEach((p) => p.classList.remove("active"));
  document.querySelectorAll(".nav button").forEach((b) => b.classList.remove("active"));
  document.getElementById("page-" + page).classList.add("active");
  document.querySelector(`.nav button[data-page="${page}"]`).classList.add("active");

  if (page === "home") loadStats();
  if (page === "history") loadHistory();
  if (page === "settings") loadSettings();
}

// --- Toast ---
function toast(msg) {
  const el = document.getElementById("toast");
  el.textContent = msg;
  el.classList.add("show");
  setTimeout(() => el.classList.remove("show"), 2000);
}

// --- Stats ---
async function loadStats() {
  try {
    const res = await fetch("/api/stats");
    const data = await res.json();

    document.getElementById("streak-number").textContent = data.streak;
    document.getElementById("saved-number").textContent =
      "\u20AC" + data.total_saved.toFixed(2);
    document.getElementById("days-total").textContent = data.total_days;
    document.getElementById("days-passed").textContent = data.days_passed;

    // Update check-in buttons state
    const btnPassed = document.getElementById("btn-passed");
    const btnStopped = document.getElementById("btn-stopped");

    btnPassed.classList.remove("done", "selected");
    btnStopped.classList.remove("done", "selected");

    if (data.checked_in_today) {
      if (data.today_passed) {
        btnPassed.classList.add("selected");
        btnStopped.classList.add("done");
      } else {
        btnStopped.classList.add("selected");
        btnPassed.classList.add("done");
      }
      document.getElementById("today-status").textContent =
        data.today_passed ? "Goed gedaan vandaag!" : "Morgen beter!";
    } else {
      document.getElementById("today-status").textContent = "";
    }
  } catch (e) {
    console.error("Failed to load stats:", e);
  }
}

// --- Check-in ---
async function doCheckin(passed) {
  try {
    const res = await fetch("/api/checkin", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ passed }),
    });
    await res.json();
    toast(passed ? "Doorgereden! \uD83D\uDE80" : "Gestopt \uD83D\uDE14");
    loadStats();
  } catch (e) {
    toast("Fout bij opslaan");
    console.error(e);
  }
}

// --- History ---
async function loadHistory() {
  try {
    const res = await fetch("/api/history");
    const data = await res.json();
    const list = document.getElementById("history-list");
    list.innerHTML = "";

    if (data.length === 0) {
      list.innerHTML =
        '<li class="history-item"><span class="date">Nog geen check-ins</span></li>';
      return;
    }

    for (const item of data) {
      const d = new Date(item.date);
      const dateStr = d.toLocaleDateString("nl-NL", {
        weekday: "short",
        day: "numeric",
        month: "short",
      });

      const li = document.createElement("li");
      li.className = "history-item";
      li.innerHTML = `
        <span class="date">${dateStr}</span>
        ${item.passed ? '<span class="saved">+\u20AC' + item.amount_saved.toFixed(2) + "</span>" : ""}
        <span class="status ${item.passed ? "passed" : "stopped"}">${item.passed ? "\u2713" : "\u2717"}</span>
      `;
      list.appendChild(li);
    }
  } catch (e) {
    console.error("Failed to load history:", e);
  }
}

// --- Settings ---
async function loadSettings() {
  try {
    const res = await fetch("/api/settings");
    const data = await res.json();
    document.getElementById("setting-time").value = data.reminder_time;
    document.getElementById("setting-amount").value = data.average_amount.toFixed(2);
  } catch (e) {
    console.error("Failed to load settings:", e);
  }
}

async function saveSettings() {
  const time = document.getElementById("setting-time").value;
  const amount = parseFloat(document.getElementById("setting-amount").value);

  try {
    await fetch("/api/settings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ reminder_time: time, average_amount: amount }),
    });
    toast("Instellingen opgeslagen");
  } catch (e) {
    toast("Fout bij opslaan");
  }
}

// --- Push Notifications ---
function urlBase64ToUint8Array(base64String) {
  const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");
  const rawData = atob(base64);
  const outputArray = new Uint8Array(rawData.length);
  for (let i = 0; i < rawData.length; i++) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}

async function subscribePush() {
  if (!("serviceWorker" in navigator) || !("PushManager" in window)) {
    toast("Push niet ondersteund");
    return;
  }

  try {
    const reg = await navigator.serviceWorker.ready;
    let sub = await reg.pushManager.getSubscription();

    if (sub) {
      // Already subscribed
      document.getElementById("btn-push").classList.add("active");
      document.getElementById("btn-push").textContent = "Notificaties aan";
      return;
    }

    sub = await reg.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlBase64ToUint8Array(VAPID_PUBLIC_KEY),
    });

    await fetch("/api/subscribe", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(sub.toJSON()),
    });

    document.getElementById("btn-push").classList.add("active");
    document.getElementById("btn-push").textContent = "Notificaties aan";
    toast("Notificaties ingeschakeld!");
  } catch (e) {
    console.error("Push subscription failed:", e);
    toast("Kon notificaties niet inschakelen");
  }
}

async function checkPushStatus() {
  if (!("serviceWorker" in navigator) || !("PushManager" in window)) return;
  try {
    const reg = await navigator.serviceWorker.ready;
    const sub = await reg.pushManager.getSubscription();
    if (sub) {
      document.getElementById("btn-push").classList.add("active");
      document.getElementById("btn-push").textContent = "Notificaties aan";
    }
  } catch (e) {
    // ignore
  }
}

// --- Service Worker Registration ---
async function registerSW() {
  if ("serviceWorker" in navigator) {
    try {
      await navigator.serviceWorker.register("/static/sw.js");
    } catch (e) {
      console.error("SW registration failed:", e);
    }
  }
}

// --- Init ---
document.addEventListener("DOMContentLoaded", () => {
  registerSW();
  showPage("home");
  checkPushStatus();

  // Nav
  document.querySelectorAll(".nav button").forEach((btn) => {
    btn.addEventListener("click", () => showPage(btn.dataset.page));
  });

  // Check-in buttons
  document.getElementById("btn-passed").addEventListener("click", () => doCheckin(true));
  document.getElementById("btn-stopped").addEventListener("click", () => doCheckin(false));

  // Settings
  document.getElementById("btn-save-settings").addEventListener("click", saveSettings);

  // Push
  document.getElementById("btn-push").addEventListener("click", subscribePush);
});
