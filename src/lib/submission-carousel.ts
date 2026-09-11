export function initSubmissionCarousel(root: HTMLElement) {
  const header = root.querySelector<HTMLElement>(".carousel-header")!;
  const track = root.querySelector<HTMLElement>("[data-carousel-track]")!;
  const previous = root.querySelector<HTMLButtonElement>("[data-carousel-prev]")!;
  const next = root.querySelector<HTMLButtonElement>("[data-carousel-next]")!;
  const controls = root.querySelector<HTMLElement>("[data-carousel-controls]")!;
  const status = root.querySelector<HTMLElement>("[data-carousel-status]")!;
  const count = root.querySelector<HTMLElement>("[data-carousel-count]")!;
  const empty = root.querySelector<HTMLElement>("[data-carousel-empty]")!;
  const emptyLabel = root.querySelector<HTMLElement>("[data-carousel-empty-label]")!;
  const cards = Array.from(track.querySelectorAll<HTMLElement>(".submission-item"));
  const visibleCards = () => cards.filter((card) => !card.hidden);
  const behavior = (): ScrollBehavior =>
    matchMedia("(prefers-reduced-motion: reduce)").matches ? "instant" : "smooth";

  function reserveSpace() {
    const hiddenCards = cards.map((card) => card.hidden);
    const trackHidden = track.hidden;
    const countHidden = count.hidden;
    const labelHidden = emptyLabel.hidden;
    const countText = count.textContent;
    const controlsClass = controls.className;
    const position = track.scrollLeft;

    // Measure the full inventory and both heading states before the browser paints.
    root.style.removeProperty("--carousel-header-height");
    root.style.removeProperty("--carousel-track-height");
    track.hidden = false;
    cards.forEach((card) => { card.hidden = false; });
    count.hidden = false;
    count.textContent = `(${cards.length})`;
    emptyLabel.hidden = true;
    const hasOverflow = track.scrollWidth > track.clientWidth + 2;
    controls.classList.toggle("hidden", !hasOverflow);
    controls.classList.toggle("flex", hasOverflow);
    const trackHeight = track.getBoundingClientRect().height;
    const filledHeaderHeight = header.getBoundingClientRect().height;

    count.hidden = true;
    emptyLabel.hidden = false;
    controls.classList.add("hidden");
    controls.classList.remove("flex");
    const headerHeight = Math.max(filledHeaderHeight, header.getBoundingClientRect().height);

    cards.forEach((card, index) => { card.hidden = hiddenCards[index]; });
    track.hidden = trackHidden;
    count.hidden = countHidden;
    count.textContent = countText;
    emptyLabel.hidden = labelHidden;
    controls.className = controlsClass;
    root.style.setProperty("--carousel-header-height", `${headerHeight}px`);
    root.style.setProperty("--carousel-track-height", `${trackHeight}px`);
    track.scrollTo({ left: position, behavior: "instant" });
  }

  function refresh() {
    const visible = visibleCards();
    const hasOverflow = track.scrollWidth > track.clientWidth + 2;
    controls.classList.toggle("hidden", !hasOverflow);
    controls.classList.toggle("flex", hasOverflow);
    previous.disabled = track.scrollLeft <= 2;
    next.disabled = track.scrollLeft >= track.scrollWidth - track.clientWidth - 2;
    const bounds = track.getBoundingClientRect();
    const inView = visible
      .map((card, index) => ({ bounds: card.getBoundingClientRect(), index }))
      .filter(({ bounds: card }) => card.right > bounds.left + 2 && card.left < bounds.right - 2);
    status.textContent = inView.length
      ? `Showing submissions ${inView[0].index + 1} to ${inView.at(-1)!.index + 1} of ${visible.length}.`
      : "No matching Microsoft submissions.";
  }

  function move(direction: number) {
    const first = visibleCards()[0];
    if (!first) return;
    const step = first.getBoundingClientRect().width + parseFloat(getComputedStyle(track).columnGap);
    const page = Math.max(1, Math.floor(track.clientWidth / step));
    track.scrollBy({ left: direction * page * step, behavior: behavior() });
  }

  previous.addEventListener("click", () => move(-1));
  next.addEventListener("click", () => move(1));
  track.addEventListener("keydown", (event) => {
    if (event.target !== track) return;
    if (event.key === "ArrowLeft" || event.key === "ArrowRight") {
      event.preventDefault();
      move(event.key === "ArrowLeft" ? -1 : 1);
    } else if (event.key === "Home" || event.key === "End") {
      event.preventDefault();
      track.scrollTo({ left: event.key === "Home" ? 0 : track.scrollWidth, behavior: behavior() });
    }
  });

  let frame = 0;
  track.addEventListener("scroll", () => {
    cancelAnimationFrame(frame);
    frame = requestAnimationFrame(refresh);
  }, { passive: true });
  reserveSpace();
  new ResizeObserver(() => {
    reserveSpace();
    refresh();
  }).observe(root);
  document.fonts.ready.then(() => {
    reserveSpace();
    refresh();
  });

  return {
    update() {
      const visible = visibleCards();
      count.textContent = `(${visible.length})`;
      count.hidden = visible.length === 0;
      emptyLabel.hidden = visible.length > 0;
      empty.hidden = visible.length > 0;
      track.hidden = visible.length === 0;
      // CSS scroll snapping must not leave a filtered card off-screen.
      track.scrollTo({ left: 0, behavior: "instant" });
      refresh();
    },
    position: () => track.scrollLeft,
    restore(position: number) {
      track.scrollTo({ left: position, behavior: "instant" });
      refresh();
    },
  };
}
