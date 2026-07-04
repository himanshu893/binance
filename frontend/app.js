const API_BASE = "http://127.0.0.1:5000";

// ─── Helpers ───────────────────────────────────────────────────────────────

function money(value) {
  const number = Number(value);
  if (Number.isNaN(number)) return value ?? "--";
  return `${number.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} USDT`;
}

async function requestJson(path, options = {}) {
  const url = path.startsWith("http") ? path : `${API_BASE}${path}`;
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || `${response.status} ${response.statusText}`);
  return data;
}

function activeNav() {
  const page = document.body.dataset.page;
  document.querySelectorAll(".nav a").forEach((link) => {
    link.classList.toggle("active", link.dataset.page === page);
  });
}

function setText(id, value) {
  const node = document.getElementById(id);
  if (node) node.textContent = value;
}

function setLoading(id, msg = "Loading…") {
  setText(id, msg);
}

// ─── Account ───────────────────────────────────────────────────────────────

async function loadAccount() {
  const ids = ["walletBalance", "availableBalance", "unrealizedPnl", "tradingStatus", "feeTier", "lastUpdated"];
  if (!ids.some((id) => document.getElementById(id))) return;

  ids.forEach((id) => setLoading(id));

  try {
    const account = await requestJson("/api/account");
    setText("walletBalance",   money(account.totalWalletBalance));
    setText("availableBalance",money(account.availableBalance));
    setText("unrealizedPnl",  money(account.totalUnrealizedProfit));
    setText("tradingStatus",  account.canTrade === false ? "Trading disabled" : "Trading enabled");
    setText("feeTier",        account.feeTier ?? "--");
    setText("lastUpdated",    new Date(account.updateTime || Date.now()).toLocaleString());
  } catch (err) {
    ids.forEach((id) => setText(id, "Error"));
    console.error("Account fetch failed:", err);
    showBanner(`Could not reach the API server: ${err.message}. Make sure server.py is running.`, "error");
  }
}

// ─── Order row renderer ────────────────────────────────────────────────────

function orderRow(order) {
  const side  = (order.side || "").toLowerCase();
  const price = (order.order_type || order.type) === "MARKET" || order.price === "0" ? "MKT" : order.price || "--";
  const time  = order.time
    ? new Date(Number.isFinite(+order.time) ? +order.time : order.time).toLocaleString()
    : "--";

  return `
    <tr>
      <td>${time}</td>
      <td>${order.symbol || "--"}</td>
      <td><span class="tag ${side === "sell" ? "sell" : "buy"}">${order.side || "--"}</span></td>
      <td>${order.order_type || order.type || "--"}</td>
      <td>${order.quantity || order.origQty || "--"}</td>
      <td>${price}</td>
      <td><span class="tag neutral">${order.status || "--"}</span></td>
    </tr>
  `;
}

// ─── Dashboard recent orders (from Binance API) ────────────────────────────

async function renderRecentOrders(limit = 5) {
  const body = document.getElementById("recentOrdersBody");
  if (!body) return;

  body.innerHTML = `<tr><td colspan="7"><div class="empty-state">Loading from Binance…</div></td></tr>`;

  try {
    const orders = await requestJson(`/api/orders?symbol=BTCUSDT&limit=${limit}`);
    if (!orders.length) {
      body.innerHTML = `<tr><td colspan="7"><div class="empty-state">No BTCUSDT orders on your account yet.</div></td></tr>`;
      return;
    }
    body.innerHTML = orders.slice(0, limit).reverse().map((o) => orderRow({
      time:       o.time,
      symbol:     o.symbol,
      side:       o.side,
      order_type: o.type,
      quantity:   o.origQty,
      price:      o.price === "0" ? "MKT" : o.price,
      status:     o.status
    })).join("");
  } catch (err) {
    body.innerHTML = `<tr><td colspan="7"><div class="empty-state">API Error: ${err.message}</div></td></tr>`;
  }
}

// ─── Order form ────────────────────────────────────────────────────────────

function setupOrderForm() {
  const form = document.getElementById("orderForm");
  if (!form) return;

  const type        = document.getElementById("orderType");
  const priceField  = document.getElementById("priceField");
  const stopField   = document.getElementById("stopPriceField");
  const tifField    = document.getElementById("timeInForceField");
  const message     = document.getElementById("orderMessage");

  function updateConditionalFields() {
    const value      = type.value;
    const needsPrice = value === "LIMIT" || value === "STOP";
    priceField.style.display = needsPrice ? "grid" : "none";
    tifField.style.display   = needsPrice ? "grid" : "none";
    stopField.style.display  = value === "STOP" ? "grid" : "none";
    document.getElementById("price").required        = needsPrice;
    document.getElementById("timeInForce").required  = needsPrice;
    document.getElementById("stopPrice").required    = value === "STOP";
  }

  type.addEventListener("change", updateConditionalFields);
  form.addEventListener("reset", () => window.setTimeout(updateConditionalFields, 0));
  updateConditionalFields();

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const data       = Object.fromEntries(new FormData(form).entries());
    const needsPrice = data.order_type === "LIMIT" || data.order_type === "STOP";
    const payload    = {
      symbol:        data.symbol || "BTCUSDT",
      side:          data.side,
      order_type:    data.order_type,
      quantity:      data.quantity,
      price:         needsPrice ? (data.price || null) : null,
      time_in_force: needsPrice ? (data.time_in_force || null) : null,
      stop_price:    data.order_type === "STOP" ? (data.stop_price || null) : null
    };

    message.className   = "message";
    message.textContent = "";

    try {
      const response = await requestJson("/api/orders", {
        method: "POST",
        body:   JSON.stringify(payload)
      });

      const orderId = response.orderId || response.algoId || "—";
      const status  = response.status || response.algoStatus || "SUBMITTED";
      message.className   = "message success show";
      message.textContent = `✓ Order ${orderId} accepted by Binance — Status: ${status}`;
      form.reset();
      updateConditionalFields();
    } catch (error) {
      message.className   = "message error show";
      message.textContent = error.message || "Order failed.";
    }
  });
}

// ─── History page ──────────────────────────────────────────────────────────

async function loadHistory() {
  const body = document.getElementById("historyBody");
  if (!body) return;

  const symbol = document.getElementById("symbolFilter")?.value || "BTCUSDT";
  body.innerHTML = `<tr><td colspan="7"><div class="empty-state">Loading from Binance…</div></td></tr>`;

  try {
    const apiOrders = await requestJson(`/api/orders?symbol=${symbol}&limit=50`);
    _lastFetchedOrders = apiOrders;   // cache for download
    if (!apiOrders.length) {
      body.innerHTML = `<tr><td colspan="7"><div class="empty-state">No ${symbol} orders found on your account.</div></td></tr>`;
      return;
    }
    body.innerHTML = [...apiOrders].reverse().map((o) => orderRow({
      time:       o.time,
      symbol:     o.symbol,
      side:       o.side,
      order_type: o.type,
      quantity:   o.origQty,
      price:      o.price,
      status:     o.status
    })).join("");
  } catch (err) {
    body.innerHTML = `<tr><td colspan="7"><div class="empty-state">API Error: ${err.message}</div></td></tr>`;
  }
}

// ─── Download helpers ──────────────────────────────────────────────────────

let _lastFetchedOrders = [];   // cache the last loaded orders for download

function triggerDownload(filename, content, mimeType) {
  const blob = new Blob([content], { type: mimeType });
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement("a");
  a.href     = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

function downloadAsJson() {
  if (!_lastFetchedOrders.length) {
    alert("No order data loaded yet. Click Refresh first.");
    return;
  }
  const symbol   = document.getElementById("symbolFilter")?.value || "BTCUSDT";
  const filename = `binance_orders_${symbol}_${new Date().toISOString().slice(0,10)}.json`;
  triggerDownload(filename, JSON.stringify(_lastFetchedOrders, null, 2), "application/json");
}

function downloadAsCsv() {
  if (!_lastFetchedOrders.length) {
    alert("No order data loaded yet. Click Refresh first.");
    return;
  }
  const symbol  = document.getElementById("symbolFilter")?.value || "BTCUSDT";
  const headers = ["orderId", "time", "symbol", "side", "type", "origQty", "price", "avgPrice", "status", "timeInForce"];
  const rows    = _lastFetchedOrders.map(o =>
    headers.map(h => {
      let val = o[h] ?? "";
      if (h === "time" && val) val = new Date(Number(val)).toLocaleString();
      if (h === "price" && val === "0") val = "MARKET";
      return `"${String(val).replace(/"/g, '""')}"`;
    }).join(",")
  );
  const csv      = [headers.join(","), ...rows].join("\n");
  const filename = `binance_orders_${symbol}_${new Date().toISOString().slice(0,10)}.csv`;
  triggerDownload(filename, csv, "text/csv");
}

// ─── History actions ───────────────────────────────────────────────────────

function setupHistoryActions() {
  const refreshBtn = document.getElementById("refreshHistory");
  if (refreshBtn) refreshBtn.addEventListener("click", loadHistory);

  const symbolFilter = document.getElementById("symbolFilter");
  if (symbolFilter) symbolFilter.addEventListener("change", loadHistory);

  const jsonBtn = document.getElementById("downloadJson");
  if (jsonBtn) jsonBtn.addEventListener("click", downloadAsJson);

  const csvBtn = document.getElementById("downloadCsv");
  if (csvBtn) csvBtn.addEventListener("click", downloadAsCsv);
}

// ─── Banner ────────────────────────────────────────────────────────────────

function showBanner(msg, type = "error") {
  let banner = document.getElementById("globalBanner");
  if (!banner) {
    banner = document.createElement("div");
    banner.id = "globalBanner";
    banner.style.cssText = "position:fixed;top:12px;left:50%;transform:translateX(-50%);z-index:999;padding:10px 20px;border-radius:8px;font-size:13px;max-width:480px;text-align:center;";
    document.body.appendChild(banner);
  }
  banner.style.background = type === "error" ? "#ff4d4f22" : "#52c41a22";
  banner.style.border      = `1px solid ${type === "error" ? "#ff4d4f" : "#52c41a"}`;
  banner.style.color       = type === "error" ? "#ff4d4f" : "#52c41a";
  banner.textContent       = msg;
  setTimeout(() => banner.remove(), 7000);
}

// ─── Init ──────────────────────────────────────────────────────────────────

document.addEventListener("DOMContentLoaded", () => {
  activeNav();
  loadAccount();
  renderRecentOrders();
  setupOrderForm();
  loadHistory();
  setupHistoryActions();
});
