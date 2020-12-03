"""Transactions handler.

Usage examples:

- Default usage auto-applies all added operations.
```
with transaction() as ops:
    op = Operation(apply_fn=your_apply_fn, rollback_fn=your_rollback_fn)
    ops.add(op)
```

- We can disable auto-apply if necessary. In this case, the context manager
will check if some operations weren't applied at the end of the transaction.
```
op = None
with transaction(auto_apply=False) as ops:
    op = Operation(apply_fn=your_apply_fn, rollback_fn=your_rollback_fn)
    ops.add(create_user)
    op.apply()
```

"""

from contextlib import contextmanager
from enum import Enum
from typing import Callable, Generic, Optional, TypeVar

try:
    from transaction import Transaction, TransactionManager  # noqa: WPS433 - nested import
    from transaction.interfaces import IDataManager  # noqa: WPS433 - nested import
    from zope.interface import implementer  # noqa: WPS433 - nested import
except ImportError as exc:
    raise Exception('You need to install the `transaction` extra to use the transaction features') from exc


@contextmanager
def transaction(auto_apply: bool = True):
    manager = TransactionManager(explicit=True)

    with manager as txn:
        ops = OperationManager(txn)

        yield ops

        if auto_apply:
            ops.apply()
        else:
            ops.ensure_applied()


class OperationState(Enum):
    pending = 'pending'
    applied = 'applied'
    errored = 'errored'
    reset = 'reset'


class InvalidState(Exception):
    ...


class OperationNotApplied(Exception):
    ...


T = TypeVar('T')

OperationApplyFn = Callable[[], Optional[T]]
OperationRollbackFn = Callable[[Optional[T]], None]


class Operation(Generic[T]):
    result: Optional[T]
    apply_fn: OperationApplyFn[T]
    rollback_fn: OperationRollbackFn[T]

    def __init__(self, apply_fn: OperationApplyFn[T], rollback_fn: OperationRollbackFn[T]):
        self.apply_fn = apply_fn
        self.rollback_fn = rollback_fn
        self.state = OperationState.pending
        self.result = None

    def apply(self):
        if self.state != OperationState.pending:
            raise InvalidState

        try:
            self.result = self.apply_fn()
            self.state = OperationState.applied
        except Exception as ex:
            self.state = OperationState.errored
            raise Exception('Failed to apply operation') from ex

    def rollback(self):
        if self.state != OperationState.applied:
            raise InvalidState

        self.rollback_fn(self.result)
        self.state = OperationState.reset


@implementer(IDataManager)
class OperationManager:  # noqa: WPS214 - too many methods
    def __init__(self, txn: Transaction):
        self.operations = []
        txn.join(self)

    def add(self, operation: Operation):
        self.operations.append(operation)

    def apply(self):
        for op in self.operations:
            op.apply()

    def abort(self, txn: Transaction):
        for op in reversed(self.operations):
            if op.state == OperationState.applied:
                op.rollback()

    def ensure_applied(self):
        for op in self.operations:
            if op.state != OperationState.applied:
                raise OperationNotApplied(op.state)

    # Methods under this comment are required as the `IDataManager` interface doesn't define any behavior
    # https://zope.readthedocs.io/en/latest/zdgbook/ComponentsAndInterfaces.html#zope-components

    def tpc_begin(self, txn):
        pass

    def tpc_vote(self, txn):
        pass

    def tpc_finish(self, txn):
        pass

    def commit(self, txn):
        pass
