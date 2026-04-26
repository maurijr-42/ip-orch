import inspect


def pytest_collection_modifyitems(items):
    """Append each test docstring summary to the verbose pytest node id."""

    for item in items:
        doc = inspect.getdoc(getattr(item, "obj", None))
        if not doc:
            continue
        summary = doc.splitlines()[0].strip()
        if summary:
            item._nodeid = f"{item.nodeid} -- {summary}"
