import { TwitterAuthInterface } from '../auth';
import { TwitterResponse, TwitterTweet, TweetV2 } from '../types/twitter';

import { RateLimiter } from '../utils/rate-limiter';

export class TwitterClient {
  private rateLimiter: RateLimiter;

  constructor(private auth: TwitterAuthInterface) {
    this.rateLimiter = new RateLimiter();
  }

  async initialize(): Promise<void> {
    await this.auth.login();
  }

  async isAuthenticated(): Promise<boolean> {
    return this.auth.isLoggedIn();
  }

  async postTweet(text: string, replyToTweetId?: string, retries: number = 3): Promise<TwitterResponse<TwitterTweet>> {
    const api = this.auth.getApi();
    if (!api) {
      throw new Error('Not authenticated. Call initialize() first.');
    }

    for (let attempt = 1; attempt <= retries; attempt++) {
      try {
        await this.rateLimiter.waitForNext();
        
        const response = await api.v2.tweet(text, {
          reply: replyToTweetId ? {
            in_reply_to_tweet_id: replyToTweetId
          } : undefined
        });

        if (!response.data) {
          throw new Error('Failed to create tweet');
        }

        const tweet: TwitterTweet = {
          id: response.data.id,
          text: response.data.text,
          created_at: new Date().toISOString(),
          author_id: response.data.id // Use tweet ID as author ID since we're using app-only auth
        };

        return { data: tweet };
      } catch (error) {
        if (attempt === retries) {
          return {
            errors: [{
              code: error instanceof Error ? 500 : 400,
              message: error instanceof Error ? error.message : String(error)
            }]
          };
        }
        // Exponential backoff
        await new Promise(resolve => setTimeout(resolve, Math.pow(2, attempt) * 1000));
      }
    }

    return {
      errors: [{
        code: 500,
        message: 'Maximum retry attempts reached'
      }]
    };
  }

  async deleteTweet(tweetId: string): Promise<boolean> {
    const api = this.auth.getApi();
    if (!api) {
      throw new Error('Not authenticated. Call initialize() first.');
    }

    try {
      await api.v2.deleteTweet(tweetId);
      return true;
    } catch {
      return false;
    }
  }
}
