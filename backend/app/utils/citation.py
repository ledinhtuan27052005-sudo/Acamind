def format_apa(author: str, year: int, title: str, journal: str = "", pages: str = "") -> str:
    """Format trích dẫn theo chuẩn APA 7th edition."""
    base = f"{author} ({year}). {title}."
    if journal:
        base += f" *{journal}*"
    if pages:
        base += f", {pages}"
    return base + "."


def format_bibtex(title: str, author: str, year: int, journal: str = "", doc_id: str = "") -> str:
    """Format BibTeX entry."""
    first_author = author.split(",")[0].split()[-1].lower() if author else "unknown"
    key = f"{first_author}{year}"
    lines = [f"@article{{{key},"]
    lines.append(f"  title = {{{title}}},")
    lines.append(f"  author = {{{author}}},")
    if journal:
        lines.append(f"  journal = {{{journal}}},")
    lines.append(f"  year = {{{year}}}")
    lines.append("}")
    return "\n".join(lines)
