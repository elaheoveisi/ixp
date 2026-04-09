from __future__ import annotations

from psychopy import event, visual


class InstructionScreen:
    """
    Display text instructions with an optional image on a PsychoPy window.

    Text is rendered via ``visual.TextBox2`` and images via ``visual.ImageStim``.
    When an image is provided to ``show()``, the text shifts to the top half of
    the screen and the image is placed below it.

    Parameters
    ----------
    win : visual.Window
        The PsychoPy window to draw on.
    text_color : str, optional
        Color of the instruction text. Default is 'white'.
    text_height : float | None, optional
        Height of the instruction text in normalized units. If ``None``
        (default), it is computed automatically as ~18px relative to the
        window's pixel height so the text appears the same physical size
        across different screen resolutions.
    wrap_width : float, optional
        Width of the text box before wrapping. Default is 1.4.
    continue_key : str, optional
        Key to press to advance past an instruction screen. Default is 'space'.

    Examples
    --------
    >>> from psychopy import visual
    >>> win = visual.Window(fullscr=True)
    >>> instructions = InstructionScreen(win)
    >>> instructions.show("Welcome! Press SPACE to begin.")
    >>> instructions.show("This is the target:", image='target.png')
    >>> instructions.show_pages([
    ...     "Page 1: In this task you will...",
    ...     "Page 2: When you see the target...",
    ... ])

    """

    def __init__(
        self,
        win: visual.Window,
        text_color: str = 'white',
        text_height: float | None = None,
        wrap_width: float = 1.4,
        line_spacing: float = 1.35,
        continue_key: str = 'space',
    ):
        self.win = win
        self.continue_key = continue_key

        if text_height is None:
            # ~18px in norm units: norm height = 2.0 spans win.size[1] pixels
            text_height = 16 / (win.size[1] / 2)

        self._letter_height = text_height
        self._line_spacing = line_spacing
        self._wrap_width = wrap_width

        self._text_stim = visual.TextBox2(
            win,
            text='',
            color=text_color,
            letterHeight=text_height,
            size=(wrap_width, 1.0),
            pos=(0, 0),
            alignment='left',
            font='Arial',
            lineSpacing=line_spacing,
        )
        self._prompt_stim = visual.TextBox2(
            win,
            text=f'Press {continue_key.upper()} to continue',
            color='lightgray',
            letterHeight=text_height * 0.75,
            size=(wrap_width, None),
            pos=(0, -0.42),
            alignment='center',
            font='Arial',
        )

    def show(
        self,
        text: str,
        image: str | None = None,
        image_pos: tuple[float, float] = (0, -0.25),
        image_size: tuple[float, float] = (0.3, 0.3),
        text_pos: tuple[float, float] | None = None,
        continue_key: str | None = None,
    ) -> None:
        """
        Display instruction text and wait for a key press.

        Parameters
        ----------
        text : str
            The instruction text to display.
        image : str, optional
            Path to an image file to display below the text.
        image_pos : tuple, optional
            Position of the image in norm units. Default is (0, -0.25).
        image_size : tuple, optional
            Size of the image in norm units. Default is (0.3, 0.3).
        text_pos : tuple, optional
            Position of the text in norm units. When an image is provided and
            this is None, defaults to (0, 0.25). When no image, defaults to
            (0, 0).
        continue_key : str, optional
            Override the default continue key for this screen only.

        """
        key = continue_key or self.continue_key
        self._prompt_stim.text = f'Press {key.upper()} to continue'

        # Estimate actual content height from line count.
        # TextBox2.size[1] reports the allocated box height, not content height,
        # so we derive it from known parameters (all resolution-scaled at init).
        n_lines = text.count('\n') + 1
        content_h = n_lines * self._letter_height * self._line_spacing

        # Give the box 50% extra height below the content so wrapping or
        # slightly-longer-than-estimated text never gets clipped at the bottom.
        box_h = content_h * 1.5

        if image is not None:
            self._text_stim.alignment = 'left'
            if text_pos is None or image_pos == (0, -0.25):
                img_h = image_size[1]
                gap = 0.10

                top_margin = 0.75  # leaves visible gap between text and screen top
                prompt_area = -0.35
                block_center = (top_margin + prompt_area) / 2  # 0.20

                # Center [content + gap + image] block; clamp so content
                # never starts above top_margin.
                total_h = content_h + gap + img_h
                block_top = min(block_center + total_h / 2, top_margin)

                # TextBox2 pos is its CENTER. We want the box top = block_top
                # so content starts exactly there and extra box space goes below.
                resolved_text_y = block_top - box_h / 2 if text_pos is None else text_pos[1]
                resolved_img_y = (block_top - content_h) - gap - img_h / 2

                self._text_stim.size = (self._wrap_width, box_h)
                self._text_stim.text = text
                self._text_stim.pos = (0, resolved_text_y)
                resolved_image_pos = (image_pos[0], resolved_img_y)
            else:
                self._text_stim.size = (self._wrap_width, box_h)
                self._text_stim.text = text
                self._text_stim.pos = text_pos
                resolved_image_pos = image_pos

            image_stim = visual.ImageStim(
                self.win,
                image=image,
                pos=resolved_image_pos,
                size=image_size,
            )
        else:
            # No image: let TextBox2 handle layout naturally.
            self._text_stim.alignment = 'center'
            self._text_stim.size = (self._wrap_width, 1.8)
            self._text_stim.text = text
            self._text_stim.pos = text_pos if text_pos is not None else (0, 0)
            image_stim = None

        event.clearEvents()
        while True:
            self._text_stim.draw()
            if image_stim is not None:
                image_stim.draw()
            self._prompt_stim.draw()
            self.win.flip()

            keys = event.getKeys(keyList=[key, 'escape'])
            if 'escape' in keys:
                self.win.close()
                return
            if key in keys:
                return

    def show_pages(
        self,
        pages: list[str | dict],
        continue_key: str | None = None,
    ) -> None:
        """
        Display multiple pages of instructions in sequence.

        Each page can be a plain string or a dict with the following keys:

        - ``text`` (str): The instruction text.
        - ``image`` (str, optional): Path to an image file.
        - ``image_pos`` (list, optional): Image position in norm units.
        - ``image_size`` (list, optional): Image size in norm units.

        Parameters
        ----------
        pages : list[str | dict]
            List of instruction pages.
        continue_key : str, optional
            Override the default continue key for all pages.

        """
        for page in pages:
            if isinstance(page, dict):
                self.show(
                    page['text'],
                    image=page.get('image'),
                    image_pos=tuple(page['image_pos']) if 'image_pos' in page else (0, -0.25),
                    image_size=tuple(page['image_size']) if 'image_size' in page else (0.3, 0.3),
                    text_pos=tuple(page['text_pos']) if 'text_pos' in page else None,
                    continue_key=continue_key,
                )
            else:
                self.show(page, continue_key=continue_key)
