import { describe, it, expect } from 'vitest';
import { NAV_SECTIONS } from '../modules/manifest.js';

describe('Navigation Manifest', () => {
  it('should export NAV_SECTIONS as a non-empty array', () => {
    expect(Array.isArray(NAV_SECTIONS)).toBe(true);
    expect(NAV_SECTIONS.length).toBeGreaterThan(0);
  });

  it('every section should have category and items', () => {
    for (const section of NAV_SECTIONS) {
      expect(section).toHaveProperty('category');
      expect(section).toHaveProperty('items');
      expect(Array.isArray(section.items)).toBe(true);
      expect(section.items.length).toBeGreaterThan(0);
    }
  });

  it('every nav item should have label, path, and icon', () => {
    for (const section of NAV_SECTIONS) {
      for (const item of section.items) {
        expect(item).toHaveProperty('label');
        expect(item).toHaveProperty('path');
        expect(item).toHaveProperty('icon');
        expect(typeof item.label).toBe('string');
        expect(item.path).toMatch(/^\//);
      }
    }
  });

  it('should not have duplicate paths', () => {
    const paths = NAV_SECTIONS.flatMap(s => s.items.map(i => i.path));
    const uniquePaths = new Set(paths);
    expect(uniquePaths.size).toBe(paths.length);
  });

  it('should include core modules (dashboard, translator, invoices, itp)', () => {
    const paths = NAV_SECTIONS.flatMap(s => s.items.map(i => i.path));
    expect(paths).toContain('/');
    expect(paths).toContain('/translator');
    expect(paths).toContain('/invoices');
    expect(paths).toContain('/itp');
  });

  it('should have at least 20 navigation items total', () => {
    const totalItems = NAV_SECTIONS.reduce((sum, s) => sum + s.items.length, 0);
    expect(totalItems).toBeGreaterThanOrEqual(20);
  });
});
