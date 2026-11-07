const kind = document.getElementById("kind");
const cat = document.getElementById("category");
function fillCategories() {
  cat.innerHTML = window.CATEGORIES[kind.value].map(c => `<option>${c}</option>`).join("");
}
kind.addEventListener("change", fillCategories);
fillCategories();

const labels = Object.keys(window.BY_CAT);
if (labels.length && window.Chart) {
  new Chart(document.getElementById("chart"), {
    type: "doughnut",
    data: { labels, datasets: [{ data: Object.values(window.BY_CAT) }] },
  });
}

const chat = document.getElementById("chat");
function addMsg(text, who) {
  const d = document.createElement("div");
  d.className = "msg " + who;
  d.textContent = text;
  chat.appendChild(d);
  chat.scrollTop = chat.scrollHeight;
}
document.getElementById("chat-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const input = document.getElementById("chat-input");
  const message = input.value.trim();
  if (!message) return;
  addMsg(message, "me");
  input.value = "";
  const r = await fetch("/api/chat", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });
  addMsg((await r.json()).reply, "bot");
});
