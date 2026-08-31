import { fileURLToPath } from "node:url";

const CANONICAL_SKILLS_PATH = fileURLToPath(new URL("../../skills", import.meta.url));

export const CANONICAL_SKILL_NAMES = Object.freeze([
  "block-kit",
  "create-slack-app",
  "slack-api",
  "slack-cli",
  "slack-docs",
  "slack-messaging",
  "slack-search",
  "test-slack-app",
]);

const isRecord = (value) => value !== null && typeof value === "object";

/**
 * Register the canonical root through the runtime-only skills config extension.
 *
 * OpenCode 1.18.18's public Config type does not expose `skills`; this boundary
 * intentionally relies only on runtime shape checks and otherwise does nothing.
 */
export const registerCanonicalSkills = (input) => {
  if (!isRecord(input)) {
    return false;
  }

  // `skills` is intentionally accessed here and nowhere else in the plugin.
  const skills = input.skills;
  if (skills === undefined) {
    if (!Object.isExtensible(input)) {
      return false;
    }
    input.skills = { paths: [CANONICAL_SKILLS_PATH] };
    return true;
  }

  if (!isRecord(skills)) {
    return false;
  }

  const paths = skills.paths;
  if (paths === undefined) {
    if (!Object.isExtensible(skills)) {
      return false;
    }
    skills.paths = [CANONICAL_SKILLS_PATH];
    return true;
  }

  if (!Array.isArray(paths) || paths.includes(CANONICAL_SKILLS_PATH)) {
    return false;
  }

  if (!Object.isExtensible(skills)) {
    return false;
  }
  skills.paths = [...paths, CANONICAL_SKILLS_PATH];
  return true;
};
