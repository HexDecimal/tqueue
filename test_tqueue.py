"""Tests for turn scheduling."""

from __future__ import annotations

import dataclasses
from typing import Any, Callable

import tqueue

# ruff: noqa: D103


@dataclasses.dataclass
class Actor:
    """A common pattern for common actors."""

    speed: int

    def act(self, tqueue: tqueue.TurnQueue[Actor]) -> None:
        """Reschedule self into the queue."""
        tqueue.schedule(self.speed, self)


def test_calls() -> None:
    lst = []
    scheduler: tqueue.TurnQueue[Callable[[], Any]] = tqueue.TurnQueue()
    scheduler.schedule(3, lambda: lst.append(3))
    func2 = scheduler.schedule(2, lambda: lst.append(2))
    scheduler.schedule(1, lambda: lst.append(1))
    scheduler.schedule(4, lambda: lst.append(4))

    print(scheduler)
    scheduler.pop().value()
    assert func2.get_time_passed(scheduler.time) == 1
    assert func2.get_time_left(scheduler.time) == 1
    assert func2.get_progress(scheduler.time) == 0.5  # noqa: PLR2004

    while scheduler:
        print(scheduler)
        scheduler.pop().value()
    assert lst == [1, 2, 3, 4]


def test_actors() -> None:
    scheduler: tqueue.TurnQueue[Actor] = tqueue.TurnQueue()
    scheduler.schedule(0, Actor(speed=3))
    scheduler.schedule(0, Actor(speed=5))
    while scheduler.time < 100:  # noqa: PLR2004
        print(scheduler)
        scheduler.pop().value.act(scheduler)
    assert len(scheduler.heap) == 2  # noqa: PLR2004
