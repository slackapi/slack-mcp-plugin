import re

from tests.skill import discover_skills

# Max skill `description` length; longer text is silently truncated (agentskills.io/specification).
MAX_DESCRIPTION_LENGTH = 1024

# Matches the trigger cue ("Use when", "whenever") a description should lead with.
TRIGGER_CUE = re.compile(r"\bwhen(ever)?\b", re.IGNORECASE)

# First-person voice; "I" needs a trailing contraction/verb (avoids "I/O", "Tier I"), and "us" is omitted ("US").
FIRST_PERSON = re.compile(
    r"\bI['’]"  # I'm, I'll, I've, I'd
    r"|\bI\s+(?:am|can|will|would|have|had|do)\b"  # I am, I can, I will, ...
    r"|\b(?:me|my|mine|myself|we|our|ours|ourselves)\b",
    re.IGNORECASE,
)


def is_kebab_case(text: str) -> bool:
    # Pattern ensures lowercase alphanumeric chunks separated by a single dash
    pattern = r"^[a-z0-9]+(-[a-z0-9]+)*$"
    return bool(re.match(pattern, text))


class TestFrontmatter:
    def setup_method(self) -> None:
        self.skills = discover_skills()

    def test_required_fields_present(self) -> None:
        for skill in self.skills:
            assert skill.frontmatter.name, f"{skill.path} is missing a frontmatter 'name'"
            assert skill.frontmatter.description, f"{skill.path} is missing a frontmatter 'description'"

    def test_name_matches_directory(self) -> None:
        for skill in self.skills:
            assert skill.frontmatter.name == skill.path.parent.name, (
                f"{skill.path} frontmatter name '{skill.frontmatter.name}' "
                f"does not match directory '{skill.path.parent.name}'"
            )

    def test_name_is_kebab_case(self) -> None:
        for skill in self.skills:
            assert is_kebab_case(skill.frontmatter.name), (
                f"{skill.path} name '{skill.frontmatter.name}' is not valid kebab-case"
            )

    def test_skill_names_are_unique(self) -> None:
        names = [skill.frontmatter.name for skill in self.skills]
        assert len(names) == len(set(names)), f"Duplicate skill names found in: {sorted(names)}"

    def test_description_length(self) -> None:
        for skill in self.skills:
            length = len(skill.frontmatter.description)
            assert length <= MAX_DESCRIPTION_LENGTH, (
                f"{skill.path} description is {length} characters, over the {MAX_DESCRIPTION_LENGTH}-character cap"
            )

    def test_description_leads_with_trigger_cue(self) -> None:
        for skill in self.skills:
            description = skill.frontmatter.description
            assert TRIGGER_CUE.search(description), (
                f"{skill.path} description should state when to use the skill "
                f'(start with "Use when"); got: {description!r}'
            )

    def test_description_is_impersonal(self) -> None:
        for skill in self.skills:
            match = FIRST_PERSON.search(skill.frontmatter.description)
            offending = match.group(0) if match else None
            assert match is None, (
                f"{skill.path} description uses first-person voice ({offending!r}); write it impersonally"
            )
