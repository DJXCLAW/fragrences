import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import sync_brand_catalog as sync
import integrate_catalog as integrate


def product(name='Pipeline test fragrance', pid=900001):
    return dict(id=pid, title=name, handle='pipeline-test-'+str(pid), vendor='Lattafa', product_type='Eau de Parfum',
                tags=['Woody','100ML'], body_html='<p>Top Notes: Bergamot, Apple</p><p>Heart Notes: Rose</p><p>Base Notes: Cedar, Musk</p>',
                variants=[dict(id=pid+1,title='2ml sample',price='1',available=True),dict(id=pid+2,title='100ML',price='45',available=True)])


class CatalogTests(unittest.TestCase):
    def test_quote_uses_same_bottle_not_sample(self):
        variant, size, price = sync.quote(product())
        self.assertEqual((variant['title'],size,price),('100ML',100.0,45.0))

    def test_missing_fields_are_not_invented(self):
        p=product();p.update(product_type='',tags=[]);p['variants']=[dict(id=1,title='Default',price='NaN')]
        item=sync.normalize('Lattafa','https://example.test','all',p,'2026-10-09')
        self.assertIsNone(item['price']);self.assertIsNone(item['size']);self.assertIsNone(item['concentration'])
        for field in sync.RATINGS:self.assertIsNone(item[field])

    def test_note_pyramid(self):
        item=sync.normalize('Lattafa','https://example.test','all',product(),'2026-10-09')
        self.assertEqual(item['notes'],'Top: Bergamot, Apple; Heart: Rose; Base: Cedar, Musk')
        self.assertEqual(item['concentration'],'EDP')
        self.assertAlmostEqual(item['perMl'],.45)

    def test_non_fragrances_excluded(self):
        for name in ['Perfume Oil','Air Freshener','Body Mist','Gift Set','Sample','Bakhoor']:
            self.assertFalse(sync.eligible('Lattafa',product(name)))
        self.assertFalse(sync.eligible('Lattafa',dict(product(),vendor='Another house')))
        self.assertTrue(sync.eligible('Lattafa',product('Incense fragrance')))

    def test_pagination(self):
        pages=[{'products':[product(pid=n) for n in range(250)]},{'products':[product(pid=250)]}]
        urls=[]
        def fetch(url):urls.append(url);return pages.pop(0)
        self.assertEqual(len(list(sync.products('https://example.test','all',fetch))),251)
        self.assertIn('page=2',urls[1])

    def test_repeated_page_rejected(self):
        batch={'products':[product(pid=n) for n in range(1,251)]}
        with self.assertRaises(ValueError):list(sync.products('https://example.test','all',lambda url:batch))

    def test_identity_aliases(self):
        self.assertEqual(integrate.key('Lattafa',"Bade'e Al Oud Oud for Glory"),integrate.key('Lattafa','Badee Al Oud For Glory'))
        self.assertEqual(integrate.key('Lattafa','Fakhar Black'),integrate.key('Lattafa','Fakhar Men'))

    def test_empty_feed_does_not_replace_files(self):
        cwd=os.getcwd()
        try:
            with tempfile.TemporaryDirectory() as directory:
                os.chdir(directory);Path('brand-catalog.json').write_text('{"sentinel":true}')
                with patch.object(sync,'products',return_value=iter([])),self.assertRaises(ValueError):sync.main()
                self.assertEqual(Path('brand-catalog.json').read_text(),'{"sentinel":true}')
        finally:os.chdir(cwd)

    def test_integration_preserves_ids_and_is_idempotent(self):
        original=Path('index.html').read_text(encoding='utf-8')
        before=integrate.site_data(original)[0]
        fixtures=[sync.normalize(brand,'https://example.test','all',product(name,pid),'2026-10-09') for brand,name,pid in [('Lattafa','Khamrah',900001),('Lattafa','Pipeline test Lattafa',900002),('French Avenue','Pipeline test French Avenue',900003)]]
        cwd=os.getcwd()
        try:
            with tempfile.TemporaryDirectory() as directory:
                os.chdir(directory);Path('index.html').write_text(original,encoding='utf-8')
                Path('brand-catalog.json').write_text(json.dumps(dict(generatedAt='2026-10-09',fragrances=fixtures,counts={'Lattafa':2,'French Avenue':1},coverage='Test fixture only')))
                with contextlib.redirect_stdout(io.StringIO()):integrate.main()
                result=Path('index.html').read_text(encoding='utf-8');data=integrate.site_data(result)[0]
                ids={i['id'] for i in data['fragrances']}
                self.assertTrue({i['id'] for i in before['fragrances']} <= ids)
                self.assertIn('F007',ids);self.assertNotIn('LTF-900001',ids)
                self.assertEqual(len(ids),len(data['fragrances']))
                self.assertIn('id="house-filter"',result)
                with contextlib.redirect_stdout(io.StringIO()):integrate.main()
                self.assertEqual(result,Path('index.html').read_text(encoding='utf-8'))
        finally:os.chdir(cwd)


if __name__=='__main__':unittest.main()
