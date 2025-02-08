export class RateLimiter {
  private lastRequest: number = 0;
  private requestCount: number = 0;
  private readonly maxRequests: number = 50;
  private readonly timeWindow: number = 15 * 60 * 1000; // 15 minutes in ms
  private readonly minDelay: number = 1000; // 1 second minimum delay between requests

  async waitForNext(): Promise<void> {
    const now = Date.now();
    const timeSinceLastRequest = now - this.lastRequest;

    // Enforce minimum delay between requests
    if (timeSinceLastRequest < this.minDelay) {
      await new Promise(resolve => setTimeout(resolve, this.minDelay - timeSinceLastRequest));
    }

    // Reset counter if time window has passed
    if (timeSinceLastRequest > this.timeWindow) {
      this.requestCount = 0;
    }

    // Check rate limit
    if (this.requestCount >= this.maxRequests) {
      const waitTime = this.timeWindow - timeSinceLastRequest;
      await new Promise(resolve => setTimeout(resolve, waitTime));
      this.requestCount = 0;
    }

    this.requestCount++;
    this.lastRequest = Date.now();
  }
}
