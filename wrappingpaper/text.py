
# Text formatting

class C:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def _text_wrapper(start, end=C.ENDC):
    return f'{start}{{}}{end}'.format

red = _text_wrapper(C.FAIL)
blue = _text_wrapper(C.OKBLUE)
green = _text_wrapper(C.OKGREEN)
yellow = _text_wrapper(C.WARNING)
bold = _text_wrapper(C.BOLD)
underline = _text_wrapper(C.UNDERLINE)

t4 = ' '*4
t2 = ' '*2

# block text helpers

def indent(x, n=1, w=4, ch=' '):
    '''Indent text using spaces.'''
    return ''.join(ch * w * n + l for l in str(x).splitlines(keepends=True))

def tabindent(x, n=1, w=4):
    '''Indent text using tabs.'''
    return indent(space2tab(x, w=w), w=1, n=n, ch='\t')


def tab2space(text, w=4):
    return text.replace('\t', ' '*w)

def space2tab(text, w=4):
    return text.replace(' '*w, '\t')


def trim_indent(text, tw=2):
    '''Remove any common indent from text.

    Arguments:
        text (str): the text to re-indent.
        tw (int): the number of spaces per tab character.
    '''
    # normalize tabs to spaces
    lines = text.replace('\t', ' '*tw).splitlines()
    # get the min indent to norm to
    m = min([len(l) - len(l.lstrip()) for l in lines if l.strip()], default=0)
    # rejoin the text with the proper indent
    return '\n'.join([l[m:] for l in lines])


def striplines(text):
    '''Like text.strip() but it only removes lines with purely whitespace and
    leaves text indentation.'''
    lines = text.splitlines()
    i, j = 0, len(lines)
    while not lines[i].strip():
        i += 1
    while not lines[j-1].strip():
        j -= 1
    return '\n'.join(lines[i:j])

def strip_trailing_whitespace(txt):
    '''remove whitespace from the end of each line.'''
    return '\n'.join(l.rstrip() for l in txt.splitlines())

def comment(txt, ch='#', n=1, spaces=1):
    '''Apply prefix to each line. Defaults to python comments.'''
    ch, spaces = ch*n, " "*spaces
    return '\n'.join(f'{ch}{spaces}{l}' for l in txt.splitlines())


def block_text(*txts, n=20, ch='*', div=''):
    '''Create a block of text with a character border.'''
    return ch * n + f'\n{comment(b_(*txts, div=div), ch=ch)}\n' + ch * n

def b_(*lines, div=''):
    '''Convert arguments to lines. Lines can be tuples (will be joined by a space.)'''
    div = f'\n{div}\n' if div else '\n'
    return div.join(
        l_(*l) if isinstance(l, (list, tuple)) else str(l)
        for l in lines if l is not None)

def l_(*line, div=' '):
    '''Convert arguments to a space separated string'''
    return div.join(map(str, line))


def fw_(*line, w=20, right=False):
    '''As a fixed width string'''
    return f"{l_(*line):{'>' if right else '<'}{w}}"

def tbl(*rows, buffer=2):
    '''Format as a table. Calculates column widths.'''
    rows = [[str(c) for c in cs] for cs in rows]
    widths = [max((len(c) for c in cs), default=0) for cs in zip(*rows)]
    return b_(*([fw_(c, w=w + buffer-1) for c, w in zip(cs, widths)] for cs in rows))



def redent(text, n=0, tw=2, stripline=True, keep_leading=False):
    '''Re-indent text.

    Arguments:
        text (str): the text to reindent
        n (int): the number of soft tabs to add before each line.
        tw (int): the width of a tab character.
        stripline (bool): If True, remove blank lines at the beginning and end.
        keep_leading (bool): If False, remove the minimum leading space from
            all lines. Otherwise, keep leading whitespace as is.

    Returns:
        reindented text.
    '''
    # normalize tabs to spaces
    lines = text.replace('\t', ' '*tw).splitlines()
    # remove the first/last line if it's blank
    if stripline:
        i1 = next((i for i, l in enumerate(lines) if l.strip()), 0)
        i2 = next((i for i, l in enumerate(lines[::-1]) if l.strip()), 0)
        lines = lines[i1:len(lines) - i2]

    # get the min indent to norm to
    m = (0 if keep_leading else min(
        (len(l) - len(l.lstrip()) for l in lines if l.strip()),
        default=0))
    # rejoin the text with the proper indent
    return '\n'.join([n * tw * ' ' + l[m:] for l in lines])


if __name__ == '__main__':
    print(red('this should be red'))
    print(blue('this should be blue'))
    print(green('this should be green'))
    print(yellow('this should be yellow'))
    print(underline('this should be underline'))

    print()
    print(b_(
        ('hi', blue('im blue'), 56),
        'okay',
        '',
        red('bloop'),
    ))

    print()
    print(block_text(
        l_('hiiii', red('okay')),
        bold('well'),
        green('alright'),
    ))
