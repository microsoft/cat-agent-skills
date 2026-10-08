import { CATEGORY_LABELS, isCategory } from "./categories";
import {
  copyGalleryFilters, countPlatforms, galleryFilterParams, matchesFilters, parseGalleryFilters,
  type FilterableSubmission, type GalleryFilters,
} from "./gallery-filters";

const SORTS = ["featured", "rating", "downloads", "name", "newest"] as const;
type SortMode = (typeof SORTS)[number];
type Refinement = "platform" | "type" | "tags" | "authors";
const FORMAT_LABELS: Record<string, string> = { skill: "Skills", plugin: "Plugins", automation: "Automations" };
const BATCH = 12;

export function initGalleryBrowser(root: HTMLElement) {
  function get<T extends Element>(selector: string): T {
    const element = root.querySelector<T>(selector);
    if (!element) throw new Error(`Missing gallery element: ${selector}`);
    return element;
  }
  const microsoftOnly = root.dataset.scope === "microsoft";
  const gallery = get<HTMLElement>("#gallery");
  const items = Array.from(gallery.querySelectorAll<HTMLElement>(".submission-item"));
  const preview = root.querySelector<HTMLElement>("#microsoft-preview-grid");
  const previewItems = Array.from(preview?.querySelectorAll<HTMLElement>(".submission-item") ?? []);
  const allItems = [...previewItems, ...items];
  const data = new Map<HTMLElement, FilterableSubmission>(allItems.map((element) => {
    const d = element.dataset;
    const category = d.category ?? "";
    return [element, {
      name: d.name ?? "", description: d.desc ?? "",
      tags: (d.tags ?? "").split(",").filter(Boolean),
      platforms: (d.platforms ?? "").split(",").filter(Boolean),
      type: d.type ?? "skill", category: isCategory(category) ? category : "productivity",
      builtByMicrosoft: d.builtByMicrosoft === "1",
      authorName: d.authorName ?? "", authorLogin: d.authorLogin ?? "", authorKey: d.authorKey ?? "",
    }];
  }));
  const authorNames = new Map([...data.values()].map((item) => [item.authorKey, item.authorName]));
  const search = get<HTMLInputElement>("#skill-search");
  const categoryOptions = get<HTMLElement>("#category-filters");
  const categories = Array.from(root.querySelectorAll<HTMLButtonElement>("button[data-category]"));
  const sortSelect = get<HTMLSelectElement>("#sort-select");
  const count = get<HTMLElement>("#result-count");
  const empty = get<HTMLElement>("#empty-state");
  const status = get<HTMLElement>("#filter-status");
  const sentinel = get<HTMLElement>("#scroll-sentinel");
  const showMore = root.querySelector<HTMLAnchorElement>("[data-show-more]");
  const back = root.querySelector<HTMLAnchorElement>("[data-gallery-back]");
  const filtersTrigger = get<HTMLButtonElement>("#filters-trigger");
  const filterCount = get<HTMLElement>("#filters-count");
  const dialog = get<HTMLDialogElement>("#filters-dialog");
  const closeFilters = get<HTMLButtonElement>("[data-close-filters]");
  const dialogBody = get<HTMLElement>(".dialog-body");
  const draftChips = get<HTMLElement>("#draft-selections");
  const apply = get<HTMLButtonElement>("#apply-filters");
  const platformInputs = Array.from(dialog.querySelectorAll<HTMLInputElement>('input[name="filter-platform"]'));
  const typeInputs = Array.from(dialog.querySelectorAll<HTMLInputElement>('input[name="filter-type"]'));
  const tagInputs = Array.from(dialog.querySelectorAll<HTMLInputElement>('input[name="filter-tag"]'));
  const authorInputs = Array.from(dialog.querySelectorAll<HTMLInputElement>('input[name="filter-author"]'));
  const tagSearch = get<HTMLInputElement>("#filter-tag-search");
  const authorSearch = get<HTMLInputElement>("#filter-author-search");
  const tagOptions = Array.from(dialog.querySelectorAll<HTMLElement>("[data-tag-option]"));
  const authorOptions = Array.from(dialog.querySelectorAll<HTMLElement>("[data-author-option]"));

  let applied = copyGalleryFilters(parseGalleryFilters(new URLSearchParams(location.search)));
  let draft = copyGalleryFilters(applied);
  let sortMode: SortMode = "featured";
  let shown = BATCH;
  let matched: HTMLElement[] = [];
  let previewMatched: HTMLElement[] = [];
  let searchTimer = 0;
  let savedOverflow = "";
  let savedGutter = "";

  function queryString() {
    const params = galleryFilterParams(applied);
    if (sortMode !== "featured") params.set("sort", sortMode);
    const query = params.toString();
    return query ? `?${query}` : "";
  }

  function updateLinks() {
    for (const link of [showMore, back]) {
      if (link) link.href = `${link.dataset.destination}${queryString()}`;
    }
  }

  function syncUrl() {
    history.replaceState(null, "", `${location.pathname}${queryString()}`);
  }

  const number = (element: HTMLElement, key: string) => Number(element.dataset[key] ?? "0") || 0;
  function sorted(list: HTMLElement[]) {
    const byName = (a: HTMLElement, b: HTMLElement) => (a.dataset.name ?? "").localeCompare(b.dataset.name ?? "");
    const field = { featured: "featured", rating: "rating", downloads: "downloads", newest: "updated", name: "" }[sortMode];
    return [...list].sort((a, b) =>
      number(a, "sample") - number(b, "sample") || (field ? number(b, field) - number(a, field) : 0) || byName(a, b),
    );
  }

  function renderGrid() {
    items.forEach((element) => { element.hidden = true; });
    matched.slice(0, shown).forEach((element) => { element.hidden = false; });
    count.textContent = `(${matched.length})`;
    empty.hidden = matched.length > 0;
  }

  function fill() {
    while (shown < matched.length) {
      const bounds = sentinel.getBoundingClientRect();
      if (bounds.top > innerHeight + 400 || bounds.bottom < 0) break;
      shown = Math.min(shown + BATCH, matched.length);
      renderGrid();
    }
  }

  function renderPreview() {
    if (!preview) return;
    previewItems.forEach((element) => { element.hidden = true; });
    preview.hidden = previewMatched.length === 0;
    get<HTMLElement>("#microsoft-empty").hidden = previewMatched.length > 0;
    get<HTMLElement>("#microsoft-count").textContent = `(${previewMatched.length})`;
    let columns = 0;
    if (previewMatched.length) {
      // Both grids use the same auto-fill tracks, including at intermediate widths.
      columns = getComputedStyle(preview).gridTemplateColumns.split(/\s+/).length;
      previewMatched.slice(0, columns).forEach((element) => { element.hidden = false; });
    }
    if (showMore) {
      showMore.hidden = previewMatched.length <= columns;
      showMore.setAttribute("aria-label", `Show all ${previewMatched.length} Microsoft submissions`);
    }
  }

  function removeRefinement(filters: ReturnType<typeof copyGalleryFilters>, field: Refinement, value: string) {
    if (field === "tags" || field === "authors") filters[field].delete(value);
    else filters[field] = "";
  }

  function renderRefinements(container: HTMLElement, filters: GalleryFilters, remove: (field: Refinement, value: string) => void) {
    const values: { field: Refinement; value: string; label: string }[] = [];
    if (filters.platform) values.push({ field: "platform", value: filters.platform, label: filters.platform });
    if (filters.type) values.push({ field: "type", value: filters.type, label: FORMAT_LABELS[filters.type] ?? filters.type });
    filters.tags.forEach((tag) => values.push({ field: "tags", value: tag, label: tag }));
    filters.authors.forEach((author) => values.push({ field: "authors", value: author, label: authorNames.get(author) ?? author }));
    container.replaceChildren();
    for (const { field, value, label } of values) {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "inline-flex max-w-full items-center gap-2 rounded-full border border-border bg-surface-2 px-3 py-1.5 text-sm text-fg focus-visible:outline-2 focus-visible:outline-accent";
      button.setAttribute("aria-label", `Remove ${field === "authors" ? "contributor" : field} filter: ${label}`);
      const text = document.createElement("span");
      text.className = "truncate";
      text.textContent = label;
      const cross = document.createElement("span");
      cross.textContent = "\u00d7";
      cross.setAttribute("aria-hidden", "true");
      button.append(text, cross);
      button.addEventListener("click", () => remove(field, value));
      container.append(button);
    }
    return values.length;
  }

  function paintApplied() {
    categories.forEach((button) => button.setAttribute("aria-pressed", String(button.dataset.category === applied.category)));
    const total = Number(Boolean(applied.platform)) + Number(Boolean(applied.type)) + applied.tags.size + applied.authors.size;
    filterCount.hidden = total === 0;
    filterCount.textContent = String(total);
    filtersTrigger.setAttribute("aria-label", total ? `Filters, ${total} active ${total === 1 ? "filter" : "filters"}` : "Filters");
    revealSelectedCategory();
  }

  function revealSelectedCategory() {
    const selected = categories.find((button) => button.getAttribute("aria-pressed") === "true");
    if (selected) revealCategory(selected);
  }

  function revealCategory(button: HTMLButtonElement) {
    const bounds = categoryOptions.getBoundingClientRect();
    const chip = button.getBoundingClientRect();
    // Only move the category strip, never the page's vertical scroll position.
    const offset = chip.left < bounds.left + 4
      ? chip.left - bounds.left - 4
      : Math.max(0, chip.right - bounds.right + 4);
    if (offset) categoryOptions.scrollBy({ left: offset, behavior: "instant" });
  }

  function refilter() {
    matched = sorted(items.filter((item) => matchesFilters(data.get(item)!, applied)));
    previewMatched = previewItems.filter((item) => matchesFilters(data.get(item)!, applied));
    const matchingSet = new Set(matched);
    gallery.append(...matched, ...items.filter((item) => !matchingSet.has(item)));
    shown = BATCH;
    renderGrid();
    renderPreview();
    fill();
    status.textContent = microsoftOnly
      ? `${matched.length} Microsoft submissions match.`
      : `${previewMatched.length} Microsoft and ${matched.length} community submissions match.`;
    paintApplied();
    updateLinks();
  }

  function commit() {
    syncUrl();
    refilter();
  }

  function flushSearch() {
    clearTimeout(searchTimer);
    applied.query = search.value.toLowerCase();
  }

  function filterPicker(options: HTMLElement[], query: string, key: "tagOption" | "authorSearch", emptyMessage: HTMLElement) {
    const term = query.trim().toLowerCase();
    options.forEach((option) => { option.hidden = !(option.dataset[key] ?? "").toLowerCase().includes(term); });
    emptyMessage.hidden = options.some((option) => !option.hidden);
  }

  function paintDraft() {
    platformInputs.forEach((input) => { input.checked = input.value === draft.platform; });
    typeInputs.forEach((input) => { input.checked = input.value === draft.type; });
    tagInputs.forEach((input) => { input.checked = draft.tags.has(input.value); });
    authorInputs.forEach((input) => { input.checked = draft.authors.has(input.value); });
    const platformCounts = countPlatforms(data.values(), draft);
    dialog.querySelectorAll<HTMLElement>("[data-platform-count]").forEach((element) => {
      element.textContent = String(platformCounts.get(element.dataset.platformCount ?? "") ?? 0);
    });
    for (const field of ["tags", "authors"] as const) {
      get<HTMLElement>(`[data-selection-count="${field}"]`).textContent = draft[field].size ? `(${draft[field].size} selected)` : "";
    }
    const draftCount = [...data.values()].filter((item) => matchesFilters(item, draft)).length;
    apply.textContent = `Show ${draftCount} ${microsoftOnly ? "Microsoft results" : "results"}`;
    get<HTMLElement>("#draft-filter-status").textContent = `${draftCount} ${microsoftOnly ? "Microsoft" : "total"} submissions match these filters.`;
    const selections = renderRefinements(draftChips, draft, (field, value) => {
      removeRefinement(draft, field, value);
      paintDraft();
      closeFilters.focus({ preventScroll: true });
    });
    draftChips.hidden = selections === 0;
  }

  function openFilters() {
    const previousQuery = applied.query;
    flushSearch();
    if (applied.query !== previousQuery) commit();
    draft = copyGalleryFilters(applied);
    tagSearch.value = authorSearch.value = "";
    filterPicker(tagOptions, "", "tagOption", get("#tag-search-empty"));
    filterPicker(authorOptions, "", "authorSearch", get("#author-search-empty"));
    get<HTMLElement>("#filters-context").textContent = [
      applied.category ? CATEGORY_LABELS[applied.category] : "All categories",
      applied.query ? `Search: ${search.value}` : "",
    ].filter(Boolean).join(" \u00b7 ");
    paintDraft();
    savedOverflow = document.documentElement.style.overflow;
    savedGutter = document.documentElement.style.scrollbarGutter;
    document.documentElement.style.scrollbarGutter = "stable";
    document.documentElement.style.overflow = "hidden";
    dialog.showModal();
    dialogBody.scrollTop = 0;
    filtersTrigger.setAttribute("aria-expanded", "true");
  }

  filtersTrigger.addEventListener("click", openFilters);
  closeFilters.addEventListener("click", () => dialog.close());
  dialog.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      event.preventDefault();
      dialog.close();
      return;
    }
    if (event.key !== "Tab") return;
    if (event.shiftKey && event.target === closeFilters) {
      event.preventDefault();
      apply.focus();
    } else if (!event.shiftKey && event.target === apply) {
      event.preventDefault();
      closeFilters.focus();
    }
  });
  dialog.addEventListener("cancel", (event) => { event.preventDefault(); dialog.close(); });
  dialog.addEventListener("click", (event) => {
    if (event.target !== dialog) return;
    const r = dialog.getBoundingClientRect();
    if (event.clientX < r.left || event.clientX > r.right || event.clientY < r.top || event.clientY > r.bottom) dialog.close();
  });
  dialog.addEventListener("close", () => {
    draft = copyGalleryFilters(applied);
    document.documentElement.style.overflow = savedOverflow;
    document.documentElement.style.scrollbarGutter = savedGutter;
    filtersTrigger.setAttribute("aria-expanded", "false");
    filtersTrigger.focus({ preventScroll: true });
  });
  apply.addEventListener("click", () => {
    applied = copyGalleryFilters(draft);
    commit();
    dialog.close();
  });
  get<HTMLButtonElement>("#clear-extra-filters").addEventListener("click", () => {
    draft.platform = draft.type = "";
    draft.tags.clear();
    draft.authors.clear();
    paintDraft();
  });
  dialog.addEventListener("change", (event) => {
    const input = event.target;
    if (!(input instanceof HTMLInputElement)) return;
    switch (input.name) {
      case "filter-platform": draft.platform = input.value; break;
      case "filter-type": draft.type = input.value; break;
      case "filter-tag": input.checked ? draft.tags.add(input.value) : draft.tags.delete(input.value); break;
      case "filter-author": input.checked ? draft.authors.add(input.value) : draft.authors.delete(input.value); break;
      default: return;
    }
    paintDraft();
  });
  tagSearch.addEventListener("input", () => filterPicker(tagOptions, tagSearch.value, "tagOption", get("#tag-search-empty")));
  authorSearch.addEventListener("input", () => filterPicker(authorOptions, authorSearch.value, "authorSearch", get("#author-search-empty")));

  search.addEventListener("input", () => {
    clearTimeout(searchTimer);
    searchTimer = window.setTimeout(() => { flushSearch(); commit(); }, 120);
  });
  categories.forEach((button) => {
    button.addEventListener("focus", () => {
      if (button.matches(":focus-visible")) revealCategory(button);
    });
    button.addEventListener("click", () => {
      flushSearch();
      const category = button.dataset.category ?? "";
      applied.category = isCategory(category) ? category : "";
      commit();
    });
  });
  root.querySelectorAll<HTMLButtonElement>("[data-clear-filters]").forEach((button) => button.addEventListener("click", () => {
    clearTimeout(searchTimer);
    applied = copyGalleryFilters(parseGalleryFilters(new URLSearchParams()));
    search.value = "";
    commit();
    search.focus({ preventScroll: true });
  }));
  sortSelect.addEventListener("change", () => {
    const selected = SORTS.find((sort) => sort === sortSelect.value);
    if (!selected) throw new Error(`Unknown gallery sort: ${sortSelect.value}`);
    sortMode = selected;
    flushSearch();
    commit();
  });

  const observer = new IntersectionObserver((entries) => {
    if (entries.some((entry) => entry.isIntersecting)) fill();
  }, { rootMargin: "400px" });
  observer.observe(sentinel);
  if (preview) new ResizeObserver(renderPreview).observe(preview);
  new ResizeObserver(revealSelectedCategory).observe(categoryOptions);
  document.fonts.ready.then(renderPreview);
  document.fonts.ready.then(revealSelectedCategory);

  function initFromUrl() {
    clearTimeout(searchTimer);
    const params = new URLSearchParams(location.search);
    applied = copyGalleryFilters(parseGalleryFilters(params));
    draft = copyGalleryFilters(applied);
    sortMode = SORTS.find((sort) => sort === params.get("sort")) ?? "featured";
    sortSelect.value = sortMode;
    search.value = applied.query;
    refilter();
  }

  // Each route/query keeps its own position; Microsoft visits must not replace home history.
  const scrollKey = () => `gallery-scroll:${location.pathname}${location.search}`;
  function saveScroll() {
    try {
      sessionStorage.setItem(scrollKey(), JSON.stringify({ shown, y: scrollY }));
    } catch (error) {
      console.warn("Could not save gallery position.", error);
    }
  }
  function restoreScroll() {
    try {
      const value: unknown = JSON.parse(sessionStorage.getItem(scrollKey()) ?? "null");
      if (value === null) return;
      if (typeof value !== "object" || !("shown" in value) || !("y" in value)
        || typeof value.shown !== "number" || typeof value.y !== "number"
        || !Number.isFinite(value.shown) || !Number.isFinite(value.y)) {
        console.warn("Ignoring invalid saved gallery position.");
        return;
      }
      shown = Math.min(Math.max(shown, value.shown), matched.length);
      renderGrid();
      window.scrollTo({ top: Math.max(0, value.y), behavior: "instant" });
    } catch (error) {
      console.warn("Could not restore gallery position.", error);
    }
  }
  history.scrollRestoration = "manual";
  initFromUrl();
  const navigation = performance.getEntriesByType("navigation")[0];
  if (navigation instanceof PerformanceNavigationTiming && ["back_forward", "reload"].includes(navigation.type)) restoreScroll();
  window.addEventListener("pageshow", (event) => {
    if (!event.persisted) return;
    if (dialog.open) dialog.close();
    initFromUrl();
    restoreScroll();
  });
  window.addEventListener("pagehide", saveScroll);
  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "hidden") saveScroll();
  });
}
