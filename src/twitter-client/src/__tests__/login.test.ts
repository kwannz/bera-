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
    try {
      // Initialize with test credentials
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

      // Log success details for debugging
      console.log('Login successful:', {
        isLoggedIn,
        hasProfile: !!profile,
        username: profile?.username
      });
    } catch (error) {
      // Enhanced error logging
      console.error('Login attempt failed:', {
        error: error instanceof Error ? error.message : String(error),
        stack: error instanceof Error ? error.stack : undefined,
        credentials: {
          hasUsername: !!process.env.tusername,
          hasPassword: !!process.env.tPassword,
          hasEmail: !!process.env.tEmail
        }
      });
      throw error;
    }
  });
});
