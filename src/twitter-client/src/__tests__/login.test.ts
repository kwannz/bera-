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
    // Skip test if credentials are not available
    if (!process.env.tusername || !process.env.tPassword || !process.env.tEmail) {
      console.warn('Skipping test: Twitter credentials not available');
      return;
    }

    try {
      await scraper.login(
        process.env.tusername,
        process.env.tPassword,
        process.env.tEmail
      );

      // Verify login state
      const isLoggedIn = await scraper.isLoggedIn();
      expect(isLoggedIn).toBe(true);

      // Verify user profile is accessible
      const profile = await scraper.me();
      expect(profile).toBeDefined();
      expect(profile?.username).toBeDefined();
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  });
});
