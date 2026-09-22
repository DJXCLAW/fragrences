/* Add approved Rakuten IDs here. They are tracking identifiers, not passwords. */
window.FRAGRANCE_ATLAS_AFFILIATE = {
  retailer: 'FragranceNet',
  publisherId: '',
  advertiserMid: '',
  destination(item) {
    return `https://www.fragrancenet.com/search?search=${encodeURIComponent(`${item.brand} ${item.name} ${item.concentration}`)}`;
  }
};

