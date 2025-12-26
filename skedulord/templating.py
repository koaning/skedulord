import datetime as dt


def render_tokens(template: str, now: dt.datetime | None = None) -> str:
    if not template:
        return template
    now = now or dt.datetime.now()
    tokens = {
        "current_date": now.date().isoformat(),
        "current_time": now.time().replace(microsecond=0).isoformat(),
        "current_datetime": now.replace(microsecond=0).isoformat(),
    }
    rendered = template
    for key, value in tokens.items():
        rendered = rendered.replace(f"{{{key}}}", value)
    return rendered
