const statusEl = document.getElementById("status");
const metaEl = document.getElementById("meta");
const tableWrapEl = document.getElementById("tableWrap");
const hiddenPlayerFields = new Set(["player_id", "nationality"]);
const hiddenClubFields = new Set(["club_id", "country", "league"]);

function setStatus(message, kind = "ok") {
  statusEl.className = `status ${kind}`;
  statusEl.textContent = message;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function renderTable(rows) {
  if (!rows.length) {
    tableWrapEl.innerHTML = "<p>No results.</p>";
    return;
  }

  const columns = Object.keys(rows[0]);
  const head = columns.map((c) => `<th>${escapeHtml(c)}</th>`).join("");
  const body = rows
    .map((row) => {
      const cells = columns
        .map((c) => `<td>${escapeHtml(typeof row[c] === "object" ? JSON.stringify(row[c]) : row[c])}</td>`)
        .join("");
      return `<tr>${cells}</tr>`;
    })
    .join("");

  tableWrapEl.innerHTML = `<table><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table>`;
}

function stripHiddenFields(row) {
  return Object.fromEntries(
    Object.entries(row).filter(([key]) => !hiddenPlayerFields.has(key)),
  );
}

function stripHiddenClubFields(row) {
  return Object.fromEntries(
    Object.entries(row).filter(([key]) => !hiddenClubFields.has(key)),
  );
}

function formatMetricValue(value) {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return String(value);
  }
  return Number.isInteger(value) ? String(value) : value.toFixed(2);
}

function formatMatchedMetrics(metrics) {
  const entries = Object.entries(metrics ?? {});
  if (!entries.length) {
    return "No matched numeric metrics";
  }

  return entries
    .map(([metric, value]) => `${metric}: ${formatMetricValue(value)}`)
    .join(" | ");
}

async function callApi(path, params = {}) {
  const url = new URL(path, window.location.origin);
  Object.entries(params).forEach(([key, value]) => {
    if (value !== null && value !== undefined && value !== "") {
      url.searchParams.set(key, value);
    }
  });

  const response = await fetch(url);
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `HTTP ${response.status}`);
  }
  return response.json();
}

document.getElementById("searchButton").addEventListener("click", async () => {
  setStatus("Searching players...");
  try {
    const data = await callApi("/api/search", {
      query: document.getElementById("searchQuery").value,
      position: document.getElementById("searchPosition").value,
      country: document.getElementById("searchCountry").value,
      limit: document.getElementById("searchLimit").value,
    });
    metaEl.textContent = `search_players returned ${data.length} row(s).`;
    const rows = data.map(stripHiddenFields);
    renderTable(rows);
    setStatus("Search complete.");
  } catch (err) {
    setStatus(`Search failed: ${err.message}`, "bad");
  }
});

document.getElementById("rankButton").addEventListener("click", async () => {
  setStatus("Ranking players...");
  try {
    const data = await callApi("/api/rank", {
      prompt: document.getElementById("rankPrompt").value,
      position: document.getElementById("rankPosition").value,
      country: document.getElementById("rankCountry").value,
      limit: document.getElementById("rankLimit").value,
    });

    const rows = data.map((entry) => ({
      requested_metrics: entry.requested_metrics.join(", "),
      matched_metrics: formatMatchedMetrics(entry.matched_metrics),
      name: entry.player.name,
      club_name: entry.player.club_name,
      position: entry.player.position,
    }));

    metaEl.innerHTML = `rank_players_by_preferences returned ${rows.length} row(s). <span class="pill">ranked</span>`;
    renderTable(rows);
    setStatus("Ranking complete.");
  } catch (err) {
    setStatus(`Ranking failed: ${err.message}`, "bad");
  }
});

document.getElementById("columnsButton").addEventListener("click", async () => {
  setStatus("Loading columns...");
  try {
    const data = await callApi("/api/columns");
    metaEl.innerHTML = `list_available_columns returned ${data.length} row(s). <span class="pill">schema</span>`;
    renderTable(data);
    setStatus("Columns loaded.");
  } catch (err) {
    setStatus(`Columns failed: ${err.message}`, "bad");
  }
});

document.getElementById("clubsButton").addEventListener("click", async () => {
  setStatus("Loading clubs...");
  try {
    const data = await callApi("/api/clubs", { limit: 100 });
    metaEl.innerHTML = `list_clubs returned ${data.length} row(s). <span class="pill">clubs</span>`;
    const rows = data.map(stripHiddenClubFields);
    renderTable(rows);
    setStatus("Clubs loaded.");
  } catch (err) {
    setStatus(`Clubs failed: ${err.message}`, "bad");
  }
});
