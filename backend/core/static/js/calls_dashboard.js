// === Auto-save form ===
function autoSaveForm() {
  const form = document.getElementById('save-form');
  if (!form) return;

  const submitForm = () => form.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));

  form.querySelectorAll('input.auto-save').forEach(el => {
    el.addEventListener('change', submitForm);
  });

  form.querySelectorAll('button.auto-save').forEach(el => {
    el.addEventListener('click', submitForm);
  });

  form.querySelectorAll('textarea.auto-save').forEach(el => {
    el.addEventListener('blur', submitForm);
  });
}

autoSaveForm();

// === Enable/disable helpers ===
function enableCall() {
  document.querySelectorAll('.call-disable').forEach(el => { el.disabled = false; });
}
function enableProduct() {
  document.querySelectorAll('.product-disable').forEach(el => { el.disabled = false; });
}
function enableCustomer() {
  document.querySelectorAll('.customer-disable').forEach(el => { el.disabled = false; });
}
function disableCall() {
  document.querySelectorAll('.call-disable').forEach(el => { el.disabled = true; });
}
function disableProduct() {
  document.querySelectorAll('.product-disable').forEach(el => { el.disabled = true; });
}
function disableCustomer() {
  document.querySelectorAll('.customer-disable').forEach(el => { el.disabled = true; });
}

// === Button highlight ===
let h_buttons = document.querySelectorAll('.can-highlight');

h_buttons.forEach(btn => {
  btn.addEventListener('click', () => {
    h_buttons.forEach(b => b.classList.remove('highlight'));
    btn.classList.add('highlight');
  });
});

function removeHighlight() {
  h_buttons.forEach(b => b.classList.remove('highlight'));
}

function highlightButton(button) {
  removeHighlight();
  button.classList.add('highlight');
}

// === Alarm modal ===
function showAlarmModal() {
  const modal = document.getElementById("alarm_modal");
  const input = document.getElementById("alarm_input");
  const note = document.getElementById("alarm_note");

  note.value = "";
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const year = today.getFullYear();
  const month = String(today.getMonth() + 1).padStart(2, '0');
  const day = String(today.getDate()).padStart(2, '0');
  const hours = String(today.getHours()).padStart(2, '0');
  const minutes = String(today.getMinutes()).padStart(2, '0');

  input.value = `${year}-${month}-${day}T${hours}:${minutes}`;
  modal.classList.remove("hidden");
}

// === SMS modal ===
function showSmsModal(multiple = false) {
  const modal = document.getElementById("sms_modal");
  const message = document.getElementById("sms_message");
  const multipleValue = document.getElementById("sms_multiple");

  if (!multiple) {
    multipleValue.innerHTML = "";
  } else {
    let recipients = Object.values(Alpine.store("customers").getSelectedCustomerData())
      .filter(c => c.phone && c.phone.trim() !== "")
      .map(c => `${c.name} ${c.phone}`)
      .join("<br/>");

    const maxLen = 400;
    let displayRecipients = recipients;
    if (recipients.length > maxLen) {
      displayRecipients = recipients.substring(0, maxLen) + "...";
    }
    multipleValue.innerHTML = displayRecipients + "<br/><br/>";
  }
  modal.classList.remove("hidden");
}

// === SMS send via WebSocket ===
function sms(multiple = false) {
  console.log("sms clicked");

  let sms_type = "single";
  let numbers = "";

  if (multiple) {
    console.log("sms multiple");
    numbers = Object.values(Alpine.store("customers").getSelectedCustomerData())
      .filter(c => c.phone && c.phone.trim() !== "")
      .map(c => `${c.phone}`)
      .join(",");
    sms_type = "multiple";
  }

  if (!ws || ws.readyState !== WebSocket.OPEN) {
    console.log("WebSocket not connected yet");
    return;
  }
  const message = document.querySelector("#sms_message").value;
  console.log("message", message);
  ws.send(JSON.stringify({ type: "sms", message: message, sms_type: sms_type, numbers: numbers }));
  document.querySelector("#sms_message").value = "";
}

// === Split.js layout ===
function setupSplit(ids, key) {
  const saved = JSON.parse(localStorage.getItem(key));
  const defaults = Array(ids.length).fill(100 / ids.length);
  Split(ids.map(id => '#' + id), {
    sizes: saved || defaults,
    gutterSize: 6,
    cursor: 'col-resize',
    minSize: 100,
    onDragEnd: sizes => localStorage.setItem(key, JSON.stringify(sizes))
  });
}

function setupRowSplit(ids, key) {
  const saved = JSON.parse(localStorage.getItem(key));
  const defaults = Array(ids.length).fill(100 / ids.length);
  Split(ids.map(id => '#' + id), {
    sizes: saved || defaults,
    direction: 'vertical',
    gutterSize: 6,
    cursor: 'row-resize',
    minSize: 100,
    onDragEnd: sizes => localStorage.setItem(key, JSON.stringify(sizes))
  });
}

setupSplit(['col1', 'col2', 'col3', 'col4'], 'layout-topRow');
setupSplit(['col5', 'col6', 'col7'], 'layout-bottomRow');
setupRowSplit(['topRow', 'bottomRow'], 'row-split');
