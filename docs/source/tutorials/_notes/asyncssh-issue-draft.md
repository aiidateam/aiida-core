# Asyncssh issue draft

For posting at https://github.com/ronf/asyncssh/issues/new.

---

**Title**: `UserKnownHostsFile /dev/null` + `StrictHostKeyChecking no` in ssh_config refuses connection instead of skipping host-key verification

**Body**:

Hi Ron,

A common OpenSSH pattern for ephemeral hosts (Docker containers in CI, dev VMs whose host keys regenerate on every restart) is:

```
Host my-ephemeral-host
    UserKnownHostsFile /dev/null
    StrictHostKeyChecking no
```

OpenSSH treats this as "skip host-key verification, do not persist anything to a known_hosts file." Asyncssh, however, parses the same config and refuses the connection with `HostKeyNotVerifiable`. The root cause appears to be the interaction between how `UserKnownHostsFile /dev/null` resolves and how `connect()` interprets the resolved value.

## Reproducer

`~/.ssh/config`:

```
Host my-host
    HostName 127.0.0.1
    Port 2222
    User someone
    IdentityFile ~/.ssh/some_key
    UserKnownHostsFile /dev/null
    StrictHostKeyChecking no
```

```python
import asyncio, asyncssh

async def main():
    async with asyncssh.connect('my-host') as conn:
        print(await conn.run('hostname'))

asyncio.run(main())
# -> asyncssh.HostKeyNotVerifiable: Host key is not trusted for host 127.0.0.1
```

## Asymmetry: config-resolved `[]` vs kwarg `[]`

What I find surprising: inspecting `SSHClientConnectionOptions(host='my-host').known_hosts` returns `[]` for the config above &mdash; and yet:

| call | known_hosts kwarg | outcome |
|---|---|---|
| `asyncssh.connect('my-host')` | (resolved from config) | `HostKeyNotVerifiable` |
| `asyncssh.connect('my-host', known_hosts=[])` | explicit `[]` | **success** (verification skipped) |
| `asyncssh.connect('my-host', known_hosts=None)` | explicit `None` | success (verification skipped) |

So the same `[]` value behaves differently depending on whether asyncssh produced it internally from ssh_config resolution or whether the caller passed it explicitly. From the caller's perspective this is hard to predict and reason about.

## What I think the expected behavior is

When `~/.ssh/config` specifies `UserKnownHostsFile /dev/null` (or any path that resolves to an empty/non-existent file) *combined with* `StrictHostKeyChecking no`, OpenSSH's semantics are "skip verification entirely." Mapping this onto asyncssh's existing semantics, this is equivalent to `known_hosts=None`.

A few possible directions, in roughly increasing scope:

1. **Treat config-resolved `[]` + `StrictHostKeyChecking no` as `known_hosts=None`.** Smallest, most targeted: only when the user explicitly opted out of strict checking does the empty-list case become "skip" rather than "refuse." Honors the intent of the combined directives.
2. **Recognize `/dev/null` (or any non-regular file) in `UserKnownHostsFile` as "skip verification."** OS-level semantics: writing to `/dev/null` is the universal "discard" sentinel; resolving it to `[]` then enforcing strict matching is the surprising step.
3. **Document the asymmetry explicitly.** If the current behavior is intentional, a doc note that "an empty list resolved from ssh_config triggers strict refusal, while an explicit empty list passed as kwarg skips verification" would at least make this predictable for callers.

I lean toward (1) or (2): the current behavior makes asyncssh diverge from OpenSSH on a config pattern that's widely used in CI / Docker / ephemeral-host setups.

## Context

This came up in aiida-core's tutorial materials, where Module 4 demonstrates SSH-based remote execution against an ephemeral SLURM container. The natural OpenSSH-style config (`/dev/null` + `StrictHostKeyChecking no`) failed only when the asyncssh transport backend was used; the OpenSSH backend worked fine on the same config. We initially worked around this in aiida-core (https://github.com/aiidateam/aiida-core/pull/7380, since closed) by detecting the resolved-`[]` case and substituting `known_hosts=None`, but that turned out to be a larger hammer than intended &mdash; the resolved-`[]` case also triggers for a first-time-on-host user with no `~/.ssh/known_hosts`, so the shim silently disabled host-key verification for them too. We've since switched to populating a dedicated known_hosts file via `ssh-keyscan`, which is the right thing for the tutorial &mdash; but that workaround doesn't address the underlying asymmetry in asyncssh.

Happy to test any patches against our setup. Asyncssh version: `<insert>`. Python: `<insert>`. OS: `<insert>`.

Thanks for asyncssh!
