from IPython.display import display, HTML


def set_css():
    return HTML('<style>{}</style><p>Loaded <code>my_styles.css</code></p>'.format(open('my_styles.css').read()))


# noinspection PyTypeChecker
def display_item(item: str):
    """Display a single item in HTML.

    Params:
    - item : str
        The item (string with HTML markup) to be displayed.
    """
    display(HTML(item))


def display_list(items):
    """Display a list of items as an unordered HTML list.

    Params:
    - items : List[str]
        A list of items (strings with HTML markup) to be displayed
    """
    html_str = "<ul>"
    for item in items:
        html_str += f"<li>{item}</li>"
    html_str += "</ul>"
    # noinspection PyTypeChecker
    display(HTML(html_str))


def display_table(df):
    """Display a Pandas DataFrame in a HTML table."""
    # noinspection PyTypeChecker
    display(HTML(f'<div class="my_table">{df.to_html()}</div>'))
