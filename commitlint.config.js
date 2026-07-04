/**
 * Conventional Commits configuration.
 * Format: <type>(<scope>): <subject>
 * Example: feat(api): add health check endpoint
 */
module.exports = {
  extends: ['@commitlint/config-conventional'],
  rules: {
    'type-enum': [
      2,
      'always',
      [
        'feat',
        'fix',
        'docs',
        'style',
        'refactor',
        'perf',
        'test',
        'build',
        'ci',
        'chore',
        'revert',
      ],
    ],
    'scope-enum': [
      2,
      'always',
      [
        'web',
        'api',
        'ai-engine',
        'worker',
        'ui',
        'config',
        'types',
        'utils',
        'sdk',
        'infra',
        'docs',
        'deps',
        'release',
        'repo',
      ],
    ],
    'subject-case': [0],
  },
};
