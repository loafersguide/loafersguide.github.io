from unittest import TestCase

from build import pandoc, top_headings


class OutlineTests(TestCase):
    def test_headings_keep_ids_and_use_plain_labels_without_subtitles(self):
        source = ('## [Read & walk](https://example.com) '
                  '[A *subtitle*]{.heading-subtitle} {#walk .special}\n\n'
                  '### Not a top-level entry\n')
        html = pandoc('-t', 'html5', input=source, capture_output=True).stdout
        self.assertEqual(top_headings(html), [('walk', 'Read & walk')])
