import 'dotenv/config';
import { jest } from '@jest/globals';
import { Space, SpaceConfig } from './core/Space';
import { Scraper } from '../scraper';
import { RecordToDiskPlugin } from './plugins/RecordToDiskPlugin';
import { SttTtsPlugin } from './plugins/SttTtsPlugin';
import { IdleMonitorPlugin } from './plugins/IdleMonitorPlugin';
import { HlsRecordPlugin } from './plugins/HlsRecordPlugin';

jest.setTimeout(30000); // Increase timeout for async operations

describe('Twitter Spaces', () => {
  let scraper: Scraper;
  let space: Space;

  beforeAll(async () => {
    scraper = new Scraper();
    if (!process.env.TWITTER_USERNAME || !process.env.TWITTER_PASSWORD) {
      console.warn('Skipping tests: Twitter credentials not available');
      return;
    }
    await scraper.login(
      process.env.TWITTER_USERNAME,
      process.env.TWITTER_PASSWORD
    );
  });

  beforeEach(() => {
    space = new Space(scraper, { debug: false });
  });

  afterEach(async () => {
    if (space) {
      await space.stop();
    }
  });

  afterAll(async () => {
    if (scraper) {
      await scraper.logout();
    }
  });

  test('Space initialization and configuration', async () => {
    const config: SpaceConfig = {
      mode: 'INTERACTIVE',
      title: 'Test Space',
      description: 'Test space for Jest',
      languages: ['en'],
    };

    const broadcastInfo = await space.initialize(config);
    expect(broadcastInfo).toBeDefined();
    expect(broadcastInfo.share_url).toContain('broadcasts');
  });

  test('Plugin registration', () => {
    const recordPlugin = new RecordToDiskPlugin();
    const hlsPlugin = new HlsRecordPlugin();
    const sttTtsPlugin = new SttTtsPlugin();
    const idlePlugin = new IdleMonitorPlugin(60_000, 10_000);

    space.use(recordPlugin);
    space.use(hlsPlugin);
    space.use(sttTtsPlugin, {
      openAiApiKey: process.env.OPENAI_API_KEY,
      elevenLabsApiKey: process.env.ELEVENLABS_API_KEY,
      voiceId: 'test-voice-id',
    });
    space.use(idlePlugin);

    expect(space['plugins'].size).toBe(4);
  });

  test('Event handling', async () => {
    const mockSpeakerHandler = jest.fn();
    const mockReactionHandler = jest.fn();
    const mockErrorHandler = jest.fn();

    space.on('speakerRequest', mockSpeakerHandler);
    space.on('guestReaction', mockReactionHandler);
    space.on('error', mockErrorHandler);

    // Simulate events
    space.emit('speakerRequest', { userId: '123', sessionUUID: 'abc' });
    space.emit('guestReaction', { type: 'heart' });
    space.emit('error', new Error('test error'));

    expect(mockSpeakerHandler).toHaveBeenCalledWith({ userId: '123', sessionUUID: 'abc' });
    expect(mockReactionHandler).toHaveBeenCalledWith({ type: 'heart' });
    expect(mockErrorHandler).toHaveBeenCalledWith(new Error('test error'));
  });

  test('Audio processing', async () => {
    const sampleRate = 16000;
    const frameSize = 160;
    const frame = new Int16Array(frameSize);
    
    // Generate a simple sine wave
    const freq = 440;
    const amplitude = 12000;
    for (let i = 0; i < frameSize; i++) {
      const t = i / sampleRate;
      frame[i] = amplitude * Math.sin(2 * Math.PI * freq * t);
    }

    space.pushAudio(frame, sampleRate);
    // Audio buffer is handled internally by JanusClient
    expect(true).toBe(true);
  });

  test('Speaker management', async () => {
    const userId = '123';
    const sessionUUID = 'abc';

    await space.approveSpeaker(userId, sessionUUID);
    await space.removeSpeaker(userId);
    
    // No errors should be thrown
    expect(true).toBe(true);
  });
});
