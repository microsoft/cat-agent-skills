interface GalleryItem {
  dataset: Record<string, string | undefined>;
}

export function compareNewest(a: GalleryItem, b: GalleryItem): number {
  const byName = () =>
    (a.dataset.name ?? "").localeCompare(b.dataset.name ?? "");
  const aCreated = a.dataset.created;
  const bCreated = b.dataset.created;

  if (aCreated === undefined) return bCreated === undefined ? byName() : 1;
  if (bCreated === undefined) return -1;

  return (
    Number(bCreated) - Number(aCreated) ||
    byName()
  );
}
