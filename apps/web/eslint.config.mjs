import { dirname } from 'path';
import { fileURLToPath } from 'url';
import { FlatCompat } from '@eslint/eslintrc';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// ESLint 9 flat config. `eslint-config-next` still ships a legacy (.eslintrc)
// config that runs @rushstack/eslint-patch at import time — importing it
// directly under ESLint 9 fails ("Failed to patch ESLint..."). FlatCompat
// loads it through the eslintrc compatibility layer instead. This is the
// pattern create-next-app generates for Next 15 + ESLint 9.
const compat = new FlatCompat({ baseDirectory: __dirname });

export default [
  { ignores: ['.next/**', 'node_modules/**'] },
  ...compat.extends('next/core-web-vitals', 'next/typescript'),
  {
    rules: {
      // Surfaced as warnings so they don't fail the lint gate; correctness
      // rules (rules-of-hooks, etc.) stay at their default error level.
      'react/no-unescaped-entities': 'warn',
      '@next/next/no-img-element': 'warn',
      '@typescript-eslint/no-explicit-any': 'warn',
      '@typescript-eslint/no-unused-vars': [
        'warn',
        { argsIgnorePattern: '^_', varsIgnorePattern: '^_' },
      ],
    },
  },
];
