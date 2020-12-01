from importlib import reload
from typing import Callable
from unittest.mock import Mock, patch

import pytest
from outcome.utils import transactions
from outcome.utils.transactions import InvalidState, Operation, OperationNotApplied, OperationState, transaction


@patch.dict('sys.modules', {'transaction': None})
def test_import_error():
    with pytest.raises(Exception):
        reload(transactions)


class TestOperation:
    def test_apply(self):
        test_operation = Operation(apply_fn=lambda: None, rollback_fn=lambda: None)
        test_operation.apply()
        assert test_operation.state == OperationState.applied

    @pytest.mark.parametrize('invalid_state', [OperationState.applied, OperationState.errored, OperationState.reset])
    def test_apply_wrong_state(self, invalid_state):
        test_operation = Operation(apply_fn=lambda: None, rollback_fn=lambda: None)
        test_operation.state = invalid_state
        with pytest.raises(InvalidState):
            test_operation.apply()

    def test_rollback(self):
        test_operation = Operation(apply_fn=lambda: None, rollback_fn=lambda: None)
        test_operation.state = OperationState.applied
        test_operation.rollback()
        assert test_operation.state == OperationState.reset

    @pytest.mark.parametrize('invalid_state', [OperationState.pending, OperationState.errored, OperationState.reset])
    def test_rollback_wrong_state(self, invalid_state):
        test_operation = Operation(apply_fn=lambda: None, rollback_fn=lambda: None)
        test_operation.state = invalid_state
        with pytest.raises(InvalidState):
            test_operation.rollback()


class TestTransaction:
    def test_auto_apply(self):
        with transaction() as ops:
            test_operation = Operation(apply_fn=lambda: None, rollback_fn=lambda: None)
            assert test_operation.state == OperationState.pending

            ops.add(test_operation)
            assert test_operation.state == OperationState.pending

        assert test_operation.state == OperationState.applied

    def test_manual_apply(self):
        with transaction(auto_apply=False) as ops:
            test_operation = Operation(apply_fn=lambda: None, rollback_fn=lambda: None)
            assert test_operation.state == OperationState.pending

            ops.add(test_operation)
            assert test_operation.state == OperationState.pending

            test_operation.apply()
            assert test_operation.state == OperationState.applied

        assert test_operation.state == OperationState.applied

    def test_manual_apply_one_op_not_applied(self):  # noqa: WPS218 - too many `assert` statements
        with pytest.raises(OperationNotApplied):
            with transaction(auto_apply=False) as ops:
                first_operation = Operation(apply_fn=lambda: None, rollback_fn=lambda: None)
                second_operation = Operation(apply_fn=lambda: None, rollback_fn=lambda: None)

                assert first_operation.state == OperationState.pending
                assert second_operation.state == OperationState.pending

                ops.add(first_operation)
                ops.add(second_operation)

                assert first_operation.state == OperationState.pending
                assert second_operation.state == OperationState.pending

                first_operation.apply()
                assert first_operation.state == OperationState.applied
                assert second_operation.state == OperationState.pending

        assert first_operation.state == OperationState.reset
        assert second_operation.state == OperationState.pending

    def test_multiple_ops_one_failed(self):  # noqa: WPS218 - too many `assert` statements
        mock_first_apply = Mock(Callable)
        mock_first_rollback = Mock(Callable)

        mock_second_apply = Mock(Callable)
        mock_second_apply.side_effect = Exception
        mock_second_rollback = Mock(Callable)

        with pytest.raises(Exception):
            with transaction() as ops:
                test_first_operation = Operation(apply_fn=mock_first_apply, rollback_fn=mock_first_rollback)
                test_second_operation = Operation(apply_fn=mock_second_apply, rollback_fn=mock_second_rollback)

                ops.add(test_first_operation)
                ops.add(test_second_operation)

                assert mock_first_apply.called is False
                assert mock_second_apply.called is False

        assert test_first_operation.state == OperationState.reset
        assert test_second_operation.state == OperationState.errored

        assert mock_first_apply.called is True
        assert mock_second_apply.called is True

        assert mock_first_rollback.called is True
        assert mock_second_rollback.called is False
