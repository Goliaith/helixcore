## Contributing to HelixCore

### Authorship and Commit Signing Requirements (Immutable)

**"MrSilhouette" is the canonical, locked author and copyright holder for this project.**

This name appears in:
- LICENSE
- pyproject.toml
- README
- All commit metadata (via Signed-off-by)

**It is not allowed to be removed, altered, or overwritten in the project's attribution or history.**

All commits pushed to this repository **must**:
1. Be authored with `user.name = "MrSilhouette"`
2. Be **GPG-signed** (`git commit -S`)
3. Contain the trailer:
   ```
   Signed-off-by: MrSilhouette <your.email@example.com>
   ```

### Local Setup (required for contributors)

```bash
git config user.name "MrSilhouette"
git config user.email "mr.silhouette@users.noreply.github.com"  # or your real email

git config commit.gpgsign true
git config user.signingkey YOUR_GPG_KEY_ID
```

Example commit:
```bash
git commit -S -m "Fix important thing

Signed-off-by: MrSilhouette <mr.silhouette@users.noreply.github.com>"
```

### GitHub Repository Settings

Maintainers must keep the following enabled for the `main` branch (Settings > Branches > Branch protection rule for `main`):

- Require signed commits
- Require linear history (recommended)
- Include administrators

This ensures that history cannot be force-pushed or rewritten without invalidating signatures, thereby protecting the locked "MrSilhouette" attribution.

### Why This Policy Exists

The identity of the project as created and stewarded by MrSilhouette is fundamental. The combination of copyright in LICENSE, author metadata, DCO sign-offs, and required GPG signatures makes the name effectively immutable.

### Pull Requests

- PRs must come from branches that follow the above rules.
- The final merge commit (or squash) will carry the MrSilhouette sign-off as appropriate.
- External contributors should still sign their own work, but the project-level attribution remains MrSilhouette.

By contributing, you agree that your work is submitted under the project's MIT license and that the primary authorship credit belongs to MrSilhouette.

Thank you for helping keep the project's identity intact.