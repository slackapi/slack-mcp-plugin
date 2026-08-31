import { registerCanonicalSkills } from "./skill-compatibility.js";
import { registerCommandsAndMcp } from "./command-and-mcp.js";

export const SlackPlugin = async () => {
  return {
    config: async (input) => {
      registerCanonicalSkills(input);
      await registerCommandsAndMcp(input);
    },
  };
};
