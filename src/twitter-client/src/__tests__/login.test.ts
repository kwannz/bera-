import { jest } from '@jest/globals';
import { Scraper } from '../scraper';
import { TwitterUserAuth } from '../auth-user';

describe('Twitter Login Tests', () => {
  let scraper: Scraper;

  beforeEach(() => {
    scraper = new Scraper();
  });

  afterEach(async () => {
    if (scraper) {
      await scraper.logout();
    }
  });

  test('login with username/password', async () => {
    await scraper.login(
      process.env.tusername!,
      process.env.tPassword!,
      process.env.tEmail
    );
    const isLoggedIn = await scraper.isLoggedIn();
    expect(isLoggedIn).toBe(true);
  });

  test('login with username/password', async () => {
    try {
      await scraper.login(
        process.env.TWITTER_USERNAME!,
        process.env.TWITTER_PASSWORD!,
        process.env.TWITTER_EMAIL
      );
      const isLoggedIn = await scraper.isLoggedIn();
      expect(isLoggedIn).toBe(true);
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  });
});
