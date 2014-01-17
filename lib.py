def slugify(value):
    """
    Normalizes string, converts to lowercase, removes non-alpha characters
    (except dot, to  make sure the file extension is kept),
    and converts spaces to hyphens.
    """
    import unicodedata
    import re
    value = unicode(value)
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
    value = unicode(re.sub('[^\w\s.-]', '', value).strip().lower())
    value = unicode(re.sub('[-\s]+', '-', value))
    return value


def readable_date(date, lang):
    from babel.dates import format_date, format_datetime, format_time
    return format_date(date, format='full', locale=lang)


def chunks(l, n):
    for i in xrange(0, len(l), n):
        yield l[i:i+n]