"""Tests for Typed Port Contracts feature."""
import pytest
from pydantic import BaseModel
from pocketflow import Node, BaseNode, Flow


# --- Pydantic models for testing ---

class TextInput(BaseModel):
    raw_text: str

class TextOutput(BaseModel):
    raw_text: str
    word_count: int

class SummaryInput(BaseModel):
    raw_text: str
    word_count: int

class SummaryOutput(BaseModel):
    summary: str

class FormatterInput(BaseModel):
    summary: str

class FormatterOutput(BaseModel):
    formatted: str

class IncompatibleInput(BaseModel):
    raw_text: int  # int instead of str — type mismatch

class Animal(BaseModel):
    name: str

class Dog(Animal):
    breed: str

class AnimalOutput(BaseModel):
    pet: Dog  # Dog is subclass of Animal

class AnimalInput(BaseModel):
    pet: Animal


# --- Typed node definitions ---

class ExtractNode(Node):
    Input = TextInput
    Output = TextOutput

    def prep(self, shared):
        return shared.get("raw_text", "")

    def exec(self, prep_res):
        return {"raw_text": prep_res, "word_count": len(prep_res.split())}

    def post(self, shared, prep_res, exec_res):
        shared.update(exec_res)


class SummarizeNode(Node):
    Input = SummaryInput
    Output = SummaryOutput

    def prep(self, shared):
        return shared.get("raw_text", "")

    def exec(self, prep_res):
        return {"summary": prep_res[:50]}

    def post(self, shared, prep_res, exec_res):
        shared.update(exec_res)


class FormatNode(Node):
    Input = FormatterInput
    Output = FormatterOutput

    def prep(self, shared):
        return shared.get("summary", "")

    def exec(self, prep_res):
        return {"formatted": f"[{prep_res}]"}

    def post(self, shared, prep_res, exec_res):
        shared.update(exec_res)


class UntypedNodeA(Node):
    def prep(self, shared):
        return shared

    def exec(self, prep_res):
        return prep_res

    def post(self, shared, prep_res, exec_res):
        pass


class UntypedNodeB(Node):
    pass


class IncompatibleNode(Node):
    Input = IncompatibleInput
    Output = SummaryOutput


class AnimalOutputNode(Node):
    Output = AnimalOutput


class AnimalInputNode(Node):
    Input = AnimalInput


class TextInputNode(Node):
    Input = TextInput


# --- Tests ---

class TestNodeDefinition:
    """Test that nodes can define Input/Output Pydantic models."""

    def test_node_has_input_type(self):
        node = ExtractNode()
        assert node.__class__.Input is TextInput

    def test_node_has_output_type(self):
        node = ExtractNode()
        assert node.__class__.Output is TextOutput

    def test_summarize_node_has_own_types(self):
        node = SummarizeNode()
        assert node.__class__.Input is SummaryInput
        assert node.__class__.Output is SummaryOutput

    def test_untyped_node_has_none_types(self):
        node = UntypedNodeA()
        assert node.__class__.Input is None
        assert node.__class__.Output is None

    def test_base_node_defaults_none(self):
        assert BaseNode.Input is None
        assert BaseNode.Output is None


class TestGraphValidationSuccess:
    """Test that >> succeeds when Output satisfies Input."""

    def test_compatible_chain(self):
        """ExtractNode.Output has raw_text + word_count, SummarizeNode.Input needs raw_text + word_count."""
        a = ExtractNode()
        b = SummarizeNode()
        result = a >> b
        assert result is b

    def test_output_superset_of_input(self):
        """Output has more fields than Input requires — should pass."""
        a = ExtractNode()  # Output: raw_text, word_count
        b = TextInputNode()  # Input: raw_text only
        result = a >> b
        assert result is b

    def test_chaining_three_nodes(self):
        """A >> B >> C where types all flow correctly."""
        a = ExtractNode()
        b = SummarizeNode()
        c = FormatNode()
        result = a >> b >> c
        assert result is c
        assert b in a.successors.values()
        assert c in b.successors.values()


class TestGraphValidationFailure:
    """Test that >> raises TypeError when Output doesn't satisfy Input."""

    def test_missing_fields(self):
        """SummarizeNode.Output (summary) doesn't have raw_text required by TextInput."""
        a = SummarizeNode()
        b = TextInputNode()
        with pytest.raises(TypeError, match="missing fields"):
            a >> b

    def test_missing_fields_message_lists_fields(self):
        """Error message should list the missing field names."""
        a = SummarizeNode()  # Output: summary
        b = ExtractNode()    # Input: raw_text
        with pytest.raises(TypeError, match="raw_text"):
            a >> b

    def test_type_mismatch(self):
        """Field exists but types are incompatible."""
        a = ExtractNode()      # Output: raw_text: str
        b = IncompatibleNode() # Input: raw_text: int
        with pytest.raises(TypeError, match="type mismatch"):
            a >> b

    def test_chain_fails_at_second_link(self):
        """A >> B succeeds, but B >> C fails."""
        a = ExtractNode()
        b = SummarizeNode()
        c = ExtractNode()  # Input needs raw_text: str, but SummarizeNode.Output only has summary
        a >> b
        with pytest.raises(TypeError, match="missing fields"):
            b >> c


class TestBackwardCompatibility:
    """Test that untyped nodes work exactly as before."""

    def test_untyped_to_untyped(self):
        a = UntypedNodeA()
        b = UntypedNodeB()
        result = a >> b
        assert result is b

    def test_typed_to_untyped(self):
        """Typed output, no input requirement — should pass."""
        a = ExtractNode()
        b = UntypedNodeA()
        result = a >> b
        assert result is b

    def test_untyped_to_typed(self):
        """No output type, typed input — should pass (can't validate)."""
        a = UntypedNodeA()
        b = SummarizeNode()
        result = a >> b
        assert result is b

    def test_conditional_transition_still_works(self):
        """The - 'action' >> node pattern should still work."""
        a = ExtractNode()
        b = SummarizeNode()
        a - "summarize" >> b
        assert a.successors["summarize"] is b


class TestSubtypeCompatibility:
    """Test that subclass types pass validation."""

    def test_subtype_output_matches_parent_input(self):
        """Dog is a subclass of Animal, so AnimalOutput.pet (Dog) should satisfy AnimalInput.pet (Animal)."""
        a = AnimalOutputNode()
        b = AnimalInputNode()
        result = a >> b
        assert result is b


class TestLifecycle:
    """Test the full prep→exec→post lifecycle with typed contracts."""

    def test_single_typed_node_lifecycle(self):
        shared = {"raw_text": "hello world foo bar"}
        node = ExtractNode()
        node.run(shared)
        assert shared["raw_text"] == "hello world foo bar"
        assert shared["word_count"] == 4

    def test_typed_flow_lifecycle(self):
        """Full flow: Extract → Summarize → Format."""
        extract = ExtractNode()
        summarize = SummarizeNode()
        fmt = FormatNode()

        extract >> summarize >> fmt

        flow = Flow(start=extract)
        shared = {"raw_text": "hello world this is a test of typed port contracts in pocketflow"}
        flow.run(shared)

        assert "summary" in shared
        assert "formatted" in shared
        assert shared["formatted"].startswith("[")
        assert shared["formatted"].endswith("]")

    def test_typed_node_with_retries(self):
        """Typed node with max_retries still works."""
        class RetryNode(Node):
            Input = TextInput
            Output = TextOutput
            def __init__(self):
                super().__init__(max_retries=3, wait=0)
                self.attempts = 0
            def exec(self, prep_res):
                self.attempts += 1
                if self.attempts < 3:
                    raise ValueError("not yet")
                return {"raw_text": "ok", "word_count": 1}
            def post(self, shared, prep_res, exec_res):
                shared.update(exec_res)

        node = RetryNode()
        shared = {}
        node.run(shared)
        assert node.attempts == 3
        assert shared["word_count"] == 1
