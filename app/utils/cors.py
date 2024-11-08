http_scheme = ["http", "https"]

dot_store = [
    "ssimartbd.com",
    "ssishopping.store",
    "test.ssishopping.store",
    "auth.ssishopping.store",
]

others = [
    "localhost:5174",
    "localhost:5173",
    "localhost:4173",
    "localhost:4174",
    "localhost:3000",
]

origins_without_scheme = [
    "*",
    *others,
    *dot_store,
]


def add_scheme(origins, schemes=http_scheme):
    array = []
    for origin in origins:
        for scheme in schemes:
            array.append(f"{scheme}://{origin}")
    return array


origins_with_scheme = [
    "*",
    *add_scheme(others),
    *add_scheme(dot_store),
]

allow_origins = origins_with_scheme
