import wrappingpaper as wp


def test_text():
    prep = lambda t: wp.text.strip_trailing_whitespace(wp.text.striplines(t)).rstrip().replace('\t', ' '*4)
    inspect = lambda *xs: print(wp.text.block_text(*xs, *(repr(x) for x in xs), div='----'))

    original = prep('''
asdf

asdfsadf
    asdf
    ''')
    indented = prep('''
    asdf

    asdfsadf
        asdf
    ''')
    # inspect(original, indented)
    # test indent
    assert wp.text.strip_trailing_whitespace(wp.text.indent(original)) == indented
    assert wp.text.trim_indent(indented) == original
    assert wp.text.strip_trailing_whitespace(wp.text.tabindent(original.replace(' '*4, '\t'))) == indented.replace(' '*4, '\t')

    assert wp.text.striplines('\n'*3 + indented + '\n'*3) == indented

    # test commenting
    commented = prep('''
# asdf
#
# asdfsadf
#     asdf
    ''')

    assert wp.text.strip_trailing_whitespace(wp.text.comment(original)) == commented
    assert wp.text.strip_trailing_whitespace(wp.text.comment(original, ch='//')) == commented.replace('#', '//')

    # test block text
    block_text = prep('''
********************
* asdf
*
* asdfsadf
*     asdf
*
* hello
********************
    ''')
    assert wp.text.strip_trailing_whitespace(wp.text.block_text(original, '', 'hello')) == block_text

    # test line and block
    assert wp.text.l_('asdf', 5, 5) == 'asdf 5 5'
    assert wp.text.b_('asdf', (5, 6, 7, 8), 5) == '''
asdf
5 6 7 8
5
    '''.strip()

    # text fixed width format
    assert wp.text.fw_('asdf', w=10) == 'asdf      '

    # test table
    assert wp.text.strip_trailing_whitespace(wp.text.tbl(
        ('asdf', 6, 7, 'asdf'),
        (5, 6, 7, 8),
        (5, 'asdf', 7, 'asdf'))) == '''
asdf  6     7  asdf
5     6     7  8
5     asdf  7  asdf
    '''.strip()

    # test colors
    assert wp.text.red('a b c') == '\033[91ma b c\033[0m'
    assert wp.text.blue('a b c') == '\033[94ma b c\033[0m'
    assert wp.text.green('a b c') == '\033[92ma b c\033[0m'
    assert wp.text.yellow('a b c') == '\033[93ma b c\033[0m'
    assert wp.text.bold('a b c') == '\033[1ma b c\033[0m'
    assert wp.text.underline('a b c') == '\033[4ma b c\033[0m'
