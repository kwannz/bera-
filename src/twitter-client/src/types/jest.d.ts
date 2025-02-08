import '@types/jest';

declare global {
  namespace jest {
    interface Matchers<R> {
      toBeString(): R;
      toBeDefined(): R;
      toBeUndefined(): R;
      toBe(expected: any): R;
      resolves: Matchers<Promise<R>>;
      rejects: Matchers<Promise<R>>;
    }
  }
}
