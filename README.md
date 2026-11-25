# A Loafer’s Guide to the U.C. Berkeley Campus

Carolyn Dougherty’s revised guide renders from `content/*.md` in one Optima-based design, with self-hosted Libertinus Sans as fallback. There is no Hugo, CMS, or external font dependency. On desktop the sidebar marks the active section. On narrow screens the sticky chapter title opens the same index. Without JavaScript the full index still works.

## Build and preview

Requires Python 3.12+ (standard library only) and Pandoc 3.1.3+. No install step or network is needed once those tools are present.

```sh
python3 -m unittest discover -s tests
python3 build.py
python3 tests/check_site.py
python3 -m http.server 8000 --directory dist
```

Publish **only `dist/`** to any static host. It includes `.nojekyll` and uses relative URLs, so it can live at a host root or a path prefix. The home page is the Introduction chapter. The Prolog and subsequent chapters retain their published `/guide/…/` routes and heading anchors. There is print CSS, but no bundled PDF.

## GitHub Pages

In **Settings → Pages → Build and deployment**, set the source to **GitHub Actions**. The workflow checks pull requests and publishes `dist/` from `main` to `loafersguide.github.io`. Do not commit generated files.

## Text and EPUB

- Edit prose in `content/`. Chapter order and slugs are explicit in `build.py`. Add a Markdown footnote with `[^label]`; simple notes sit beside their references in the right gutter on wide screens and in the text column on narrower screens. Richer notes stay linked endnotes, and the EPUB keeps conventional linked notes.
- Presentation lives in `templates/` and `assets/*.css`, not in the manuscript.
- For dashes, follow [Butterick’s conventions](https://practicaltypography.com/hyphens-and-dashes.html): use spaced em dashes for breaks in prose, unspaced en dashes for ranges and paired terms such as east–west, and hyphens for compound modifiers such as four-story.
- `python3 build.py epub` creates `proofs/loafers-guide.epub` from the same sources. It is a reflowable EPUB 3 proof, not a public download; `epubcheck proofs/loafers-guide.epub` validates it. Keep reader-device testing and final release metadata for an EPUB release.

## Editorial handoff

The source is Carolyn’s December 4, 2020 Word revision. The text is historical and has not been rewritten as present-day campus directions.
