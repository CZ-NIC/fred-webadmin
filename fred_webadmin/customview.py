class CustomView(Exception):
    def __init__(self, rendered_view):
        self.rendered_view = rendered_view
        super(CustomView, self).__init__()

