import { TwitterApi } from 'twitter-api-v2';
import { CookieJar } from 'tough-cookie';
import { Headers } from 'headers-polyfill';

export interface TwitterAuthOptions {
  fetch?: typeof fetch;
  transform?: {
    request?: (...args: Parameters<typeof fetch>) => Parameters<typeof fetch> | Promise<Parameters<typeof fetch>>;
    response?: (response: Response) => Response | Promise<Response>;
  };
}

export interface TwitterAuthInterface {
  login(): Promise<void>;
  isLoggedIn(): Promise<boolean>;
  getApi(): TwitterApi | null;
  getCookieJar(): CookieJar;
}

export class TwitterAuth implements TwitterAuthInterface {
  private api: TwitterApi | null = null;
  private cookieJar: CookieJar;

  constructor(
    private readonly apiKey: string = process.env.TWITTER_API_KEY || '',
    private readonly apiSecret: string = process.env.TWITTER_API_SECRET || '',
    private readonly bearerToken: string = process.env.TWITTER_BEARER_TOKEN || '',
    private readonly options?: TwitterAuthOptions
  ) {
    this.cookieJar = new CookieJar();
  }

  async login(): Promise<void> {
    try {
      // Initialize Twitter API client with OAuth 2.0 app-only authentication
      this.api = new TwitterApi(this.bearerToken);

    } catch (error) {
      throw new Error(`Login failed: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  async isLoggedIn(): Promise<boolean> {
    if (!this.api) return false;
    try {
      const response = await this.api.v2.me();
      return !!response.data;
    } catch {
      return false;
    }
  }

  getApi(): TwitterApi | null {
    return this.api;
  }

  getCookieJar(): CookieJar {
    return this.cookieJar;
  }
}
