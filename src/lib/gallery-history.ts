export interface GalleryPosition {
  shown: number;
  y: number;
}

export class GalleryHistory {
  private entryId = "";
  private positions = new Map<string, GalleryPosition>();

  constructor(
    private history: Pick<History, "state" | "replaceState" | "pushState">,
    private storage: () => Pick<Storage, "getItem" | "setItem">,
  ) {
    this.activate();
  }

  activate() {
    const id: unknown = this.history.state?.galleryEntryId;
    this.entryId = typeof id === "string" && id ? id : crypto.randomUUID();
    if (id !== this.entryId) {
      this.history.replaceState({ ...this.history.state, galleryEntryId: this.entryId }, "");
    }
  }

  updateUrl(url: string, replace: boolean) {
    if (replace) this.history.replaceState(this.history.state, "", url);
    else this.history.pushState(null, "", url);
    this.activate();
  }

  // During popstate, history.state already belongs to the destination, but this ID is still the departure.
  capture(position: GalleryPosition) {
    this.positions.set(this.entryId, { ...position });
    try {
      this.storage().setItem(`gallery-scroll:${this.entryId}`, JSON.stringify(position));
    } catch (error) {
      console.warn("Could not save gallery position.", error);
    }
  }

  save(position: GalleryPosition) {
    this.capture(position);
    if (this.history.state?.galleryEntryId === this.entryId) {
      this.history.replaceState({ ...this.history.state, gallery: position }, "");
    }
  }

  read(): GalleryPosition | undefined {
    const cached = this.positions.get(this.entryId);
    if (cached) return cached;
    let value: unknown = this.history.state?.gallery;
    try {
      const stored = this.storage().getItem(`gallery-scroll:${this.entryId}`);
      if (stored !== null) value = JSON.parse(stored);
    } catch (error) {
      console.warn("Could not restore gallery position.", error);
    }
    if (value == null) return;
    if (typeof value !== "object" || !("shown" in value) || !("y" in value)
      || typeof value.shown !== "number" || typeof value.y !== "number"
      || !Number.isFinite(value.shown) || !Number.isFinite(value.y)) {
      console.warn("Ignoring invalid saved gallery position.");
      return;
    }
    return { shown: value.shown, y: value.y };
  }
}
