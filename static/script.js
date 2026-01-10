// =========================
// Buttons
// =========================
const runBtn = document.getElementById("runBtn");
const autoBtn = document.getElementById("autoBtn");
const clearHistoryBtn = document.getElementById("clearHistoryBtn");

const downloadJsonBtn = document.getElementById("downloadJsonBtn");
const downloadTxtBtn = document.getElementById("downloadTxtBtn");
const exportCsvBtn = document.getElementById("exportCsvBtn");

const themeBtn = document.getElementById("themeBtn");

// Run button inner items
const runText = document.getElementById("runText");
const loader = document.getElementById("loader");

// Status indicators
const serverStatus = document.getElementById("serverStatus");
const autoStatus = document.getElementById("autoStatus");
const shortageCountBadge = document.getElementById("shortageCountBadge");

// Audio
const alertSound = document.getElementById("alertSound");

// =========================
// Stats cards
// =========================
const timeValue = document.getElementById("timeValue");
const hourValue = document.getElementById("hourValue");
const cloudValue = document.getElementById("cloudValue");
const sunriseValue = document.getElementById("sunriseValue");
const sunsetValue = document.getElementById("sunsetValue");

const solarValue = document.getElementById("solarValue");
const batteryValue = document.getElementById("batteryValue");
const demandValue = document.getElementById("demandValue");
const supplyValue = document.getElementById("supplyValue");

// Distribution
const hospitalValue = document.getElementById("hospitalValue");
const schoolValue = document.getElementById("schoolValue");
const homesValue = document.getElementById("homesValue");

// Suggestions + Alert
const alertBox = document.getElementById("alertBox");
const suggestionsList = document.getElementById("suggestions");

// Explain AI
const aiExplainText = document.getElementById("aiExplainText");

// History table
const historyBody = document.getElementById("historyBody");
// =========================
// ⬆ Scroll to Top Button
// =========================
const scrollTopBtn = document.getElementById("scrollTopBtn");

window.addEventListener("scroll", () => {
  if (window.scrollY > 300) {
    scrollTopBtn.classList.add("show");
  } else {
    scrollTopBtn.classList.remove("show");
  }
});

scrollTopBtn.addEventListener("click", () => {
  window.scrollTo({ top: 0, behavior: "smooth" });
});

// =========================
// Sidebar active link highlight
// =========================
const navLinks = document.querySelectorAll(".nav-link");
const sections = ["dashboard", "reports", "about"].map(id => document.getElementById(id));

window.addEventListener("scroll", () => {
  let current = "dashboard";

  sections.forEach(sec => {
    const top = sec.offsetTop - 140;
    if (window.scrollY >= top) current = sec.id;
  });

  navLinks.forEach(link => {
    link.classList.remove("active");
    if (link.getAttribute("href") === "#" + current) {
      link.classList.add("active");
    }
  });
});


// Charts
let powerChart = null;
let trendChart = null;

// History array
let historyRuns = [];

// Auto-run interval
let autoInterval = null;

// Trend last values
let lastDemand = null;
let lastSupply = null;

// shortage counter
let shortageCount = 0;

// =========================
// 🌙 Theme Toggle
// =========================
function setTheme(isDark) {
  if (isDark) {
    document.body.classList.add("dark");
    themeBtn.textContent = "☀️ Light Mode";
  } else {
    document.body.classList.remove("dark");
    themeBtn.textContent = "🌙 Dark Mode";
  }
}

const savedTheme = localStorage.getItem("theme");
setTheme(savedTheme === "dark");

themeBtn.addEventListener("click", () => {
  const isDarkNow = document.body.classList.contains("dark");
  const newTheme = isDarkNow ? "light" : "dark";
  localStorage.setItem("theme", newTheme);
  setTheme(newTheme === "dark");
});

// =========================
// CSV Export
// =========================
function downloadCSV(rows) {
  const header = ["#", "Hour", "Weather", "Homes", "Demand(kW)", "Supply(kW)", "Status"];
  const csv = [header.join(",")];

  rows.forEach((r, idx) => {
    const status = r.total_supply_kw >= r.total_demand_kw ? "OK" : "SHORTAGE";
    csv.push(
      [
        idx + 1,
        r.hour,
        r.weather,
        r.homes,
        r.total_demand_kw,
        r.total_supply_kw,
        status
      ].join(",")
    );
  });

  const blob = new Blob([csv.join("\n")], { type: "text/csv" });
  const url = URL.createObjectURL(blob);

  const a = document.createElement("a");
  a.href = url;
  a.download = "microgrid_history.csv";
  document.body.appendChild(a);
  a.click();
  a.remove();

  URL.revokeObjectURL(url);
}

exportCsvBtn.addEventListener("click", () => {
  if (historyRuns.length === 0) {
    alert("No history found. Run simulation first!");
    return;
  }
  downloadCSV(historyRuns);
});

// =========================
// Charts update
// =========================
function updateBarChart(data) {
  const ctx = document.getElementById("powerChart").getContext("2d");

  const labels = ["Solar", "Battery Support", "Total Supply", "Total Demand"];
  const values = [
    data.solar_power_kw,
    data.battery_support_kw,
    data.total_supply_kw,
    data.total_demand_kw
  ];

  if (powerChart) powerChart.destroy();

  powerChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels,
      datasets: [{ label: "Power (kW)", data: values }]
    },
    options: {
      responsive: true,
      scales: { y: { beginAtZero: true } }
    }
  });
}

function updateTrendChart() {
  const ctx = document.getElementById("trendChart").getContext("2d");

  const reversed = [...historyRuns].reverse(); // oldest -> newest
  const labels = reversed.map((_, i) => `Run ${i + 1}`);

  const demandSeries = reversed.map(r => r.total_demand_kw);
  const supplySeries = reversed.map(r => r.total_supply_kw);

  if (trendChart) trendChart.destroy();

  trendChart = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [
        { label: "Demand (kW)", data: demandSeries, tension: 0.3 },
        { label: "Supply (kW)", data: supplySeries, tension: 0.3 }
      ]
    },
    options: {
      responsive: true,
      plugins: { legend: { display: true } },
      scales: { y: { beginAtZero: true } }
    }
  });
}

// =========================
// ✅ Main Simulation Function
// =========================
async function runSimulation() {
  runText.textContent = "Running...";
  loader.classList.remove("hidden");
  runBtn.disabled = true;

  try {
    const weather = document.getElementById("weather").value;
    const homesCount = document.getElementById("homesCount").value;
    const batteryCap = document.getElementById("batteryCap").value;

    const res = await fetch(`/simulate?weather=${weather}&homes=${homesCount}&batteryCap=${batteryCap}`);
    const data = await res.json();

    serverStatus.textContent = "🟢 Server Online";

    // =========================
    // Stat Cards
    // =========================
    if (data.current_time) timeValue.textContent = data.current_time;
    hourValue.textContent = data.hour;

    if (data.cloud_cover_percent !== undefined) cloudValue.textContent = data.cloud_cover_percent;
    if (data.sunrise_time) sunriseValue.textContent = data.sunrise_time;
    if (data.sunset_time) sunsetValue.textContent = data.sunset_time;

    solarValue.textContent = data.solar_power_kw;
    batteryValue.textContent = data.battery_level_percent;

    // =========================
    // Trend arrows
    // =========================
    if (lastDemand !== null) {
      if (data.total_demand_kw > lastDemand) demandValue.textContent = data.total_demand_kw + " ↑";
      else if (data.total_demand_kw < lastDemand) demandValue.textContent = data.total_demand_kw + " ↓";
      else demandValue.textContent = data.total_demand_kw;
    } else {
      demandValue.textContent = data.total_demand_kw;
    }

    if (lastSupply !== null) {
      if (data.total_supply_kw > lastSupply) supplyValue.textContent = data.total_supply_kw + " ↑";
      else if (data.total_supply_kw < lastSupply) supplyValue.textContent = data.total_supply_kw + " ↓";
      else supplyValue.textContent = data.total_supply_kw;
    } else {
      supplyValue.textContent = data.total_supply_kw;
    }

    lastDemand = data.total_demand_kw;
    lastSupply = data.total_supply_kw;

    // =========================
    // Distribution
    // =========================
    hospitalValue.textContent = data.distribution.hospital_kw;
    schoolValue.textContent = data.distribution.school_kw;
    homesValue.textContent = data.distribution.homes_kw;

    // =========================
    // Alert
    // =========================
    alertBox.textContent = data.alert;
    alertBox.classList.remove("good", "bad");

    const ok = data.total_supply_kw >= data.total_demand_kw;
    alertBox.classList.add(ok ? "good" : "bad");

    // shortage sound + counter
    if (!ok) {
      shortageCount += 1;
      shortageCountBadge.textContent = `⚠️ Shortages: ${shortageCount}`;
      alertSound.currentTime = 0;
      alertSound.play().catch(() => {});
    }

    // =========================
    // Suggestions
    // =========================
    suggestionsList.innerHTML = "";
    if (data.suggestions && data.suggestions.length > 0) {
      data.suggestions.forEach((s) => {
        const li = document.createElement("li");
        li.textContent = s;
        suggestionsList.appendChild(li);
      });
    } else {
      const li = document.createElement("li");
      li.textContent = "No suggestions available.";
      suggestionsList.appendChild(li);
    }

    // =========================
    // Explain AI
    // =========================
    aiExplainText.textContent =
      "AI in this project works as an intelligent decision system. It allocates energy using priority rules " +
      "(Hospital > School > Homes), uses real weather data (cloud cover) to estimate solar generation, detects shortages, " +
      "and provides AI recommendations to reduce load and improve microgrid stability.";

    // =========================
    // History
    // =========================
    historyRuns.unshift(data);
    historyRuns = historyRuns.slice(0, 10);

    historyBody.innerHTML = "";
    historyRuns.forEach((run, index) => {
      const tr = document.createElement("tr");
      const statusOK = run.total_supply_kw >= run.total_demand_kw;

      tr.innerHTML = `
        <td>${index + 1}</td>
        <td>${run.hour}</td>
        <td>${run.weather}</td>
        <td>${run.homes}</td>
        <td>${run.total_demand_kw}</td>
        <td>${run.total_supply_kw}</td>
        <td>
          <span class="badge ${statusOK ? "ok" : "warn"}">
            ${statusOK ? "✅ OK" : "⚠️ Shortage"}
          </span>
        </td>
      `;
      historyBody.appendChild(tr);
    });

    // =========================
    // Charts
    // =========================
    updateBarChart(data);
    updateTrendChart();

  } catch (err) {
    console.error(err);
    serverStatus.textContent = "🔴 Server Offline / Error";
    alertBox.textContent = "❌ Error running simulation. Please check server.";
    alertBox.classList.remove("good");
    alertBox.classList.add("bad");
  } finally {
    runText.textContent = "Run Simulation";
    loader.classList.add("hidden");
    runBtn.disabled = false;
  }
}

// Manual run
runBtn.addEventListener("click", runSimulation);

// Auto run
autoBtn.addEventListener("click", () => {
  if (autoInterval) {
    clearInterval(autoInterval);
    autoInterval = null;

    autoBtn.textContent = "▶ Auto Run";
    autoBtn.style.opacity = "1";
    autoStatus.textContent = "⏹ Auto Run: OFF";
  } else {
    runSimulation();
    const interval = parseInt(document.getElementById("interval").value);
    autoInterval = setInterval(runSimulation, interval);

    autoBtn.textContent = "⏸ Stop Auto";
    autoBtn.style.opacity = "0.9";
    autoStatus.textContent = `▶ Auto Run: ON (${interval / 1000} sec)`;
  }
});

// Clear history
clearHistoryBtn.addEventListener("click", () => {
  historyRuns = [];
  lastDemand = null;
  lastSupply = null;

  historyBody.innerHTML = `
    <tr>
      <td colspan="7">History cleared ✅ Run simulation to add new records.</td>
    </tr>
  `;
});

// Downloads
downloadJsonBtn.addEventListener("click", () => {
  window.location.href = "/download/json";
});

downloadTxtBtn.addEventListener("click", () => {
  window.location.href = "/download/txt";
});

// Initial UI state
autoStatus.textContent = "⏹ Auto Run: OFF";
serverStatus.textContent = "🟢 Server Online";
shortageCountBadge.textContent = "⚠️ Shortages: 0";
