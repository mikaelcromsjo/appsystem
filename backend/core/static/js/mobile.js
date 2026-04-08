// === WebSocket (mobile) ===
let ws;
let wsToken;
const name_label = document.querySelector("#name");
const numer_label = document.querySelector("#number");
const call_button = document.querySelector("#call_href");
const sms_button = document.querySelector("#sms_href");

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
        console.log("data", data);

        if (data.type === 'customer_info') {
          call_button.style.display = "none";
          let oldCallHref = call_button.href;

          console.log("info");
          name_label.textContent = data.name;
          numer_label.textContent = data.number;
          call_button.href = "tel:" + data.number;

          if (data.number) {
            console.log("display");
            call_button.style.display = "block";
          }

          if (oldCallHref !== call_button.href) {
            console.log("change");
            sms_button.href = "";
            sms_button.style.display = "none";
          }
        }

        if (data.type === 'sms' && data.sms_type === 'multiple') {
          console.log("m");
          name_label.textContent = "Fler mottagare";
          numer_label.textContent = "...";
          sms_button.href = "sms:" + data.numbers + "?&body=" + encodeURIComponent(data.message);
          sms_button.style.display = "block";
          call_button.style.display = "none";
        } else if (data.type === "sms") {
          console.log("s");
          sms_button.href = "sms:" + numer_label.textContent + "?&body=" + encodeURIComponent(data.message);
          sms_button.style.display = "block";
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

function call() {
  console.log("call clicked");
  if (!ws || ws.readyState !== WebSocket.OPEN) {
    console.log("WebSocket not connected yet");
    return;
  }
  const number = document.querySelector("#number").textContent;
  console.log(number);
  ws.send(JSON.stringify({ call: true, number: number }));
}

connectWS();
