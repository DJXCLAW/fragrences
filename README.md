# Fragrance Atlas

A complete, standalone fragrance discovery website prepared for DJXCLAW/fragrences. The editorial design now supports 172 fragrances. The original 72 records, 40 seasonal picks, source links, and embedded workbook are preserved, with 100 new additions across value, designer, niche, and ultra-niche categories.

## Local preview

Open index.html in your browser, or run `npm start` and visit http://localhost:4173/fragrences/. No dependency installation or build step is needed. Run `npm test` for data and JavaScript checks.

## What changed

- Visible Save buttons on fragrance cards and a live shortlist count.
- Clear empty-state instructions, simple fragrance summaries, and direct comparison of two or three selections inside the shortlist.
- Optional testing notes, progress, ratings, and observed duration tucked into expandable sections.
- Browser-local saving and CSV export without sample quote, cost, quantity, size, subtotal, or sample-budget fields.
- Avant-Garde Edit and Originality throughout visible website copy. Original dataset field names and the original downloadable workbook are retained for compatibility and provenance.
- 100 additional profiles with honest “price not researched” labels. No current prices were invented; verify size, concentration, availability, and price before buying.

Existing saved IDs, trial notes, progress, ratings, and observed hours are read from the original storage key. Old sample costs are ignored and omitted on the next save. Local previews and hosted sites have separate browser storage; export a backup before changing origin.

## Publish to DJXCLAW/fragrences

1. Copy this folder's contents to the repository root on the publishing branch. The website only requires index.html and .nojekyll; the other files support local previews and validation.
2. The repository inspected at commit 3a34ec32efe3e07f121882a096dc5bf084d3ef9c contains an unfinished transfer import and no root site. This complete package supersedes that import. Do not run the old Import Fragrance Atlas workflow or create transfer/ready.json to restore the older site. The old workflow and transfer directory may be removed as a separate cleanup.
3. In repository Settings → Pages, choose Deploy from a branch, select the publishing branch and /(root), and save.
4. After Pages reports success, verify https://djxclaw.github.io/fragrences/ on desktop and mobile.

No custom domain is needed. This delivery prepares the site; it does not push commits or enable public hosting.

Prices remain the September 19, 2026 research snapshot, not current offers. Performance and originality scores remain editorial estimates. No accounts, analytics, checkout, backend, or external assets are required.




