import { OllamaClient } from '../ai';
import { describe, beforeEach, it, expect } from '@jest/globals';

describe('OllamaClient', () => {
  let client: OllamaClient;

  beforeEach(() => {
    client = new OllamaClient();
  });

  it('should generate response successfully', async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ response: 'Test response' })
    });
    const response = await client.generateResponse('Test prompt');
    expect(response).toBeDefined();
    expect(typeof response).toBe('string');
  });

  it('should generate tweet response successfully', async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ response: 'Test tweet response' })
    });
    const response = await client.generateTweetResponse('Berachain ecosystem update');
    expect(response).toBeDefined();
    expect(typeof response).toBe('string');
  });
});
