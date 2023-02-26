def invalid_comment_text(text: str) -> bool | str:
    if len(text) > 4000:
        return "Comment is too long."
    else:
        return False
