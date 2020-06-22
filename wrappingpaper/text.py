


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
