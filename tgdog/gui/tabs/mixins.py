from tgdog.enums import PaginatorMode
from tgdog.gui.buttons import SimpleButton


class PaginatedTabMixin:
    mode = PaginatorMode.STANDARD
    add_page_info_into_text = True

    async def build(self, *args, page_number=1, **kwargs):
        await super().build(*args, **kwargs)
        await self.update(page_number)

    async def set_page(self, page):
        raise NotImplementedError

    async def set_next_page(self):
        raise NotImplementedError

    async def set_previous_page(self):
        raise NotImplementedError

    async def update(self, page_number):
        await self.keyboard.clear()
        use_page_numbers = self.mode != PaginatorMode.NO_PAGES
        if use_page_numbers:
            info = await self.set_page(page_number)
        else:
            info = await (self.set_previous_page if page_number == -1 else self.set_next_page)()
        total_pages = info.pop('total_pages', None)
        is_first_page = info.pop('is_first_page', False)
        is_last_page = info.pop('is_last_page', False)
        if use_page_numbers and self.add_page_info_into_text:
            line = f'Страница {page_number}'
            if total_pages is not None:
                line += f' / {total_pages}'
            line += '.'
            self.text.append_to_body('\n\n' + line)
        # if use_page_numbers is False - simple scrolling without page numbers
        if use_page_numbers:
            is_first_page = page_number == 1
            # if total_pages is None - infinite scrolling
            if total_pages is not None:  # Regular paginated set of fixed size
                is_last_page = page_number == total_pages
        first_buttons_row = []
        last_buttons_row = []
        if not use_page_numbers:
            if not is_first_page:
                first_buttons_row.append(SimpleButton(
                    '<',
                    name='page_button',
                    callback=self.on_previous_page,
                ))
            if not is_last_page:
                first_buttons_row.append(SimpleButton(
                    '>',
                    name='page_button',
                    callback=self.on_next_page,
                ))
        else:
            if not is_last_page:
                first_buttons_row.append(SimpleButton(
                    str(page_number + 1),
                    name='page_button',
                    callback=self.on_page,
                    arg=page_number + 1
                ))
                if total_pages is not None:
                    for p in range(page_number + 2, page_number + min(4, total_pages - page_number)):
                        first_buttons_row.append(SimpleButton(
                            str(p),
                            name='page_button',
                            callback=self.on_page,
                            arg=p
                        ))
                    if page_number + 1 < total_pages:
                        first_buttons_row.append(SimpleButton(
                            str(total_pages),
                            name='page_button',
                            callback=self.on_page,
                            arg=total_pages
                        ))
            if not is_first_page:
                last_buttons_row.append(SimpleButton(
                    str(page_number - 1),
                    name='page_button',
                    callback=self.on_page,
                    arg=page_number - 1
                ))
                for p in list(range(max(2, page_number - 3), page_number - 1)):
                    last_buttons_row.insert(-1, SimpleButton(
                        str(p),
                        name='page_button',
                        callback=self.on_page,
                        arg=p
                    ))
                if page_number > 2:
                    last_buttons_row.insert(0, SimpleButton(
                        '1',
                        name='page_button',
                        callback=self.on_page,
                        arg=1
                    ))
        if first_buttons_row:
            self.keyboard.add_row(*first_buttons_row)
        if last_buttons_row:
            self.keyboard.add_row(*last_buttons_row)

    async def on_page(self, arg):
        await self.update(int(arg))

    async def on_next_page(self, arg):
        await self.update(1)

    async def on_previous_page(self, arg):
        await self.update(-1)
