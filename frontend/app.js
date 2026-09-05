const recordButton = document.querySelector("#recordButton");
const recordLabel = document.querySelector("#recordLabel");
const recordStatus = document.querySelector("#recordStatus");
const audioFile = document.querySelector("#audioFile");
const transcriptInput = document.querySelector("#transcript");
const analyzeButton = document.querySelector("#analyzeButton");
const clearButton = document.querySelector("#clearButton");
const retryButton = document.querySelector("#retryButton");
const charCount = document.querySelector("#charCount");
const responseState = document.querySelector("#responseState");
const inputMode = document.querySelector("#inputMode");
const emptyState = document.querySelector("#emptyState");
const loadingState = document.querySelector("#loadingState");
const result = document.querySelector("#result");
const errorState = document.querySelector("#errorState");
const errorMessage = document.querySelector("#errorMessage");

let recorder;
let audioChunks = [];
let recordedAudio;
let lastRequest;

function updateCount() {
  const count = transcriptInput.value.trim().length;
  charCount.textContent = `${count.toLocaleString()} character${count === 1 ? "" : "s"}`;
}

function setMode(label, status) {
  inputMode.textContent = label;
  recordStatus.textContent = status;
}

function resetOutput() {
  emptyState.hidden = false;
  loadingState.hidden = true;
  result.hidden = true;
  errorState.hidden = true;
  responseState.textContent = "waiting";
}

function setBusy(isBusy) {
  analyzeButton.disabled = isBusy;
  analyzeButton.querySelector("span").textContent = isBusy ? "Analyzing..." : "Analyze note";
  responseState.textContent = isBusy ? "working" : "ready";
  emptyState.hidden = isBusy;
  loadingState.hidden = !isBusy;
  result.hidden = true;
  errorState.hidden = true;
}

function showError(message) {
  emptyState.hidden = true;
  loadingState.hidden = true;
  result.hidden = true;
  errorState.hidden = false;
  errorMessage.textContent = message;
  responseState.textContent = "needs attention";
}

function renderList(element, items) {
  element.replaceChildren();
  items.forEach((item) => {
    const li = document.createElement("li");
    li.textContent = item;
    element.append(li);
  });
}

function renderResult(data) {
  document.querySelector("#summary").textContent = data.summary || "No summary returned.";
  const actionItems = document.querySelector("#actionItems");
  actionItems.replaceChildren();
  document.querySelector("#actionCount").textContent = `${data.action_items.length} found`;
  data.action_items.forEach((item, index) => {
    const article = document.createElement("article");
    article.className = "action-item";
    const owner = item.owner || "Unassigned";
    const dueDate = item.due_date || "No due date";
    article.innerHTML = `<span class="action-number">${String(index + 1).padStart(2, "0")}</span><div><p class="task"></p><p class="meta"></p></div><span class="priority ${item.priority}">${item.priority}</span>`;
    article.querySelector(".task").textContent = item.task || "Untitled task";
    article.querySelector(".meta").textContent = `${owner} / ${dueDate}`;
    actionItems.append(article);
  });

  const decisionsSection = document.querySelector("#decisionsSection");
  decisionsSection.hidden = !data.decisions.length;
  renderList(document.querySelector("#decisions"), data.decisions);
  const questionsSection = document.querySelector("#questionsSection");
  questionsSection.hidden = !data.unanswered_questions.length;
  renderList(document.querySelector("#questions"), data.unanswered_questions);
  const transcriptSection = document.querySelector("#transcriptSection");
  transcriptSection.hidden = !data.transcript;
  document.querySelector("#returnedTranscript").textContent = data.transcript || "";
  emptyState.hidden = true;
  loadingState.hidden = true;
  errorState.hidden = true;
  result.hidden = false;
  responseState.textContent = "complete";
}

async function analyze() {
  const transcript = transcriptInput.value.trim();
  if (!transcript && !recordedAudio && !audioFile.files[0]) {
    showError("Add a transcript, record a note, or choose an audio file first.");
    return;
  }

  setBusy(true);
  const request = recordedAudio || audioFile.files[0] ? { type: "audio", value: recordedAudio || audioFile.files[0] } : { type: "text", value: transcript };
  lastRequest = request;
  try {
    let response;
    if (request.type === "audio") {
      const body = new FormData();
      body.append("file", request.value, request.value.name || "voice-note.webm");
      response = await fetch("/action-items/audio", { method: "POST", body });
    } else {
      response = await fetch("/action-items/text", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ transcript: request.value }) });
    }
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "The note could not be analyzed.");
    renderResult(data);
  } catch (error) {
    showError(error.message || "Something went wrong while analyzing the note.");
  } finally {
    analyzeButton.disabled = false;
    analyzeButton.querySelector("span").textContent = "Analyze note";
  }
}

async function toggleRecording() {
  if (recorder?.state === "recording") {
    recorder.stop();
    return;
  }
  if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
    showError("This browser cannot record audio. Use the upload control or paste a transcript instead.");
    return;
  }
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    audioChunks = [];
    recorder = new MediaRecorder(stream);
    recorder.ondataavailable = (event) => { if (event.data.size) audioChunks.push(event.data); };
    recorder.onstop = () => {
      stream.getTracks().forEach((track) => track.stop());
      recordedAudio = new Blob(audioChunks, { type: recorder.mimeType || "audio/webm" });
      recordButton.classList.remove("is-recording");
      recordButton.setAttribute("aria-pressed", "false");
      recordLabel.textContent = "Record again";
      setMode("recorded", "Ready to analyze your recording.");
    };
    recorder.start();
    recordButton.classList.add("is-recording");
    recordButton.setAttribute("aria-pressed", "true");
    recordLabel.textContent = "Stop recording";
    setMode("recording", "Microphone is listening...");
  } catch (error) {
    showError("Microphone access was not granted. Check browser permissions or use a transcript.");
  }
}

transcriptInput.addEventListener("input", updateCount);
recordButton.addEventListener("click", toggleRecording);
audioFile.addEventListener("change", () => { recordedAudio = undefined; if (audioFile.files[0]) setMode("audio selected", audioFile.files[0].name); });
analyzeButton.addEventListener("click", analyze);
retryButton.addEventListener("click", () => { if (lastRequest) analyze(); });
clearButton.addEventListener("click", () => { transcriptInput.value = ""; recordedAudio = undefined; audioFile.value = ""; updateCount(); setMode("ready", "Your browser recording stays here until you send it."); resetOutput(); });
updateCount();
