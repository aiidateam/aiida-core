# Code review guidelines

## Standards

- Technical facts and data overrule personal preferences.
- Don't block a PR over minor stylistic preferences — but do request changes for issues you are aware of.
- Be responsive to review requests.
  AiiDA users who put in the effort of contributing back deserve our attention the most, and timely review is a big motivator.
- Look at every line of code that is being modified.

## Communication

- Offer encouragement for things done well, don't just point out mistakes.
- Fine to mention what could be improved but is not mandatory -- prefix such comments with "Nit:" for "nitpick".
- Share knowledge that helps the submitter improve their understanding of the code.
  Clarify where you do or don't expect action.

## Checklist

### Scope

- Are you being asked to review more than ~400 lines of code?
  Don't be shy to ask the submitter to split the PR -- review effectiveness [drops substantially beyond a few hundred lines](https://smartbear.com/learn/code-review/best-practices-for-peer-code-review/).
- Are there parts of the codebase that have not been modified but *should* be adapted to the changes?
- Does the code change require a documentation update?

### Design

- Is the PR focused on a single issue?
- Does this change belong in the codebase?
- Is it well-integrated?

### Functionality

- Does the code do what the developer intended?
- Are there edge cases where it could break?
- Ideally, dogfood new features during review (check out the branch and try them) -- this is difficult to assess from code alone.

### Complexity

- Any complex lines, functions, or classes that are not easy to understand?
- Over-engineering: is the code too complex for the problem at hand?

### Tests

- Are there tests for new functionality?
- For bug fixes: is there a test that breaks if the bug resurfaces?
- Are the tests correct, useful, and easy to understand?

### Naming

- Good names are long enough to communicate what the item does, without being so long that they become hard to read.

### Comments

- Do comments explain *why* code exists rather than *what* it is doing?

### Style and consistency

- Does the contribution follow AiiDA {doc}`coding style <coding_style>` (mostly enforced automatically via pre-commit hooks)?
- Prefix style suggestions with "Nit:".

## Sources

- [Google Engineering Practices](https://google.github.io/eng-practices/review/reviewer/standard.html)
- [SmartBear: Best Practices for Peer Code Review](https://smartbear.com/learn/code-review/best-practices-for-peer-code-review/)
- [Code Review Guidelines for Humans](https://phauer.com/2018/code-review-guidelines/)
