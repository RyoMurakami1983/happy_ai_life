'use strict';

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const os = require('os');

// --- 定数 ---
const SUMMARY_START_MARKER = '<!-- SESSION:SUMMARY:START -->';
const SUMMARY_END_MARKER = '<!-- SESSION:SUMMARY:END -->';
const SESSION_SEPARATOR = '\n---\n';
const MAX_USER_MESSAGES = 10;
const MAX_TOOLS = 20;
const MAX_FILES = 30;
const MAX_MESSAGE_LENGTH = 200;
const SESSION_MAX_AGE_DAYS = 7;

// --- ファイル操作 ---

function ensureDir(dirPath) {
  try {
    if (!fs.existsSync(dirPath)) {
      fs.mkdirSync(dirPath, { recursive: true });
    }
    return true;
  } catch (err) {
    log(`Failed to create directory: ${dirPath} — ${err.message}`);
    return false;
  }
}

function readFileSafe(filePath) {
  try {
    return fs.readFileSync(filePath, 'utf8');
  } catch {
    return null;
  }
}

function writeFileSafe(filePath, content) {
  try {
    ensureDir(path.dirname(filePath));
    fs.writeFileSync(filePath, content, 'utf8');
    return true;
  } catch (err) {
    log(`Write failed: ${filePath} — ${err.message}`);
    return false;
  }
}

// --- Git 情報 ---

function getGitBranch(cwd) {
  try {
    return execSync('git rev-parse --abbrev-ref HEAD', {
      cwd,
      encoding: 'utf8',
      timeout: 5000,
      stdio: ['pipe', 'pipe', 'pipe'],
    }).trim();
  } catch {
    return 'unknown';
  }
}

function getGitRoot(cwd) {
  try {
    return execSync('git rev-parse --show-toplevel', {
      cwd,
      encoding: 'utf8',
      timeout: 5000,
      stdio: ['pipe', 'pipe', 'pipe'],
    }).trim();
  } catch {
    return cwd;
  }
}

// --- 日付・ID ---

function getDateString() {
  const now = new Date();
  return now.toISOString().slice(0, 10);
}

function getTimeString() {
  const now = new Date();
  return now.toISOString().slice(11, 19);
}

function shortId(uuid) {
  if (!uuid || typeof uuid !== 'string') return 'unknown';
  return uuid.slice(0, 8);
}

// --- プロジェクト名 ---

function getProjectName(cwd) {
  const root = getGitRoot(cwd);
  return path.basename(root);
}

// --- セッションディレクトリ ---

/** プロジェクトローカルのセッション保存先 */
function getProjectSessionsDir(cwd) {
  const root = getGitRoot(cwd);
  return path.join(root, '.github', 'sessions');
}

/** Copilot のグローバル session-state ディレクトリ */
function getGlobalSessionStateDir() {
  return path.join(os.homedir(), '.copilot', 'session-state');
}

// --- events.jsonl パーサー ---

/**
 * Copilot の events.jsonl をパースしてセッション要約を抽出する。
 *
 * events.jsonl は Copilot が自動保存する JSONL で、以下のイベントタイプを含む:
 * - session.start: セッション開始メタデータ
 * - user.message: ユーザー発言 (data.content)
 * - tool.execution_start: ツール実行開始 (data.toolName, data.arguments)
 * - assistant.message: アシスタント応答
 */
function extractSessionSummary(eventsPath) {
  const content = readFileSafe(eventsPath);
  if (!content) return null;

  const lines = content.split('\n').filter(Boolean);
  const userMessages = [];
  const toolsUsed = new Set();
  const filesModified = new Set();
  let parseErrors = 0;

  for (const line of lines) {
    try {
      const entry = JSON.parse(line);

      // ユーザーメッセージ
      if (entry.type === 'user.message') {
        const text = typeof entry.data?.content === 'string'
          ? entry.data.content
          : '';
        const cleaned = stripAnsi(text).trim();
        if (cleaned) {
          userMessages.push(cleaned.slice(0, MAX_MESSAGE_LENGTH));
        }
      }

      // ツール使用
      if (entry.type === 'tool.execution_start' && entry.data?.toolName) {
        const toolName = entry.data.toolName;
        // report_intent は内部用なのでスキップ
        if (toolName !== 'report_intent') {
          toolsUsed.add(toolName);
        }

        // apply_patch からファイルパスを抽出
        if (toolName === 'apply_patch' && entry.data.arguments) {
          const patchText = typeof entry.data.arguments === 'string'
            ? entry.data.arguments
            : JSON.stringify(entry.data.arguments);
          extractFilesFromPatch(patchText, filesModified);
        }

        // create_file / replace_string_in_file 等の filePath 引数
        const args = entry.data.arguments;
        if (args && typeof args === 'object') {
          const fp = args.filePath || args.file_path || args.path;
          if (fp && typeof fp === 'string' && isModifyingTool(toolName)) {
            filesModified.add(fp);
          }
        }
      }
    } catch {
      parseErrors++;
    }
  }

  if (parseErrors > 0) {
    log(`Skipped ${parseErrors}/${lines.length} unparseable lines`);
  }

  if (userMessages.length === 0) return null;

  return {
    userMessages: userMessages.slice(-MAX_USER_MESSAGES),
    toolsUsed: Array.from(toolsUsed).slice(0, MAX_TOOLS),
    filesModified: Array.from(filesModified).slice(0, MAX_FILES),
    totalMessages: userMessages.length,
  };
}

/** apply_patch のテキストから変更ファイルパスを抽出 */
function extractFilesFromPatch(text, fileSet) {
  // "*** Add File: <path>" / "*** Update File: <path>" / "*** Delete File: <path>"
  const regex = /\*\*\*\s+(?:Add|Update|Delete)\s+File:\s+(.+)/g;
  let match;
  while ((match = regex.exec(text)) !== null) {
    const fp = match[1].trim();
    if (fp) fileSet.add(fp);
  }
}

function isModifyingTool(name) {
  const modifiers = new Set([
    'apply_patch', 'create_file', 'replace_string_in_file',
    'multi_replace_string_in_file', 'edit_notebook_file',
  ]);
  return modifiers.has(name);
}

// --- セッションファイル生成 ---

function buildSessionHeader(today, currentTime, metadata, existingContent) {
  const headingMatch = existingContent
    ? existingContent.match(/^#\s+.+$/m)
    : null;
  const heading = headingMatch ? headingMatch[0] : `# Session: ${today}`;

  const date = extractHeaderField(existingContent, 'Date') || today;
  const started = extractHeaderField(existingContent, 'Started') || currentTime;

  return [
    heading,
    `**Date:** ${date}`,
    `**Started:** ${started}`,
    `**Last Updated:** ${currentTime}`,
    `**Project:** ${metadata.project}`,
    `**Branch:** ${metadata.branch}`,
    `**Worktree:** ${metadata.worktree}`,
    ...(metadata.reason ? [`**Reason:** ${metadata.reason}`] : []),
    '',
  ].join('\n');
}

function extractHeaderField(content, label) {
  if (!content) return null;
  const escaped = label.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const match = content.match(new RegExp(`\\*\\*${escaped}:\\*\\*\\s*(.+)$`, 'm'));
  return match ? match[1].trim() : null;
}

function mergeSessionHeader(content, today, currentTime, metadata) {
  const sepIndex = content.indexOf(SESSION_SEPARATOR);
  if (sepIndex === -1) return null;

  const existingHeader = content.slice(0, sepIndex);
  const body = content.slice(sepIndex + SESSION_SEPARATOR.length);
  const newHeader = buildSessionHeader(today, currentTime, metadata, existingHeader);
  return `${newHeader}${SESSION_SEPARATOR}${body}`;
}

function buildSummarySection(summary) {
  let section = '## セッション要約（YWT）\n\n';

  section += '### Y（やったこと）\n';
  for (const msg of summary.userMessages) {
    section += `- ${msg.replace(/\n/g, ' ').replace(/`/g, '\\`')}\n`;
  }
  if (summary.filesModified.length > 0) {
    section += '\n**変更ファイル:**\n';
    for (const f of summary.filesModified) {
      section += `- ${f}\n`;
    }
  }
  section += '\n';

  section += '### W（わかったこと）\n';
  section += '<!-- furikaeri-ywt skill で記入。/exit で直接終了した場合は手動で記入 -->\n';
  section += '- \n\n';

  section += '### T（つぎにやること）\n';
  section += '<!-- furikaeri-ywt skill で記入。/exit で直接終了した場合は手動で記入 -->\n';
  section += '- \n\n';

  if (summary.toolsUsed.length > 0) {
    section += `### 使用ツール\n${summary.toolsUsed.join(', ')}\n\n`;
  }

  section += `### 統計\n- ユーザーメッセージ数: ${summary.totalMessages}\n`;
  return section;
}

function buildSummaryBlock(summary) {
  return `${SUMMARY_START_MARKER}\n${buildSummarySection(summary).trim()}\n${SUMMARY_END_MARKER}`;
}

// --- セッションファイル検索 ---

/**
 * 指定ディレクトリから maxAge 日以内の *-session.md を検索。
 * 最新順にソートして返す。
 */
function findRecentSessions(dir, maxAge) {
  if (!fs.existsSync(dir)) return [];

  const cutoff = Date.now() - (maxAge || SESSION_MAX_AGE_DAYS) * 24 * 60 * 60 * 1000;
  const results = [];

  try {
    const entries = fs.readdirSync(dir);
    for (const name of entries) {
      if (!name.endsWith('-session.md')) continue;
      const fullPath = path.join(dir, name);
      try {
        const stat = fs.statSync(fullPath);
        if (stat.mtimeMs >= cutoff) {
          results.push({ path: fullPath, mtime: stat.mtimeMs, basename: name });
        }
      } catch {
        // stat 失敗はスキップ
      }
    }
  } catch {
    // ディレクトリ読み取り失敗
  }

  return results.sort((a, b) => b.mtime - a.mtime);
}

// --- ユーティリティ ---

function stripAnsi(text) {
  if (typeof text !== 'string') return '';
  // eslint-disable-next-line no-control-regex
  return text.replace(/\x1b\[[0-9;]*m/g, '');
}

function escapeRegExp(value) {
  return String(value).replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function log(message) {
  process.stderr.write(`[session-hook] ${message}\n`);
}

// --- stdin 読み取り ---

const MAX_STDIN = 1024 * 1024;

function readStdin() {
  return new Promise((resolve) => {
    let raw = '';
    process.stdin.setEncoding('utf8');
    process.stdin.on('data', (chunk) => {
      if (raw.length < MAX_STDIN) {
        raw += chunk.substring(0, MAX_STDIN - raw.length);
      }
    });
    process.stdin.on('end', () => resolve(raw));
    process.stdin.on('error', () => resolve(raw));
  });
}

module.exports = {
  SUMMARY_START_MARKER,
  SUMMARY_END_MARKER,
  SESSION_SEPARATOR,
  SESSION_MAX_AGE_DAYS,
  ensureDir,
  readFileSafe,
  writeFileSafe,
  getGitBranch,
  getGitRoot,
  getDateString,
  getTimeString,
  shortId,
  getProjectName,
  getProjectSessionsDir,
  getGlobalSessionStateDir,
  extractSessionSummary,
  buildSessionHeader,
  mergeSessionHeader,
  buildSummaryBlock,
  findRecentSessions,
  stripAnsi,
  escapeRegExp,
  log,
  readStdin,
};
