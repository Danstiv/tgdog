from tgdog.db import tables
from tgdog.gui.buttons import SimpleButton
from tgdog.gui.tabs.tab import Tab


class NumberSelectionTab(Tab):
    table = tables.NumberSelectionTab
    MAX_STEP = 10**10

    async def build(self, *args, step=1, **kwargs):
        await super().build(*args, **kwargs)
        self.row.selected_value = self.row.initial_value
        self.keyboard.buttons = [
            [SimpleButton(
                f'-{step}',
                name='previous_value',
                arg=self.row.selected_value-step,
                callback=self.on_value_btn
            )],
            [SimpleButton(
                f'+{step}',
                name='next_value',
                arg=self.row.selected_value+step,
                callback=self.on_value_btn
            )],
            [
                SimpleButton(
                    '<',
                    name='decrease_step',
                    arg=max(1, int(step/10)),
                    callback=self.on_step_btn
                ),
                SimpleButton(
                    '>',
                    name='increase_step',
                    arg=min(self.MAX_STEP, step*10),
                    callback=self.on_step_btn
                ),
            ],
            [await self.get_done_button()],
        ]

    async def get_text_data(self):
        return {
            'selected_value': self.row.selected_value,
        }

    def get_value_buttons(self):
        return (
            self.keyboard.find_buttons_by_name('previous_value')[0],
            self.keyboard.find_buttons_by_name('next_value')[0],
        )

    async def on_value_btn(self, arg):
        new_value = int(arg)
        step = abs(new_value - self.row.selected_value)
        if self.row.min_value is not None:
            new_value = max(self.row.min_value, new_value)
        if self.row.max_value is not None:
            new_value = min(self.row.max_value, new_value)
        if new_value == self.row.selected_value:
            return
        self.row.selected_value = new_value
        previous_value_button, next_value_button = self.get_value_buttons()
        previous_value_button.row.arg = new_value - step
        next_value_button.row.arg = new_value + step
        await self.on_value_selected(new_value)

    async def on_value_selected(self, selected_value):
        pass

    async def on_step_btn(self, arg):
        new_step = int(arg)
        decrease_step_button = self.keyboard.find_buttons_by_name('decrease_step')[0]
        increase_step_button = self.keyboard.find_buttons_by_name('increase_step')[0]
        decrease_step_button.row.arg = max(1, int(new_step/10))
        increase_step_button.row.arg = min(self.MAX_STEP, new_step*10)
        previous_value_button, next_value_button = self.get_value_buttons()
        previous_value_button.row.arg = self.row.selected_value - new_step
        previous_value_button.set_text(f'-{new_step}')
        next_value_button.row.arg = self.row.selected_value + new_step
        next_value_button.set_text(f'+{new_step}')

    async def get_done_button(self):
        return SimpleButton(
            'Готово',
            callback=self.on_done_btn,
        )

    async def on_done_btn(self, arg):
        raise NotImplementedError
