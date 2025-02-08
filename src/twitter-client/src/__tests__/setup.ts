import { jest } from '@jest/globals';
import dotenv from 'dotenv';

// Load environment variables from .env file
dotenv.config();

// Mock environment variables for testing
process.env.TWITTER_USERNAME = 'myjoi_ai';
process.env.TWITTER_PASSWORD = 'joiapp1278!';
process.env.TWITTER_EMAIL = 'joiweb3@gmail.com';
process.env.TWITTER_API_KEY = process.env.APIKey;
process.env.TWITTER_API_SECRET = process.env.APIKeySecret;
process.env.TWITTER_BEARER_TOKEN = process.env.BearerToken;

// Mock fetch for testing
global.fetch = jest.fn().mockImplementation(async () => ({
  ok: true,
  json: async () => ({}),
  text: async () => "",
  headers: new Map(),
  status: 200,
  statusText: "OK",
  arrayBuffer: async () => new ArrayBuffer(0),
  blob: async () => new Blob(),
  formData: async () => new FormData(),
  clone: () => Promise.resolve({} as Response),
  body: null,
  bodyUsed: false,
  redirected: false,
  type: "basic" as ResponseType,
  url: "",
})) as unknown as typeof fetch;

// Mock Headers for testing
class MockHeaders {
  private headers = new Map<string, string>();
  
  set(key: string, value: string) { this.headers.set(key, value); }
  get(key: string) { return this.headers.get(key); }
  append(key: string, value: string) { this.headers.set(key, value); }
  delete(key: string) { this.headers.delete(key); }
  entries() { return this.headers.entries(); }
  forEach(callback: (value: string, key: string) => void) { this.headers.forEach(callback); }
  has(key: string) { return this.headers.has(key); }
  keys() { return this.headers.keys(); }
  values() { return this.headers.values(); }
}

global.Headers = MockHeaders as unknown as typeof Headers;
