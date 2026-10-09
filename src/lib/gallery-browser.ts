import { compareNewest, compareRecentlyUpdated } from "./gallery-sort";
import { PLATFORMS } from "./skills";
import {
  copyGalleryFilters, countFacet, FORMAT_LABELS, galleryFilterParams, matchesFilters, parseGalleryFilters,
  type FilterableSubmission, type GalleryFilters,
} from "./gallery-filters";

const SORTS = ["featured", "rating", "downloads", "name", "newest", "updated"] as const;
type SortMode = (typeof SORTS)[number];
type Refinement = "types" | "tags" | "authors";
const BATCH = 12;

export function initGalleryBrowser(root: HTMLElement) {
  function get<T extends Element>(selector: string): T {
    const element = root.querySelector<T>(selector);
    if (!element) throw new Error(`Missing gallery element: ${selector}`);
    return element;
  }
  const gallery = get<HTMLElement>("#gallery");
  const items = Array.from(gallery.querySelectorAll<HTMLElement>(".submission-item"));
  const data = new Map<HTMLElement, FilterableSubmission>(items.map((element) => {
    const d = element.dataset;
    return [element, {
      name: d.name ?? "", description: d.desc ?? "",
      tags: (d.tags ?? "").split(",").filter(Boolean),
      platforms: (d.platforms ?? "").split(",").filter(Boolean),
      type: d.type ?? "skill",
      authorName: d.authorName ?? "", authorLogin: d.authorLogin ?? "", authorKey: d.authorKey ?? "",
    }];
  }));
  const authorNames = new Map([...data.values()].map((item) => [item.authorKey, item.authorName]));
  const search = get<HTMLInputElement>("#skill-search");
  const filterOptions = get<HTMLElement>("#filter-options");
  const appliedChips = get<HTMLElement>("#applied-filters");
  const platformPills = Array.from(root.querySelectorAll<HTMLButtonElement>("button[data-platform]"));
  const sortSelect = get<HTMLSelectElement>("#sort-select");
  const count = get<HTMLElement>("#result-count");
  const empty = get<HTMLElement>("#empty-state");
  const status = get<HTMLElement>("#filter-status");
  const sentinel = get<HTMLElement>("#scroll-sentinel");
  const filtersTrigger = get<HTMLButtonElement>("#filters-trigger");
  const filterCount = get<HTMLElement>("#filters-count");
  const dialog = get<HTMLDialogElement>("#filters-dialog");
  const closeFilters = get<HTMLButtonElement>("[data-close-filters]");
  const dialogBody = get<HTMLElement>(".dialog-body");
  const draftChips = get<HTMLElement>("#draft-selections");
  const apply = get<HTMLButtonElement>("#apply-filters");
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
  let searchTimer = 0;
  let savedOverflow = "";
  let savedGutter = "";

  function queryString() {
    const params = galleryFilterParams(applied);
    if (sortMode !== "featured") params.set("sort", sortMode);
    const query = params.toString();
    return query ? `?${query}` : "";
  }

  function syncUrl(replace: boolean) {
    const next = `${location.pathname}${queryString()}`;
    if (next === `${location.pathname}${location.search}`) return;
    saveScroll();
    if (replace) history.replaceState(null, "", next);
    else history.pushState(null, "", next);
  }

  const number = (element: HTMLElement, key: string) => Number(element.dataset[key] ?? "0") || 0;
  function sorted(list: HTMLElement[]) {
    const byName = (a: HTMLElement, b: HTMLElement) => (a.dataset.name ?? "").localeCompare(b.dataset.name ?? "");
    return [...list].sort((a, b) => {
      const sampleDiff = number(a, "sample") - number(b, "sample");
      if (sampleDiff) return sampleDiff;
      switch (sortMode) {
        case "newest": return compareNewest(a, b);
        case "updated": return compareRecentlyUpdated(a, b);
        case "name": return byName(a, b);
        default: return number(b, sortMode) - number(a, sortMode) || byName(a, b);
      }
    });
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

  function removeRefinement(filters: ReturnType<typeof copyGalleryFilters>, field: Refinement, value: string) {
    if (field === "authors") filters.author = "";
    else filters[field].delete(value);
  }

  function renderRefinements(container: HTMLElement, filters: GalleryFilters, remove: (field: Refinement, value: string) => void) {
    const values: { field: Refinement; value: string; label: string }[] = [];
    filters.types.forEach((type) => values.push({ field: "types", value: type, label: FORMAT_LABELS[type] ?? type }));
    filters.tags.forEach((tag) => values.push({ field: "tags", value: tag, label: tag }));
    if (filters.author) values.push({ field: "authors", value: filters.author, label: authorNames.get(filters.author) ?? filters.author });
    container.replaceChildren();
    for (const { field, value, label } of values) {
      const button = document.createElement("button");
      button.type = "button";
      button.dataset.filterKey = `${field}:${value}`;
      button.className = "inline-flex max-w-full items-center gap-2 rounded-full border border-border bg-surface px-3 py-1.5 text-sm text-fg focus-visible:outline-2 focus-visible:outline-accent";
      const fieldLabel = field === "types" ? "format" : field === "authors" ? "contributor" : "tag";
      button.setAttribute("aria-label", `Remove ${fieldLabel} filter: ${label}`);
      button.title = label;
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
    platformPills.forEach((button) => {
      const selected = applied.platform === button.dataset.platform;
      button.setAttribute("aria-checked", String(selected));
      button.tabIndex = selected ? 0 : -1;
    });
    const total = renderRefinements(appliedChips, applied, (field, value) => {
      const buttons = Array.from(appliedChips.querySelectorAll<HTMLButtonElement>("button"));
      const index = buttons.findIndex((button) => button.dataset.filterKey === `${field}:${value}`);
      removeRefinement(applied, field, value);
      flushSearch();
      commit();
      const remaining = appliedChips.querySelectorAll<HTMLButtonElement>("button");
      const next = remaining[Math.min(index, remaining.length - 1)] ?? filtersTrigger;
      next.focus({ preventScroll: true });
      if (next !== filtersTrigger) revealFilter(next);
    });
    appliedChips.hidden = total === 0;
    filterCount.hidden = total === 0;
    filterCount.textContent = String(total);
    filtersTrigger.setAttribute("aria-label", total ? `Filters, ${total} active ${total === 1 ? "filter" : "filters"}` : "Filters");
    revealCurrentFilter();
  }

  function revealCurrentFilter() {
    const firstApplied = appliedChips.querySelector<HTMLButtonElement>("button");
    const selected = platformPills.find((button) => button.getAttribute("aria-checked") === "true");
    const button = firstApplied ?? selected;
    if (button) revealFilter(button);
  }

  function revealFilter(button: HTMLButtonElement) {
    const bounds = filterOptions.getBoundingClientRect();
    const chip = button.getBoundingClientRect();
    // Reveal horizontally without moving the visitor's position in the gallery.
    const offset = chip.left < bounds.left + 4
      ? chip.left - bounds.left - 4
      : Math.max(0, chip.right - bounds.right + 4);
    if (offset) filterOptions.scrollBy({ left: offset, behavior: "instant" });
  }

  function refilter() {
    matched = sorted(items.filter((item) => matchesFilters(data.get(item)!, applied)));
    const matchingSet = new Set(matched);
    gallery.append(...matched, ...items.filter((item) => !matchingSet.has(item)));
    shown = BATCH;
    renderGrid();
    fill();
    status.textContent = `${matched.length} submissions match.`;
    paintApplied();
  }

  function commit(replace = false) {
    syncUrl(replace);
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
    typeInputs.forEach((input) => { input.checked = draft.types.has(input.value); });
    tagInputs.forEach((input) => { input.checked = draft.tags.has(input.value); });
    authorInputs.forEach((input) => { input.checked = draft.author === input.value; });
    const typeCounts = countFacet(data.values(), draft, "types");
    const tagCounts = countFacet(data.values(), draft, "tags");
    const authorCounts = countFacet(data.values(), draft, "authors");
    dialog.querySelectorAll<HTMLElement>("[data-type-count]").forEach((element) => {
      element.textContent = String(typeCounts.get(element.dataset.typeCount ?? "") ?? 0);
    });
    dialog.querySelectorAll<HTMLElement>("[data-tag-count]").forEach((element) => {
      element.textContent = String(tagCounts.get(element.dataset.tagCount ?? "") ?? 0);
    });
    dialog.querySelectorAll<HTMLElement>("[data-author-count]").forEach((element) => {
      element.textContent = String(authorCounts.get(element.dataset.authorCount ?? "") ?? 0);
    });
    for (const field of ["types", "tags"] as const) {
      get<HTMLElement>(`[data-selection-count="${field}"]`).textContent = draft[field].size ? `(${draft[field].size} selected)` : "";
    }
    get<HTMLElement>('[data-selection-count="authors"]').textContent = draft.author ? "(1 selected)" : "";
    const draftCount = [...data.values()].filter((item) => matchesFilters(item, draft)).length;
    apply.textContent = `Show ${draftCount} results`;
    get<HTMLElement>("#draft-filter-status").textContent = `${draftCount} submissions match these filters.`;
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
    if (applied.query !== previousQuery) commit(true);
    draft = copyGalleryFilters(applied);
    tagSearch.value = authorSearch.value = "";
    filterPicker(tagOptions, "", "tagOption", get("#tag-search-empty"));
    filterPicker(authorOptions, "", "authorSearch", get("#author-search-empty"));
    get<HTMLElement>("#filters-context").textContent = [
      applied.platform || "All platforms",
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
    const previous = new Set(Array.from(appliedChips.querySelectorAll<HTMLButtonElement>("button"), (button) => button.dataset.filterKey));
    const changed = galleryFilterParams(applied).toString() !== galleryFilterParams(draft).toString();
    applied = copyGalleryFilters(draft);
    if (changed) commit();
    const added = Array.from(appliedChips.querySelectorAll<HTMLButtonElement>("button")).find((button) => !previous.has(button.dataset.filterKey));
    if (added) revealFilter(added);
    dialog.close();
  });
  get<HTMLButtonElement>("#clear-extra-filters").addEventListener("click", () => {
    draft.types.clear();
    draft.tags.clear();
    draft.author = "";
    paintDraft();
  });
  dialog.addEventListener("change", (event) => {
    const input = event.target;
    if (!(input instanceof HTMLInputElement)) return;
    switch (input.name) {
      case "filter-type": input.checked ? draft.types.add(input.value) : draft.types.delete(input.value); break;
      case "filter-tag": input.checked ? draft.tags.add(input.value) : draft.tags.delete(input.value); break;
      case "filter-author": if (input.checked) draft.author = input.value; break;
      default: return;
    }
    paintDraft();
  });
  tagSearch.addEventListener("input", () => filterPicker(tagOptions, tagSearch.value, "tagOption", get("#tag-search-empty")));
  authorSearch.addEventListener("input", () => filterPicker(authorOptions, authorSearch.value, "authorSearch", get("#author-search-empty")));

  search.addEventListener("input", () => {
    clearTimeout(searchTimer);
    searchTimer = window.setTimeout(() => { flushSearch(); commit(true); }, 120);
  });
  filterOptions.addEventListener("focusin", (event) => {
    const button = event.target;
    if (button instanceof HTMLButtonElement && button.matches(":focus-visible")) revealFilter(button);
  });
  platformPills.forEach((button, index) => {
    button.addEventListener("click", () => {
      if (button.dataset.platform === applied.platform) return;
      flushSearch();
      applied.platform = PLATFORMS.find((platform) => platform === button.dataset.platform) ?? "";
      commit();
      revealFilter(button);
    });
    button.addEventListener("keydown", (event) => {
      const direction = ["ArrowRight", "ArrowDown"].includes(event.key) ? 1
        : ["ArrowLeft", "ArrowUp"].includes(event.key) ? -1 : 0;
      if (!direction) return;
      event.preventDefault();
      const next = platformPills[(index + direction + platformPills.length) % platformPills.length];
      next.focus({ preventScroll: true });
      next.click();
    });
  });
  get<HTMLButtonElement>("[data-clear-filters]").addEventListener("click", () => {
    clearTimeout(searchTimer);
    applied = copyGalleryFilters(parseGalleryFilters(new URLSearchParams()));
    search.value = "";
    commit();
    search.focus({ preventScroll: true });
  });
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
  new ResizeObserver(() => { revealCurrentFilter(); fill(); }).observe(filterOptions);
  document.fonts.ready.then(revealCurrentFilter);

  function initFromUrl() {
    clearTimeout(searchTimer);
    const params = new URLSearchParams(location.search);
    applied = copyGalleryFilters(parseGalleryFilters(params));
    const previous = params.toString();
    if (applied.platform) params.set("platform", applied.platform);
    else params.delete("platform");
    if (applied.author) params.set("author", applied.author);
    else params.delete("author");
    if (params.toString() !== previous) {
      const query = params.toString();
      history.replaceState(history.state, "", `${location.pathname}${query ? `?${query}` : ""}${location.hash}`);
    }
    draft = copyGalleryFilters(applied);
    sortMode = SORTS.find((sort) => sort === params.get("sort")) ?? "featured";
    sortSelect.value = sortMode;
    search.value = applied.query;
    refilter();
  }

  const scrollKey = () => `gallery-scroll:${location.pathname}${location.search}`;
  function saveScroll() {
    const position = { shown, y: scrollY };
    history.replaceState({ ...history.state, gallery: position }, "");
    try {
      sessionStorage.setItem(scrollKey(), JSON.stringify(position));
    } catch (error) {
      console.warn("Could not save gallery position.", error);
    }
  }
  function restoreScroll() {
    try {
      const value: unknown = history.state?.gallery ?? JSON.parse(sessionStorage.getItem(scrollKey()) ?? "null");
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
  window.addEventListener("popstate", () => {
    if (dialog.open) dialog.close();
    initFromUrl();
    restoreScroll();
  });
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
