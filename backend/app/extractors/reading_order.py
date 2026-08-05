from dataclasses import dataclass

import numpy as np

from app.extractors.layout import LayoutElement


@dataclass(frozen=True)
class ReadingGroup:
    elements: list[LayoutElement]
    atomic: bool = False


def build_reading_groups(
    elements: list[LayoutElement],
    atomic_elements: list[LayoutElement],
    *,
    page_width: float,
    page_left: float = 0,
) -> list[ReadingGroup] | None:
    """지속적인 세로 여백이 있을 때만 좌우 열 읽기 순서를 만든다."""
    if len(elements) < 6 or page_width <= 0:
        return None

    lines = _group_lines(elements)
    gutter = _find_column_gutter(elements, page_width, page_left)
    if gutter is None:
        return None

    gutter_x1, gutter_x2 = gutter
    spanning_lines: list[list[LayoutElement]] = []
    column_elements: list[LayoutElement] = []

    for line in lines:
        if _is_spanning_line(line, gutter_x1, gutter_x2):
            spanning_lines.append(line)
        else:
            column_elements.extend(line)

    separators = [
        ReadingGroup(line)
        for line in spanning_lines
    ] + [
        ReadingGroup([element], atomic=True)
        for element in atomic_elements
    ]
    separators.sort(key=lambda group: _group_center_y(group.elements))

    groups: list[ReadingGroup] = []
    remaining = list(column_elements)
    previous_y = float("-inf")

    for separator in separators:
        separator_y = _group_center_y(separator.elements)
        band = [
            element
            for element in remaining
            if previous_y <= _center_y(element) < separator_y
        ]
        groups.extend(_column_groups(band, gutter_x1, gutter_x2))
        groups.append(separator)
        band_ids = {id(element) for element in band}
        remaining = [element for element in remaining if id(element) not in band_ids]
        previous_y = separator_y

    groups.extend(_column_groups(remaining, gutter_x1, gutter_x2))
    return groups


def _find_column_gutter(
    elements: list[LayoutElement],
    page_width: float,
    page_left: float,
) -> tuple[float, float] | None:
    bin_count = 160
    y_bin_count = 240
    page_top = min(item.y for item in elements)
    page_bottom = max(_y2(item) for item in elements)
    content_height = max(page_bottom - page_top, 1.0)
    occupied = np.zeros((y_bin_count, bin_count), dtype=bool)
    page_center = page_left + page_width / 2

    for item in elements:
        item_width = max(_x2(item) - item.x, 1.0)
        if (
            item_width >= page_width * 0.35
            and item.x < page_center < _x2(item)
        ):
            continue
        x_start = _to_bin(item.x, page_left, page_width, bin_count)
        x_end = _to_bin(_x2(item), page_left, page_width, bin_count)
        y_start = _to_bin(item.y, page_top, content_height, y_bin_count)
        y_end = _to_bin(_y2(item), page_top, content_height, y_bin_count)
        occupied[y_start : y_end + 1, x_start : x_end + 1] = True

    vertical_density = occupied.mean(axis=0)
    inner_start = round(bin_count * 0.15)
    inner_end = bin_count - inner_start
    inner_density = vertical_density[inner_start:inner_end]
    density_reference = float(np.quantile(inner_density, 0.75))
    density_limit = max(0.04, density_reference * 0.30)
    whitespace = vertical_density <= density_limit

    whitespace[:inner_start] = False
    whitespace[inner_end:] = False

    median_height = float(
        np.median([max(_y2(item) - item.y, 1.0) for item in elements])
    )
    minimum_width = max(page_width * 0.025, median_height * 1.25)
    candidates: list[tuple[float, float, float]] = []

    start = None
    for index, is_empty in enumerate(np.append(whitespace, False)):
        if is_empty and start is None:
            start = index
        elif not is_empty and start is not None:
            x1 = page_left + start / bin_count * page_width
            x2 = page_left + index / bin_count * page_width
            if x2 - x1 >= minimum_width:
                center_ratio = ((_center(x1, x2) - page_left) / page_width)
                if not 0.25 <= center_ratio <= 0.75:
                    start = None
                    continue
                mean_density = float(vertical_density[start:index].mean())
                score = (x2 - x1) * (1.0 - mean_density)
                candidates.append((score, x1, x2))
            start = None

    for _, x1, x2 in sorted(candidates, reverse=True):
        left = [item for item in elements if _center_x(item) < x1]
        right = [item for item in elements if _center_x(item) > x2]
        if len(left) < 3 or len(right) < 3:
            continue
        if min(len(left), len(right)) / max(len(left), len(right)) < 0.2:
            continue
        return x1, x2

    return None


def _group_lines(elements: list[LayoutElement]) -> list[list[LayoutElement]]:
    lines: list[list[LayoutElement]] = []
    for element in sorted(elements, key=lambda item: (_center_y(item), item.x)):
        matching = next(
            (line for line in lines if _vertical_overlap(element, line) >= 0.45),
            None,
        )
        if matching is None:
            lines.append([element])
        else:
            matching.append(element)
    return lines


def _vertical_overlap(element: LayoutElement, line: list[LayoutElement]) -> float:
    element_y2 = _y2(element)
    line_y1 = min(item.y for item in line)
    line_y2 = max(_y2(item) for item in line)
    overlap = max(0.0, min(element_y2, line_y2) - max(element.y, line_y1))
    return overlap / min(max(element_y2 - element.y, 1.0), max(line_y2 - line_y1, 1.0))


def _column_groups(
    elements: list[LayoutElement],
    gutter_x1: float,
    gutter_x2: float,
) -> list[ReadingGroup]:
    left: list[LayoutElement] = []
    right: list[LayoutElement] = []
    ambiguous: list[LayoutElement] = []
    for item in elements:
        center_x = _center_x(item)
        if center_x < gutter_x1:
            left.append(item)
        elif center_x > gutter_x2:
            right.append(item)
        else:
            ambiguous.append(item)

    groups = []
    if left:
        groups.append(ReadingGroup(left))
    if right:
        groups.append(ReadingGroup(right))
    groups.extend(ReadingGroup([item]) for item in sorted(ambiguous, key=lambda x: (x.y, x.x)))
    return groups


def _intersects_gutter(element: LayoutElement, x1: float, x2: float) -> bool:
    return element.x < x2 and _x2(element) > x1


def _is_spanning_line(
    line: list[LayoutElement],
    gutter_x1: float,
    gutter_x2: float,
) -> bool:
    if any(_intersects_gutter(item, gutter_x1, gutter_x2) for item in line):
        return True

    left = [item for item in line if _center_x(item) < gutter_x1]
    right = [item for item in line if _center_x(item) > gutter_x2]
    if not left or not right or len(line) < 3:
        return False

    median_height = float(
        np.median([max(_y2(item) - item.y, 1.0) for item in line])
    )
    narrow_count = sum(
        max(_x2(item) - item.x, 1.0) <= median_height * 2.5
        for item in line
    )
    bridge_gap = min(item.x for item in right) - max(_x2(item) for item in left)
    return narrow_count >= len(line) / 2 and bridge_gap <= median_height * 5.0


def _center(value1: float, value2: float) -> float:
    return (value1 + value2) / 2


def _to_bin(
    value: float,
    page_left: float,
    page_width: float,
    bin_count: int,
) -> int:
    normalized = (value - page_left) / page_width
    return min(max(int(normalized * bin_count), 0), bin_count - 1)


def _x2(element: LayoutElement) -> float:
    return element.x2 if element.x2 is not None else element.x


def _y2(element: LayoutElement) -> float:
    return element.y2 if element.y2 is not None else element.y


def _center_x(element: LayoutElement) -> float:
    return (element.x + _x2(element)) / 2


def _center_y(element: LayoutElement) -> float:
    return (element.y + _y2(element)) / 2


def _group_center_y(elements: list[LayoutElement]) -> float:
    return min(_center_y(element) for element in elements)
