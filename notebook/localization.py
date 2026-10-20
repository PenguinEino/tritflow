"""Translate notebook presentation strings without editing circuit identifiers.

The Japanese notebook shares every executable method and assertion with the
English one. Only string-literal prose is translated when building code cells;
HDL, comments, dictionary field names and numeric inputs retain their meaning.
"""

from io import StringIO
from html.parser import HTMLParser
import tokenize
import unicodedata
import xml.etree.ElementTree as ET


def translate_text(text, translations):
    """Replace explicit presentation phrases, longest first, exactly once."""
    for before, after in sorted(translations.items(), key=lambda item: -len(item[0])):
        text = text.replace(before, after)
    return text


def localize_source(source, translations):
    """Translate literal text; never replace tokens in executable expressions."""
    # In Python 3.12, f-string prose is FSTRING_MIDDLE; ordinary strings remain
    # STRING. Older builders expose the whole f-string as STRING instead.
    kinds = {tokenize.STRING, getattr(tokenize, 'FSTRING_MIDDLE', tokenize.STRING)}
    tokens = [token._replace(string=translate_text(token.string, translations))
              if token.type in kinds else token
              for token in tokenize.generate_tokens(StringIO(source).readline)]
    return tokenize.untokenize(tokens)


def localize_svg(source, translations):
    """Translate SVG text labels, preserving HDL blocks, geometry and values."""
    svg = ET.fromstring(source)
    for element in svg.iter():
        if element.tag.rsplit('}', 1)[-1] not in {'text', 'tspan'}:
            continue
        if element.text and 'mono' not in element.get('style', '').lower():
            original = element.text
            element.text = translate_text(element.text, translations)
            if any('\u3040' <= c <= '\u9fff' for c in element.text):
                style = element.get('style', '')
                # Browser fallback supplies Japanese glyphs without a new
                # pinned native font or any change to the shared paper assets.
                import re
                style = re.sub(r'font-family:[^;]*',
                               "font-family: 'Noto Sans CJK JP', 'Noto Serif CJK JP', sans-serif", style)
                # CJK glyphs are wider than the paper's narrow Roman text. Keep a
                # translated label inside its original panel's text footprint.
                units = lambda s: sum(2.6 if unicodedata.east_asian_width(c) in {'W', 'F'} else 1 for c in s)
                ratio = .85 * min(1, units(original) / max(1, units(element.text)))
                style = re.sub(r'font-size: ([\d.]+)px',
                               lambda m: f'font-size: {float(m[1])*ratio:.4g}px', style)
                element.set('style', style)
    ET.register_namespace('', 'http://www.w3.org/2000/svg')
    ET.register_namespace('xlink', 'http://www.w3.org/1999/xlink')
    return ET.tostring(svg, encoding='unicode')


def localize_html(source, translations):
    """Translate text nodes, keeping scripts, data links and reports byte exact."""
    class Labels(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=False)
            self.output, self.literal = [], []

        def handle_starttag(self, tag, attrs):
            self.output.append(self.get_starttag_text())
            if tag in {'script', 'style', 'pre'}:
                self.literal.append(tag)

        def handle_startendtag(self, tag, attrs):
            self.output.append(self.get_starttag_text())

        def handle_endtag(self, tag):
            self.output.append(f'</{tag}>')
            if self.literal and self.literal[-1] == tag:
                self.literal.pop()

        def handle_data(self, data):
            self.output.append(data if self.literal else translate_text(data, translations))

        def handle_entityref(self, name):
            self.output.append(f'&{name};')

        def handle_charref(self, name):
            self.output.append(f'&#{name};')

        def handle_comment(self, data):
            self.output.append(f'<!--{data}-->')

    parser = Labels()
    parser.feed(source)
    parser.close()
    return ''.join(parser.output)
