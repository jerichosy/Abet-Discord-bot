# Dependency update policy

Dependency CI runs on every pull request and requires its entire verification job to succeed. The protected default branch requires `Dependency CI Gate` from GitHub Actions on an up-to-date branch.

Auto-merge remains disabled: this application lacks sufficient behavioral regression coverage for unattended dependency updates. Build and smoke checks improve detection, but bot commands/external integrations or Electron playback still need dedicated tests. Dependabot PRs require manual review.

Major and potentially breaking pre-1.0 updates may still be proposed by Dependabot for manual review; this policy does not suppress security updates.
