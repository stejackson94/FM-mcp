const statusEl = document.getElementById("status");
const metaEl = document.getElementById("meta");
const tableWrapEl = document.getElementById("tableWrap");
const dataSourceEl = document.getElementById("dataSource");
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

function normalizeColumnLabel(columnName) {
  return String(columnName)
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "");
}

function renderTable(rows) {
  if (!rows.length) {
    tableWrapEl.innerHTML = "<p>No results.</p>";
    return;
  }

  const columns = Object.keys(rows[0]);
  const head = columns.map((c) => `<th>${escapeHtml(normalizeColumnLabel(c))}</th>`).join("");
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

function rankBadge(index) {
  if (index === 0) {
    return "🥇";
  }
  if (index === 1) {
    return "🥈";
  }
  if (index === 2) {
    return "🥉";
  }
  return "🎯";
}

function rankHeadline(index) {
  if (index === 0) {
    return "Best fit overall";
  }
  if (index === 1) {
    return "Best pure profile";
  }
  if (index === 2) {
    return "Safe option";
  }
  return "Strong alternative";
}

function renderRankCards(entries) {
  if (!entries.length) {
    tableWrapEl.innerHTML = "<p>No ranked matches.</p>";
    return;
  }

  const cards = entries
    .map((entry, index) => {
      const explanation = normalizeExplanation(entry, index, entries.length);
      const player = entry.player ?? {};
      const meta = buildPlayerMeta(player);
      const minutes = entry?.player?.metrics?.Mins;
      const minutesLabel = (minutes !== undefined && minutes !== null && String(minutes).trim() !== "")
        ? String(minutes)
        : "Not listed";
      const explanationSource = explanation.source || "unknown";
      return `
        <article class="rank-card">
          <h3>${rankBadge(index)} ${escapeHtml(rankHeadline(index))}: ${escapeHtml(entry.player.name)}</h3>
          <p class="rank-card-meta">${meta}</p>
          <p class="rank-card-meta"><strong>Minutes:</strong> ${escapeHtml(minutesLabel)}</p>
          <section class="rank-card-section">
            <strong>Matched Metrics</strong>
            <div class="metric-list">${renderMatchedMetrics(entry.matched_metrics)}</div>
          </section>
          <section class="rank-card-section">
            <strong>Why He Fits</strong>
            <div class="rank-card-copy">${formatNarrative(explanation.whyFit)}</div>
          </section>
          <section class="rank-card-section">
            <strong>Role Use</strong>
            <div class="rank-card-copy">${formatNarrative(explanation.tacticalUse)}</div>
          </section>
          <section class="rank-card-section">
            <strong>Risk</strong>
            <div class="rank-card-copy">${formatNarrative(explanation.caveat)}</div>
          </section>
          <p class="rank-card-source"><strong>Explanation source:</strong> ${escapeHtml(explanationSource)}</p>
        </article>
      `;
    })
    .join("");

  tableWrapEl.innerHTML = `<section class="rank-cards">${cards}</section>`;
}

function rankedTableRows(entries) {
  return entries.map((entry, index) => {
    const explanation = normalizeExplanation(entry, index, entries.length);
    const minutes = entry?.player?.metrics?.Mins;
    const minutesLabel =
      minutes !== undefined && minutes !== null && String(minutes).trim() !== ""
        ? String(minutes)
        : "unknown";
    return {
      name: entry.player.name,
      club_name: entry.player.club_name,
      position: entry.player.position,
      minutes: minutesLabel,
      matched_metrics: formatMatchedMetrics(entry.matched_metrics),
      why_he_fits: explanation.whyFit,
      tactical_use: explanation.tacticalUse,
      caveat: explanation.caveat,
      explanation_source: explanation.source,
    };
  });
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
    .join(", ");
}

function normalizePlayerText(value) {
  const text = String(value ?? "").trim();
  if (!text || text === "-" || text.toLowerCase() === "unknown") {
    return "";
  }
  return text;
}

function buildPlayerMeta(player) {
  const clubName = normalizePlayerText(player?.club_name);
  const position = normalizePlayerText(player?.position);
  const nationality = normalizePlayerText(player?.nationality);
  const parts = [];

  if (clubName) {
    parts.push(`<strong>Club:</strong> ${escapeHtml(clubName)}`);
  }
  if (position) {
    parts.push(`<strong>Position:</strong> ${escapeHtml(position)}`);
  }
  if (nationality) {
    parts.push(`<strong>Nation:</strong> ${escapeHtml(nationality)}`);
  }

  return parts.join("<span class=\"rank-card-dot\">•</span>") || "<strong>Player context:</strong> Not listed";
}

function renderMatchedMetrics(metrics) {
  const entries = Object.entries(metrics ?? {});
  if (!entries.length) {
    return '<span class="metric-chip metric-chip-empty">No matched numeric metrics</span>';
  }

  return entries
    .map(([metric, value]) => (`
      <span class="metric-chip">
        <span class="metric-chip-label">${escapeHtml(metric)}</span>
        <span class="metric-chip-value">${escapeHtml(formatMetricValue(value))}</span>
      </span>
    `).trim())
    .join("");
}

function formatNarrative(text) {
  return escapeHtml(text).replaceAll("\n", "<br>");
}

function getTopMatchedMetrics(metrics, count = 2) {
  return Object.entries(metrics ?? {})
    .filter(([, value]) => typeof value === "number" && !Number.isNaN(value))
    .sort((a, b) => b[1] - a[1])
    .slice(0, count)
    .map(([metric, value]) => `${metric} (${formatMetricValue(value)})`);
}

function scoreBand(score) {
  if (typeof score !== "number" || Number.isNaN(score)) {
    return "solid";
  }
  if (score >= 0.75) {
    return "elite";
  }
  if (score >= 0.55) {
    return "strong";
  }
  if (score >= 0.4) {
    return "balanced";
  }
  return "situational";
}

function buildWhyFit(entry, index, total) {
  const topMetrics = getTopMatchedMetrics(entry.matched_metrics, 2);
  const profile = scoreBand(entry.score);
  const playerName = normalizePlayerText(entry.player?.name) || "This player";
  const position = normalizePlayerText(entry.player?.position) || "multiple roles";
  const clubName = normalizePlayerText(entry.player?.club_name);
  const nationality = normalizePlayerText(entry.player?.nationality);
  const context = [nationality && clubName ? `${nationality} at ${clubName}` : nationality || clubName, position]
    .filter(Boolean)
    .join(", ") || "Limited club context in this export";

  const opener =
    index === 0
      ? `${playerName} is the strongest match in this result set`
      : `${playerName} ranks #${index + 1} of ${total}`;

  const metricSummary = topMetrics.length
    ? `${topMetrics.join(" and ")} are the clearest indicators for this brief.`
    : "The export shows a workable profile, but with limited numeric evidence in this result.";

  const whyFit = `${opener}.
- Profile: ${context}.
- Evidence: ${metricSummary}
- System fit: ${profile.charAt(0).toUpperCase()}${profile.slice(1)} match for the requested role.`;

  let caveat = "Caveat: Review full attributes and role familiarity before signing.";
  if (profile === "situational") {
    caveat = "Caveat: More of a specialist option for narrower tactical setups.";
  } else if (position.includes(",")) {
    caveat = "Caveat: Versatile profile may be less role-pure than a specialist.";
  }

  const tacticalUse = `- Usage: play as ${position} in a role that maximizes ${topMetrics[0] || "the top matched metric"} while giving him repeatable actions in his strongest phases.`;

  return { whyFit, caveat, tacticalUse };
}

function normalizeExplanation(entry, index, total) {
  const serverExplanation = entry.explanation;
  if (
    serverExplanation
    && typeof serverExplanation.why_fit === "string"
    && typeof serverExplanation.caveat === "string"
    && typeof serverExplanation.tactical_use === "string"
  ) {
    return {
      whyFit: serverExplanation.why_fit,
      caveat: serverExplanation.caveat,
      tacticalUse: serverExplanation.tactical_use,
      source: serverExplanation.source || "server",
    };
  }

  const fallback = buildWhyFit(entry, index, total);
  return {
    whyFit: fallback.whyFit,
    caveat: fallback.caveat,
    tacticalUse: fallback.tacticalUse,
    source: "local",
  };
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

async function postJson(path) {
  const response = await fetch(path, { method: "POST" });
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `HTTP ${response.status}`);
  }
  return response.json();
}

async function refreshDataSource() {
  try {
    const data = await callApi("/api/data-status");
    if (data.mode === "uploaded") {
      const names = (data.uploaded_files ?? []).join(", ") || "uploaded.html";
      dataSourceEl.textContent = `Data source: uploaded file (${names}) - ${data.player_count} players loaded.`;
      return;
    }

    dataSourceEl.textContent = `Data source: default input_data folder - ${data.player_count} players loaded.`;
  } catch (err) {
    dataSourceEl.textContent = `Data source: unavailable (${err.message})`;
  }
}

document.getElementById("rankButton").addEventListener("click", async () => {
  setStatus("Ranking players...");
  tableWrapEl.innerHTML = "";
  metaEl.innerHTML = "Preparing new ranking...";
  try {
    const data = await callApi("/api/rank", {
      prompt: document.getElementById("rankPrompt").value,
      formation: document.getElementById("rankFormation").value,
      min_minutes: document.getElementById("rankMinMinutes").value,
      limit: document.getElementById("rankLimit").value,
    });
    const viewMode = document.getElementById("rankViewMode").value;

    if (viewMode === "table") {
      metaEl.innerHTML = `rank_players_by_preferences returned ${data.length} row(s). <span class="pill">table</span>`;
      renderTable(rankedTableRows(data));
    } else {
      metaEl.innerHTML = `rank_players_by_preferences returned ${data.length} row(s). <span class="pill">cards</span>`;
      renderRankCards(data);
    }
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

document.getElementById("uploadButton").addEventListener("click", async () => {
  const fileInput = document.getElementById("uploadFile");
  const selectedFile = fileInput.files[0];
  if (!selectedFile) {
    setStatus("Please choose an HTML file first.", "bad");
    return;
  }

  setStatus("Uploading and validating file...");
  try {
    const formData = new FormData();
    formData.append("file", selectedFile);

    const response = await fetch("/api/upload", {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const message = await response.text();
      throw new Error(message || `HTTP ${response.status}`);
    }

    const data = await response.json();
    fileInput.value = "";
    metaEl.innerHTML = `Upload complete. ${data.player_count} player(s) loaded from uploaded HTML. <span class="pill">uploaded</span>`;
    tableWrapEl.innerHTML = "";
    await refreshDataSource();
    setStatus("Upload complete.");
  } catch (err) {
    setStatus(`Upload failed: ${err.message}`, "bad");
  }
});

document.getElementById("clearDataButton").addEventListener("click", async () => {
  setStatus("Clearing uploaded data...");
  try {
    const data = await postJson("/api/clear-data");
    metaEl.innerHTML = `Clear data complete. Removed ${data.removed_files} uploaded file(s). <span class="pill">reset</span>`;
    tableWrapEl.innerHTML = "";
    await refreshDataSource();
    setStatus("Uploaded data cleared.");
  } catch (err) {
    setStatus(`Clear data failed: ${err.message}`, "bad");
  }
});

void refreshDataSource();
