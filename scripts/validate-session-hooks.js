#!/usr/bin/env node
'use strict';

const assert = require('assert');
const fs = require('fs');
const os = require('os');
const path = require('path');

const {
  isTemplateOnly,
  buildInstructionsContent,
  extractSectionListItems,
  parseOpenIssues,
} = require('../.github/hooks/scripts/session-start.js');
const {
  createNewSession,
  updateExistingSession,
} = require('../.github/hooks/scripts/session-end.js');
const {
  SESSION_SEPARATOR,
  SUMMARY_START_MARKER,
  SUMMARY_END_MARKER,
  findRecentFurikaeriDocs,
} = require('../.github/hooks/scripts/lib/session-utils.js');

function makeTempFile(name) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'session-hooks-'));
  return path.join(dir, name);
}

function makeTempDir(prefix = 'session-hooks-dir-') {
  return fs.mkdtempSync(path.join(os.tmpdir(), prefix));
}

function sampleMetadata() {
  return {
    project: 'happy_ai_life_coding_Environment',
    branch: 'feature/furikaeri-practice',
    worktree: 'C:\\tools\\happy_ai_life_coding_Environment',
    reason: 'manual-test',
  };
}

function sampleSummary() {
  return {
    userMessages: ['レビュー対応を実施した'],
    filesModified: ['.github/hooks/scripts/session-start.js'],
    toolsUsed: ['view', 'apply_patch'],
    totalMessages: 1,
  };
}

function run(name, fn) {
  try {
    fn();
    console.log(`PASS: ${name}`);
  } catch (error) {
    console.error(`FAIL: ${name}`);
    console.error(error.stack || error.message);
    process.exitCode = 1;
  }
}

run('template-only: Y/W/T/Notes/Context placeholder only', () => {
  const content = [
    '# Session: test',
    '---',
    '### Y（やったこと）',
    '- [ ]',
    '',
    '### W（わかったこと）',
    '<!-- comment -->',
    '- ',
    '',
    '### T（つぎにやること）',
    '-',
    '',
    '### Notes for Next Session',
    '-',
    '',
    '### Context to Load',
    '```',
    '[relevant files]',
    '```',
    '',
  ].join('\n');

  assert.strictEqual(isTemplateOnly(content), true);
});

run('non-template: Notes に実内容がある', () => {
  const content = [
    '# Session: test',
    '---',
    '### Y（やったこと）',
    '- [ ]',
    '',
    '### W（わかったこと）',
    '- ',
    '',
    '### T（つぎにやること）',
    '- ',
    '',
    '### Notes for Next Session',
    '- 次は PR コメント返信を確認する',
    '',
    '### Context to Load',
    '```',
    '[relevant files]',
    '```',
    '',
  ].join('\n');

  assert.strictEqual(isTemplateOnly(content), false);
});

run('non-template: Context に実ファイルがある', () => {
  const content = [
    '# Session: test',
    '---',
    '### Y（やったこと）',
    '- [ ]',
    '',
    '### W（わかったこと）',
    '- ',
    '',
    '### T（つぎにやること）',
    '- ',
    '',
    '### Notes for Next Session',
    '-',
    '',
    '### Context to Load',
    '```',
    '.github/hooks/scripts/session-start.js',
    '```',
    '',
  ].join('\n');

  assert.strictEqual(isTemplateOnly(content), false);
});

run('non-template: Y にコードフェンス内容がある', () => {
  const content = [
    '# Session: test',
    '---',
    '### Y（やったこと）',
    '```js',
    'const x = 1;',
    '```',
    '',
    '### W（わかったこと）',
    '- ',
    '',
    '### T（つぎにやること）',
    '- ',
    '',
    '### Notes for Next Session',
    '-',
    '',
    '### Context to Load',
    '```',
    '[relevant files]',
    '```',
    '',
  ].join('\n');

  assert.strictEqual(isTemplateOnly(content), false);
});

run('findRecentFurikaeriDocs: filename timestamp order を使う', () => {
  const dir = makeTempDir();
  fs.writeFileSync(path.join(dir, '20260401-101010-alpha.md'), '# alpha', 'utf8');
  fs.writeFileSync(path.join(dir, '20260401-121500-beta.md'), '# beta', 'utf8');
  fs.writeFileSync(path.join(dir, 'ignore.txt'), 'x', 'utf8');

  const results = findRecentFurikaeriDocs(dir, 3);
  assert.deepStrictEqual(results.map((item) => item.basename), [
    '20260401-121500-beta.md',
    '20260401-101010-alpha.md',
  ]);
});

run('findRecentFurikaeriDocs: invalid filename timestamp は mtime にフォールバックする', () => {
  const dir = makeTempDir();
  const validPath = path.join(dir, '20260401-121500-valid.md');
  const invalidPath = path.join(dir, '20261399-996060-invalid.md');

  fs.writeFileSync(validPath, '# valid', 'utf8');
  fs.writeFileSync(invalidPath, '# invalid', 'utf8');
  const older = new Date('2026-04-01T12:14:59Z');
  const newer = new Date('2026-04-01T12:15:00Z');
  fs.utimesSync(validPath, newer, newer);
  fs.utimesSync(invalidPath, older, older);

  const results = findRecentFurikaeriDocs(dir, 3);
  assert.deepStrictEqual(results.map((item) => item.basename), [
    '20260401-121500-valid.md',
    '20261399-996060-invalid.md',
  ]);
  assert.strictEqual(results[1].timestamp, results[1].mtime);
});

run('buildInstructionsContent: shared furikaeri context を含む', () => {
  const dir = makeTempDir();
  const sharedPath = path.join(dir, '20260401-121500-beta.md');
  fs.writeFileSync(sharedPath, [
    '# Furikaeri Share',
    '',
    '## Executive Summary',
    '- shared summary',
    '',
    '## Session Notes',
    '- shared note',
    '',
  ].join('\n'), 'utf8');

  const written = buildInstructionsContent(
    '# Private Session\nprivate body',
    '2026-04-01-aaaa1111-session.md',
    [{ basename: '2026-04-01-aaaa1111-session.md' }],
    [{ basename: '20260401-121500-beta.md', path: sharedPath }]
  );

  assert.ok(written.includes('Latest Shared Furikaeri Context'));
  assert.ok(written.includes('shared summary'));
  assert.ok(written.includes('shared note'));
});

run('extractSectionListItems: Next Steps の番号付き項目を拾う', () => {
  const content = [
    '# Furikaeri Share',
    '',
    '## Next Steps',
    '1. `copilot-authoring-beta` に「抽象化 → review → 発展」の型を追加する案を Issue 化する。',
    '2. hooks 追加時の設計・review の型を再利用可能な形で整理する。',
    '',
    '## Other Recent Shared Furikaeri',
    '- archive',
  ].join('\n');

  assert.deepStrictEqual(extractSectionListItems(content, 'Next Steps'), [
    '`copilot-authoring-beta` に「抽象化 → review → 発展」の型を追加する案を Issue 化する。',
    'hooks 追加時の設計・review の型を再利用可能な形で整理する。',
  ]);
});

run('parseOpenIssues: gh issue list の JSON を読む', () => {
  const issues = parseOpenIssues(JSON.stringify([
    { number: 56, title: 'copilot-authoring-beta: hooks追加の抽象→review→発展の型を追加する', url: 'https://example.com/56' },
    { number: 57, title: 'session-start: open issue と前回の Try/T をもとに次の一手を提案する', url: 'https://example.com/57' },
  ]));

  assert.deepStrictEqual(issues, [
    { number: 56, title: 'copilot-authoring-beta: hooks追加の抽象→review→発展の型を追加する', url: 'https://example.com/56' },
    { number: 57, title: 'session-start: open issue と前回の Try/T をもとに次の一手を提案する', url: 'https://example.com/57' },
  ]);
});

run('buildInstructionsContent: private context がなくても shared を含む', () => {
  const dir = makeTempDir();
  const sharedPath = path.join(dir, '20260401-121500-beta.md');
  fs.writeFileSync(sharedPath, '# shared only', 'utf8');

  const written = buildInstructionsContent(
    '',
    '',
    [],
    [{ basename: '20260401-121500-beta.md', path: sharedPath }]
  );

  assert.ok(written.includes('No recent private session context was found.'));
  assert.ok(written.includes('shared only'));
});

run('buildInstructionsContent: suggested next steps に open issue を含む', () => {
  const dir = makeTempDir();
  const sharedPath = path.join(dir, '20260401-121500-beta.md');
  fs.writeFileSync(sharedPath, [
    '# Furikaeri Share',
    '',
    '## Next Steps',
    '1. `copilot-authoring-beta` に「抽象化 → review → 発展」の型を追加する案を Issue 化する。',
    '2. hooks 追加時の設計・review の型を再利用可能な形で整理する。',
    '',
  ].join('\n'), 'utf8');

  const written = buildInstructionsContent(
    '',
    '',
    [],
    [{ basename: '20260401-121500-beta.md', path: sharedPath }],
    [
      { number: 56, title: 'copilot-authoring-beta: hooks追加の抽象→review→発展の型を追加する', url: 'https://example.com/56' },
      { number: 57, title: 'session-start: open issue と前回の Try/T をもとに次の一手を提案する', url: 'https://example.com/57' },
    ]
  );

  assert.ok(written.includes('## Suggested Next Steps'));
  assert.ok(written.includes('### From latest furikaeri'));
  assert.ok(written.includes('### Open issues'));
  assert.ok(written.includes('#56: copilot-authoring-beta: hooks追加の抽象→review→発展の型を追加する'));
  assert.ok(written.includes('> Suggested next move:'));
});

run('createNewSession: bare template に summary marker を含む', () => {
  const sessionFile = makeTempFile('bare-session.md');

  createNewSession(
    sessionFile,
    '2026-03-29',
    '14:00',
    sampleMetadata(),
    null
  );

  const written = fs.readFileSync(sessionFile, 'utf8');
  assert.ok(written.includes(SUMMARY_START_MARKER));
  assert.ok(written.includes(SUMMARY_END_MARKER));
  assert.ok(written.includes('### Notes for Next Session'));
  assert.ok(written.includes('[relevant files]'));
});

run('updateExistingSession: marker なし legacy でも手書き領域を保持', () => {
  const sessionFile = makeTempFile('legacy-session.md');
  const legacyBody = [
    '## セッション要約（YWT）',
    '',
    '### Y（やったこと）',
    '- 以前の要約',
    '',
    '### W（わかったこと）',
    '- keep learned',
    '',
    '### T（つぎにやること）',
    '- keep next',
    '',
    '### Notes for Next Session',
    '- keep note',
    '',
    '### Context to Load',
    '```',
    'src/keep.js',
    '```',
    '',
  ].join('\n');

  fs.writeFileSync(
    sessionFile,
    `# Session: legacy${SESSION_SEPARATOR}${legacyBody}`,
    'utf8'
  );

  updateExistingSession(
    sessionFile,
    '2026-03-29',
    '14:05',
    sampleMetadata(),
    sampleSummary()
  );

  const written = fs.readFileSync(sessionFile, 'utf8');
  assert.ok(written.includes(SUMMARY_START_MARKER));
  assert.ok(written.includes('- keep learned'));
  assert.ok(written.includes('- keep next'));
  assert.ok(written.includes('- keep note'));
  assert.ok(written.includes('src/keep.js'));
});

run('updateExistingSession: summary 前の手書き見出しを重複保持しない', () => {
  const sessionFile = makeTempFile('legacy-preface-session.md');
  const content = [
    '# Session: legacy-preface',
    '**Date:** 2026-03-29',
    '---',
    '### W（わかったこと）',
    '- do not preserve this misplaced section',
    '',
    '## セッション要約（YWT）',
    '',
    '### Y（やったこと）',
    '- old summary',
    '',
    '### W（わかったこと）',
    '- keep this section after summary',
    '',
  ].join('\n');

  fs.writeFileSync(sessionFile, content, 'utf8');

  updateExistingSession(
    sessionFile,
    '2026-03-29',
    '14:12',
    sampleMetadata(),
    sampleSummary()
  );

  const written = fs.readFileSync(sessionFile, 'utf8');
  assert.ok(!written.includes('- do not preserve this misplaced section'));
  assert.ok(written.includes('- keep this section after summary'));
});

run('updateExistingSession: marker あり再実行でも手書き領域を保持', () => {
  const sessionFile = makeTempFile('marked-session.md');
  const content = [
    '# Session: marked',
    SESSION_SEPARATOR.trim(),
    SUMMARY_START_MARKER,
    '## セッション要約（YWT）',
    '',
    '### Y（やったこと）',
    '- old summary',
    SUMMARY_END_MARKER,
    '',
    '### W（わかったこと）',
    '- keep W',
    '',
    '### T（つぎにやること）',
    '- keep T',
    '',
    '### Notes for Next Session',
    '- keep notes',
    '',
    '### Context to Load',
    '```',
    'src/context.js',
    '```',
    '',
  ].join('\n');

  fs.writeFileSync(sessionFile, content, 'utf8');

  updateExistingSession(
    sessionFile,
    '2026-03-29',
    '14:10',
    sampleMetadata(),
    sampleSummary()
  );

  const written = fs.readFileSync(sessionFile, 'utf8');
  assert.ok(written.includes('- keep W'));
  assert.ok(written.includes('- keep T'));
  assert.ok(written.includes('- keep notes'));
  assert.ok(written.includes('src/context.js'));
  assert.ok(written.includes('レビュー対応を実施した'));
});

if (process.exitCode) {
  process.exit(process.exitCode);
}
