export function cleanText(text: string): string {
  return text
    .replace(/\r\n/g, "\n")
    .replace(/(subscribe|sign up|advertisement)/gi, "")
    .replace(/\t/g, " ")
    .replace(/[ ]{2,}/g, " ")
    .replace(/ *\n */g, "\n")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}