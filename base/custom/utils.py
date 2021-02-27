from django.utils.http import urlencode


def get_query_string(data, new_params=None, remove=None):
    #  from django source code
    if new_params is None:
        new_params = {}
    if remove is None:
        remove = []
    p = data.copy()
    for r in remove:
        for k in list(p):
            if k.startswith(r):
                del p[k]
    for k, v in new_params.items():
        if v is None:
            if k in p:
                del p[k]
        else:
            p[k] = v
    return f"?{urlencode(sorted(p.items()))}"
