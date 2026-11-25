#!/usr/bin/env python3
"""Render one manuscript to a static site or a private EPUB proof."""
from collections import namedtuple
from html import escape
from pathlib import Path
import os
import re
import shutil
from string import Template
import subprocess
import sys
import tempfile

BASE = Path(__file__).resolve().parent
SITE = BASE / 'dist'
TITLE = 'A Loafer’s Guide to the U.C. Berkeley Campus'
AUTHOR = 'Carolyn Dougherty'
MARKDOWN = 'markdown+smart+gfm_auto_identifiers'

ORDER = ('introduction', 'prolog', 'history-and-development', 'existing-campus', 'resources', 'epilog', 'bibliography')
Chapter = namedtuple('Chapter', 'slug title file')
CHAPTERS = [Chapter(slug, (BASE / f'content/{slug}.md').read_text().splitlines()[0].removeprefix('# '),
                    BASE / f'content/{slug}.md') for slug in ORDER]




def pandoc(*args, **kwargs):
    return subprocess.run(['pandoc', '--from=' + MARKDOWN, *args], cwd=BASE, check=True, text=True, **kwargs)


def html(source, notes=False):
    args = ['--lua-filter=templates/sidenotes.lua'] if notes else []
    return pandoc('-t', 'html5', '--wrap=none', *args, input=source, stdout=subprocess.PIPE).stdout


def tmpl(name, **values):
    return Template((BASE / f'templates/{name}.html').read_text()).substitute(values)


def route(slug=''):
    return f'guide/{slug}/' if slug and slug != 'introduction' else ''


def rel(current, target):
    return os.path.relpath(target or '.', current or '.') + '/'


def root_for(current):
    return rel(current, '').rstrip('/')


def top_headings(fragment):
    return re.findall(r'<h2 id="([^"]+)">(.*?)</h2>', fragment)


def book_outline(chapter, outlines):
    path = route(chapter.slug)
    branches = []
    for entry in CHAPTERS:
        is_current = entry == chapter
        url = page_link(path, entry)
        current = ' aria-current="page"' if is_current else ''
        section_url = '' if is_current else url
        links = ''.join(
            f'<li><a href="{section_url}#{anchor}"><span class="chapter-toc-label">'
            f'{outline_label(label)}</span></a></li>'
            for anchor, label in outlines[entry.slug]
        )
        subsections = f'<ul class="chapter-toc-sections">{links}</ul>' if links else ''
        branches.append(f'<li><a class="chapter-toc-chapter" href="{url}"{current}>'
                        f'<span class="chapter-toc-label">{escape(entry.title)}</span></a>'
                        f'{subsections}</li>')
    return ('<nav class="chapter-toc" id="contents" aria-label="Book contents">'
            f'<div class="chapter-toc-track"><ol>{"".join(branches)}</ol></div></nav>')


def outline_label(heading):
    return re.sub(r'<span class="heading-subtitle">.*?</span>', '', heading).strip()


def render(output, path, title, content, track_index=False):
    title_piece = f'{escape(title)} | ' if title else ''
    root = root_for(path)
    script = f'<script defer src="{root}/assets/chapter-index.js"></script>' if track_index else ''
    page = tmpl('page', title=title_piece + TITLE, root=root,
                main=content, chapter_index_script=script, skip_target='#chapter-text')
    write(output / path / 'index.html', page)


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def redirect(output, path, href, label):
    write(output / path / 'index.html',
          f'<!doctype html><html lang="en"><meta charset="utf-8"><title>{label} — {TITLE}</title>'
          f'<meta http-equiv="refresh" content="0;url={href}"><a href="{href}">{label}</a></html>')


def page_link(current, chapter):
    if not chapter:
        return rel(current, '') + '#contents'
    return rel(current, route(chapter.slug))


def adjacent(current, chapter, forward=False):
    url = page_link(current, chapter)
    direction = 'next' if forward else 'prev'
    label = 'Next' if forward else 'Previous'
    arrow = '→' if forward else '←'
    title = escape(chapter.title) if chapter else 'Contents'
    return (f'<a class="{direction}" href="{url}" rel="{direction}"><span class="kicker">'
            f'<span aria-hidden="true">{arrow}</span> {label}</span><strong>{title}</strong></a>')


def web():
    fragments = {c.slug: html(c.file.read_text().partition('\n')[2], notes=True) for c in CHAPTERS}
    outlines = {slug: top_headings(fragment) for slug, fragment in fragments.items()}
    with tempfile.TemporaryDirectory(dir=BASE, prefix='.site-') as temp:
        output = Path(temp) / 'site'
        shutil.copytree(BASE / 'assets', output / 'assets', ignore=shutil.ignore_patterns('epub.css'))
        write(output / '.nojekyll', '')
        for i, chapter in enumerate(CHAPTERS):
            path = route(chapter.slug)
            fragment = fragments[chapter.slug]
            index = book_outline(chapter, outlines)
            prev = adjacent(path, CHAPTERS[i-1]) if i else ''
            next_link = adjacent(path, CHAPTERS[i+1] if i+1 < len(CHAPTERS) else None, True)
            chapter_end = tmpl('chapter-end', author=escape(AUTHOR), links=prev + next_link)
            if not path:
                render(output, '', '', tmpl('opening', heading=escape(TITLE), toc=index, text=fragment,
                                            chapter_end=chapter_end), track_index=True)
                continue
            render(output, path, chapter.title,
                   tmpl('chapter', heading=escape(chapter.title), toc=index, text=fragment,
                        chapter_end=chapter_end),
                   track_index=True)

        for slug, label, anchor in [('', 'Contents', '#contents'), ('introduction/', 'Introduction', '#welcome-title')]:
            href = ('../../' if slug else '../') + anchor
            redirect(output, 'guide/' + slug, href, label)


        if SITE.exists():
            shutil.rmtree(SITE)
        output.rename(SITE)
    print(f'Guide with {len(CHAPTERS)} chapters → {SITE}')


def epub():
    out = BASE / 'proofs' / 'loafers-guide.epub'
    out.parent.mkdir(exist_ok=True)
    source = '\n\n'.join(c.file.read_text() for c in CHAPTERS)
    pandoc('-t', 'epub3', '--toc', '--toc-depth=2', '--split-level=1', '--css=assets/epub.css',
           '-M', f'title={TITLE}', '-M', f'author={AUTHOR}', '-M', 'lang=en-US', '-o', str(out), input=source)
    print(out)


if __name__ == '__main__':
    if not shutil.which('pandoc'):
        sys.exit('Install Pandoc 3.1.3 or newer (https://pandoc.org/installing.html).')
    if sys.argv[1:] == ['epub']:
        epub()

    elif not sys.argv[1:]:
        web()
    else:
        sys.exit('Usage: python3 build.py [epub]')
