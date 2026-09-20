# Fragrance Atlas

**Find your uncommon.** A responsive fragrance-discovery launch page built from the 72-fragrance Fragrance Atlas workbook.

## Preview on your computer

Download this repository as a ZIP and extract it, then double-click `preview.html`. It is a self-contained preview with the styles, code, fragrance data, and workbook download embedded. On Windows, `START_PREVIEW.bat` opens the modular `index.html` instead.

For a localhost preview, install Node.js 18 or newer, open a terminal in this folder, and run:

```sh
npm start
```

Open **http://localhost:4173**. No `npm install` step is needed. The server binds only to `127.0.0.1`; press Ctrl+C to stop it.

## What is included

- All 72 fragrance profiles, recorded bottle sizes and concentrations, reference prices, source links, notes, and performance caveats.
- Search, category/price/season/night/longevity/projection filters, sorting, progressive loading, and comparison of up to three fragrances.
- Forty seasonal and nighttime picks and 21 Weird Lab profiles.
- A three-question, rules-based scent finder.
- A browser-local sample shortlist with budget tracking, trial notes, personal ratings, and CSV export.
- Responsive layouts, keyboard-accessible controls, dialog focus management, reduced-motion support, and print styles.
- The original spreadsheet content and a JSON dataset export.

## Source data and limitations

The source workbook is `downloads/Fragrance_Atlas_72_Colognes.xlsx`. Its research snapshot is **September 19, 2026**. The site converts that dataset; it does not independently re-research the recorded product claims.

Prices are archived reference quotes, not live retail offers, sample prices, or lowest-price claims. A quote belongs to its listed bottle size and concentration. Missing USD quotes remain missing; foreign-currency quotes are not silently converted.

Longevity, projection, seasonal fits, everyday ease, weirdness, plain-language profiles, and drydowns retain the workbook's editorial caveats. They are not controlled measurements, verified averages, firsthand wear tests, or guarantees. Notes are scent vocabulary, not complete ingredient lists. Body-fluid and fuel descriptions represent artistic concepts rather than proof of literal ingredients.

Bottle illustrations are original CSS artwork, not the brands' real packaging. Brand names identify the fragrances discussed. Fragrance Atlas is a working project title, not a trademark-clearance claim.

## Privacy and commerce

There is no backend, sign-in, email collection, analytics, payment processing, checkout, or affiliate tracking. Shortlists stay in the visitor's browser when local storage is available. Private browsing, file URLs, clearing browser data, or changing the site origin can affect saved items; export CSV to keep a backup.

This is a discovery guide, not a fragrance retailer. Outbound links lead to the source pages recorded in the workbook, where prices and availability may have changed.

## Files and editing

```text
index.html                     Modular page for static hosting
preview.html                   Self-contained local preview
assets/styles.css              Styling and bottle illustrations
assets/app.js                  Search, comparison, finder, and planner
assets/data.js                 Fragrance data, loaded without fetch
 downloads/fragrances.json      Readable dataset export
 downloads/Fragrance_Atlas_72_Colognes.xlsx
server.cjs                     Dependency-free localhost server
package.json                   npm start / npm run check
START_PREVIEW.bat               Windows open-in-browser helper
.nojekyll                      GitHub Pages static-site marker
QA.md                          Original validation scope and limitations
```

Keep `index.html`, `assets`, and `downloads` together. Edit copy in `index.html`, styling in `assets/styles.css`, and behavior in `assets/app.js`. Keep the JSON export synchronized with `assets/data.js`. The standalone preview is a generated snapshot and needs rebuilding after changes.

Run syntax checks with:

```sh
npm run check
```

## GitHub Pages

The repository is **DJXCLAW/fragrences**. To publish the static site, open **Settings > Pages > Build and deployment**, select **Deploy from a branch**, choose **main** and **/(root)**, and save.

Once GitHub Pages reports a successful deployment, the expected project URL is:

**https://djxclaw.github.io/fragrences/**

Committing the source is separate from enabling Pages. The expected address is not a claim that deployment has completed.

GitHub documentation: https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site
