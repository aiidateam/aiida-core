.. _how-to:collaborate:

***********************************
How to collaborate through a collab
***********************************

Two or more colleagues working on the same project can share one logical provenance graph.
Each keeps their own AiiDA profile on their own machine, and can pull the provenance the others produced or push their own to them.
Such a group of profiles is called a *collab*.

A collab is peer to peer: there is no server, and any pair of peers can sync directly.
Only **sealed** provenance travels; running or unfinished processes stay local until they seal.
Syncing is additive in both directions — no peer can delete a node from your profile, whatever they do on theirs.
The one thing a sync can overwrite is the extras of nodes you share, and only if the collab agreed on that: see :ref:`extras <how-to:collaborate:extras>`.

.. _how-to:collaborate:trust:

Trust model and network
=======================

The peers of a collab must already be inside one trusted private network, such as a `WireGuard <https://www.wireguard.com/>`__ or `tailscale <https://tailscale.com/>`__ network.
That network provides the encryption and the peer identity; the collab endpoint itself speaks plain HTTP bound to the private address, refuses to listen on all interfaces, and authenticates every request with the shared token of the collab as a bearer token.
AiiDA assumes exactly one thing about that network: that peers are reachable at the addresses they gave. How that reachability exists is invisible to it, and IPv4 and IPv6 addresses work equally well.
Joining the collab is the consent: any peer holding the code can pull from you.
Pushing *into* your profile is opt-in — ``verdi collab config --accept-push`` allows it (see :ref:`serving <how-to:collaborate:serving>`); peers that are refused are told so and simply skip you.

**Credentials are never transferred.**
Computers travel as plain entities (hostname, transport and scheduler configuration), but the credentials to access them live in ``AuthInfo`` entries, which never leave your profile.
Each peer attaches their own credentials to a shared computer with ``verdi computer configure``.

.. _how-to:collaborate:setup:

Setting up
==========

The first peer creates the collab on the profile they already work in:

.. code-block:: console

    $ verdi collab init
    Report: A collab agrees on what it shares beyond provenance nodes. The choice is made once, now, ...
      extras `local`: extras stop travelling once the node has, and stay yours to edit
      extras `sync`:  On nodes you share, the extras of whoever edited them last replace everyone else's: ...
    extras mode (local, sync) [local]: local
      groups `local`: your groups stay yours, and no sync creates one
      groups `grow`:  a node curated into a group joins it on every peer, additions only
    groups mode (local, grow) [local]: grow
    accept pushes from peers into this profile? [y/N]: y
      100.64.0.1 (tailscale0)
      192.168.1.24 (wlan0)
    This machine's address on the private network of the collab: 100.64.0.1
    Report: started the daemon of profile `main`, which serves http://100.64.0.1:9137.
    Success: profile `main` serves the collab at http://100.64.0.1:9137.
    Report: Run `verdi collab link` for the code that lets others join, and `verdi -p main config set collab.accept_push <bool>` to change whether peers may push into this profile.

What the collab shares beyond provenance nodes is settled here and never again — see :ref:`choosing the policy <how-to:collaborate:policy>`; ``--extras-mode`` and ``--groups-mode`` script both answers.
The address is the other thing you have to supply (``--bind`` scripts it).
It cannot be guessed: a machine has several addresses, and which network the collaborators share is not observable from here — a default-route guess picks the institution LAN exactly when a private overlay is in use.
It is validated by binding it, so an address that is not this machine's fails right there instead of at the next daemon start, and an IPv6 address is served and announced as ``http://[fd7a::2]:9137``.
A free port is picked and persisted (``--port`` chooses one), so the URL your peers were given keeps working across restarts.
Whether peers may push *into* your profile is asked here too, defaulting to refusing them (``--accept-push``/``--no-accept-push`` script the answer, and ``verdi config set collab.accept_push`` changes it later).

The endpoint that serves your provenance is supervised by the daemon, which the setup starts for you — or restarts, if one was already running, since a daemon fixes the list of what it supervises when it starts and would otherwise serve everything except the collab.
A daemon that cannot be started is reported as a warning rather than failing the setup: the profile is a member of the collab either way.
Ask for the code that lets others join:

.. code-block:: console

    $ verdi collab link
    eyJjb2xsYWIiOiAiNGRhO...

That one code carries everything a newcomer needs: which collab, whom to ask, the key to ask with, and the terms it runs on.
Any member can hand one out — once the collab exists, its creator is nobody special — so a newcomer joins through whoever happens to be online.
It is a command of its own, and not a line of ``verdi status``, because it carries the token: ``verdi status`` is what you paste into a bug report, and anyone reading one would be holding the key to your collab.

Joining creates a new profile:

.. code-block:: console

    $ verdi collab join eyJjb2xsYWIiOiAiNGRhO...
    name of the profile to create [collab]: fusion
    Report: this collab shares extras `local` and groups `grow`.
    accept pushes from peers into this profile? [y/N]: y
    This machine's address on the private network of the collab: 100.64.0.2
    set up profile `fusion` quickly, with SQLite storage and no external services? [Y/n]: y
    Report: learned about peer `bob` at http://100.64.0.1:9137
    Report: started the daemon of profile `fusion`, which serves http://100.64.0.2:9137.
    Success: profile `fusion` serves the collab at http://100.64.0.2:9137.
    Report: Run `verdi collab link` for the code that lets others join, and `verdi -p fusion config set collab.accept_push <bool>` to change whether peers may push into this profile.

A collab is one logical provenance graph, so joining always sets up a fresh profile rather than folding the work you already have into someone else's.
You are asked what to call it (``--profile-name`` scripts the answer, and ``--non-interactive`` takes ``collab``).
The terms and the address are asked for before anything is created, since neither a declined policy nor a mistyped address must leave a half-made profile behind; the quick setup then runs ``verdi presto``, which makes the new profile your default one — ``verdi profile set-default`` puts that back if you would rather keep working in the profile you had.
The join announces you to the member whose code you used and brings back its whole roster, so a single contact is enough to know everybody.
That announcement is the one step that can still fail after the profile exists, because it carries the profile's UUID: if the member whose code you used cannot be reached, the new profile is deleted again — storage and all — so that a retry with a code from somebody who is online starts from nothing.

After changing a ``collab.*`` option by hand, restart the daemon — except ``collab.token`` and ``collab.accept_push``, which the endpoint re-reads on every request, so that a rotation and a withdrawal of consent to be pushed to both take effect at once.
The commands in :ref:`serving <how-to:collaborate:serving>` write these options and restart the endpoint for you, so a hand-edit is not the way to change any of them.

.. _how-to:collaborate:members:

Members, nicknames and addresses
================================

Each member is identified by the UUID of its profile: permanent, pinned at the first contact, and what the sync cursors and the log key on.
If the same URL later answers as a different profile, the sync is refused rather than mixing two histories.
Held against every contact as well is the policy of the collab (see :ref:`below <how-to:collaborate:policy>`), which is refused if a peer declares another one.
So is the identity of the collab itself, so a token that was shared too widely cannot splice two collabs into one.

A **nickname** is a local display alias: how you address and see that collaborator in commands, prompts, ``verdi status`` and the log.
It is local to your machine and travels nowhere — the same person may be called different things on different machines, and renaming a peer here changes nothing anywhere else.
Two peers may not share one, so a member whose announced name is already taken on your machine is stored under a deduplicated one (``alice-2``).

Membership spreads by itself: every pull and push carries your own entry and the peers you know, so a member who joined through someone else reaches you at the next sync.
Whatever a contact adds or corrects is reported in the command output and appears in ``verdi status``.

If your address changes, ``verdi collab config --bind`` (or ``--port``) is the whole of it: it validates the new address, moves the endpoint onto it and announces it to your peers right there — see :ref:`serving <how-to:collaborate:serving>`.
The announcement corrects the peers that answer, and gossip carries the correction on to the others.
Until one contact happens you are unreachable: nobody can discover an address nobody knows.
The other way round, a peer you know to have moved can be corrected by hand:

.. code-block:: console

    $ verdi collab peer set alice --url http://100.64.0.9:9137
    $ verdi collab peer set alice --nickname ali

A hand-corrected URL is a local guess, and the owner's own announcement supersedes it at the first contact that carries one.
A peer that has never answered at the address it announced is flagged as such in ``verdi status`` and in sync output; that flag is the only way a wrong address given at join can come to light, since nothing can call back at join time.

.. _how-to:collaborate:serving:

Serving: the address, consent to pushes, going offline
======================================================

What your profile serves is changed in one place:

.. code-block:: console

    $ verdi collab config

Called bare it asks for all three settings, offering what is configured now as the default of each; ``--accept-push``/``--no-accept-push``, ``--bind`` and ``--port`` set them without asking anything.
With ``--non-interactive`` and no option there is nobody to ask, so it prints the three settings — consent to pushes, the address, and whether this profile is in service — and changes nothing.

Consent to being pushed to is re-read by the endpoint on every request, so granting or withdrawing it holds from the next request on, with no restart.

A changed address is validated by binding it, so one that is not this machine's is refused before anything is written.
It is then written, the collab endpoint of a running daemon is restarted onto it — the workers keep running — and it is announced to every peer that answers, so that nobody has to wait for a sync to find you again.
An offline profile skips the restart, its endpoint having no address to re-read while it idles; the announcement still goes out, and ``verdi collab online`` is what puts it on the new address.
A peer that does not answer learns it from gossip at its next sync, as every address change did before.

To stop serving without stopping the daemon:

.. code-block:: console

    $ verdi collab offline
    $ verdi collab online

Being offline is persisted in ``collab.online`` and survives a daemon restart: the endpoint process starts, reads it and idles instead of binding a socket.
Everything else keeps running — the workers, and the hooks that record the tombstones and the group memberships a later sync needs — which is the difference between this and switching ``collab.enabled`` off.
Your own ``verdi collab pull`` and ``push`` are unaffected: neither has ever needed your endpoint.
To your peers you look like a member that is simply down, and ``verdi status`` warns you that they cannot reach you.

.. _how-to:collaborate:rotation:

Rotating the key, leaving, splitting
====================================

The token is the whole of the authentication: holding it is being a member.
So the way to end somebody's membership — a leaked code, a collaborator who left the project, a group that wants to go its own way — is to replace the token and not hand the new one to them:

.. code-block:: console

    $ verdi collab rotate

This mints a new token, prints a fresh join code and tells every peer it currently syncs with that the old key is retired.
Hand the code to the members that stay, out of band, person to person: sending it through the collab itself would deliver it to whoever you just excluded, since that channel is keyed by the very token being retired.
For the same reason the signal your peers receive is advisory — it makes their ``verdi status`` ask them to rekey, and does nothing else.
What actually enforces a rotation is that your endpoint stops honouring the old token from the next request on.

Whoever receives the code applies it:

.. code-block:: console

    $ verdi collab rekey <code>

Nothing is lost by it: the roster, the cursors, the tombstones and the log are all kept, and syncing resumes exactly where it stopped.
What the new key does reset is the *standing* of every peer, described next.
Rekeying announces you to the member whose code you used, which is how the collab learns you are back.

Rotating and rekeying each put every peer *dormant* on the machine that ran them — nobody has been seen under the new key there yet.
Dormant peers are never contacted and do not appear in ``verdi status``, but nothing about them is thrown away: when one of them turns up under the current token, directly or vouched for by a peer that has already seen it, it is recognized by the UUID of its profile and comes back with its nickname and its cursor intact.
A member offline for a week simply rekeys when it returns.

Two consequences worth knowing:

* **Exclusion completes when the last member has rekeyed.** Until then the excluded member's still-valid old token opens the endpoints of everyone who has not, because a peer-to-peer collab has no central switch to throw.
* **Splitting is the same operation.** A subgroup rotates and shares the new code among themselves; the other branch never presents it, and rests dormant — invisible and never contacted — on the side that rotated. On its own side nothing changed: a member that runs neither ``rotate`` nor ``rekey`` keeps the others in its roster, and they answer its every sync with a 401 — reported as refusing the current key, in ``verdi status`` and in the sync output — until it rekeys or switches collab off. Both branches keep the collab UUID, since both descend from the same provenance lineage, so a later cross-branch rekey is a benign reunion: the negotiation dedupes everything already shared. Splicing two *unrelated* collabs stays impossible, which is what that UUID check is for.

**Leaving** needs no command: set ``collab.enabled`` to ``False`` and restart the daemon.
Your endpoint stops, your syncs stop, and nothing is announced — to the others you look like an offline peer until the next rotation leaves you dormant like anyone who never rekeys.
Coming back is switching it on again; nothing changed on either side.

Day-to-day use
==============

.. code-block:: console

    $ verdi status              # one line per active peer — online, offline, refusing the key, or never having answered
    $ verdi collab pull         # fetch and import the new sealed provenance of every peer
    $ verdi collab pull alice   # ... or of the named peers only
    $ verdi collab push         # send my new sealed provenance to every peer that accepts pushes
    $ verdi collab push alice   # ... or to the named peers only
    $ verdi collab log          # the history of every pull, push and extras refresh
    $ verdi collab link         # the code that admits a newcomer — it carries the key, so hand it over out of band
    $ verdi collab config       # what this profile serves: consent to pushes, and the address it is reached at
    $ verdi collab offline      # stop serving, without stopping the daemon workers (`online` serves again)
    $ verdi collab rotate       # replace the key of the collab (see above)
    $ verdi collab rekey <code> # adopt a replaced key

Before any payload travels, ``pull`` and ``push`` negotiate with the peer and ask for confirmation with the node count and size they negotiated; the question defaults to no, so a bare Enter leaves both profiles untouched.
Pass ``--force`` to skip the prompts (for scripts), or ``--dry-run`` to only see what a sync would transfer, per peer, without transferring anything.
A peer that is offline, busy, refuses pushes, declares a different policy or runs an aiida-core whose archives this one cannot read is skipped with a warning, and the remaining peers are synced.
A delta that arrives but cannot be imported — bytes that are not a readable archive, or provenance linked to a node the receiving profile holds nowhere — is skipped the same way, with a warning naming the peer it came from; nothing lands from it, and the next sync delivers it once whatever diverged has been sorted out.
The only difference is the exit code: a transfer that started and failed makes the command exit non-zero, so a scheduled sync reports a problem, while peers that were merely skipped without transferring anything leave it at zero.

Every contact also exchanges the aiida-core and archive format versions of both sides.
A delta travels as an archive, so that format is the only compatibility that matters: the storage of each profile is its own business, and a collab of PostgreSQL and SQLite profiles is perfectly normal.
Whichever side would send an archive the other cannot read is refused up front, instead of failing mid-transfer — a pull tells you to upgrade your aiida-core, a push tells you to ask your collaborator to upgrade theirs.
An older peer is no obstacle in either direction: its archives are migrated forward when they are imported.

On SQLite storage, ``pull`` refuses to import while daemon workers are running, because SQLite allows only one writer at a time; pass ``--pause-my-daemon`` to stop the workers around the import and restart them afterwards.
PostgreSQL profiles need no pause.

The endpoint serves at most ``collab.max_concurrency`` peers at once (default 2, pulls and pushes combined); peers beyond that are answered busy and simply retry.

One profile runs one sync command at a time: a second ``pull`` or ``push`` started while the first is still going — a scheduled sync overlapping a manual one, most often — stops immediately and tells you to wait, rather than negotiating against a profile the first is still writing to.
This is about *your* commands only; pushes your daemon receives from peers are serialized separately and are unaffected.

.. note::

    Collabs are not supported on Windows: the locks that guard the collab state file and the configuration file, the one that serializes imports and the one that keeps your own sync commands apart, are all ``fcntl``-based, so on Windows concurrent syncs and daemon-received pushes run unguarded — a ``verdi collab rotate`` racing a sync the daemon is serving can be reverted by it.

.. _how-to:collaborate:deletion:

Deletion never propagates
=========================

Push and pull can only add nodes.
There is no force push, and no peer can delete a node from your profile (an extras key is another matter under the ``sync`` policy).

When you delete nodes from your own profile, they are recorded in a local *tombstone* store, and pulls skip them so that your deletions are not undone by the next sync.
To change your mind, run ``verdi collab pull --include-deleted``: the tombstoned nodes are imported again and their tombstones dropped.
The tombstones, the sync cursors and the log belong to your profile and are deleted with it, so a profile you later create under the same name starts afresh instead of inheriting what a dead one held.
If provenance in a delta depends on a node you deleted (for example, a peer ran a new calculation on data you removed), that node is imported again regardless, because provenance is never imported with holes in it — and it keeps its tombstone, since changing your mind is what ``--include-deleted`` is for.

A tombstone says "do not deliver this to me again", not "pretend I do not have it".
So a node that is back in your profile — brought back that way, or by ``--include-deleted`` — takes part in everything a node of yours takes part in: its extras are replicated under the ``sync`` policy, and it can be curated into a shared group and that membership travels.
What its tombstone keeps doing is the one thing it is for, which is to stop the node itself from being delivered a second time.

.. note::

    Tombstones are kept for good and never pruned or aged out, because a deletion is never undone: a peer that was offline for a year must still not hand the node back.
    What goes on the wire is bounded by the sync at hand, though, and not by everything you ever deleted: a peer offers you a list of what its delta holds, and you name back only those of them you deleted, so that it cuts them out before it builds the archive.
    A profile that deleted a very large campaign therefore keeps a correspondingly large collab state file, and that file is the whole of what stays behind.
    Short of ``--include-deleted``, which drops the tombstones of the nodes it brings back, only deleting the profile clears them.

.. _how-to:collaborate:extras:

Extras: the one thing that can change after it travelled
========================================================

Nodes are immutable once stored, so a pull can only add them — with one exception, the extras, which stay mutable for the life of a node.
A collab therefore agrees on one of two policies, chosen once by whoever creates it (see :ref:`choosing the policy <how-to:collaborate:policy>`):

``local`` (the default)
    Extras stop travelling once the node has. A node carries whatever extras it had when it was first exported, and nothing after that: later edits stay on the side that made them, and a sync never touches an extra of a node you already hold.

``sync``
    The extras of shared nodes keep being replicated. On each node, the side that **modified the node** most recently wins, and its whole extras dict replaces the other's — so a key you deleted disappears on the other side too, rather than coming back.
    "Most recently" is the node's ``mtime``, compared across machines: this is the one place in a collab where two clocks meet, so keep them NTP-synced.

.. warning::

    The clock is the node's ``mtime``, not a record of what the extras were, so *anything* that touches a node makes that side the winner and publishes its whole extras dict — including writing one of your own underscore-prefixed extras, which are exempt from travelling but not from moving the clock.
    Pull before you edit, as you would with any last-writer-wins system.

Under ``sync``, keys starting with an underscore are exempt in both directions: an incoming snapshot never overwrites them and yours are never sent.
They are the private namespace of each profile — AiiDA's own caching extras live there.
(The exemption is about the replication of shared nodes; a brand-new node still carries the extras it has when it is first exported, minus the caching ones, which never travel under either policy.)

When you join a ``sync`` collab, the join warns you about all of this and asks for confirmation before anything is created; declining leaves no profile behind and writes nothing.
Afterwards, every ``pull`` and ``push`` prompt tells you how many nodes' extras the transfer would replace, and ``--dry-run`` reports the same without transferring anything.

.. _how-to:collaborate:groups:

Groups
======

Like the extras policy, a collab agrees on one groups policy, chosen once when it is created:

``local`` (the default)
    Groups stay where they were made. A sync carries nodes only, and your groups are yours.

``grow``
    Curated groups and their membership travel. When a sync carries a node, it carries the curated groups that node is in and its membership in them; and when you curate a node your collaborators **already hold** — or make a whole group over nodes you shared long ago — that reaches them too, on the next sync in either direction, without a single node travelling.
    The group is created on the other side if it is new there, under the same UUID everywhere, with its label deduplicated if that label is already taken there.
    Only additions travel — removing a node from a group never removes it anywhere else, exactly as deleting a node never propagates. Relabelling a group does not travel either.
    The groups AiiDA generates itself (``core.import`` and ``core.auto``) are left out: they record how provenance arrived in *your* profile and mean nothing in someone else's.

    ``pull`` and ``push`` count the memberships a sync would add in their prompt and in ``--dry-run``, and a sync that carries no node at all but does carry memberships is a real sync: it prompts, applies them and moves the cursor on.
    A membership whose node the other side does not hold is simply dropped there; it arrives with the node, whenever a later sync delivers it.
    A peer that *deleted* the node drops the membership for good and does not pass it on, exactly as it stops passing on the node itself — so a third peer that still holds that node learns of the curation from whoever made it, on their next direct contact, rather than through the one that deleted it.

    Removing a node from a shared group is not durable, and this is the one surprise of ``grow`` worth knowing before you rely on it.
    A group is offered whole, because a peer that does not hold it needs the full set to create it — so the next time a collaborator curates anything into that same group, the offer that reaches you carries every member of it, the one you removed included, and it is added back.
    Nothing tells you when that happens, and there is no way to say "not that one": under ``grow`` the set of members only ever grows.
    The only thing that keeps a node out for good is not putting it in a shared group in the first place.

    One way of curating does not travel: ``verdi archive import --group`` writes its memberships straight to the database rather than through the group, which is the only door a curation is noticed at.
    Nodes the archive brings with it are unaffected — they travel as new nodes, in the groups the delta carries — but a node your collaborators *already* hold, added to a group this way, stays put.
    ``verdi group add-nodes`` on those same nodes fixes it: adding a node that is already in the group changes nothing locally and is noticed all the same, so the membership goes out on the next sync.

.. _how-to:collaborate:policy:

Choosing the policy of a collab, once
=====================================

The two policies above — extras and groups — are the whole of what a collab shares beyond provenance nodes, and they are **chosen once, by whoever creates the collab, and never change**:

.. code-block:: console

    $ verdi collab init --extras-mode sync --groups-mode grow

Without the options, ``verdi collab init`` explains both and asks; both default to ``local``.
There is no way to change the answer afterwards, in band or out: the policy is stored as a single ``collab.policy`` option that ``verdi config set`` cannot write, and every member's endpoint declares it on every contact.
Nor is there a way around that by clearing the option: a profile whose policy no longer matches the collab's is simply refused by every peer, so unsetting it costs you the collab rather than buying you new terms.
A peer that declares a different policy than yours is refused with a message naming both — since the policy cannot change, that can only mean a ``config.json`` was edited by hand — and the sync continues with your other peers.

Whoever joins adopts the collab's policy and chooses nothing: the join code carries it, so the terms are shown before anything is created, and joining a ``sync`` collab asks for consent right there.
That is also why any member can hand out a join code — every copy of the policy is equally authoritative.

To collaborate on different terms, found a new collab and join it: ``verdi collab init`` on a fresh profile, with the policy you want.
What decides what enters *your* profile is always your own copy of the policy, never what a peer declares or serves — so a peer whose configuration was tampered with cannot make your profile take extras or groups it did not agree to.

.. _how-to:collaborate:caching:

Caching across peers
====================

By default, pulled calculations are **never** cache hits for your own submissions: the hash of a calculation includes the UUID of the computer it ran on, and your peer's computers are not yours.
Pulled nodes also arrive without any hash, so they are invisible to the caching engine.

A computer that arrives through the collab is labelled ``<label>@collab``, so ``verdi computer list`` tells your own machines apart from the ones a peer's calculations ran on.
Every member that imports the computer writes the same marker, and writing it onto a label that already carries it changes nothing, so a machine your collaborator calls ``lumi`` is ``lumi@collab`` on every member of the collab except the one that runs it.
Labels still have to be unique within your profile, so where two collaborators each run a ``lumi`` the second one to reach you is ``lumi-2@collab``: the marker stays at the end, and the number, once drawn, travels on with the machine unless it too is taken where the machine next lands.

If you decide that such a machine is equivalent to one of yours — "same inputs on their cluster give the result mine would" is a scientific judgement, which is why it is opt-in — declare it:

.. code-block:: console

    $ verdi collab map-computer lumi@collab=leonardo

Both halves have to be computers you hold, so the mapping is declared after the machine has reached you — through a pull from whoever runs it, or from any peer that already holds it — and never at ``verdi collab init``: until it arrives there is nothing here to name, and a mapping naming a computer you do not hold is refused, listing the peer computers that have arrived.
The left half must be the peer's machine, so it has to be one that arrived through the collab and carries ``@collab``; naming your own ``lumi`` there is refused, since it would write the remapped hashes onto your own calculations. If the halves are simply the wrong way round, the refusal says so and spells the pair you meant.
Waiting costs nothing — the command applies the mapping to the calculations you already pulled as well.

Calculations that ran on the peer computer ``lumi@collab`` then carry the hash they would have on your computer ``leonardo``, and an identical local submission is a cache hit on them.
Everything else about the node is untouched: it keeps its UUID, its attributes and its repository content, and it still records that it actually ran on the peer's machine.
One limitation: a calculation whose *inputs* carry a computer of their own — a ``RemoteData`` input of a restarted calculation, for example — still hashes differently from a local submission, because the hashes of inputs are not remapped, so such calculations silently stay cache misses.

.. warning::

    A cache hit on a pulled calculation clones its outputs, including a ``RemoteData`` that points at the **peer's** cluster.
    Retrieved outputs are complete and local, but workflows that restart from the remote working directory will not find it unless you can reach that filesystem.

.. _how-to:collaborate:timestamps:

Unreachable data and timestamp surprises
========================================

Stashed and remote data live on the filesystem of whoever ran the calculation.
Unless you have access to that filesystem (for example a shared cluster), a pulled ``RemoteData`` or stashed folder is unreachable from your side — the provenance is complete, the files on the peer's cluster are simply not yours to read.

A node's primary key is assigned by the database of the profile it lands in, so the same node has a different PK on every member of the collab.
When you talk to a collaborator about a specific node, use its UUID — or a unique prefix of it, which ``verdi node show 3f4a1b2c`` resolves like the full one.
Preserving PKs across profiles is not on the table: it would mean partitioning a 4-byte id space between the members, which survives neither their number nor SQLite's ``max(rowid) + 1`` allocator.

Import preserves timestamps, so ``ctime`` and ``mtime`` mean "when it happened on the peer's side", never "when it arrived here".
Two consequences:

- ``verdi process list --past-days 1`` will not show processes pulled today that ran last month — it asks when the process ran, not when it arrived.
- An incremental ``verdi profile dump`` selects nodes modified since the last dump and silently skips pulled nodes with older timestamps.
  After a pull, run ``verdi profile dump --no-filter-by-last-dump-time`` once; the dump tracker avoids re-dumping what it already wrote.
