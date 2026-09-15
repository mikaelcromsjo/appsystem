# Debugging Guide

**Load: when investigating errors or bugs**

## Debugging rules

- **Error immediately after writing code → read that code first.** Before investigating routes, DB, config, or anything external, re-read every line just written. The bug is almost always there.

- **If the same files are being checked a second time without new findings → stop and ask the user.** Repeating searches is a signal that the hypothesis is wrong, not that it needs more searching.

- **Do not chase error messages literally.** A misleading error (e.g. "resource not found" from a template crash) is common — look at what changed, not what the message says.
