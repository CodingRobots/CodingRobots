def select_view_module(name):
    global selectedview
    if name == 'pygame':
        import pgview
        selectedview = pgview

    elif name == 'pyqt':
        import qt4view
        selectedview = qt4view

    elif name == 'none':
        import noview
        selectedview = noview

def get_view_module():
    global selectedview
    return selectedview
