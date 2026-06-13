"""Utility functions used across the application."""


def format_currency(amount: float, currency: str = "USD") -> str:
    """Format a number as a currency string.

    Supports USD, EUR, and GBP formatting with appropriate symbols.

    Args:
        amount: The numeric amount to format.
        currency: Currency code (USD, EUR, GBP).

    Returns:
        Formatted currency string like "$1,234.56"
    """
    symbols = {"USD": "$", "EUR": "€", "GBP": "£"}
    symbol = symbols.get(currency, "$")
    return f"{symbol}{amount:,.2f}"


def paginate(items: list, page: int = 1, per_page: int = 20) -> dict:
    """Paginate a list of items.

    Returns a page of results with pagination metadata.

    Args:
        items: Full list to paginate.
        page: Page number (1-indexed).
        per_page: Items per page.

    Returns:
        Dict with 'items', 'page', 'per_page', 'total', 'pages'.
    """
    total = len(items)
    pages = max(1, (total + per_page - 1) // per_page)
    page = max(1, min(page, pages))

    start = (page - 1) * per_page
    end = start + per_page

    return {
        "items": items[start:end],
        "page": page,
        "per_page": per_page,
        "total": total,
        "pages": pages,
    }


def sanitize_input(text: str) -> str:
    """Sanitize user input by removing dangerous characters.

    Strips HTML tags and potential SQL injection patterns.
    This is a basic sanitizer — use a proper library in production.

    Args:
        text: Raw user input string.

    Returns:
        Sanitized string safe for display and storage.
    """
    import re
    # Remove HTML tags
    text = re.sub(r"<[^>]+>", "", text)
    # Remove SQL injection patterns
    text = re.sub(r"(--|;|'|\")", "", text)
    return text.strip()
