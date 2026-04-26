#!/usr/bin/env node
/**
 * SessionEnd Hook — セッション要約を .github/sessions/ に保存する
 *
 * Copilot のセッション終了時に発火する sessionEnd イベントで実行される。
 * 公式入力: { timestamp, cwd, reason }
 *
 * ~/.copilot/session-state/ 内の最新 events.jsonl を解析し、
 * プロジェクトローカルの session.md に要約を書き出す。
 *
 * 設計原則:
 * - 冪等: 何度走っても結果が同じ
 * - 非破壊: ユーザー手書き領域は上書きしない
 * - 非ブロッキング: 常に exit 0
 */
'use strict';

const fs = require('fs');
const path = require('path');
const {
  SUMMARY_START_MARKER,
  SUMMARY_END_MARKER,
  SESSION_SEPARATOR,
  ensureDir,
  readFileSafe,
  writeFileSafe,
  getGitBranch,
  getDateString,
  getTimeString,
  shortId,
  getProjectName,
  getProjectSessionsDir,
  getGlobalSessionStateDir,
  isRegularFileNoSymlink,
  extractSessionSummary,
  buildSessionHeader,
  mergeSessionHeader,
  buildSummaryBlock,
  escapeRegExp,
  log,
  readStdin,
} = require('./lib/session-utils');
const {
  validateTechnologyConsistency,
} = require('./lib/decision-validation');

async function main() {
  const raw = await readStdin();
  const cwd = process.cwd();

  // 公式 sessionEnd 入力: { timestamp, cwd, reason }
  let reason = null;
  try {
    const input = JSON.parse(raw);
    reason = input.reason || null;
  } catch {
    // パース失敗: 無視して続行
  }

  // 最新の events.jsonl をプロジェクト cwd ベースで探す
  const eventsPath = findLatestEventsForProject(cwd);

  const sessionsDir = getProjectSessionsDir(cwd);
  const today = getDateString();
  const idShort = shortId(
    eventsPath ? path.basename(path.dirname(eventsPath)) : 'manual'
  );
  const sessionFile = path.join(sessionsDir, `${today}-${idShort}-session.md`);

  const metadata = {
    project: getProjectName(cwd),
    branch: getGitBranch(cwd),
    worktree: cwd,
    reason: reason,
  };

  if (!ensureDir(sessionsDir)) return;

  const currentTime = getTimeString();
  let summary = null;
  if (eventsPath) {
    summary = extractSessionSummary(eventsPath);
    if (summary) {
      log(`Extracted summary from: ${eventsPath}`);
    }
  } else {
    log('No events.jsonl found — header update only');
  }

  // 既存ファイルの更新 or 新規作成
  if (fs.existsSync(sessionFile)) {
    updateExistingSession(sessionFile, today, currentTime, metadata, summary);
  } else {
    createNewSession(sessionFile, today, currentTime, metadata, summary);
  }

  // Decision Log validation (soft validation — warnings only, non-blocking)
  validateSessionForDecisionConsistency(sessionFile, cwd);
}

/**
 * cwd に対応する最新の events.jsonl を ~/.copilot/session-state/ から探す。
 * workspace.yaml の cwd / git_root が一致するセッションのうち最新を返す。
 * セキュリティ: symlink は無視（読み込まない）
 */
function findLatestEventsForProject(cwd) {
  const stateDir = getGlobalSessionStateDir();
  if (!fs.existsSync(stateDir)) return null;

  let best = null;
  let bestMtime = 0;

  try {
    const entries = fs.readdirSync(stateDir);
    for (const name of entries) {
      const sessionDir = path.join(stateDir, name);
      const wsYaml = path.join(sessionDir, 'workspace.yaml');
      const events = path.join(sessionDir, 'events.jsonl');

      if (!fs.existsSync(events)) continue;

      // セキュリティ: events.jsonl が symlink の場合はスキップ
      // isRegularFileNoSymlink() で一箇所に集約
      if (!isRegularFileNoSymlink(events)) continue;

      // workspace.yaml からプロジェクトパスを簡易マッチ
      // readFileSafe() は内部で symlink チェック済み
      const yaml = readFileSafe(wsYaml);
      if (yaml) {
        const cwdMatch = yaml.match(/^cwd:\s*(.+)$/m);
        const gitMatch = yaml.match(/^git_root:\s*(.+)$/m);
        const dirFromYaml = cwdMatch?.[1]?.trim() || gitMatch?.[1]?.trim() || '';

        // パス正規化して比較
        if (normalizePath(dirFromYaml) !== normalizePath(cwd)) continue;
      }

      try {
        const stat = fs.statSync(events);
        if (stat.mtimeMs > bestMtime) {
          bestMtime = stat.mtimeMs;
          best = events;
        }
      } catch {
        // stat 失敗はスキップ
      }
    }
  } catch {
    // ディレクトリ列挙失敗
  }

  return best;
}

function normalizePath(p) {
  if (!p) return '';
  return p.replace(/\\/g, '/').replace(/\/$/, '').toLowerCase();
}

/**
 * Validate session for technology consistency with prior decisions.
 * Appends warnings to session file if detected (soft validation).
 *
 * @param {string} sessionFile - Path to session file
 * @param {string} cwd - Current working directory (repo root)
 */
function validateSessionForDecisionConsistency(sessionFile, cwd) {
  const content = readFileSafe(sessionFile);
  if (!content) {
    return; // Can't read session — skip validation
  }

  const validation = validateTechnologyConsistency(content, cwd);
  if (!validation.isValid || validation.warnings.length > 0) {
    // Append validation warnings to session file
    let updatedContent = content;

    // Add validation warning section if there are warnings
    if (validation.warnings.length > 0) {
      const warningSection = [
        '',
        '---',
        '## Validation Warnings',
        '',
        '### Technology Consistency',
        ...validation.warnings.map(w => `${w}`),
        '',
      ].join('\n');

      updatedContent = `${updatedContent.trimEnd()}${warningSection}`;
    }

    if (writeFileSafe(sessionFile, updatedContent)) {
      log('Added Decision Log validation warnings to session file');
    }
  }
}



function buildHandwrittenSections() {
  return [
    '### W（わかったこと）',
    '<!-- furikaeri-practice skill で記入。/exit で直接終了した場合は手動で記入 -->',
    '- ',
    '',
    '### T（つぎにやること）',
    '<!-- furikaeri-practice skill で記入。/exit で直接終了した場合は手動で記入 -->',
    '- ',
    '',
    '### Notes for Next Session',
    '-',
    '',
    '### Context to Load',
    '```',
    '[relevant files]',
    '```',
  ].join('\n');
}

function findLegacyHandwrittenStart(content) {
  const headings = [
    '### W（わかったこと）',
    '### T（つぎにやること）',
    '### T（次にやること）',
    '### Notes for Next Session',
    '### Context to Load',
  ];

  let earliest = -1;
  for (const heading of headings) {
    const index = content.indexOf(heading);
    if (index !== -1 && (earliest === -1 || index < earliest)) {
      earliest = index;
    }
  }

  return earliest;
}

function updateExistingSession(sessionFile, today, currentTime, metadata, summary) {
  let content = readFileSafe(sessionFile);
  if (!content) {
    log(`Failed to read existing session: ${sessionFile}`);
    return;
  }

  // ヘッダの Last Updated を更新
  const merged = mergeSessionHeader(content, today, currentTime, metadata);
  if (merged) {
    content = merged;
  } else {
    log('Failed to normalize header — skipping header update');
  }

  // Summary ブロックを冪等に置換
  if (summary) {
    const summaryBlock = buildSummaryBlock(summary);
    const startEsc = escapeRegExp(SUMMARY_START_MARKER);
    const endEsc = escapeRegExp(SUMMARY_END_MARKER);

    if (
      content.includes(SUMMARY_START_MARKER) &&
      content.includes(SUMMARY_END_MARKER)
    ) {
      // マーカー範囲だけ置換（冪等）
      content = content.replace(
        new RegExp(`${startEsc}[\\s\\S]*?${endEsc}`),
        summaryBlock
      );
    } else {
      // 旧形式: legacy summary だけ差し替え、W/T/Notes/Context などの手書き領域は保持する
      const legacyMatch = content.match(
        /## (?:Session Summary|Current State|セッション要約(?:（YWT）)?)/m
      );

      if (legacyMatch && typeof legacyMatch.index === 'number') {
        const summaryStart = legacyMatch.index;
        const tail = content.slice(summaryStart);
        const handwrittenStart = findLegacyHandwrittenStart(tail);
        const separatorIndex = content.indexOf(SESSION_SEPARATOR);
        const preservedPrefix =
          separatorIndex === -1
            ? content.slice(0, summaryStart).trimEnd()
            : content.slice(0, separatorIndex + SESSION_SEPARATOR.length).trimEnd();
        const handwrittenBlock =
          handwrittenStart === -1
            ? buildHandwrittenSections()
            : tail.slice(handwrittenStart).trimStart();

        content = [
          preservedPrefix,
          summaryBlock,
          '',
          handwrittenBlock,
          '',
        ].join('\n');
      } else {
        content = `${content.trimEnd()}\n\n${summaryBlock}\n\n${buildHandwrittenSections()}\n`;
      }
    }
  }

  if (writeFileSafe(sessionFile, content)) {
    log(`Updated: ${sessionFile}`);
  } else {
    log(`Failed to update: ${sessionFile}`);
  }
}

function createNewSession(sessionFile, today, currentTime, metadata, summary) {
  const header = buildSessionHeader(today, currentTime, metadata, '');

  let body;
  if (summary) {
    body = [
      buildSummaryBlock(summary),
      '',
      buildHandwrittenSections(),
    ].join('\n');
  } else {
    body = [
      SUMMARY_START_MARKER,
      '## セッション要約（YWT）',
      '',
      '### Y（やったこと）',
      '- [ ]',
      SUMMARY_END_MARKER,
      '',
      buildHandwrittenSections(),
    ].join('\n');
  }

  const content = `${header}${SESSION_SEPARATOR}${body}\n`;
  if (writeFileSafe(sessionFile, content)) {
    log(`Created: ${sessionFile}`);
  } else {
    log(`Failed to create: ${sessionFile}`);
  }
}

if (require.main === module) {
  main().catch((err) => {
    log(`Error: ${err.message}`);
    process.exit(0);
  });
}

module.exports = {
  updateExistingSession,
  createNewSession,
  buildHandwrittenSections,
  findLegacyHandwrittenStart,
};
