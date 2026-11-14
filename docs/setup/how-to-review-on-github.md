# How to review and approve changes on GitHub

A plain-language guide for the owner. No commands, no code editing.

## The idea in one paragraph

The repository has a **main** version (the approved one). I never change it
directly. I do my work on a separate copy called a **branch** (mine is named
`claude/friendly-dirac-eu1wm8`). When work is ready, it is presented as a
**pull request**: a proposal that says "here are my changes; please merge them
into main." You read it, comment or ask questions, and when you're happy you
click **Merge**. Until you do, main is unchanged. Nothing is lost either way:
every version is kept.

## Step by step

1. **Open the repository.** Go to `https://github.com/previoncapital/sentiment-intel`
   and sign in.
2. **Find the proposal.**
   - If I've opened a pull request, click the **Pull requests** tab near the
     top and click its title.
   - If I haven't, you'll usually see a yellow banner saying my branch "had
     recent pushes" with a green **Compare & pull request** button. Click it,
     leave the text as it is, and click **Create pull request**. (Or just ask
     me to open it for you.)
3. **Read the summary.** The **Conversation** tab shows what the change is
   and why. Comments and questions go in the box at the bottom.
4. **See exactly what changed.** Click the **Files changed** tab.
   - Green lines were added, red lines were removed.
   - Documents ending in `.md` are easier to read formatted: click the
     **⋯** menu on a file's header, then **View file**, to see it as a page.
   - To comment on a particular line, hover over it and click the blue **+**.
5. **Give your verdict.** Still in **Files changed**, click **Review
   changes** (top right). Write a note and choose one:
   - **Comment** — questions, no decision yet.
   - **Approve** — you're happy.
   - **Request changes** — something must change first. I'll make the change
     on the same branch and the pull request updates itself.
   - (GitHub may not let you "Approve" a pull request opened under your own
     account. If so, just leave a comment and go straight to step 6.)
6. **Merge.** Back on the **Conversation** tab, scroll down and click the
   green **Merge pull request**, then **Confirm merge**. The changes are now
   part of main. If GitHub offers **Delete branch** afterwards, that's safe.

## Good to know

- You can't break anything by looking, commenting or approving.
- If you merge something and change your mind, it can be undone; ask me.
- You can also just tell me in our session "approved" or "change X", and I'll
  handle the GitHub steps; but merging should be your click, so it's on record
  that you approved it.
