import asyncio
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from pocketflow import AsyncNode, AsyncParallelBatchFlow, AsyncParallelBatchNode


class TrackingParallelNode(AsyncParallelBatchNode):
    def __init__(self, *, fail_fast=False, delay=0.05, fail_on=None, events=None):
        super().__init__(fail_fast=fail_fast)
        self.delay = delay
        self.fail_on = fail_on
        self.events = events if events is not None else []

    async def prep_async(self, shared):
        return shared["items"]

    async def exec_async(self, item):
        self.events.append(("start", item))
        try:
            if item == self.fail_on:
                await asyncio.sleep(self.delay / 2)
                self.events.append(("fail", item))
                raise ValueError(f"boom-{item}")
            await asyncio.sleep(self.delay)
            self.events.append(("done", item))
            return item * 10
        except asyncio.CancelledError:
            self.events.append(("cancel", item))
            raise

    async def post_async(self, shared, prep_res, exec_res):
        shared["results"] = exec_res
        return "done"


class FlowWorkerNode(AsyncNode):
    def __init__(self, *, delay=0.05, fail_on=None, events=None):
        super().__init__()
        self.delay = delay
        self.fail_on = fail_on
        self.events = events if events is not None else []

    async def prep_async(self, shared):
        return self.params["item"]

    async def exec_async(self, item):
        self.events.append(("start", item))
        try:
            if item == self.fail_on:
                await asyncio.sleep(self.delay / 2)
                self.events.append(("fail", item))
                raise ValueError(f"flow-boom-{item}")
            await asyncio.sleep(self.delay)
            self.events.append(("done", item))
            return item * 10
        except asyncio.CancelledError:
            self.events.append(("cancel", item))
            raise

    async def post_async(self, shared, prep_res, exec_res):
        shared.setdefault("results", {})[prep_res] = exec_res
        return "done"


class TrackingParallelFlow(AsyncParallelBatchFlow):
    async def prep_async(self, shared):
        return [{"item": item} for item in shared["items"]]


@pytest.mark.asyncio
async def test_async_parallel_batch_node_default_behavior_is_not_fail_fast():
    node = TrackingParallelNode()
    assert node.fail_fast is False


@pytest.mark.asyncio
async def test_async_parallel_batch_node_fail_fast_false_keeps_running_tasks_alive():
    events = []
    shared = {"items": [1, 2, 3]}
    node = TrackingParallelNode(fail_fast=False, fail_on=2, delay=0.05, events=events)

    with pytest.raises(ValueError, match="boom-2"):
        await node.run_async(shared)

    await asyncio.sleep(0.06)

    assert ("done", 1) in events
    assert ("done", 3) in events
    assert all(event[0] != "cancel" for event in events)


@pytest.mark.asyncio
async def test_async_parallel_batch_node_fail_fast_true_cancels_remaining_tasks():
    events = []
    shared = {"items": [1, 2, 3]}
    node = TrackingParallelNode(fail_fast=True, fail_on=2, delay=0.05, events=events)

    with pytest.raises(ExceptionGroup) as exc_info:
        await node.run_async(shared)

    assert len(exc_info.value.exceptions) == 1
    assert isinstance(exc_info.value.exceptions[0], ValueError)
    assert ("fail", 2) in events
    assert ("cancel", 1) in events
    assert ("cancel", 3) in events
    assert ("done", 1) not in events
    assert ("done", 3) not in events


@pytest.mark.asyncio
async def test_async_parallel_batch_node_success_is_identical_in_both_modes():
    shared_false = {"items": [1, 2, 3]}
    shared_true = {"items": [1, 2, 3]}

    results_false = await TrackingParallelNode(fail_fast=False, delay=0.01).run_async(shared_false)
    results_true = await TrackingParallelNode(fail_fast=True, delay=0.01).run_async(shared_true)

    assert results_false == "done"
    assert results_true == "done"
    assert shared_false["results"] == [10, 20, 30]
    assert shared_true["results"] == [10, 20, 30]


@pytest.mark.asyncio
async def test_async_parallel_batch_flow_default_behavior_is_not_fail_fast():
    flow = TrackingParallelFlow()
    assert flow.fail_fast is False


@pytest.mark.asyncio
async def test_async_parallel_batch_flow_fail_fast_false_keeps_running_flows_alive():
    events = []
    shared = {"items": [1, 2, 3]}
    worker = FlowWorkerNode(delay=0.05, fail_on=2, events=events)
    flow = TrackingParallelFlow(start=worker, fail_fast=False)

    with pytest.raises(ValueError, match="flow-boom-2"):
        await flow.run_async(shared)

    await asyncio.sleep(0.06)

    assert ("done", 1) in events
    assert ("done", 3) in events
    assert shared["results"] == {1: 10, 3: 30}
    assert all(event[0] != "cancel" for event in events)


@pytest.mark.asyncio
async def test_async_parallel_batch_flow_fail_fast_true_cancels_remaining_flows():
    events = []
    shared = {"items": [1, 2, 3]}
    worker = FlowWorkerNode(delay=0.05, fail_on=2, events=events)
    flow = TrackingParallelFlow(start=worker, fail_fast=True)

    with pytest.raises(ExceptionGroup) as exc_info:
        await flow.run_async(shared)

    assert len(exc_info.value.exceptions) == 1
    assert isinstance(exc_info.value.exceptions[0], ValueError)
    assert ("fail", 2) in events
    assert ("cancel", 1) in events
    assert ("cancel", 3) in events
    assert ("done", 1) not in events
    assert ("done", 3) not in events
    assert "results" not in shared


@pytest.mark.asyncio
async def test_async_parallel_batch_flow_success_is_identical_in_both_modes():
    worker_false = FlowWorkerNode(delay=0.01)
    worker_true = FlowWorkerNode(delay=0.01)
    shared_false = {"items": [1, 2, 3]}
    shared_true = {"items": [1, 2, 3]}

    result_false = await TrackingParallelFlow(start=worker_false, fail_fast=False).run_async(shared_false)
    result_true = await TrackingParallelFlow(start=worker_true, fail_fast=True).run_async(shared_true)

    assert result_false is None
    assert result_true is None
    assert shared_false["results"] == {1: 10, 2: 20, 3: 30}
    assert shared_true["results"] == {1: 10, 2: 20, 3: 30}
