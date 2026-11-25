"""Validate the generated site without starting a server."""
from html.parser import HTMLParser
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1] / 'dist'


class Page(HTMLParser):
    def __init__(self, file):
        super().__init__(convert_charrefs=True)
        self.ids = set()
        self.links = []
        self.scripts = []
        self.theme_colors = []
        self.refresh = []
        self.headings = []
        self.text = []
        self.feed(file.read_text(encoding='utf-8'))
        assert not re.search(r'(?<! )—|—(?! )', ''.join(self.text)), f'unspaced em dash: {file}'

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            attr = attrs['id']
            assert attr not in self.ids, f'duplicate id: {attr}'
            self.ids.add(attr)
        if tag == 'script':
            assert 'defer' in attrs, 'the optional chapter index script must not block rendering'
            self.scripts.append(attrs.get('src'))
        if tag == 'meta' and attrs.get('name') == 'theme-color':
            self.theme_colors.append(attrs.get('content'))
        if tag == 'meta' and attrs.get('http-equiv') == 'refresh':
            self.refresh.append(attrs['content'])
        if tag == 'h2' and 'id' in attrs:
            self.headings.append(attrs['id'])
        self.links.extend(attrs[a] for a in ('href', 'src') if a in attrs)

    def handle_data(self, data):
        self.text.append(data)


pages = {file: Page(file) for file in ROOT.rglob('*.html')}
chapters = ('introduction', 'prolog', 'history-and-development', 'existing-campus', 'resources', 'epilog', 'bibliography')
reading_pages = {'index.html', *(f'guide/{slug}/index.html' for slug in chapters[1:])}
redirect_pages = {'guide/index.html': '../#contents', 'guide/introduction/index.html': '../../#welcome-title'}
assert {file.relative_to(ROOT).as_posix() for file in pages} == reading_pages | redirect_pages.keys()
css = (ROOT / 'assets/site.css').read_text(encoding='utf-8')
paper = re.search(r':root\s*\{[^}]*--paper:\s*(#[0-9a-fA-F]{6})\s*;', css)[1]
for file, page in pages.items():
    relative_file = file.relative_to(ROOT).as_posix()
    expected_scripts = (['./assets/chapter-index.js'] if relative_file == 'index.html' else
                        ['../../assets/chapter-index.js'] if relative_file in {
                            f'guide/{slug}/index.html' for slug in chapters[1:]
                        } else [])
    assert page.scripts == expected_scripts, (relative_file, page.scripts)
    html = file.read_text(encoding='utf-8')
    assert 'class="masthead"' not in html and 'Digital edition by' not in html
    if relative_file in redirect_pages:
        destination = redirect_pages[relative_file]
        assert page.refresh == [f'0;url={destination}'] and page.links == [destination]
    if expected_scripts:
        assert page.theme_colors == [paper], (relative_file, page.theme_colors)
        assert html.count('<nav class="pagination"') == 1
        before, end = html.split('<footer class="chapter-end">', 1)
        assert '</article>' in before and end.index('class="chapter-colophon"') < end.index('class="pagination"')
        assert 'Back to top' not in html
    if expected_scripts and relative_file != 'index.html':
        assert re.search(r'<article class="prose"[^>]*aria-labelledby="chapter-heading">\s*'
                         r'<h1 class="chapter-label" id="chapter-heading">', html)
        assert 'chapter-meta' not in html
    index = re.search(r'<nav class="chapter-toc"[^>]*>(.*?)</nav>', html, re.S)
    if expected_scripts:
        assert index
        assert re.findall(r'href="#([^"]+)"', index[1]) == page.headings
        chapter_urls = re.findall(r'class="chapter-toc-chapter" href="([^"]+)"', index[1])
        assert (file.parent / chapter_urls[0]).resolve() == ROOT
        assert [(file.parent / url).resolve().name for url in chapter_urls[1:]] == list(chapters[1:])
        assert index[1].count('aria-current="page"') == 1
        assert '<details' not in index[1] and '<summary' not in index[1]
    for link in page.links:
        parsed = urlsplit(link)
        if parsed.netloc or parsed.scheme:
            continue
        path = unquote(parsed.path)
        target = (file.parent / path).resolve() if path else file
        if target.is_dir():
            target /= 'index.html'
        assert target.is_file(), (file, link)
        if parsed.fragment:
            assert unquote(parsed.fragment) in pages[target].ids, (file, link)

legacy = {
    'resources': {'libraries', 'food-and-drink', 'hangouts', 'campus-treasures-and-museums', 'the-engineers-tour'},
    'existing-campus': {'concordance-of-building-names-or-which-moses-was-moses-hall-named-after',
                        'academic-buildings', 'dorms', 'mottoes-and-memorials', 'classical-inscriptions',
                        'english-inscriptions', 'memorials', 'benches', 'class-gifts', 'campus-art',
                        'plants-and-trees', 'strawberry-creek-and-its-bridges',
                        'the-campanile-and-other-clocks', 'campus-gates'},
    'epilog': {'a-trip-down-the-wurster-stairwell'},
}
for slug, anchors in legacy.items():
    assert anchors <= pages[ROOT / f'guide/{slug}/index.html'].ids
assert not list(ROOT.rglob('*.pdf')) and not list(ROOT.rglob('*.epub'))
opening = (ROOT / 'index.html').read_text(encoding='utf-8')
assert re.findall(r'<h1[^>]*>(.*?)</h1>', opening) == ['A Loafer’s Guide to the U.C. Berkeley Campus']
assert 'welcome-title' in pages[ROOT / 'index.html'].ids
assert re.search(r'<nav class="pagination"[^>]*><a class="next" href="guide/prolog/" rel="next">', opening)
prolog = (ROOT / 'guide/prolog/index.html').read_text(encoding='utf-8')
assert '<h1 class="chapter-label" id="chapter-heading">Prolog</h1>' in prolog
assert re.search(r'<a class="prev" href="../../" rel="prev">.*?<strong>Introduction</strong>', prolog)
assert {p.name for p in (ROOT / 'assets').glob('*.css')} == {'site.css'}
print(f'{len(pages)} pages: internal links, legacy chapter anchors, and static output verified')
