@AGENTS.md


## Code

The smallest change that satisfies the requirement. Prefer extending an existing function or module over adding a new one. No abstraction, configuration knob, or extensibility hook until there is a second caller that needs it.

No defensive code for conditions that cannot currently occur. No compatibility shims for versions we do not support.

Comments explain *why*, never *what*. If a comment restates the line below it, delete the comment. If the code needs a comment to be readable, first try renaming things.

Delete code that a change makes dead. Do not leave it commented out — that is what git is for.

## Tests

Test the functionality, not the implementation. The minimum suite that would actually fail if the feature broke, and no more.

Mock anything slow or external: network, filesystem beyond a tmpdir, databases, subprocesses, time, third-party APIs. CI time is a real cost.

One test per behavior. No parametrized matrices covering combinations that cannot differ. No test helper frameworks, custom assertion DSLs, or fixture hierarchies built for a single test file — a test that needs its own framework to be readable is over-engineered.

A test that cannot fail is worse than no test. Before adding one, know what break it catches.

It's better to run pytest via "-n auto" to speed up


## Development phases

Don't worry about migration between development phases. All phases in this PR are still a PR, there're no users yet.
