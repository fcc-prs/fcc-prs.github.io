# Summary Guidelines

## Include

Prioritise in this order:

1. Breaking changes or API/interface modifications with potential downstream impact
2. Significant new physics or reconstruction features
3. Important bug fixes that affect correctness or usability

## Exclude

- Pure build-system or CMake changes with no user-visible effect (e.g. moving a
  `find_package` inside a `BUILD_TESTING` block, adding a CMake minimum version bump)
- CI/CD configuration changes
- Trivial bot dependency bumps (dependabot, renovate)
- Code style, linting, or minor cleanup
- Mechanical API migration PRs that only update call sites to a new but equivalent
  interface, with no new functionality or user-visible change. Indicator: diff is
  purely renaming or replacing deprecated symbols, no new parameters or behaviours.

## Repository-specific rules

- **key4hep/k4geo**: only include PRs where at least one changed file is under an
  FCC-related path (e.g. `FCCee/`, `FCC/`, `ALLEGRO`, `IDEA`, `CLD`) or is a
  detector driver file (under `detector/`) that is referenced by an FCC compact
  file. Exclude any PR whose changed files are entirely within non-FCC experiment
  folders such as `MuColl/`, `ILD/`, `CLIC/`, `LUXE/`, `SiD/` — even if the PR
  description mentions shared components.

## Style

- A PR that belongs in Omitted must NOT appear in the Summary section at all — not even
  as a placeholder, cross-reference, or "see Omitted" note. The two sections are mutually
  exclusive: every PR appears in exactly one of them.
- If every PR from a given repository is excluded, that repository must be omitted from
  the Summary entirely — no bullet, no heading, no mention. It will be represented only
  through its individual entries in the Omitted section.
- Group all notable PRs from the same repository into a single bullet.
- Bullet format:
    **[org/repo](repo_url)** — narrative description of the combined changes,
    referencing each PR inline as [#num](pr_url).
- Each bullet: two to four sentences covering the most important changes in that
  repo and any downstream impact.
- If a repository has only one notable PR, a single sentence is fine.
- Include every repository that has at least one PR meeting the Include criteria above;
  do not cap the number of bullets.
