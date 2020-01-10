import string


def reduce_text(text, limit):
    if len(text) <= limit:
        return text
    new_text = text[:limit]
    new_text_split = new_text.split(' ')
    slice_size = -1 if len(new_text_split) > 1 else 1
    clean_text = ' '.join(new_text_split[:slice_size])

    if clean_text[-1] in string.punctuation:
        clean_text = clean_text[:-1]

    if isinstance(clean_text, unicode):
        return u'{0}...'.format(clean_text)
    else:
        return u'{0}...'.format(clean_text.decode('utf-8'))


def format_date(date, fmt='%d %b %Y, %H:%M CET'):
    return date.strftime(fmt)
