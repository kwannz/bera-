import { TwitterClient } from '../client';
import { TwitterResponse, TwitterTweet } from '../types/twitter';

export class BerachainMonitor {
  constructor(private client: TwitterClient) {}

  async postPriceUpdate(price: number, volume: number, change24h: number): Promise<TwitterResponse<TwitterTweet>> {
    const formattedVolume = volume >= 1000 ? `${(volume / 1000).toFixed(1)}B` : `${volume.toFixed(1)}M`;
    const message = `🐻 BERA: $${price.toFixed(2)} | Volume: $${formattedVolume} | ${change24h >= 0 ? '+' : ''}${change24h.toFixed(1)}% 24h #Berachain`;
    return await this.client.postTweet(message);
  }

  async postNewsUpdate(title: string, summary: string): Promise<TwitterResponse<TwitterTweet>> {
    const message = `🐻 ${title}\n${summary}\n#Berachain #DeFi`;
    return await this.client.postTweet(message);
  }

  async postIDOUpdate(name: string, date: string, status: string): Promise<TwitterResponse<TwitterTweet>> {
    const message = `🚀 Upcoming IDO: ${name}\n📅 ${date}\n📊 Status: ${status}\n#Berachain #IDO`;
    return await this.client.postTweet(message);
  }
}
