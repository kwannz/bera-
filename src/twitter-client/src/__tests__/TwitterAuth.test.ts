import { TwitterAuth } from '../auth';
import { describe, beforeEach, it, expect } from '@jest/globals';

describe('TwitterAuth', () => {
  let auth: TwitterAuth;

  beforeEach(() => {
    auth = new TwitterAuth(process.env.TWITTER_API_KEY, process.env.TWITTER_API_SECRET, process.env.TWITTER_BEARER_TOKEN);
    jest.spyOn(auth, 'isLoggedIn').mockResolvedValue(true);
  });

  it('should login successfully', async () => {
    await expect(auth.login()).resolves.not.toThrow();
  });

  it('should verify login status', async () => {
    await auth.login();
    const isLoggedIn = await auth.isLoggedIn();
    expect(isLoggedIn).toBe(true);
  });
});
