import { describe, it, expect } from 'vitest';

describe('API Client', () => {
  it('should export a default axios instance', async () => {
    const mod = await import('../api/client.js');
    const api = mod.default;
    expect(api).toBeDefined();
    expect(typeof api.get).toBe('function');
    expect(typeof api.post).toBe('function');
    expect(typeof api.put).toBe('function');
    expect(typeof api.delete).toBe('function');
  });

  it('should not have hardcoded localhost in base URL', async () => {
    const mod = await import('../api/client.js');
    const api = mod.default;
    const baseURL = api.defaults.baseURL || '';
    expect(baseURL).not.toContain('localhost');
    expect(baseURL).not.toContain('127.0.0.1');
  });

  it('should have a default timeout set', async () => {
    const mod = await import('../api/client.js');
    const api = mod.default;
    expect(api.defaults.timeout).toBeGreaterThan(0);
  });

  it('should set Content-Type to JSON', async () => {
    const mod = await import('../api/client.js');
    const api = mod.default;
    expect(api.defaults.headers['Content-Type']).toBe('application/json');
  });

  it('should export named helper functions', async () => {
    const mod = await import('../api/client.js');
    expect(typeof mod.createProgressWebSocket).toBe('function');
    expect(typeof mod.uploadFile).toBe('function');
    expect(typeof mod.checkHealth).toBe('function');
    expect(typeof mod.logPageView).toBe('function');
  });
});
