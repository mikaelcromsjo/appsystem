// === Mobile redirect ===
if (/Mobi|Android/i.test(navigator.userAgent)) {
  window.location.href = "/calls/number";
}

// === Toolbox ===
const toolboxToggle = document.getElementById('toolboxToggle');
const toolboxButtons = document.getElementById('toolboxButtons');
const btnFullscreen = document.getElementById('btnFullscreen');
const btnFontIncrease = document.getElementById('btnFontIncrease');
const btnFontDecrease = document.getElementById('btnFontDecrease');
const btnBgToggle = document.getElementById('btnBgToggle');
const body = document.body;

let fontSize = Number(localStorage.getItem('fontSize')) || 16;
console.log(localStorage.getItem('fontSize'));
document.documentElement.style.fontSize = fontSize + 'px';
console.log(document.documentElement.style.fontSize);
let isDark = localStorage.getItem('isDark') == "true";
setDark();
let open = false;

toolboxToggle.addEventListener('click', () => {
  open = !open;

  if (open) {
    toolboxButtons.style.display = 'flex';
    requestAnimationFrame(() => {
      toolboxButtons.classList.remove('opacity-0', 'scale-0', 'pointer-events-none');
      toolboxButtons.classList.add('opacity-100', 'scale-100');
    });
  } else {
    toolboxButtons.classList.remove('opacity-100', 'scale-100');
    toolboxButtons.classList.add('opacity-0', 'scale-0', 'pointer-events-none');

    toolboxButtons.addEventListener(
      'transitionend',
      () => {
        if (!open) toolboxButtons.style.display = 'none';
      },
      { once: true }
    );
  }
});

btnFullscreen.addEventListener('click', () => {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen();
  } else {
    document.exitFullscreen();
  }
});

btnFontIncrease.addEventListener('click', () => {
  fontSize = Math.min(25, fontSize + 2);
  document.documentElement.style.fontSize = fontSize + 'px';
  localStorage.setItem('fontSize', fontSize);
});

btnFontDecrease.addEventListener('click', () => {
  fontSize = Math.max(10, fontSize - 2);
  document.documentElement.style.fontSize = fontSize + 'px';
  localStorage.setItem('fontSize', fontSize);
});

btnBgToggle.addEventListener('click', () => {
  isDark = !isDark;
  setDark();
});

function setDark() {
  localStorage.setItem('isDark', isDark);
  console.log("asd");
  if (isDark) {
    document.documentElement.style.filter = 'invert(1) hue-rotate(180deg)';
    document.querySelectorAll('img, video, iframe').forEach(el => {
      el.style.filter = 'invert(1) hue-rotate(180deg)';
    });
  } else {
    document.documentElement.style.filter = '';
    document.querySelectorAll('img, video, iframe').forEach(el => {
      el.style.filter = '';
    });
  }
}

// === HTMX popup feedback ===
function showPopup(evt) {
  const xhr = evt.detail.xhr;
  const status = xhr.status;
  const popup = document.getElementById('popup');
  if (!popup) return;

  let messages = [];
  let error_fields = [];
  let isError = false;

  const hx_message = xhr.getResponseHeader("HX-Popup-Message");
  if (hx_message) {
    messages.push(hx_message);
    isError = status >= 400;
  } else if (xhr.getResponseHeader('Content-Type')?.includes('application/json')) {
    try {
      const data = JSON.parse(xhr.responseText);

      if (status >= 400) isError = true;

      if (data.detail) {
        if (Array.isArray(data.detail)) {
          data.detail.forEach(err => {
            console.log('Error detail:', err);

            let field = '';
            if (Array.isArray(err.loc) && err.loc.length > 0) {
              field = err.loc[err.loc.length - 1];
            }

            const msg = err.msg || '${field}: Felaktigt fält';
            messages.push(`${msg}`);
            error_fields.push(`${field}`);
          });
        } else if (typeof data.detail === 'string') {
          messages.push(data.detail);
        }
      }

      if (status === 200 && messages.length === 0) {
        messages.push("Ok!");
        isError = false;
      }
    } catch (err) {
      messages.push("Error parsing JSON response");
      isError = true;
    }
  } else if (status >= 400) {
    messages.push("Unexpected server response");
    isError = true;
  }

  if (messages.length) {
    popup.innerText = messages.join('\n');

    popup.classList.remove(
      'bg-green-100', 'text-green-800', 'border-green-300',
      'bg-red-100', 'text-red-800', 'border-red-300'
    );

    if (isError) {
      popup.classList.add('bg-red-100', 'text-red-800', 'border-red-300');
    } else {
      popup.classList.add('bg-green-100', 'text-green-800', 'border-green-300');
    }

    popup.style.display = 'block';
    popup.style.opacity = '1';
    popup.style.zIndex = 9999;

    setTimeout(() => {
      popup.style.opacity = '0';
      setTimeout(() => popup.style.display = 'none', 300);
    }, 2000);

    if (error_fields.length > 0) {
      showValidationErrors(error_fields, messages);
    }
  }
}

document.body.addEventListener('htmx:afterSwap', showPopup);

// === Alpine: confirm dialog ===
document.addEventListener("alpine:init", () => {
  console.log("init event listener");
  Alpine.directive("confirm", (el, { expression }) => {
    el.addEventListener("click", (e) => {
      e.preventDefault();
      el.dispatchEvent(new CustomEvent("confirm-dialog", {
        bubbles: true,
        detail: { message: expression, target: el }
      }));
    });
  });
});

function confirmDialog() {
  return {
    show: false,
    message: "",
    targetEl: null,
    open(e) {
      this.targetEl = e.detail.target;
      this.message = e.detail.message;
      this.show = true;
    },
    cancel() {
      this.show = false;
      this.targetEl = null;
    },
    proceed() {
      this.show = false;
      if (this.targetEl) {
        htmx.trigger(this.targetEl, "confirmed");
      }
    }
  }
}

// === WebSocket ===
let ws;
let wsToken;
const nameEl = document.querySelector("#name");
const numberEl = document.querySelector("#number");
const callHref = document.querySelector("#call_href");

async function fetchToken() {
  const res = await fetch(`${location.protocol}//${location.host}/get-ws-token`, {
    credentials: "include"
  });
  const data = await res.json();
  wsToken = data.ws_token;
}

function createWebSocket(url) {
  return new Promise((resolve, reject) => {
    const socket = new WebSocket(url);

    socket.onopen = () => resolve(socket);
    socket.onerror = () => reject(new Error(`Cannot connect via ${url}`));
  });
}

async function connectWS() {
  await fetchToken();

  const protocols = ["wss", "ws"];
  let connected = false;

  for (let proto of protocols) {
    const url = `${proto}://${location.host}/calls/ws?token=${wsToken}`;
    try {
      ws = await createWebSocket(url);
      console.log(`WebSocket connected via ${proto}!`);
      connected = true;

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log("Recieved", data);
        if (data.call) {
          enableCall();
        }
        if (data.type === 'alarm') {
          const message = `${data.customer}: ${data.note || "Alarm"}`;
          window.dispatchEvent(new CustomEvent("show-alert", { detail: message }));
        }
      };

      ws.onclose = () => {
        console.log(`WebSocket (${proto}) closed. Reconnecting in 1s...`);
        setTimeout(connectWS, 1000);
      };

      setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: "ping" }));
        }
      }, 10000);

      break;
    } catch (err) {
      console.warn(`${proto} connection failed, trying next...`);
    }
  }

  if (!connected) {
    console.error("Failed to connect via both WSS and WS. Retrying in 5s...");
    setTimeout(connectWS, 5000);
  }
}

connectWS();

// === Alpine stores ===
document.addEventListener('alpine:init', () => {

  Alpine.store('customers', {
    selected: JSON.parse(localStorage.getItem('selectedCustomers') || '{}'),
    showSelect: true,
    visible: {},
    inTable: {},

    init() {
      Alpine.effect(() => {
        localStorage.setItem('selectedCustomers', JSON.stringify(this.selected));
      });
      Alpine.effect(() => {
        this.initInTable();
      });
    },

    initInTable() {
      const checkboxes = document.querySelectorAll('.customer-checkbox');
      this.inTable = {};
      this.visible = {};
      checkboxes.forEach(cb => {
        const id = cb.dataset.id;
        if (id) this.inTable[id] = true;
      });
    },

    getVisibleIds() {
      const visibleIds = Object.keys(this.visible)
        .filter(id => this.visible[id])
        .map(id => parseInt(id));

      if (visibleIds.length === 0) {
        return Object.keys(this.inTable).map(id => parseInt(id));
      }
      return visibleIds;
    },

    selectVisible() {
      const visibleIds = this.getVisibleIds();
      visibleIds.forEach(id => this.selected[id] = true);
    },

    clearVisible() {
      const visibleIds = this.getVisibleIds();
      visibleIds.forEach(id => this.selected[id] = false);
    },

    isRowVisible(id) {
      return Object.keys(this.visible).length === 0 || this.visible[id] === true;
    },

    selectedCustomerData: [],
    setSelectedCustomerData(data) {
      this.selectedCustomerData = data;
    },
    getSelectedCustomerData() {
      return this.selectedCustomerData;
    },

    toggleSelect() {
      this.showSelect = !this.showSelect;
      localStorage.setItem('showSelect', JSON.stringify(this.showSelect));
    },

    clearSelectedIds() {
      for (const id in this.selected) {
        if (this.selected.hasOwnProperty(id)) {
          this.selected[id] = false;
        }
      }
      localStorage.removeItem('selectedCustomers');
    },

    getSelectedIds() {
      return Object.keys(this.selected)
        .filter(id => this.selected[id])
        .map(id => parseInt(id));
    },
  });

  Alpine.store('productFilters', {
    filter_a: true,
    filter_b: true,
    filter_c: true,
    filter_d: true,
    filter_e: true,
    filter_f: true,
    filter_g: true
  });

  Alpine.store('product', {
    id: "",
    type_id: "",
  });

  Alpine.store('customer', {
    comment: "",
    id: "",
  });

  Alpine.store('call', {
    comment: "",
    id: "",
  });

  Alpine.store('productCustomer', {
    status: "0",
    type_status: "0",
  });

  Alpine.store('modal', {
    title: "",
    submit: "",
    open: false
  });

});

// === Reload helpers ===
function reloadCallsDashboard() {
  htmx.ajax('GET', '/calls/dashboard', { target: '#calls_content' });
}

function reloadCallsCustomers() {
  document.getElementById('reload-customers-btn').click();
}

function reloadCallsProducts() {
  htmx.ajax('GET', '/calls/products_list/', { target: '#calls-product-list' });
}

function reloadAlarms() {
  htmx.ajax('GET', '/alarms/', { target: '#alarm_content' });
}

function reloadCustomers() {
  htmx.ajax('GET', '/customers/', { target: '#customer_content' });
  reloadCallsCustomers();
}

function reloadProducts() {
  htmx.ajax('GET', '/products/', { target: '#product_content' });
  htmx.ajax('GET', '/calls/products/', { target: '#calls-product-list' });
}

document.body.addEventListener('callsCustomersReload', reloadCallsCustomers);
document.body.addEventListener('callsProductsReload', reloadCallsProducts);
document.body.addEventListener('callsDashboardReload', reloadCallsDashboard);
document.body.addEventListener('alarmsReload', reloadAlarms);
document.body.addEventListener('customersReload', reloadCustomers);
document.body.addEventListener('productsReload', reloadProducts);

// === Validation errors ===
function showValidationErrors(error_fields, messages) {
  document.querySelectorAll(".input-error").forEach(field => {
    field.classList.remove("input-error");
  });
  document.querySelectorAll(".error-msg").forEach(msg => {
    msg.remove();
  });

  error_fields.forEach((fieldName, index) => {
    console.log(`[name="${fieldName}"]`);
    const field = document.querySelector(`[name="${fieldName}"]`);
    if (field) {
      field.classList.add("input-error");

      let errorSpan = document.createElement("span");
      errorSpan.className = "error-msg";
      errorSpan.textContent = messages[index];
      field.parentNode.insertBefore(errorSpan, field.nextSibling);

      field.addEventListener("input", () => {
        field.classList.remove("input-error");
        if (errorSpan) errorSpan.remove();
      }, { once: true });
    }
  });
}

// === Tagify ===
function initTagify(el) {
  const input = el.querySelector('input');
  if (!input) return;

  const object_type = el.dataset.objectType;
  if (!object_type) return;
  if (input._tagify) return;

  const tagify = new Tagify(input, {
    whitelist: [],
    dropdown: {
      maxItems: 20,
      classname: 'tags-look',
      enabled: 0,
      closeOnSelect: false
    },
    enforceWhitelist: false,
    delimiters: ",",
  });

  fetch(`/tags/all?object_type=${encodeURIComponent(object_type)}`)
    .then(res => res.json())
    .then(data => tagify.settings.whitelist = data)
    .catch(err => console.error(`[Tagify:${object_type}] preload suggestions error:`, err));

  tagify.on('input', debounce(e => {
    const q = e.detail.value;
    if (!q) return;
    const filtered = tagify.settings.whitelist.filter(tag => tag.toLowerCase().includes(q.toLowerCase()));
    tagify.dropdown.show.call(tagify, q, filtered);
  }, 200));

  input._tagify = tagify;
}

function debounce(fn, delay) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), delay);
  };
}

// === Table search (Alpine component) ===
function searchTable() {
  return {
    query: '',
    filterRows() {
      const rows = document.querySelectorAll('tbody tr');
      const q = this.query.toLowerCase();
      rows.forEach(row => {
        const id = parseInt(row.dataset.id);
        const text = [
          row.cells[1].textContent,
          row.cells[2].textContent,
          row.cells[3].textContent
        ].join(' ').toLowerCase();
        if (text.includes(q)) {
          Alpine.store('customers').visible[id] = true;
        } else {
          Alpine.store('customers').visible[id] = false;
        }
      });
    }
  }
}

// === Print table ===
function printTable(tableId) {
  const table = document.getElementById(tableId).outerHTML;
  const newWindow = window.open("");
  newWindow.document.write(`
    <html>
      <head>
        <title>Print Table</title>
        <style>
          table { border-collapse: collapse; width: 100%; }
          th, td { border: 1px solid black; padding: 8px; text-align: left; }
        </style>
      </head>
      <body>`);
  newWindow.document.write(table);
  newWindow.document.write("</body></html>");
  newWindow.document.close();
  newWindow.print();
}

// === Enter key submits focused element ===
document.addEventListener('keydown', function(e) {
  if (e.key === 'Enter' && e.target.tagName !== 'TEXTAREA') {
    e.preventDefault();
    const el = document.activeElement;
    if (el && el.tabIndex >= 0 && typeof el.click === 'function') {
      el.click();
    }
  }
});
