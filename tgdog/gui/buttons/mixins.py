from tgdog.gui.buttons.base_button import BaseButton


class ButtonWithCallback(BaseButton):

    def __init__(self, *args, callback=None, **kwargs):
        if callback is not None:
            kwargs['callback_name'] = callback.__name__
        super().__init__(*args, **kwargs)

    async def _stub_callback(self, *args, **kwargs):
        pass

    @property
    def callback(self):
        if self.row.callback_name is not None:
            return getattr(self.keyboard.tab, self.row.callback_name)
        return self._stub_callback
