'use strict';

const fs = require('fs');
const path = require('path');

/**
 * Decision Log Validation Module
 *
 * Validates that technology recommendations in the current session are consistent
 * with prior decision records. Provides soft validation (warnings, not blocking).
 *
 * Design:
 * - Extract tech keywords from session content (language/framework names)
 * - Compare against prior Decision Log files in .github/decisions/tech-selection/
 * - Alert user if mismatch is detected
 * - Gracefully handle missing directories or malformed entries
 */

/**
 * Extract technology recommendations from session content.
 * Returns a set of detected technology names.
 *
 * @param {string} sessionContent - Full session markdown content
 * @returns {Set<string>} Detected technology names
 */
function extractTechnologies(sessionContent) {
  const detected = new Set();

  if (!sessionContent || typeof sessionContent !== 'string') {
    return detected;
  }

  // Check each technology by creating a fresh regex for each pattern
  // to avoid /g flag statefulness issues
  const patterns = [
    { regex: /node\.?js|javascript(?!\.)/gi, name: 'Node.js' },
    { regex: /\bpython\b/gi, name: 'Python' },
    { regex: /c#|csharp|\.net|dotnet/gi, name: 'C#/.NET' },
    { regex: /\b(?:go|golang)\b/gi, name: 'Go' },
    { regex: /\brust\b/gi, name: 'Rust' },
    { regex: /\bjava\b/gi, name: 'Java' },
    { regex: /typescript|(?:^|\W)ts(?:\W|$)/gi, name: 'TypeScript' },
    { regex: /\breact\b/gi, name: 'React' },
    { regex: /\bvue\b/gi, name: 'Vue' },
    { regex: /\bangular\b/gi, name: 'Angular' },
    { regex: /\bexpress\b/gi, name: 'Express' },
    { regex: /fastapi|django|flask/gi, name: 'Python Framework' },
  ];

  for (const { regex, name } of patterns) {
    if (regex.test(sessionContent)) {
      detected.add(name);
    }
  }

  return detected;
}

/**
 * Parse technology from a Decision Log file.
 * Looks for "Technology Selected:" or similar markers.
 *
 * @param {string} content - Decision Log file content
 * @returns {string|null} Detected technology or null
 */
function parseTechnologyFromDecisionLog(content) {
  if (!content || typeof content !== 'string') {
    return null;
  }

  // Match patterns like:
  // - "Technology Selected: Node.js"
  // - "Technology: C#"
  // - "Technology Choice: Go"
  const match = content.match(/Technology(?:\s+(?:Selected|Choice))?\s*:\s*([^\n:]+)/i);
  if (match) {
    return match[1].trim();
  }

  return null;
}

/**
 * Find all Decision Log files in .github/decisions/tech-selection/.
 * Returns in reverse chronological order (newest first).
 *
 * @param {string} repoRoot - Repository root path
 * @returns {Array<{ path: string, basename: string }>} Decision log files
 */
function findDecisionLogFiles(repoRoot) {
  const decisionDir = path.join(repoRoot, '.github', 'decisions', 'tech-selection');

  if (!fs.existsSync(decisionDir)) {
    return [];
  }

  try {
    const files = fs.readdirSync(decisionDir)
      .filter(f => f.endsWith('.md'))
      .map(basename => ({
        basename,
        path: path.join(decisionDir, basename),
      }))
      .sort((a, b) => b.basename.localeCompare(a.basename)); // Reverse chronological

    return files;
  } catch (err) {
    // Silently handle read errors
    return [];
  }
}

/**
 * Read file safely (check for symlinks, handle errors gracefully).
 *
 * @param {string} filePath - File path
 * @returns {string|null} File content or null on error
 */
function readFileSafe(filePath) {
  try {
    // Check for symlink
    const stat = fs.lstatSync(filePath);
    if (stat.isSymbolicLink()) {
      return null;
    }

    return fs.readFileSync(filePath, 'utf8');
  } catch {
    return null;
  }
}

/**
 * Validate technology consistency between current session and prior decisions.
 *
 * Returns validation result with warnings if detected.
 * This is a soft validation (non-blocking).
 *
 * @param {string} sessionContent - Full session markdown content
 * @param {string} repoRoot - Repository root path
 * @returns {object} Validation result: { isValid, warnings: string[] }
 */
function validateTechnologyConsistency(sessionContent, repoRoot) {
  const result = {
    isValid: true,
    warnings: [],
  };

  // 1. Extract technologies from current session
  const currentTechs = extractTechnologies(sessionContent);
  if (currentTechs.size === 0) {
    // No technologies detected — nothing to validate
    return result;
  }

  // 2. Find prior Decision Log files
  const decisionFiles = findDecisionLogFiles(repoRoot);
  if (decisionFiles.length === 0) {
    // No prior decisions — nothing to compare
    return result;
  }

  // 3. Compare current technologies against prior decisions
  for (const decisionFile of decisionFiles) {
    const content = readFileSafe(decisionFile.path);
    if (!content) {
      continue; // Skip unreadable files
    }

    const priorTech = parseTechnologyFromDecisionLog(content);
    if (!priorTech) {
      continue; // Skip if technology not found in decision log
    }

    // Check for mismatch: if session mentions a different technology
    let mismatchFound = false;
    for (const tech of currentTechs) {
      if (!priorTech.toLowerCase().includes(tech.toLowerCase()) &&
          !tech.toLowerCase().includes(priorTech.toLowerCase())) {
        mismatchFound = true;
        break;
      }
    }

    if (mismatchFound) {
      const warning = `⚠️  Technology Consistency Warning\n` +
        `  Prior decision recorded (${decisionFile.basename}): ${priorTech}\n` +
        `  Current session mentions: ${Array.from(currentTechs).join(', ')}\n` +
        `  Please review if this is an intentional change.`;
      result.warnings.push(warning);
    }
  }

  return result;
}

/**
 * Validate Decision Log file format.
 * Secondary validation: checks if file is well-formed.
 *
 * Returns validation result with issues if any.
 *
 * @param {string} filePath - Path to Decision Log file
 * @returns {object} Validation result: { isValid, errors: string[] }
 */
function validateDecisionLogFormat(filePath) {
  const result = {
    isValid: true,
    errors: [],
  };

  const content = readFileSafe(filePath);
  if (!content) {
    result.isValid = false;
    result.errors.push('Unable to read file or file is a symlink.');
    return result;
  }

  // Check for required sections
  const requiredSections = [
    { pattern: /^#+\s+/, label: 'Heading' },
    { pattern: /Technology\s+(?:Selected|Choice)?:?/i, label: 'Technology declaration' },
  ];

  for (const { pattern, label } of requiredSections) {
    if (!pattern.test(content)) {
      result.isValid = false;
      result.errors.push(`Missing ${label} section.`);
    }
  }

  return result;
}

module.exports = {
  extractTechnologies,
  parseTechnologyFromDecisionLog,
  findDecisionLogFiles,
  validateTechnologyConsistency,
  validateDecisionLogFormat,
  readFileSafe,
};
