class CpuBackend:
    """Example backend plugin. Every plugin should offer health()."""

    def health(self):
        return True

    def run(self, fn, *args):
        return fn(*args)
