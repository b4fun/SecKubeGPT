import typing as t


def section_title(s: str='', fill_char='=', total_width=80) -> str:
    if not s:
        return fill_char * total_width

    s = f' {s} '
    filler_width = (total_width - len(s)) // 2
    filler = fill_char * filler_width
    return filler + s.center(total_width - 2 * filler_width) + filler


def log_data(section: str, data: any):
    print(section_title(section))
    print(data)
    print(section_title())


def normalize_text(s: t.Optional[str]) -> str:
    if not s:
        return ''
    return s.strip()