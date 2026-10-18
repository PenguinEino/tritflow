"""Portable Colab Markdown: dollar math and width-constrained illustrations.

Keep equations in ordinary Markdown, separate from HTML image/table blocks.
Only presentation is transformed; measured quantities and code stay unchanged.
"""

from html import escape
import re


def colab_math(text):
    """Use Colab's inline/display dollar delimiters, preserving fenced code."""
    parts = re.split(r'(```[\s\S]*?```)',text)
    for i,part in enumerate(parts):
        if part.startswith('```'):
            continue
        part = part.replace(r'\[','$$').replace(r'\]','$$')
        part = part.replace(r'\(','$').replace(r'\)','$')
        part = part.replace(r'\operatorname',r'\mathrm')
        part = re.sub(r'\\rm\s+([A-Za-z]+)',r'\\mathrm{\1}',part)
        parts[i] = part.replace('$$\n$$','$$\n\n$$')
    return ''.join(parts)


def responsive_image(data, alt):
    """Embed the committed PNG without its native pixel width widening Colab."""
    return (f'<img alt="{escape(alt,quote=True)}" src="data:image/png;base64,{data}" width="100%" '
            'style="display:block;max-width:100%;width:100%;height:auto;" />')


def _inline(text):
    text = escape(text.replace(r'\|','|'))
    return re.sub(r'`([^`]+)`',r'<code style="white-space:normal;overflow-wrap:anywhere">\1</code>',text)


def wrap_tables(text):
    """Give prose tables fixed container width and wrapping cells, without pandas.

    Long scope descriptions wrap within their column instead of imposing an
    intrinsic minimum table width. A scroll container remains a fallback.
    """
    lines = text.splitlines(); output = []; index = 0
    while index < len(lines):
        if not (lines[index].startswith('|') and index+1 < len(lines)
                and re.fullmatch(r'[|\s:\-]+',lines[index+1])):
            output.append(lines[index]); index += 1; continue
        rows = []
        while index < len(lines) and lines[index].startswith('|'):
            line = lines[index]
            if not re.fullmatch(r'[|\s:\-]+',line):
                rows.append([part.strip() for part in re.split(r'(?<!\\)\|',line.strip().strip('|'))])
            index += 1
        columns = len(rows[0])
        if _is_prose_table(rows):
            output.extend(_prose_list(rows))
            continue
        # A percentage-width table can otherwise contribute its intrinsic width
        # to Colab's surrounding flex item before the column width is resolved.
        output.append('<div style="display:block;width:100%;min-width:0;max-width:100%;overflow-x:auto;contain:inline-size;box-sizing:border-box;">\n'
                      '<table width="100%" style="width:100%;min-width:0;max-width:100%;table-layout:fixed;border-collapse:collapse;">')
        for row_index,row in enumerate(rows):
            tag = 'th' if row_index == 0 else 'td'
            cells = []
            for col,value in enumerate(row):
                width = ('20%' if col == 0 else '80%') if columns == 2 else f'{100/columns:g}%'
                style = ('white-space:normal;overflow-wrap:anywhere;word-break:normal;'
                         f'min-width:0;vertical-align:top;text-align:left;padding:.45em .7em;width:{width};')
                cells.append(f'<{tag} width="{width}" style="{style}">{_inline(value)}</{tag}>')
            output.append('<tr>'+''.join(cells)+'</tr>')
        output.append('</table>\n</div>')
    return '\n'.join(output)


def _is_prose_table(rows):
    """Two-column label/description tables with sentence-length cells.

    Colab drops inline styles in Markdown cells and truncates long table cells
    with an ellipsis, so such tables read better as labelled paragraphs.
    """
    body = rows[1:]
    return (len(rows[0]) == 2 and bool(body)
            and max(len(row[1]) for row in body if len(row) == 2) > 120)


def _prose_list(rows):
    """Render label/description rows as Markdown paragraphs that always wrap."""
    lines = []
    for row in rows[1:]:
        label, description = row[0].rstrip('.'), row[1]
        lines += [f'**{label}.** {description}', '']
    return lines


def colab_markdown(text):
    return wrap_tables(colab_math(text))
