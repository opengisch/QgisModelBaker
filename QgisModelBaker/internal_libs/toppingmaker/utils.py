import re
import unicodedata


# - [ ] That's a duplicate with projecttopping utils - see on ordering in the end where it should be
def slugify(text: str) -> str:
    if not text:
        return text
    slug = unicodedata.normalize("NFKD", text)
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", slug).strip("_")
    slug = re.sub(r"[-]+", "_", slug)
    slug = slug.lower()
    return slug
