import { TwitterResponse, TwitterTweet } from '../types/twitter';

export interface OllamaResponse {
  model: string;
  created_at: string;
  response: string;
  done: boolean;
}

export class OllamaClient {
  private readonly baseUrl: string;
  private readonly model: string;

  constructor(baseUrl: string = 'http://localhost:11434', model: string = 'deepseek-r1:1.5b') {
    this.baseUrl = baseUrl;
    this.model = model;
  }

  async generateResponse(prompt: string): Promise<string> {
    try {
      const response = await fetch(`${this.baseUrl}/api/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          model: this.model,
          prompt,
          stream: false
        })
      });

      if (!response.ok) {
        throw new Error(`Ollama API error: ${response.status}`);
      }

      const data = await response.json() as OllamaResponse;
      return data.response;
    } catch (error) {
      throw new Error(`Failed to generate response: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  async generateTweetResponse(context: string): Promise<string> {
    const prompt = `Generate a tweet about ${context}. Keep it concise and engaging. Include relevant hashtags.`;
    return this.generateResponse(prompt);
  }
}
