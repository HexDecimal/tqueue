# This is free and unencumbered software released into the public domain.
#
# Anyone is free to copy, modify, publish, use, compile, sell, or
# distribute this software, either in source code form or as a compiled
# binary, for any purpose, commercial or non-commercial, and by any
# means.
#
# In jurisdictions that recognize copyright laws, the author or authors
# of this software dedicate any and all copyright interest in the
# software to the public domain. We make this dedication for the benefit
# of the public at large and to the detriment of our heirs and
# successors. We intend this dedication to be an overt act of
# relinquishment in perpetuity of all present and future rights to this
# software under copyright law.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
# For more information, please refer to <http://unlicense.org/>
"""A priority queue scheduler for use in game development.

See the queued turns time system:
http://www.roguebasin.com/index.php?title=Time_Systems#Queued_turns
"""
from __future__ import annotations

import heapq
from typing import (
    Any,
    Dict,
    Iterable,
    Iterator,
    List,
    NamedTuple,
    Optional,
    Tuple,
)


class Ticket(NamedTuple):
    """Describes a scheduled object.

    `time` is when `actor` will run.

    `uid` is a unique number used as a tie-breaker when sorting.
    It enforces that Ticket's with the same `time` will run in FIFO order.

    `actor` is the Schedulable instance attached to this Ticket.
    `actor.sched_ticket`

    `insert_time` is the time this Ticket was inserted into the schedule.
    This can be used to get the delta time of this Ticket with
    `time - insert_time` or some equivalent.
    """

    time: int
    uid: int
    actor: Schedulable
    insert_time: int


class TurnQueue:
    def __init__(
        self,
        time: int = 0,
        next_uid: int = 0,
        heap: Iterable[Ticket] = (),
    ) -> None:
        self.time = time  # Current time.
        self.next_uid = next_uid  # Sorting tie-breaker.
        # Priority queue of events maintained by heapq
        self.heap: List[Ticket] = list(heap)
        heapq.heapify(self.heap)

    def clean(self) -> None:
        """Remove all invalid tickets from this schedulers heap.

        This is a relatively expensive operation.  It might be useful to cull
        references to objects but in general this will happen automatically
        during normal use.
        """
        self.heap = [t for t in self.heap if t is t.actor.sched_ticket]
        heapq.heapify(self.heap)

    def __bool__(self) -> bool:
        """Return True if a valid ticket exists in this scheduler."""
        try:
            self.peek()
        except IndexError:
            return False
        return True

    def peek(self) -> Ticket:
        """Return the next valid ticket without running it.

        IndexError will be raised if no valid ticket exists.
        """
        while self.heap[0] is not self.heap[0].actor.sched_ticket:
            # Ticket was invalid and will be dropped.
            heapq.heappop(self.heap)
        return self.heap[0]

    def next(self) -> None:
        """Run the next scheduled actor.

        IndexError will be raised if the scheduler has no valid tickets to run.
        """
        next_ticket = self.peek()
        self.time, _, actor, _ = next_ticket
        actor.sched_on_turn(next_ticket)
        if actor.sched_ticket is next_ticket:
            raise RuntimeError(
                f"Schedulable object {actor} did not update its schedule."
                "\nTo reschedule this object call `self.sched_reschedule`"
                "\nOr if done set `self.sched_ticket = None`"
                " to remove it from the schedule."
            )

    def __getnewargs_ex__(self) -> Tuple[Tuple[()], Dict[str, Any]]:
        """If this scheduler is pickled it will call clean automatically."""
        self.clean()
        return (), {
            "time": self.time,
            "next_uid": self.next_uid,
            "heap": self.heap,
        }

    def __repr__(self) -> str:
        """A string representation of this instance, including all tickets."""
        return "%s(time=%r, next_uid=%r, heap=%r)" % (
            self.__class__.__name__,
            self.time,
            self.next_uid,
            self.heap,
        )


class Schedulable:
    """A mix-in class for actor-like classes.

    When this class is constructed it is bound to a specific `TurnQueue`
    instance `scheduler` which will be available as `self.sched_queue`.

    `self.sched_ticket` is the `Ticket` for this actor.  It will start as
    `None` which means this actor is not scheduled.  So `self.sched_schedule`
    should be called after this object is constructed or in the constructer
    after `Schedulable` is initialized.

    This object can always check `self.sched_queue.time` to get the current
    time and `self.sched_ticket.time` to get its own scheduled time.
    """

    def __init__(self, scheduler: TurnQueue, *args: Any, **kargs: Any):
        """This is a mix-in so extra arguments as passed to the next class
        in the `Method Resolution Order`."""
        self.sched_queue = scheduler
        self.sched_ticket: Optional[Ticket] = None
        super().__init__(*args, **kargs)  # type: ignore

    def __new_ticket(self, time: int) -> Ticket:
        """Returns a unique Ticket which will sort in FIFO order.

        This is not used directly, but is called from `sched_schedule` or
        `sched_reschedule`.
        """
        ticket = Ticket(
            time, self.sched_queue.next_uid, self, self.sched_queue.time
        )
        # Sort tickets with the same time in FIFO order.
        self.sched_queue.next_uid += 1
        return ticket

    def sched_schedule(self, interval: int) -> None:
        """Insert an actor onto the queue and assign its Ticket.

        `interval` is the amount of time passed before `sched_on_turn` is
        called.

        Each instance can only be scheduled once.  If this instance was
        already scheduled then its previous ticket will become invalid.

        You may remove this instance from the schedule at anytime by setting
        `self.sched_ticket = None`.

        `self.sched_ticket` is updated with a new Ticket.
        """
        self.sched_ticket = self.__new_ticket(self.sched_queue.time + interval)
        heapq.heappush(self.sched_queue.heap, self.sched_ticket)

    def sched_reschedule(self, interval: int) -> None:
        """Reschedule an actor that's being processed.

        `interval` is the amount of time passed before `sched_on_turn` is
        called.

        This is the optimal function to call from `sched_on_turn` when an
        actor runs over multiple turns.

        This must be called from `sched_on_turn`.
        This must be called for the same instance by the same instance.
        This must only be called once on each call to `sched_on_turn`.

        `self.sched_ticket` is updated with a new Ticket.
        """
        if self.sched_ticket is not self.sched_queue.heap[0]:
            raise RuntimeError(
                "Reschedule failed because this wasn't the active actor."
                " Make sure this function wasn't called twice."
            )
        self.sched_ticket = self.__new_ticket(self.sched_queue.time + interval)
        heapq.heapreplace(self.sched_queue.heap, self.sched_ticket)

    def sched_on_turn(self, ticket: Ticket) -> None:
        """Called on this objects turn.
        Needs to be overridden by subclasses.

        This function must either call `self.sched_reschedule` or
        set `self.sched_ticket = None` before returning.

        `self.sched_ticket is self.sched_queue.peek()` will be True when this
        function begins.  If it is still True when this function returns then
        an error will be raised.

        The `ticket` parameter is the same object as `self.sched_ticket`, but
        with a more strict type hint.

        `self.sched_time_passed` can be used to get the delta time of this
        Ticket.
        """
        raise NotImplementedError(
            "Must be overridden by subclasses, see docstring for more info."
        )

    @property
    def sched_time_passed(self) -> int:
        """The amount of time passed since this object was last scheduled."""
        assert self.sched_ticket
        return self.sched_queue.time - self.sched_ticket.insert_time

    @property
    def sched_time_left(self) -> int:
        """The amount of time until this scheduled object is triggered."""
        assert self.sched_ticket
        return self.sched_ticket.time - self.sched_queue.time

    @property
    def sched_progress(self) -> float:
        """The progress of the last scheduled action.  From 0 to 1."""
        assert self.sched_ticket
        return self.sched_time_passed / (
            self.sched_ticket.time - self.sched_ticket.insert_time
        )


__all__ = (
    "Ticket",
    "TurnQueue",
    "Schedulable",
)
