/* Local CSV/JSON import helpers for the standalone offline report. */
(function (root) {
  "use strict";
  const MAX_BYTES = 5 * 1024 * 1024;
  const MAX_ROWS = 5000;
  const REQUIRED = ["package_name", "name", "category", "installation_count", "average_score", "version", "last_update"];
  const COLUMNS = ["package_name", "name", "category", "sub_category", "installation_count", "average_score", "comment_count", "version", "last_update", "source"];

  function validateRecords(records) {
    if (!Array.isArray(records) || records.length > MAX_ROWS) throw new Error("حداکثر ۵۰۰۰ ردیف قابل پردازش است.");
    return records.map((record, index) => {
      if (!record || typeof record !== "object" || Array.isArray(record)) throw new Error("ساختار ردیف " + (index + 1) + " معتبر نیست.");
      for (const key of REQUIRED) {
        if (!(key in record)) throw new Error("ستون لازم در ردیف " + (index + 1) + " پیدا نشد: " + key);
      }
      const text = (key, max) => {
        const value = record[key] == null ? "" : String(record[key]).trim();
        if (value.length > max) throw new Error("مقدار یکی از ستون‌ها بیش از حد طولانی است.");
        return value;
      };
      const integer = (key) => {
        const raw = record[key] == null || record[key] === "" ? "0" : String(record[key]).trim();
        if (!/^\d+$/.test(raw) || !Number.isSafeInteger(Number(raw))) throw new Error("عدد نامعتبر در ستون " + key + "، ردیف " + (index + 1));
        return Number(raw);
      };
      const ratingRaw = record.average_score == null || record.average_score === "" ? "0" : String(record.average_score).trim();
      const rating = Number(ratingRaw);
      if (!/^(?:\d+)(?:\.\d+)?$/.test(ratingRaw) || !Number.isFinite(rating) || rating < 0 || rating > 5) {
        throw new Error("امتیاز باید عددی بین صفر و پنج باشد؛ ردیف " + (index + 1));
      }
      const packageName = text("package_name", 200);
      const name = text("name", 300);
      if (!packageName || !name) throw new Error("شناسه و نام برنامه در ردیف " + (index + 1) + " الزامی است.");
      return {
        package_name: packageName, name,
        category: text("category", 160) || "نامشخص",
        sub_category: text("sub_category", 160),
        installation_count: integer("installation_count"),
        average_score: rating,
        comment_count: integer("comment_count"),
        version: text("version", 100),
        last_update: text("last_update", 64),
        source: text("source", 64)
      };
    });
  }

  function parseCsv(source) {
    if (typeof source !== "string") throw new Error("محتوای CSV متنی نیست.");
    if (new TextEncoder().encode(source).length > MAX_BYTES) throw new Error("حجم فایل نباید از ۵ مگابایت بیشتر باشد.");
    const input = source.replace(/^\uFEFF/, "");
    const rows = [];
    let row = [], field = "", quoted = false, closedQuote = false;
    for (let i = 0; i < input.length; i++) {
      const ch = input[i];
      if (quoted) {
        if (ch === '"' && input[i + 1] === '"') { field += '"'; i++; }
        else if (ch === '"') { quoted = false; closedQuote = true; }
        else field += ch;
      } else if (closedQuote && ch !== "," && ch !== "\n" && ch !== "\r") {
        throw new Error("ساختار نقل‌قول CSV معتبر نیست.");
      } else if (ch === '"') {
        if (field !== "") throw new Error("نقل‌قول CSV در جای نامعتبر است.");
        quoted = true; closedQuote = false;
      } else if (ch === ",") {
        row.push(field); field = ""; closedQuote = false;
      } else if (ch === "\n" || ch === "\r") {
        if (ch === "\r" && input[i + 1] === "\n") i++;
        row.push(field);
        if (row.some((cell) => cell.trim() !== "")) rows.push(row);
        if (rows.length > MAX_ROWS + 1) throw new Error("حداکثر ۵۰۰۰ ردیف قابل پردازش است.");
        row = []; field = ""; closedQuote = false;
      } else {
        field += ch;
      }
    }
    if (quoted) throw new Error("یک مقدار CSV بسته نشده است.");
    row.push(field);
    if (row.some((cell) => cell.trim() !== "")) rows.push(row);
    if (!rows.length) throw new Error("فایل CSV خالی است.");
    const headers = rows.shift().map((item) => item.trim());
    if (new Set(headers).size !== headers.length) throw new Error("نام ستون تکراری است.");
    for (const key of REQUIRED) if (!headers.includes(key)) throw new Error("ستون لازم پیدا نشد: " + key);
    if (rows.length > MAX_ROWS) throw new Error("حداکثر ۵۰۰۰ ردیف قابل پردازش است.");
    const records = rows.map((cells, index) => {
      if (cells.length !== headers.length) throw new Error("تعداد خانه‌های ردیف " + (index + 2) + " با سرستون‌ها سازگار نیست.");
      const item = {};
      headers.forEach((key, column) => { if (COLUMNS.includes(key)) item[key] = cells[column]; });
      return item;
    });
    return validateRecords(records);
  }

  function parseJson(source) {
    if (typeof source !== "string") throw new Error("محتوای JSON متنی نیست.");
    if (new TextEncoder().encode(source).length > MAX_BYTES) throw new Error("حجم فایل نباید از ۵ مگابایت بیشتر باشد.");
    let value;
    try { value = JSON.parse(source); } catch (_) { throw new Error("ساختار JSON قابل خواندن نیست."); }
    const records = Array.isArray(value) ? value : value && (value.app_details || value.records);
    if (!Array.isArray(records)) throw new Error("JSON باید آرایه‌ای از ردیف‌های app_details یا records باشد.");
    return validateRecords(records);
  }

  if (typeof module !== "undefined" && module.exports) module.exports = { parseCsv, parseJson, validateRecords, MAX_BYTES, MAX_ROWS };
  root.ReportImport = { parseCsv, parseJson, validateRecords, MAX_BYTES, MAX_ROWS };
})(typeof window !== "undefined" ? window : globalThis);

/* All interactions are local DOM operations. No network calls or storage. */
(function () {
  "use strict";
  if (typeof document === "undefined") return;
  const search = document.getElementById("search");
  const category = document.getElementById("category-filter");
  const sort = document.getElementById("sort-order");
  const tbody = document.querySelector("#apps tbody");
  const results = document.getElementById("results-count");
  const empty = document.getElementById("empty");
  const reset = document.getElementById("reset-filters");
  const emptyReset = document.getElementById("empty-reset");
  const theme = document.getElementById("theme-toggle");
  const importInput = document.getElementById("local-data-file");
  const importStatus = document.getElementById("local-data-status");
  const resetData = document.getElementById("reset-local-data");
  const reportMode = document.querySelector(".report-mode");
  let categoryBars = document.querySelector(".category-bars");
  let metrics = Array.from(document.querySelectorAll(".metric-number"));
  const tableCount = document.querySelector(".table-count");
  const originalRows = Array.from(tbody.querySelectorAll("tr"));
  let activeRows = originalRows.slice();
  const originalOptions = Array.from(category.options).map((option) => option.cloneNode(true));
  const originalBars = categoryBars.cloneNode(true);
  const originalMetrics = metrics.map((node) => node.cloneNode(true));
  const originalMode = reportMode.textContent;
  const originalCount = tableCount.textContent;

  function normalize(value) {
    return String(value || "").normalize("NFKC")
      .replace(/ي/g, "ی").replace(/ك/g, "ک")
      .toLocaleLowerCase("fa-IR").trim();
  }
  function update() {
    const query = normalize(search.value);
    const selected = category.value;
    const order = sort.value;
    const rows = activeRows.slice();
    if (order === "installs") rows.sort((a, b) => Number(b.dataset.installs) - Number(a.dataset.installs));
    else if (order === "rating") rows.sort((a, b) => Number(b.dataset.rating) - Number(a.dataset.rating));
    else rows.sort((a, b) => a.dataset.name.localeCompare(b.dataset.name, "fa"));
    let visible = 0;
    for (const row of rows) {
      const matchesText = !query || normalize(row.dataset.search).includes(query);
      const matchesCategory = !selected || row.dataset.category === selected;
      row.hidden = !(matchesText && matchesCategory);
      if (!row.hidden) visible++;
      tbody.appendChild(row);
    }
    empty.hidden = visible !== 0;
    results.textContent = visible.toLocaleString("fa-IR") + " نتیجه از " + activeRows.length.toLocaleString("fa-IR") + " برنامه";
  }
  function clearFilters() {
    search.value = ""; category.value = ""; sort.value = "name"; update(); search.focus();
  }
  function textCell(value, className, dir) {
    const cell = document.createElement("td");
    cell.textContent = value;
    if (className) cell.className = className;
    if (dir) cell.dir = dir;
    return cell;
  }
  function renderRecord(record, index) {
    const tr = document.createElement("tr");
    tr.dataset.name = record.name;
    tr.dataset.search = [record.name, record.package_name, record.category, record.sub_category].join(" ");
    tr.dataset.category = record.category;
    tr.dataset.installs = String(record.installation_count);
    tr.dataset.rating = String(record.average_score);
    const appCell = textCell("", "app-cell");
    appCell.dataset.label = "اپلیکیشن";
    const details = document.createElement("div"); details.className = "app-details";
    const monogram = document.createElement("span"); monogram.className = "app-monogram tint-" + (index % 4);
    monogram.setAttribute("aria-hidden", "true"); monogram.textContent = record.name.slice(0, 1);
    const copy = document.createElement("span");
    const title = document.createElement("strong"); title.className = "app-title"; title.dir = "auto"; title.textContent = record.name;
    const packageName = document.createElement("small"); packageName.className = "app-package"; packageName.dir = "ltr"; packageName.textContent = record.package_name;
    copy.append(title, packageName); details.append(monogram, copy); appCell.replaceChildren(details); tr.append(appCell);
    const categoryCell = document.createElement("td"); categoryCell.dataset.label = "دسته‌بندی";
    const pill = document.createElement("span"); pill.className = "category-pill"; pill.dir = "auto"; pill.textContent = record.category;
    categoryCell.append(pill); tr.append(categoryCell);
    tr.append(textCell(record.installation_count.toLocaleString("fa-IR"), "data-num", "ltr"));
    const ratingCell = document.createElement("td"); ratingCell.dataset.label = "امتیاز";
    const ratingChip = document.createElement("span"); ratingChip.className = "rating-chip";
    const star = document.createElement("span"); star.className = "rating-star"; star.setAttribute("aria-hidden", "true"); star.textContent = "★";
    ratingChip.append(star, document.createTextNode(record.average_score ? record.average_score.toFixed(1) : "—"));
    ratingCell.append(ratingChip); tr.append(ratingCell);
    tr.append(textCell(record.version || "—", "data-num", "ltr"));
    tr.append(textCell(record.last_update || "—", "data-num", "ltr"));
    return tr;
  }
  function updateSummary(records) {
    const categories = new Map(); let installs = 0, score = 0, rated = 0;
    for (const record of records) {
      categories.set(record.category, (categories.get(record.category) || 0) + 1);
      installs += record.installation_count;
      if (record.average_score > 0) { score += record.average_score; rated++; }
    }
    metrics[0].textContent = records.length.toLocaleString("fa-IR");
    metrics[1].textContent = categories.size.toLocaleString("fa-IR");
    metrics[2].textContent = installs.toLocaleString("fa-IR");
    metrics[3].replaceChildren(document.createTextNode((rated ? score / rated : 0).toFixed(1) + " "));
    const small = document.createElement("small"); small.textContent = "/ ۵"; metrics[3].append(small);
    tableCount.textContent = records.length.toLocaleString("fa-IR") + " برنامه";
    categoryBars.replaceChildren();
    const sorted = Array.from(categories.entries()).sort((a, b) => b[1] - a[1]).slice(0, 5);
    for (const [label, count] of sorted) {
      const percent = records.length ? Math.round(100 * count / records.length) : 0;
      const item = document.createElement("div"); item.className = "category-row";
      const info = document.createElement("div"); info.className = "bar-info";
      const name = document.createElement("span"); name.dir = "auto"; name.textContent = label;
      const amount = document.createElement("span"); amount.textContent = count.toLocaleString("fa-IR") + " برنامه · " + percent.toLocaleString("fa-IR") + "٪";
      info.append(name, amount);
      const track = document.createElement("div"); track.className = "bar-track"; track.setAttribute("role", "meter");
      track.setAttribute("aria-label", label); track.setAttribute("aria-valuemin", "0"); track.setAttribute("aria-valuemax", "100"); track.setAttribute("aria-valuenow", String(percent));
      const fill = document.createElement("div"); fill.className = "bar-fill"; fill.style.setProperty("--bar", percent + "%");
      track.append(fill); item.append(info, track); categoryBars.append(item);
    }
    if (!sorted.length) { const note = document.createElement("p"); note.className = "section-helper"; note.textContent = "هیچ ردیفی در فایل نیست."; categoryBars.append(note); }
  }
  function applyRecords(records) {
    activeRows = records.map(renderRecord); tbody.replaceChildren(...activeRows);
    const options = [originalOptions[0]];
    for (const name of Array.from(new Set(records.map((record) => record.category))).sort((a, b) => a.localeCompare(b, "fa"))) {
      const option = document.createElement("option"); option.value = name; option.textContent = name; options.push(option);
    }
    category.replaceChildren(...options); updateSummary(records);
    reportMode.textContent = "فایل محلی شما · بدون بارگذاری";
    importStatus.textContent = records.length.toLocaleString("fa-IR") + " ردیف فقط در این زبانه پردازش شد.";
    resetData.disabled = false; clearFilters();
  }
  function restoreReport() {
    activeRows = originalRows.slice(); tbody.replaceChildren(...originalRows);
    category.replaceChildren(...originalOptions.map((option) => option.cloneNode(true)));
    categoryBars.replaceWith(originalBars.cloneNode(true)); categoryBars = document.querySelector(".category-bars");
    originalMetrics.forEach((metric, index) => metrics[index].replaceWith(metric.cloneNode(true)));
    metrics = Array.from(document.querySelectorAll(".metric-number"));
    reportMode.textContent = originalMode; tableCount.textContent = originalCount;
    resetData.disabled = true; importInput.value = "";
    importStatus.textContent = "گزارش اصلی بازیابی شد؛ هیچ فایلی ذخیره نشده است.";
    clearFilters();
  }
  importInput.addEventListener("change", async function () {
    const file = importInput.files && importInput.files[0]; if (!file) return;
    if (file.size > window.ReportImport.MAX_BYTES) { importStatus.textContent = "حجم فایل نباید از ۵ مگابایت بیشتر باشد."; importInput.value = ""; return; }
    importStatus.textContent = "در حال خواندن فایل روی همین دستگاه…";
    try {
      const source = await file.text();
      const extension = file.name.toLowerCase().split(".").pop();
      const records = extension === "json" ? window.ReportImport.parseJson(source) :
        extension === "csv" ? window.ReportImport.parseCsv(source) : (() => { throw new Error("فقط فایل CSV یا JSON پذیرفته می‌شود."); })();
      applyRecords(records);
    } catch (error) {
      importStatus.textContent = error instanceof Error ? error.message : "فایل قابل پردازش نیست.";
    } finally { importInput.value = ""; }
  });
  resetData.addEventListener("click", restoreReport);
  search.addEventListener("input", update); category.addEventListener("change", update); sort.addEventListener("change", update);
  reset.addEventListener("click", clearFilters); emptyReset.addEventListener("click", clearFilters);
  theme.addEventListener("click", function () {
    const dark = document.documentElement.getAttribute("data-theme") !== "dark";
    if (dark) document.documentElement.setAttribute("data-theme", "dark"); else document.documentElement.removeAttribute("data-theme");
    theme.setAttribute("aria-pressed", String(dark)); theme.title = dark ? "نمای روشن" : "نمای تیره";
  });
  document.addEventListener("keydown", function (event) {
    if (event.key !== "/" || event.ctrlKey || event.altKey || event.metaKey || event.target.closest("input,textarea,select,[contenteditable]")) return;
    event.preventDefault(); search.focus();
  });
  update();
})();
