# Summary Guidelines

## Include

Prioritise in this order:

1. Breaking changes or API/interface modifications with potential downstream impact
2. Significant new physics or reconstruction features
3. Important bug fixes that affect correctness or usability

## Exclude

- Build-system, CMake, and packaging changes, including install-path fixes, CMake
  target migrations, and external-data or download-mechanism changes (e.g. moving a
  `find_package` inside a `BUILD_TESTING` block, replacing wget with `ExternalData`,
  switching to an upstream-provided CMake target)
- CI/CD configuration changes, runtime CI checks, and test-infrastructure additions
- Trivial bot dependency bumps (dependabot, renovate)
- Code style, linting, or minor cleanup
- Mechanical API migration PRs that only update call sites to a new but equivalent
  interface, with no new functionality or user-visible change. Indicator: diff is
  purely renaming or replacing deprecated symbols, no new parameters or behaviours.
- Internal implementation fixes (buffer bounds, unit bookkeeping, edge-case guards)
  that do not change user-observable physics output or cause crashes in production
  FCC workflows
- Fixes to example scripts, steering-file templates, or example configurations —
  unless the example is a canonical production steering file

## Repository-specific rules

- **key4hep/k4geo**: only include PRs where at least one changed file is under an
  FCC-related path (e.g. `FCCee/`, `FCC/`, `ALLEGRO`, `IDEA`, `CLD`) or is a
  detector driver file (under `detector/`) that is referenced by an FCC compact
  file. Exclude any PR whose changed files are entirely within non-FCC experiment
  folders such as `MuColl/`, `ILD/`, `CLIC/`, `LUXE/`, `SiD/` — even if the PR
  description mentions shared components.
- **All repositories**: exclude CMake flags or code guards added solely to enable
  compilation in non-FCC experiment stacks (e.g. Muon Collider, ILD, SiD), even
  if the change is in an otherwise FCC-relevant package.
- **Multi-experiment packages** (e.g. k4ActsTracking, k4geo outside FCC paths):
  only include PRs where the description or changed files clearly indicate FCC
  relevance. Exclude PRs that are explicitly targeted at non-FCC experiments
  (Muon Collider, ILD, CLIC, LUXE, SiD) even if they add significant new
  functionality.

## Tense and voice

- Keep descriptions concise and direct. Both past tense ("ECAL clustering chain added…") and
  present tense ("Renames DCHdigi_v02…") are acceptable when the subject leads. Avoid
  verbose passive constructions with an article: "The X was changed/added/fixed" — prefer
  "X changed/added/fixed" or "Renames X…" with X as the direct subject.
- Avoid filler connectors such as "Also", "Additionally", "Furthermore", "Now", "Moreover". Start each clause or sentence directly with its subject.

## Style

- A PR that belongs in Omitted must NOT appear in the Summary section at all — not even
  as a placeholder, cross-reference, or "see Omitted" note. The two sections are mutually
  exclusive: every PR appears in exactly one of them.
- If every PR from a given repository is excluded, that repository must be omitted from
  the Summary entirely — no bullet, no heading, no mention. It will be represented only
  through its individual entries in the Omitted section.
- One bullet per pull request. Exception: if a PR is a minor direct follow-up to
  another PR already included (e.g. a thread-safety fix that completes the previous
  PR's work), reference it as "(see also **org/repo#N**)" at the end of the parent
  entry rather than giving it its own bullet.
- Bullet format:
    **[org/repo#num](pr_url)** — one to two sentences describing the change,
    its motivation, and any downstream impact.
- Omit implementation-level detail (internal code paths, variable names, data
  structures). State what changed, why it matters, and any downstream impact.
  Where possible, name the affected FCC experiment or workflow (ALLEGRO, CLD, IDEA,
  etc.) and describe the observable symptom that was fixed (crashes, wrong output,
  excessive memory use) rather than the internal mechanism.
- No backtick or code formatting in descriptions — write class names, function names,
  and tool names as plain text.
- Descriptions must be plain prose — no nested or sub-bullets within a PR entry.
- Aim for 5–10 bullets. If more PRs qualify, apply the Include priority order to
  select the most significant; move the rest to Omitted with reason "lower priority".
