/* All interactions are local DOM operations. No network calls or storage. */
(function () {
  "use strict";
  const search = document.getElementById("search");
  const category = document.getElementById("category-filter");
  const sort = document.getElementById("sort-order");
  const tbody = document.querySelector("#apps tbody");
  const results = document.getElementById("results-count");
  const empty = document.getElementById("empty");
  const reset = document.getElementById("reset-filters");
  const emptyReset = document.getElementById("empty-reset");
  const theme = document.getElementById("theme-toggle");
  const originalRows = Array.from(tbody.querySelectorAll("tr"));

  function normalize(value) {
    return String(value || "").normalize("NFKC")
      .replace(/ي/g, "ی").replace(/ك/g, "ک")
      .toLocaleLowerCase("fa-IR").trim();
  }

  function update() {
    const query = normalize(search.value);
    const selected = category.value;
    const order = sort.value;
    const rows = originalRows.slice();
    if (order === "installs") {
      rows.sort((a, b) => Number(b.dataset.installs) - Number(a.dataset.installs));
    } else if (order === "rating") {
      rows.sort((a, b) => Number(b.dataset.rating) - Number(a.dataset.rating));
    } else {
      rows.sort((a, b) => a.dataset.name.localeCompare(b.dataset.name, "fa"));
    }
    let visible = 0;
    for (const row of rows) {
      const matchesText = !query || normalize(row.dataset.search).includes(query);
      const matchesCategory = !selected || row.dataset.category === selected;
      row.hidden = !(matchesText && matchesCategory);
      if (!row.hidden) visible++;
      tbody.appendChild(row);
    }
    empty.hidden = visible !== 0;
    results.textContent = visible.toLocaleString("fa-IR") + " نتیجه از " +
      originalRows.length.toLocaleString("fa-IR") + " برنامه";
  }

  function clearFilters() {
    search.value = "";
    category.value = "";
    sort.value = "name";
    update();
    search.focus();
  }

  search.addEventListener("input", update);
  category.addEventListener("change", update);
  sort.addEventListener("change", update);
  reset.addEventListener("click", clearFilters);
  emptyReset.addEventListener("click", clearFilters);

  theme.addEventListener("click", function () {
    const dark = document.documentElement.getAttribute("data-theme") !== "dark";
    if (dark) document.documentElement.setAttribute("data-theme", "dark");
    else document.documentElement.removeAttribute("data-theme");
    theme.setAttribute("aria-pressed", String(dark));
    theme.title = dark ? "نمای روشن" : "نمای تیره";
  });

  document.addEventListener("keydown", function (event) {
    if (event.key !== "/" || event.ctrlKey || event.altKey || event.metaKey ||
        event.target.closest("input,textarea,select,[contenteditable]")) return;
    event.preventDefault();
    search.focus();
  });
  update();
})();
