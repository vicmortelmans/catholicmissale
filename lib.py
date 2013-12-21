import re

def slugify(value):
    """
    Normalizes string, converts to lowercase, removes non-alpha characters
    (except dot, to  make sure the file extension is kept),
    and converts spaces to hyphens.
    """
    import unicodedata
    value = unicode(value)
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
    value = unicode(re.sub('[^\w\s.-]', '', value).strip().lower())
    value = unicode(re.sub('[-\s]+', '-', value))
    return value


