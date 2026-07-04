// @ts-check
const base = require('./base');
const react = require('eslint-plugin-react');
const reactHooks = require('eslint-plugin-react-hooks');

/** ESLint flat config for Next.js apps. Extends the shared base. */
module.exports = [
  ...base,
  {
    files: ['**/*.{ts,tsx}'],
    plugins: { react, 'react-hooks': reactHooks },
    languageOptions: {
      parserOptions: { ecmaFeatures: { jsx: true } },
    },
    settings: { react: { version: 'detect' } },
    rules: {
      'react/react-in-jsx-scope': 'off',
      'react/prop-types': 'off',
      'react-hooks/rules-of-hooks': 'error',
      'react-hooks/exhaustive-deps': 'warn',
    },
  },
];
