class Register:
    def __init__(self):
        self.renderers = {}

    def register(self, cls):
        self.renderers[cls.get_id()] = cls
        cls.filetype_specialized = {}
        cls.dont_list = False

    def get_renderers_choices(self):
        choices = [(o.get_id(), o.description) for o in self.renderers.values()]
        return [("", "---------")] + sorted(choices, key=lambda x: x[1])

    def get_render(self, render_id, filetype=None):
        render = self.renderers[render_id]
        if filetype and filetype in render.filetype_specialized:
            cls = render.filetype_specialized[filetype]

            def factory(resultado):
                return cls(render(resultado))

            return factory

        return render

    def list(self):
        return self.renderers.keys()


register_obj = Register()


def register(cls):
    register_obj.register(cls)
    return cls


def get_choices():
    return register_obj.get_renderers_choices()


def get_renderer(render_id, filetype):
    return register_obj.get_render(render_id, filetype)


class FiletypeRender:
    def __init__(self, filetype):
        self.filetype = filetype

    def register(self, render):
        def register_specialized(cls):
            if self.filetype in render.filetype_specialized:
                raise ValueError("Já definido")
            render.filetype_specialized[self.filetype] = cls
            return cls

        return register_specialized
