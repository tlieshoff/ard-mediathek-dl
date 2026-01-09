(function () {

    const toastRoot = document.getElementById("toastRoot");
  function toast(message, type = "info", timeout = 3200) {
    if (!toastRoot) return;
    const el = document.createElement("div");
    el.className = `toast toast--${type}`;
    el.textContent = message;
    toastRoot.appendChild(el);
    setTimeout(() => {
      el.classList.add("toast--hide");
      setTimeout(() => el.remove(), 250);
    }, timeout);
  }


  const input = document.getElementById("searchInput");
  const clearBtn = document.getElementById("clearBtn");
  const list = document.getElementById("libraryList");
  const countEl = document.getElementById("countFiltered");

  function applyFilter() {
    if (!input || !list || !countEl) return;
    const q = (input.value || "").trim().toLowerCase();
    let shown = 0;

    for (const card of list.querySelectorAll(".card")) {
      const hay = (card.getAttribute("data-search") || "");
      const match = !q || hay.includes(q);
      card.style.display = match ? "" : "none";
      if (match) shown++;
    }
    countEl.textContent = String(shown);

    const url = new URL(window.location.href);
    if (q) url.searchParams.set("q", q);
    else url.searchParams.delete("q");
    window.history.replaceState({}, "", url.toString());
  }

  if (input && list && countEl) {
    input.addEventListener("input", applyFilter);
    if (clearBtn) {
      clearBtn.addEventListener("click", () => {
        input.value = "";
        input.focus();
        applyFilter();
      });
    }
    applyFilter();
  }


  const dlUrl = document.getElementById("dlUrl");
  const dlQuality = document.getElementById("dlQuality");
  const dlAutoBest = document.getElementById("dlAutoBest");
  const dlSubtitles = document.getElementById("dlSubtitles");
  const dlBtn = document.getElementById("dlBtn");

  async function startDownload() {
    const url = (dlUrl?.value || "").trim();
    if (!url) {
      toast("Please paste a URL first.", "warn");
      return;
    }

    const quality = dlQuality?.value || "best";
    const autoBest = !!dlAutoBest?.checked;
    const subtitles = !!dlSubtitles?.checked;

    dlBtn?.setAttribute("disabled", "disabled");

    try {
      const res = await fetch("/api/download", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url, quality, autoBest, subtitles }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Download request failed");
      }

      toast("Queued download ✅", "ok");
      await refreshJobs();



    } catch (e) {
      toast(String(e.message || e), "err", 4500);
    } finally {
      dlBtn?.removeAttribute("disabled");
    }
  }

  if (dlBtn) {
    dlBtn.addEventListener("click", startDownload);
  }
  if (dlUrl) {
    dlUrl.addEventListener("keydown", (e) => {
      if (e.key === "Enter") startDownload();
    });
  }


  const jobsList = document.getElementById("jobsList");
  let lastJobSnapshot = new Map();

  function escapeHtml(s) {
    return String(s)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function jobBadge(status) {
    const s = status || "queued";
    if (s === "done") return `<span class="badge badge--ok">done</span>`;
    if (s === "failed") return `<span class="badge badge--err">failed</span>`;
    if (s === "running") return `<span class="badge badge--run">running</span>`;
    return `<span class="badge">queued</span>`;
  }

  function renderJobs(jobs) {
    if (!jobsList) return;

    if (!jobs || jobs.length === 0) {
      jobsList.innerHTML = `<div class="emptySmall">No jobs yet.</div>`;
      return;
    }

    jobsList.innerHTML = jobs
      .slice(0, 10)
      .map((j) => {
        const pct = Math.max(0, Math.min(100, Number(j.progress || 0)));
        const logs = (j.logs || [])
          .slice(-6)
          .map((l) => `<div class="logLine">${escapeHtml(l)}</div>`)
          .join("");

        const output = j.outputPath
          ? `<div class="jobMeta"><span class="tag">output</span><code>${escapeHtml(j.outputPath)}</code></div>`
          : "";

        const err = j.error ? `<div class="jobError">${escapeHtml(j.error)}</div>` : "";

        return `
          <div class="job">
            <div class="jobTop">
              <div class="jobTitle">${escapeHtml(j.url)}</div>
              <div class="jobRight">
                ${jobBadge(j.status)}
                <span class="tag">${escapeHtml(j.quality)}</span>
              </div>
            </div>

            <div class="progress">
              <div class="progressBar" style="width:${pct}%;"></div>
            </div>

            <div class="jobMetaRow">
              <span class="tag">${pct.toFixed(0)}%</span>
              <span class="tag">${escapeHtml(String(j.status))}</span>
              ${j.subtitles ? `<span class="tag">subs</span>` : ``}
              ${j.autoBest ? `<span class="tag">auto-best</span>` : ``}
            </div>

            ${output}
            ${err}

            <div class="jobLogs">${logs || `<div class="logLine faint">…</div>`}</div>
          </div>
        `;
      })
      .join("");
  }

  async function refreshJobs() {
    const res = await fetch("/api/jobs");
    const data = await res.json();
    const jobs = data.jobs || [];


    let finishedNow = false;
    for (const j of jobs) {
      const prev = lastJobSnapshot.get(j.id);
      if (prev && prev !== "done" && j.status === "done") finishedNow = true;
      lastJobSnapshot.set(j.id, j.status);
    }

    renderJobs(jobs);

    if (finishedNow) {
      toast("Download finished 🎬 Added to library.", "ok");
      await refreshLibrary();
    }
  }

  async function refreshLibrary() {
    const q = (input?.value || "").trim();
    const res = await fetch("/api/library" + (q ? `?q=${encodeURIComponent(q)}` : ""));
    const data = await res.json();
    const items = data.items || [];

    if (!list) return;

    if (items.length === 0) {
      list.innerHTML = `
        <div class="empty">
          <div class="empty__title">No downloads found</div>
          <div class="empty__text">Use the download box on the left.</div>
        </div>
      `;
      if (countEl) countEl.textContent = "0";
      return;
    }

    list.innerHTML = items
      .map((it) => {
        const hay = `${it.title} ${it.series} ${it.date} ${it.id}`.toLowerCase();
        return `
          <article class="card" data-search="${escapeHtml(hay)}">
            <div class="card__body">
              <div class="card__title">${escapeHtml(it.title)}</div>
              <div class="card__meta">
                <span class="tag">${escapeHtml(it.series)}</span>
                <span class="tag">${escapeHtml(it.date)}</span>
                <span class="tag">${escapeHtml(it.sizeHuman)}</span>
                <span class="tag">${escapeHtml(it.mtimeHuman)}</span>
                <span class="tag">${Number(it.subtitleCount || 0)} subs</span>
              </div>
            </div>
            <div class="card__actions">
              <a class="btn" href="${escapeHtml(it.watchUrl)}">Watch</a>
            </div>
          </article>
        `;
      })
      .join("");

    if (countEl) countEl.textContent = String(items.length);
    applyFilter();
  }

  // start polling
  if (jobsList) {
    refreshJobs().catch(() => {});
    setInterval(() => refreshJobs().catch(() => {}), 1200);
  }
})();
