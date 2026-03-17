export function isAllowedSource(url: string): boolean {
  const blockedDomains = [
    "youtube.com",
    "twitter.com",
    "x.com",
    "reddit.com",
    "facebook.com",
  ];

  const blockedPatterns = ["/channel/", "/watch", "/video", "/shorts"];

  const lower = url.toLowerCase();

  if (blockedDomains.some((domain) => lower.includes(domain))) {
    return false;
  }

  if (blockedPatterns.some((pattern) => lower.includes(pattern))) {
    return false;
  }

  return true;
}