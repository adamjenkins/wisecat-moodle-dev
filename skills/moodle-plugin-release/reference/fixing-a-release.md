# Fixing a release after the tag exists

Read this when a tag already exists and something in that release is wrong, when a release workflow run failed,
or when you are not sure whether a commit or tag has reached the remote.

## First, find out what is on the remote

A note, a commit message or your own memory that says "not pushed yet" is a snapshot. Somebody may have pushed
since. Read the remote itself before touching any tag or rewriting any commit:

```bash
git fetch origin --tags
git ls-remote origin 'refs/tags/v1.4.2*'          # any line: the tag is published
git branch -r --contains <release-commit>          # any line: the commit is on a remote branch
git status -sb                                     # ahead/behind against the tracking branch
```

For a public GitHub repository the same facts are readable anonymously, for example
`curl -s https://api.github.com/repos/<owner>/<repo>/git/refs/tags/v1.4.2`. A successful read is evidence. A
failed read (an authentication error, no network, a rate limit) is not evidence that the tag or commit is
absent; treat the state as unknown and do not rewrite anything.

## Decide by what is published

| State | What to do |
|---|---|
| Tag and commit both local only | Delete the tag (`git tag -d v1.4.2`), fix the commit (`git commit --amend` or a new commit), re-tag, read back |
| Commit pushed, tag local only | Do not amend. Make a follow-up commit, move the local tag onto it (`git tag -d` then `git tag -a`), read back |
| Tag pushed | Leave it. Put the fix in a new commit under the changelog's `[Unreleased]`, bump `version` and `release`, and release a new version |
| Tag pushed and the release workflow ran | Same as above. The directory already holds that version; a moved tag does not replace it |

Why a published tag is never moved: other clones, Packagist and the Plugins directory have already recorded
what the tag pointed to. Moving it makes two different trees carry the same version number, and the version
users installed can no longer be reproduced.

## Tagging a commit that is already pushed

When the branch was pushed first (the normal order) and the tag is to be added afterwards:

1. Find that commit's CI run on the hosting service and read its result for this exact commit hash.
2. Tag only on a green run. A red run means the fix goes into a new commit, which gets its own CI run and
   then the tag.
3. A local pass on a development site is not a substitute. The CI site has only standard plugins and runs the
   database and PHP rows of the matrix; failures that appear only there (a missing `require_once` hidden by
   another plugin, PostgreSQL-only behaviour, a Behat step that needs a clean site) are the usual reason a
   locally green commit is red.

## A failed release workflow run

- Read the run's log. The common causes are a missing or expired `MOODLE_MARKETPLACE_TOKEN` secret and a
  version the directory rejects (a `version` not higher than the last release, or a validation error in the
  ZIP).
- Token problem: create a new token on the Moodle Marketplace under "Account Settings > Security"
  (https://marketplace.moodle.com/account/security; it is shown once), update the repository secret, and
  re-run the workflow with `workflow_dispatch` and the existing tag. Do not re-tag.
- The workflow's last step prints the HTTP status and the response body, and fails on anything but 201; a
  rejected version lists its reasons under "Validation Violations" in that step's log
  (`moodlehq/moodle-plugin-release`, workflow revision 2026091801, read, not run).
- Package or version problem: the tag's tree is wrong, so fix it in a new commit and release a new version.
- The tag-push run uses the workflow file in the tagged tree, so a tag cut while that file was broken or
  missing gets no good run from the push. A `workflow_dispatch` run uses the workflow file on the branch you
  select: fix the file on the default branch, then dispatch it with the existing tag as input. (Reasoned from
  GitHub's documented behaviour for each event, not run.)

## Pushing several releases at once

GitHub creates no push event for tags when one push updates more than three tags, so the tag-triggered
workflow does not run for any of them. Push the branches, wait for their CI runs, then push the tags one per
`git push origin <tag>`. If a batch was already pushed and nothing ran, trigger each release with
`workflow_dispatch` and its tag rather than deleting and re-pushing tags.

## After the push

Until the push is confirmed by a read of the remote, write the release up as "committed and tagged, push
pending", never as pushed. Once confirmed, check that the release workflow run went green and that the version
appears in the public plugin list (`https://download.moodle.org/api/1.3/pluglist.php`) and, for a Composer
package, in Packagist's `p2` JSON.
