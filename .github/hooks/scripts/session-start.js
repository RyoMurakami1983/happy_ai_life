#!/usr/bin/env node
/**
 * SessionStart Hook — 前回セッションの要約をコンテキストに注入する
 *
 * .github/sessions/ 内の最新セッションファイルを読み、
 * stdout に JSON を出力して Copilot の additionalContext に注入する。
 *
 * 設計原則:
 * - 雛形のままのファイルは注入しない
 * - エラー時は exit 0 で非ブロッキング
 */
'use strict';

const path = require('path');
const {
  SESSION_MAX_AGE_DAYS,
  readFileSafe,
  getProjectSessionsDir,
  ensureDir,
  findRecentSessions,
  stripAnsi,
  log,
} = require('./lib/session-utils');

async function main() {
  const cwd = process.cwd();
  const sessionsDir = getProjectSessionsDir(cwd);

  ensureDir(sessionsDir);

  const additionalContextParts = [];

  // 直近のセッションファイルを検索
  const recentSessions = findRecentSessions(sessionsDir, SESSION_MAX_AGE_DAYS);

  if (recentSessions.length > 0) {
    const latest = recentSessions[0];
    log(`Found ${recentSessions.length} recent session(s)`);
    log(`Latest: ${latest.path}`);

    const content = stripAnsi(readFileSafe(latest.path) || '');

    // 雛形のまま（未編集）なら注入しない
    if (content && !content.includes('[Session context goes here]')) {
      additionalContextParts.push(`Previous session summary:\n${content}`);
    }

    // 複数セッションがある場合、一覧を報告
    if (recentSessions.length > 1) {
      const sessionList = recentSessions
        .slice(0, 5)
        .map((s) => `  - ${s.basename}`)
        .join('\n');
      log(`Recent sessions:\n${sessionList}`);
    }
  } else {
    log('No recent sessions found');
  }

  // コンテキストを stdout に出力
  await writePayload(additionalContextParts.join('\n\n'));
}

function writePayload(additionalContext) {
  return new Promise((resolve, reject) => {
    const payload = JSON.stringify({
      hookSpecificOutput: {
        hookEventName: 'SessionStart',
        additionalContext,
      },
    });

    process.stdout.write(payload, (err) => {
      if (err) {
        log(`stdout write error: ${err.message}`);
        reject(err);
        return;
      }
      resolve();
    });
  });
}

main().catch((err) => {
  log(`Error: ${err.message}`);
  process.exitCode = 0;
});
