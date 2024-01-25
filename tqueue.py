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

__all__ = (
    "Ticket",
    "TurnQueue",
)

import heapq
from typing import Generic, Iterable, NamedTuple, TypeVar

T = TypeVar("T")


class Ticket(NamedTuple, Generic[T]):
    """Describes a scheduled object."""

    time: int
    """The time this Ticket will be returned from the scheduler."""
    uid: int
    """A unique number which enforces FIFO ordering of tickets with the same `time`."""
    value: T
    """The scheduled object."""
    insert_time: int
    """The time this ticket was inserted into the scheduler.

    This can be used to get the delta time of this Ticket with
    `time - insert_time` or some equivalent.
    """

    def get_time_passed(self, current_time: int) -> int:
        """Return the amount of time passed since this Ticket was initially scheduled."""
        return current_time - self.insert_time

    def get_time_left(self, current_time: int) -> int:
        """Return the amount of time until this Ticket is triggered."""
        return self.time - current_time

    def get_progress(self, current_time: int) -> float:
        """Return the current progress of this Ticket as a float from 0 to 1."""
        return self.get_time_passed(current_time) / (
            self.time - self.insert_time
        )


class TurnQueue(Generic[T]):
    """Turned queue manager."""

    def __init__(
        self,
        time: int = 0,
        next_uid: int = 0,
        heap: Iterable[Ticket[T]] = (),
    ) -> None:
        """Initialize the scheduler."""
        self.time = time
        """The current tick. Always the time of the most recently popped ticket."""
        self.next_uid = next_uid
        """Incrementing unique id used to enforce FIFO order on tickets."""
        self.heap: list[Ticket[T]] = list(heap)
        """The heap queue of events maintained by Python's `heapq` module."""
        heapq.heapify(self.heap)

    def __bool__(self) -> bool:
        """Return True if a scheduled object exists in this scheduler."""
        return bool(self.heap)

    def peek(self) -> Ticket[T]:
        """Return the next scheduled ticket without removing it.

        IndexError will be raised if the heap is empty.
        """
        return self.heap[0]

    def schedule(self, interval: int, value: T) -> Ticket[T]:
        """Schedule `value` to be returned after `internal` time passes.

        Returns the new Ticket associated with the scheduled `value`.
        """
        ticket = Ticket(self.time + interval, self.next_uid, value, self.time)
        self.next_uid += 1
        heapq.heappush(self.heap, ticket)
        return ticket

    def pop(self) -> Ticket[T]:
        """Pop and return the next scheduled Ticket from the queue.

        This will set `TurnQueue.time` to the tickets current time.
        """
        ticket = heapq.heappop(self.heap)
        self.time = ticket.time
        return ticket

    def __repr__(self) -> str:
        """A string representation of this instance, including all tickets."""
        return "{}(time={!r}, next_uid={!r}, heap={!r})".format(
            self.__class__.__name__,
            self.time,
            self.next_uid,
            self.heap,
        )
