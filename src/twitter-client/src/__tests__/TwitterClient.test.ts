import { TwitterAuth } from '../auth';
import { TwitterClient } from '../client';
import { describe, beforeEach, it, expect, jest } from '@jest/globals';
import { TwitterApi } from 'twitter-api-v2';
import type { TweetV2PostTweetResult } from 'twitter-api-v2';

describe('TwitterClient', () => {
  let client: TwitterClient;
  let auth: TwitterAuth;

  beforeEach(() => {
    const mockApi = {
      v2: {
        tweet: jest.fn<(...args: any[]) => Promise<TweetV2PostTweetResult>>().mockResolvedValue({
          data: {
            id: '123',
            text: 'Test tweet',
            author_id: '456'
          }
        } as TweetV2PostTweetResult)
      }
    } as unknown as TwitterApi;

    auth = new TwitterAuth(process.env.TWITTER_API_KEY, process.env.TWITTER_API_SECRET, process.env.TWITTER_BEARER_TOKEN);
    jest.spyOn(auth, 'getApi').mockReturnValue(mockApi);
    jest.spyOn(auth, 'login').mockResolvedValue();
    jest.spyOn(auth, 'isLoggedIn').mockResolvedValue(true);
    
    client = new TwitterClient(auth);
  });

  it('should initialize successfully', async () => {
    await expect(client.initialize()).resolves.not.toThrow();
  });

  it('should post tweet successfully', async () => {
    await client.initialize();
    const response = await client.postTweet('Test tweet from Berachain bot');
    expect(response.data).toBeDefined();
    expect(response.errors).toBeUndefined();
  });
});
