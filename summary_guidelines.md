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

## Style

- Each bullet: one or two sentences — what changed and why it matters or what
  downstream impact it may have
- Link the PR as [org/repo#num](url)
- Aim for 5–15 bullets total
