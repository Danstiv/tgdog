from tgdog.db import tables
from tgdog.gui.buttons import SimpleButton, SingleSelectButton
from tgdog.gui.keyboards import GridKeyboard
from tgdog.gui.tabs.tab import Tab
from tgdog.gui.tabs.time_zone_selection_tab.time_zones import TIME_ZONES

PAGE_SIZE = 9


class TimeZoneSelectionTab(Tab):
    table = tables.TimeZoneSelectionTab

    def get_keyboard(self):
        return GridKeyboard(self, width=3)

    async def build(self, *args, start_offset=0, **kwargs):
        await super().build(*args, selected_time_zone_offset=start_offset, **kwargs)
        start_time_zone_index = self.get_start_time_zone_index_from_offset(start_offset)
        await self.set_time_zones_page(self.get_time_zones_page(start_time_zone_index))

    @staticmethod
    def get_start_time_zone_index_from_offset(offset):
        time_zone_index = 0
        for i, time_zone in enumerate(TIME_ZONES):
            if time_zone[1] == offset:
                time_zone_index = i
                break
        # Rounding to the start of the page.
        return time_zone_index // PAGE_SIZE * PAGE_SIZE

    @staticmethod
    def get_time_zones_page(start_index):
        page = {'start_index': start_index, 'time_zones': []}
        index = start_index
        # There is probably a more elegant / performant way to do this.
        while len(page['time_zones']) < PAGE_SIZE:
            page['time_zones'].append(TIME_ZONES[index])
            index += 1
            if index == len(TIME_ZONES):
                index = 0
        return page

    async def set_time_zones_page(self, page):
        await self.keyboard.clear()
        for time_zone in page['time_zones']:
            self.keyboard.add_button(SingleSelectButton(
                time_zone[0],
                name='time_zone_button',
                arg=time_zone[1],
                callback=self._on_time_zone_selected,
                is_checked=time_zone[1] == self.row.selected_time_zone_offset,
            ))
        previous_page_start_index = page['start_index'] - PAGE_SIZE
        if previous_page_start_index < 0:
            previous_page_start_index += len(TIME_ZONES)
        next_page_start_index = page['start_index'] + PAGE_SIZE
        if next_page_start_index >= len(TIME_ZONES):
            next_page_start_index -= len(TIME_ZONES)
        self.keyboard.add_button(SimpleButton(
            '<',
            callback=self.on_change_page,
            arg=previous_page_start_index,
        ))
        self.keyboard.add_button(await self.get_done_button())
        self.keyboard.add_button(SimpleButton(
            '>',
            callback=self.on_change_page,
            arg=next_page_start_index,
        ))

    async def _on_time_zone_selected(self, arg):
        self.row.selected_time_zone_offset = arg
        await self.on_time_zone_selected(arg)

    async def on_time_zone_selected(self, selected_time_zone):
        pass

    async def on_change_page(self, arg):
        new_page = self.get_time_zones_page(int(arg))
        await self.set_time_zones_page(new_page)

    async def get_done_button(self):
        return SimpleButton(
            'Готово',
            callback=self.on_done_btn,
        )

    async def on_done_btn(self, arg):
        raise NotImplementedError
