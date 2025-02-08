import { TwitterAuth } from '../auth';
import { TwitterClient } from '../client';
import { BerachainMonitor } from '../berachain';
import { describe, beforeEach, it, expect, jest } from '@jest/globals';
import { TwitterApi } from 'twitter-api-v2';
import type { TweetV2PostTweetResult } from 'twitter-api-v2';

describe('BerachainMonitor', () => {
  let monitor: BerachainMonitor;
  let client: TwitterClient;
  let auth: TwitterAuth;

  beforeEach(async () => {
    const mockApi = {
      v2: {
        tweet: jest.fn().mockImplementation(() => Promise.resolve({
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
    await client.initialize();
    monitor = new BerachainMonitor(client);
  });

  it('should post price update successfully', async () => {
    const response = await monitor.postPriceUpdate(8.5, 10, 5);
    expect(response.data).toBeDefined();
    expect(response.errors).toBeUndefined();
  });

  it('should post news update successfully', async () => {
    const response = await monitor.postNewsUpdate(
      'Berachain Update',
      'New features released'
    );
    expect(response.data).toBeDefined();
    expect(response.errors).toBeUndefined();
  });
});
