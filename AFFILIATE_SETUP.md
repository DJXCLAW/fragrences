# Affiliate links: FragranceNet through Rakuten

The website is prepared to make a tracked FragranceNet search link for every
one of the 172 fragrance profiles. It intentionally keeps those links hidden
until the account is approved, so visitors are never sent through invalid
tracking URLs.

## One-time account steps

1. Create a **Rakuten Advertising Publisher** account and add the live site:
   `https://djxclaw.github.io/fragrences/`
2. Apply to the **FragranceNet.com** advertiser program in the Rakuten
   Publisher Dashboard and wait for approval.
3. In the approved advertiser profile, copy:
   - the 11-character **Publisher / Encrypted ID**;
   - the advertiser **MID** for FragranceNet.

Do not share a password, tax form, or payment details. The two IDs above are
tracking identifiers used in public links.

## Activate the links

Open `affiliate-config.js` and place the two IDs between the quotes for
`publisherId` and `advertiserMid`. Then publish both `index.html` and
`affiliate-config.js` together. Each profile will show **Check current
availability** and state the affiliate disclosure directly beneath it.

The first version routes visitors to a FragranceNet search for the exact brand,
fragrance, and concentration. Once the product feed is available in Rakuten,
replace those search destinations with exact bottle URLs and check the 172
matches before promoting them.

## Disclosure

The site uses this disclosure beside every active link:

> Affiliate link to FragranceNet. Fragrance Atlas may earn a commission at no
> extra cost to you; editorial rankings are independent.

