interface GalleryItem {
  dataset: Record<string, string | undefined>;
}

export function compareNewest(left: GalleryItem, right: GalleryItem): number {
  return compareDates(left, right, left.dataset.created, right.dataset.created);
}

export function compareRecentlyUpdated(left: GalleryItem, right: GalleryItem): number {
  return compareDates(
    left,
    right,
    left.dataset.updated ?? left.dataset.created,
    right.dataset.updated ?? right.dataset.created,
  );
}

function compareDates(
  left: GalleryItem,
  right: GalleryItem,
  leftDate: string | undefined,
  rightDate: string | undefined,
): number {
  const byName = () =>
    (left.dataset.name ?? "").localeCompare(right.dataset.name ?? "");

  if (leftDate === undefined) return rightDate === undefined ? byName() : 1;
  if (rightDate === undefined) return -1;

  return Number(rightDate) - Number(leftDate) || byName();
}