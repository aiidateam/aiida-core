from click import Choice


class LazyChoice(Choice):
    """
    This is a subclass of click's Choice ParamType that evaluates the set of choices
    lazily. This is useful if the choices set requires an import that is slow. Using
    the vanilla click.Choice will call this on import which will slow down verdi and
    its autocomplete. This type will generate the choices set lazily through the
    choices property
    """

    def __init__(self, callable):
        self.callable = callable

    @property
    def choices(self):
        return self.callable()
