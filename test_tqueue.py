from typing import Any, Callable

import tqueue


class CallFunc(tqueue.Schedulable):
    """A common pattern for run once actions."""

    def __init__(
        self,
        scheduler: tqueue.TurnQueue,
        interval: int,
        func: Callable[[], Any],
    ):
        super().__init__(scheduler)
        self.func = func
        self.sched_schedule(interval)

    def sched_on_turn(self) -> None:
        self.func()
        self.sched_ticket = None


class Actor(tqueue.Schedulable):
    """A common pattern for common actors."""

    def __init__(self, speed: int, **kargs: Any):
        super().__init__(**kargs)
        self.speed = speed
        self.sched_schedule(speed)

    def sched_on_turn(self) -> None:
        assert self.sched_queue.time == self.sched_ticket.time
        delta_time = self.sched_queue.time - self.sched_ticket.insert_time
        assert delta_time == self.speed
        self.sched_reschedule(self.speed)


def test_calls() -> None:
    lst = []
    scheduler = tqueue.TurnQueue()
    CallFunc(scheduler, 3, lambda: lst.append(3))
    CallFunc(scheduler, 2, lambda: lst.append(2))
    CallFunc(scheduler, 1, lambda: lst.append(1))
    CallFunc(scheduler, 4, lambda: lst.append(4))
    while scheduler:
        print(scheduler)
        scheduler.next()
    assert lst == [1, 2, 3, 4]


def test_actors() -> None:
    scheduler = tqueue.TurnQueue()
    actors = [
        Actor(scheduler=scheduler, speed=3),
        Actor(scheduler=scheduler, speed=5),
    ]
    while scheduler.time < 100:
        print(scheduler)
        scheduler.next()
