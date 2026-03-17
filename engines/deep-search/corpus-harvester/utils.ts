export function slugify(value: string): string {
  const lowered = value.toLowerCase().trim();
  const whitespaceNormalized = lowered.replace(/\s+/g, "_");
  const punctuationRemoved = whitespaceNormalized.replace(/[^a-z0-9_-]+/g, "");
  const collapsedUnderscores = punctuationRemoved.replace(/_+/g, "_");
  const finalValue = collapsedUnderscores.replace(/^_+|_+$/g, "");
  return finalValue.length > 0 ? finalValue : "unknown";
}

export function normalizeDateToYYYYMMDD(value?: string): string {
  if (!value || value.trim().length === 0) {
    return "unknown_date";
  }

  const trimmed = value.trim();
  const isoLike = trimmed.match(/^(\d{4})-(\d{2})-(\d{2})/);
  if (isoLike) {
    return `${isoLike[1]}-${isoLike[2]}-${isoLike[3]}`;
  }

  const parsed = new Date(trimmed);
  if (Number.isNaN(parsed.getTime())) {
    return "unknown_date";
  }

  return parsed.toISOString().slice(0, 10);
}

export function safeString(value?: string): string {
  return (value ?? "").trim();
}

export function ensureArray(value?: string[]): string[] {
  if (!value) {
    return [];
  }

  return value
    .map((item) => item.trim())
    .filter((item) => item.length > 0);
}

export function currentTimestampISO(): string {
  return new Date().toISOString();
}
