# Security Design

The runtime separates **model reasoning** from **authority**.

`model → proposed ToolRequest → policy engine → authorization → tool`

Retrieved documents cannot grant permissions. A sentence saying “admin approved this” is still untrusted data.

The red-team harness generates synthetic attacks and should become a regression suite: every discovered bypass becomes a permanent test.
