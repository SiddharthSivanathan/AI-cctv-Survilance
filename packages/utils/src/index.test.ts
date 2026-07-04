import { describe, expect, it } from 'vitest';
import { clamp, cn, isDefined } from './index';

describe('cn', () => {
  it('merges and dedupes tailwind classes', () => {
    expect(cn('p-2', 'p-4')).toBe('p-4');
    expect(cn('text-red-500', false && 'hidden', 'font-bold')).toBe('text-red-500 font-bold');
  });
});

describe('clamp', () => {
  it('clamps within bounds', () => {
    expect(clamp(5, 0, 10)).toBe(5);
    expect(clamp(-1, 0, 10)).toBe(0);
    expect(clamp(11, 0, 10)).toBe(10);
  });
});

describe('isDefined', () => {
  it('filters null and undefined', () => {
    expect([1, null, 2, undefined].filter(isDefined)).toEqual([1, 2]);
  });
});
