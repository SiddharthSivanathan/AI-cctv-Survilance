import next from 'eslint-config-next';

/** Next.js flat ESLint config for the web app. */
export default [
  ...next(),
  {
    ignores: ['.next/**', 'node_modules/**'],
  },
];
