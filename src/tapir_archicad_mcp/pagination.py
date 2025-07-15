import base64
from pydantic import BaseModel
from typing import List, Optional, Any, Tuple, Dict

PAGINATION_CACHE: Dict[str, Tuple[BaseModel, float]] = {}
CACHE_LIFETIME_SECONDS = 300
PAGE_SIZE = 100

class PaginatedResult(BaseModel):
    """A generic container for a paginated list and the next token."""
    items: List[Any]
    next_page_token: Optional[str] = None

def handle_paginated_request(
    full_list: List[Any],
    page_token: Optional[str] = None
) -> PaginatedResult:
    """
    Takes a full list and a page token, and returns a paginated slice and the next token.
    This function is completely data-agnostic.
    """
    start_index = 0
    if page_token:
        try:
            start_index = int(base64.b64decode(page_token).decode('utf-8'))
        except (TypeError, ValueError):
            raise ValueError("Invalid or expired page_token.")

    end_index = start_index + PAGE_SIZE
    page_items = full_list[start_index:end_index]

    new_next_token = None
    if end_index < len(full_list):
        new_next_token = base64.b64encode(str(end_index).encode('utf-8')).decode('utf-8')

    return PaginatedResult(items=page_items, next_page_token=new_next_token)