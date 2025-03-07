import { jest } from '@jest/globals';
import dotenv from 'dotenv';

describe('Test Environment Setup', () => {
  beforeAll(() => {
    // Load environment variables from .env file
    dotenv.config();

    // Verify required environment variables
    const requiredVars = ['tusername', 'tPassword', 'tEmail'];
    const missingVars = requiredVars.filter(v => !process.env[v]);
    if (missingVars.length > 0) {
      throw new Error(`Missing required environment variables: ${missingVars.join(', ')}`);
    }

    // Log environment status (without exposing values)
    console.log('Environment variables status:', {
      hasUsername: !!process.env.tusername,
      hasPassword: !!process.env.tPassword,
      hasEmail: !!process.env.tEmail
    });

    // Mock fetch
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

    // Mock Headers
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
  });

  test('Environment variables are set', () => {
    expect(process.env.TWITTER_USERNAME).toBeDefined();
    expect(process.env.TWITTER_PASSWORD).toBeDefined();
    expect(process.env.TWITTER_EMAIL).toBeDefined();
    expect(process.env.TWITTER_API_KEY).toBeDefined();
    expect(process.env.TWITTER_API_SECRET).toBeDefined();
    expect(process.env.TWITTER_BEARER_TOKEN).toBeDefined();
  });

  test('Global fetch is mocked', () => {
    expect(global.fetch).toBeDefined();
    expect(jest.isMockFunction(global.fetch)).toBe(true);
  });

  test('Headers class is mocked', () => {
    const headers = new Headers();
    expect(headers).toBeDefined();
    expect(headers.set).toBeDefined();
    expect(headers.get).toBeDefined();
  });
});
