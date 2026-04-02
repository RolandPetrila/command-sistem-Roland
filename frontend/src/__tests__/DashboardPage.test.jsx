import { describe, it, expect } from 'vitest';

describe('DashboardPage', () => {
  it('should be importable as a module', async () => {
    // Dynamic import to verify the module loads without syntax errors
    const mod = await import('../pages/DashboardPage.jsx');
    expect(mod).toBeDefined();
    expect(mod.default).toBeDefined();
    expect(typeof mod.default).toBe('function');
  });

  it('should be a React component (function)', async () => {
    const { default: DashboardPage } = await import('../pages/DashboardPage.jsx');
    // React functional components are functions
    expect(DashboardPage.name).toBe('DashboardPage');
  });
});

describe('Dashboard helper: formatRelativeTime', () => {
  // Test the module can be loaded — DashboardPage inlines its helpers
  // so we just verify import stability
  it('module does not throw on import', async () => {
    await expect(import('../pages/DashboardPage.jsx')).resolves.toBeDefined();
  });
});
