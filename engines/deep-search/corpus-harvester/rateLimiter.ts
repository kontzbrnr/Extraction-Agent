export function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export class RequestPerMinuteLimiter {
  private nextAllowedAt = 0;
  private readonly minIntervalMs: number;

  constructor(requestsPerMinute: number) {
    this.minIntervalMs = Math.ceil(60000 / Math.max(1, requestsPerMinute));
  }

  async waitTurn(label: string): Promise<void> {
    const now = Date.now();
    const waitMs = this.nextAllowedAt > now ? this.nextAllowedAt - now : 0;
    if (waitMs > 0) {
      console.log(`[RateLimit] delaying ${label} by ${waitMs}ms`);
      await sleep(waitMs);
    }
    this.nextAllowedAt = Date.now() + this.minIntervalMs;
  }
}

export class PerDomainCooldownLimiter {
  private readonly cooldownMs: number;
  private readonly nextAllowedAtByDomain = new Map<string, number>();

  constructor(cooldownMs: number) {
    this.cooldownMs = Math.max(0, cooldownMs);
  }

  async waitTurn(url: string): Promise<void> {
    if (this.cooldownMs === 0) {
      return;
    }

    let hostname = "__unknown__";
    try {
      hostname = new URL(url).hostname || "__unknown__";
    } catch {
      hostname = "__unknown__";
    }

    const now = Date.now();
    const nextAllowedAt = this.nextAllowedAtByDomain.get(hostname) ?? 0;
    if (nextAllowedAt > now) {
      const waitMs = nextAllowedAt - now;
      console.log(`[RateLimit] domain cooldown ${hostname} delay ${waitMs}ms`);
      await sleep(waitMs);
    }

    this.nextAllowedAtByDomain.set(hostname, Date.now() + this.cooldownMs);
  }
}

export async function runWithConcurrency<T>(
  items: T[],
  maxConcurrent: number,
  worker: (item: T) => Promise<void>
): Promise<void> {
  const width = Math.max(1, Math.min(maxConcurrent, items.length || 1));
  let index = 0;

  async function runner(): Promise<void> {
    while (true) {
      const current = index;
      index += 1;
      if (current >= items.length) {
        return;
      }
      await worker(items[current]);
    }
  }

  await Promise.all(Array.from({ length: width }, () => runner()));
}
