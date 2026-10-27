# Dependency update policy

Dependency CI runs on every pull request and requires its entire verification job to succeed. The protected default branch requires `Dependency CI Gate` from GitHub Actions on an up-to-date branch.

Successful project builds are sufficient evidence for auto-merge eligibility under the owner-approved policy. Useful application tests, source lint and dependency consistency checks remain enabled; comprehensive coverage and extensive tests of third-party libraries are not prerequisites. All required CI checks must pass on an up-to-date branch; failing or missing required checks and branch protections must never be bypassed.

Verified Dependabot PRs are eligible only if every dependency has a strictly increasing minor or patch version within the same numeric major, including pre-1.0 updates (0.x to 0.y and 0.0.x patches). The owner intentionally accepts the risk of breaking changes within major zero, including registry compatibility-major labels for such updates. Numeric major changes (including 0.x to 1.0), prereleases, downgrades, ranges, missing or unreliable metadata, unclassifiable container tags, date-based versions and maintainer changes require manual review. Every dependency in a grouped PR must qualify. A successful build is evidence, not a guarantee against every regression.

Major updates may still be proposed by Dependabot for manual review; this policy does not suppress security updates.
