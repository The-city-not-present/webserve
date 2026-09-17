
import re



def get_matching_endpoint(path: str, endpoints: dict):
    """Checks if path is in endpoints dict, and returns entity from that dict, if found, or None otherwise

Input args:
- path to check, assuming it is not unescaped
- a dict with mathing patterns as keys, and values to return as values

Returns:
- what is matching in "endpoints" dict, or None

endpoints dict keys can be:
- exact strings
- regexs from re.compile()
- callables
- otherwise, ignored

If there are multiple matches, the one thah matches logest sequence is returned. However, "exact match" takes priority over more general regex match

Path is not unescaped - if it containes %20's, make sure your endpoint definitions are checking the same.
"""

    def get_matching_pattern_substring(path, pattern):
        if callable(pattern):
            if pattern(f'{path}'):
                return f'{path}', 1
        elif isinstance(pattern, str):
            if f'{path}' == f'{pattern}':
                return f'{path}', 0
        elif isinstance(pattern, re.Pattern):
            matches = re.match(pattern,f'{path}')
            if matches:
                return f'{matches[0]}', 2
        return None, None

    # longest matching
    best_match = None
    best_length = -1
    best_priority = 999

    for pattern, renderer in endpoints.items():
        matching_str, priority = get_matching_pattern_substring(path,pattern)
        if matching_str is not None:
            # bigger length takes priority, or we check the returned "priority", if tied
            if (len(matching_str) > best_length) or ( (len(matching_str) == best_length) and (priority<best_priority) ):
                best_match = renderer
                best_length = len(matching_str)
                best_priority = priority
    return best_match
