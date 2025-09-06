#!/usr/bin/env python3
"""
Comprehensive test suite for PRP Builder Pattern
Tests fluent interface, validation, and PRP construction
"""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from subforge.core.context_engineer import ContextPackage
from subforge.core.prp.base import PRP, PRPType
from subforge.core.prp.builder import PRPBuilder


class TestPRPBuilder:
    """Test suite for PRP Builder"""
    
    @pytest.fixture
    def builder(self):
        """Create a fresh builder instance"""
        return PRPBuilder()
    
    @pytest.fixture
    def mock_context_package(self):
        """Create mock context package"""
        package = Mock(spec=ContextPackage)
        package.project_context = {"type": "backend"}
        package.examples = ["example1", "example2"]
        package.patterns = ["pattern1", "pattern2"]
        package.to_markdown = Mock(return_value="# Context Package")
        return package
    
    def test_initialization(self, builder):
        """Test builder initialization"""
        assert builder._id is None
        assert builder._type is None
        assert builder._title is None
        assert builder._context_package is None
        assert builder._execution_prompt is None
        assert builder._validation_checklist == []
        assert builder._success_metrics == []
        assert builder._output_specification == {}
        assert builder._created_at is None
    
    def test_fluent_interface(self, builder, mock_context_package):
        """Test builder chaining (fluent interface)"""
        # All methods should return self for chaining
        result = (
            builder
            .with_id("test-id")
            .with_type(PRPType.FACTORY_ANALYSIS)
            .with_title("Test PRP")
            .with_context_package(mock_context_package)
            .with_execution_prompt("Test prompt")
            .add_validation_item("Check 1")
            .add_success_metric("Metric 1")
            .with_output_specification({"format": "json"})
        )
        
        assert result is builder
    
    def test_complete_prp_construction(self, builder, mock_context_package):
        """Test building complete PRP"""
        prp = (
            builder
            .with_id("prp-123")
            .with_type(PRPType.FACTORY_GENERATION)
            .with_title("Generation PRP")
            .with_context_package(mock_context_package)
            .with_execution_prompt("Generate agents")
            .add_validation_item("Validate syntax")
            .add_validation_item("Check completeness")
            .add_success_metric("All agents created")
            .add_success_metric("Tests pass")
            .with_output_specification({"format": "markdown", "count": 5})
            .build()
        )
        
        assert isinstance(prp, PRP)
        assert prp.id == "prp-123"
        assert prp.type == PRPType.FACTORY_GENERATION
        assert prp.title == "Generation PRP"
        assert prp.context_package == mock_context_package
        assert prp.execution_prompt == "Generate agents"
        assert len(prp.validation_checklist) == 2
        assert "Validate syntax" in prp.validation_checklist
        assert "Check completeness" in prp.validation_checklist
        assert len(prp.success_metrics) == 2
        assert "All agents created" in prp.success_metrics
        assert "Tests pass" in prp.success_metrics
        assert prp.output_specification["format"] == "markdown"
        assert prp.output_specification["count"] == 5
        assert prp.created_at is not None
    
    def test_builder_validation(self, builder):
        """Test validation during build"""
        # Try to build without required fields
        with pytest.raises(ValueError, match="Missing required fields"):
            builder.build()
        
        # Add ID but still missing other fields
        builder.with_id("test-id")
        with pytest.raises(ValueError, match="Missing required fields"):
            builder.build()
        
        # Add type
        builder.with_type(PRPType.VALIDATION_COMPREHENSIVE)
        with pytest.raises(ValueError, match="Missing required fields"):
            builder.build()
        
        # Add title
        builder.with_title("Test Title")
        with pytest.raises(ValueError, match="Missing required fields"):
            builder.build()
        
        # Add context package
        builder.with_context_package(Mock(spec=ContextPackage))
        with pytest.raises(ValueError, match="Missing required fields"):
            builder.build()
        
        # Now it should build successfully with remaining defaults
        builder.with_execution_prompt("Test prompt")
        prp = builder.build()
        assert prp is not None
    
    def test_builder_reset(self, builder, mock_context_package):
        """Test builder reset functionality"""
        # Build first PRP
        prp1 = (
            builder
            .with_id("prp-1")
            .with_type(PRPType.FACTORY_ANALYSIS)
            .with_title("First PRP")
            .with_context_package(mock_context_package)
            .with_execution_prompt("First prompt")
            .build()
        )
        
        # Builder should auto-reset after build
        assert builder._id is None
        assert builder._type is None
        
        # Build second PRP
        prp2 = (
            builder
            .with_id("prp-2")
            .with_type(PRPType.FACTORY_GENERATION)
            .with_title("Second PRP")
            .with_context_package(mock_context_package)
            .with_execution_prompt("Second prompt")
            .build()
        )
        
        # PRPs should be different
        assert prp1.id != prp2.id
        assert prp1.type != prp2.type
        assert prp1.title != prp2.title
        assert prp1.execution_prompt != prp2.execution_prompt
    
    def test_partial_builds(self, builder, mock_context_package):
        """Test building with missing optional components"""
        # Build with minimal required fields
        prp = (
            builder
            .with_id("minimal")
            .with_type(PRPType.VALIDATION_COMPREHENSIVE)
            .with_title("Minimal PRP")
            .with_context_package(mock_context_package)
            .with_execution_prompt("Minimal prompt")
            .build()
        )
        
        # Optional fields should have defaults
        assert prp.validation_checklist == []
        assert prp.success_metrics == []
        assert prp.output_specification == {}
        assert prp.created_at is not None
    
    def test_adding_multiple_validation_items(self, builder, mock_context_package):
        """Test adding multiple validation checklist items"""
        prp = (
            builder
            .with_id("multi-validation")
            .with_type(PRPType.FACTORY_ANALYSIS)
            .with_title("Multi Validation")
            .with_context_package(mock_context_package)
            .with_execution_prompt("Test")
            .add_validation_item("Check 1")
            .add_validation_item("Check 2")
            .add_validation_item("Check 3")
            .build()
        )
        
        assert len(prp.validation_checklist) == 3
        assert prp.validation_checklist == ["Check 1", "Check 2", "Check 3"]
    
    def test_adding_multiple_success_metrics(self, builder, mock_context_package):
        """Test adding multiple success metrics"""
        prp = (
            builder
            .with_id("multi-metrics")
            .with_type(PRPType.FACTORY_GENERATION)
            .with_title("Multi Metrics")
            .with_context_package(mock_context_package)
            .with_execution_prompt("Test")
            .add_success_metric("Metric 1")
            .add_success_metric("Metric 2")
            .add_success_metric("Metric 3")
            .add_success_metric("Metric 4")
            .build()
        )
        
        assert len(prp.success_metrics) == 4
        assert all(f"Metric {i}" in prp.success_metrics for i in range(1, 5))
    
    def test_with_validation_checklist_replace(self, builder, mock_context_package):
        """Test replacing entire validation checklist"""
        checklist = ["New Check 1", "New Check 2", "New Check 3"]
        
        prp = (
            builder
            .with_id("replace-checklist")
            .with_type(PRPType.VALIDATION_COMPREHENSIVE)
            .with_title("Replace Checklist")
            .with_context_package(mock_context_package)
            .with_execution_prompt("Test")
            .add_validation_item("Old Check")  # This will be replaced
            .with_validation_checklist(checklist)
            .build()
        )
        
        assert prp.validation_checklist == checklist
        assert "Old Check" not in prp.validation_checklist
    
    def test_with_success_metrics_replace(self, builder, mock_context_package):
        """Test replacing entire success metrics list"""
        metrics = ["New Metric 1", "New Metric 2"]
        
        prp = (
            builder
            .with_id("replace-metrics")
            .with_type(PRPType.FACTORY_ANALYSIS)
            .with_title("Replace Metrics")
            .with_context_package(mock_context_package)
            .with_execution_prompt("Test")
            .add_success_metric("Old Metric")  # This will be replaced
            .with_success_metrics(metrics)
            .build()
        )
        
        assert prp.success_metrics == metrics
        assert "Old Metric" not in prp.success_metrics
    
    def test_complex_output_specification(self, builder, mock_context_package):
        """Test complex output specification"""
        output_spec = {
            "format": "json",
            "structure": {
                "agents": ["type1", "type2"],
                "workflows": {
                    "count": 3,
                    "types": ["deployment", "testing"]
                }
            },
            "validation": {
                "required": True,
                "level": "strict"
            }
        }
        
        prp = (
            builder
            .with_id("complex-output")
            .with_type(PRPType.FACTORY_GENERATION)
            .with_title("Complex Output")
            .with_context_package(mock_context_package)
            .with_execution_prompt("Test")
            .with_output_specification(output_spec)
            .build()
        )
        
        assert prp.output_specification == output_spec
        assert prp.output_specification["structure"]["workflows"]["count"] == 3
        assert prp.output_specification["validation"]["level"] == "strict"
    
    def test_custom_created_at(self, builder, mock_context_package):
        """Test setting custom creation timestamp"""
        custom_time = datetime(2024, 1, 1, 12, 0, 0)
        
        prp = (
            builder
            .with_id("custom-time")
            .with_type(PRPType.FACTORY_ANALYSIS)
            .with_title("Custom Time")
            .with_context_package(mock_context_package)
            .with_execution_prompt("Test")
            .with_created_at(custom_time)
            .build()
        )
        
        assert prp.created_at == custom_time
    
    def test_auto_generated_created_at(self, builder, mock_context_package):
        """Test auto-generated creation timestamp"""
        with patch('subforge.core.prp.builder.datetime') as mock_datetime:
            mock_now = datetime(2024, 3, 15, 10, 30, 0)
            mock_datetime.now.return_value = mock_now
            
            prp = (
                builder
                .with_id("auto-time")
                .with_type(PRPType.FACTORY_ANALYSIS)
                .with_title("Auto Time")
                .with_context_package(mock_context_package)
                .with_execution_prompt("Test")
                .build()
            )
            
            assert prp.created_at == mock_now
    
    def test_builder_with_all_prp_types(self, builder, mock_context_package):
        """Test builder with all PRP types"""
        prp_types = [
            PRPType.FACTORY_ANALYSIS,
            PRPType.FACTORY_GENERATION,
            PRPType.AGENT_SPECIALIZATION,
            PRPType.WORKFLOW_OPTIMIZATION,
            PRPType.VALIDATION_COMPREHENSIVE
        ]
        
        for prp_type in prp_types:
            prp = (
                builder
                .with_id(f"test-{prp_type.value}")
                .with_type(prp_type)
                .with_title(f"Test {prp_type.value}")
                .with_context_package(mock_context_package)
                .with_execution_prompt(f"Prompt for {prp_type.value}")
                .build()
            )
            
            assert prp.type == prp_type
            assert prp_type.value in prp.id
    
    def test_builder_empty_collections(self, builder, mock_context_package):
        """Test that empty collections are handled correctly"""
        prp = (
            builder
            .with_id("empty-collections")
            .with_type(PRPType.FACTORY_ANALYSIS)
            .with_title("Empty Collections")
            .with_context_package(mock_context_package)
            .with_execution_prompt("Test")
            .with_validation_checklist([])
            .with_success_metrics([])
            .with_output_specification({})
            .build()
        )
        
        assert prp.validation_checklist == []
        assert prp.success_metrics == []
        assert prp.output_specification == {}
    
    def test_builder_none_values(self, builder, mock_context_package):
        """Test handling of None values"""
        # None values should be rejected for required fields
        with pytest.raises(ValueError):
            builder.with_id(None).build()
        
        with pytest.raises(ValueError):
            builder.with_id("test").with_type(None).build()
        
        with pytest.raises(ValueError):
            builder.with_id("test").with_type(PRPType.FACTORY_ANALYSIS).with_title(None).build()
    
    def test_builder_special_characters(self, builder, mock_context_package):
        """Test builder with special characters in strings"""
        prp = (
            builder
            .with_id("special-chars-123_ABC")
            .with_type(PRPType.FACTORY_GENERATION)
            .with_title("Special: Title with 'quotes' and \"double quotes\"")
            .with_context_package(mock_context_package)
            .with_execution_prompt("Prompt with\nnewlines\tand\ttabs")
            .add_validation_item("Check with special chars: <>&")
            .add_success_metric("Metric with emoji 🚀")
            .build()
        )
        
        assert "special-chars-123_ABC" == prp.id
        assert "quotes" in prp.title
        assert "\n" in prp.execution_prompt
        assert "\t" in prp.execution_prompt
        assert "<>&" in prp.validation_checklist[0]
        assert "🚀" in prp.success_metrics[0]
    
    def test_builder_long_strings(self, builder, mock_context_package):
        """Test builder with very long strings"""
        long_prompt = "A" * 10000  # 10k character prompt
        long_title = "B" * 500     # 500 character title
        
        prp = (
            builder
            .with_id("long-strings")
            .with_type(PRPType.FACTORY_ANALYSIS)
            .with_title(long_title)
            .with_context_package(mock_context_package)
            .with_execution_prompt(long_prompt)
            .build()
        )
        
        assert len(prp.execution_prompt) == 10000
        assert len(prp.title) == 500
    
    def test_builder_rapid_reuse(self, builder, mock_context_package):
        """Test rapid reuse of builder for multiple PRPs"""
        prps = []
        
        for i in range(10):
            prp = (
                builder
                .with_id(f"rapid-{i}")
                .with_type(PRPType.FACTORY_GENERATION)
                .with_title(f"Rapid PRP {i}")
                .with_context_package(mock_context_package)
                .with_execution_prompt(f"Prompt {i}")
                .add_validation_item(f"Check {i}")
                .add_success_metric(f"Metric {i}")
                .build()
            )
            prps.append(prp)
        
        # All PRPs should be unique
        assert len(prps) == 10
        assert len(set(prp.id for prp in prps)) == 10
        assert all(f"rapid-{i}" == prps[i].id for i in range(10))
    
    def test_builder_method_order_independence(self, builder, mock_context_package):
        """Test that builder methods can be called in any order"""
        # Build PRP with methods in different order
        prp1 = (
            builder
            .with_execution_prompt("Prompt")
            .with_title("Title")
            .with_context_package(mock_context_package)
            .with_id("order-1")
            .with_type(PRPType.FACTORY_ANALYSIS)
            .build()
        )
        
        prp2 = (
            builder
            .with_type(PRPType.FACTORY_ANALYSIS)
            .with_id("order-2")
            .with_execution_prompt("Prompt")
            .with_context_package(mock_context_package)
            .with_title("Title")
            .build()
        )
        
        # Both should work correctly
        assert prp1.id == "order-1"
        assert prp2.id == "order-2"
        assert prp1.title == prp2.title == "Title"
        assert prp1.execution_prompt == prp2.execution_prompt == "Prompt"


class TestPRPBuilderIntegration:
    """Integration tests for PRP Builder with other components"""
    
    def test_builder_with_real_context_package(self):
        """Test builder with real ContextPackage instance"""
        from subforge.core.context_engineer import ContextPackage
        
        # Create real context package with required arguments
        context = ContextPackage(
            project_context={"name": "RealProject", "type": "backend"},
            technical_context={"language": "python", "framework": "fastapi"},
            examples=["Real example 1", "Real example 2"],
            patterns=["Pattern A", "Pattern B"],
            validation_gates=["Gate 1", "Gate 2"],
            references=["Ref 1", "Ref 2"],
            success_criteria=["Criteria 1", "Criteria 2"]
        )
        
        builder = PRPBuilder()
        prp = (
            builder
            .with_id("real-context")
            .with_type(PRPType.FACTORY_ANALYSIS)
            .with_title("Real Context Test")
            .with_context_package(context)
            .with_execution_prompt("Test with real context")
            .build()
        )
        
        assert prp.context_package == context
        assert prp.context_package.project_context["name"] == "RealProject"
    
    def test_builder_prp_to_markdown(self):
        """Test that built PRP can be converted to markdown"""
        context = Mock(spec=ContextPackage)
        context.to_markdown = Mock(return_value="# Mocked Context")
        
        builder = PRPBuilder()
        prp = (
            builder
            .with_id("markdown-test")
            .with_type(PRPType.FACTORY_GENERATION)
            .with_title("Markdown Test PRP")
            .with_context_package(context)
            .with_execution_prompt("Generate markdown")
            .add_validation_item("Validate markdown syntax")
            .add_success_metric("Valid markdown produced")
            .with_output_specification({"format": "markdown"})
            .build()
        )
        
        markdown = prp.to_markdown()
        
        assert "# PRP: Markdown Test PRP" in markdown
        assert "markdown-test" in markdown
        assert "factory_generation" in markdown
        assert "Generate markdown" in markdown
        assert "Validate markdown syntax" in markdown
        assert "Valid markdown produced" in markdown
        assert "# Mocked Context" in markdown
    
    def test_builder_with_strategy_pattern(self):
        """Test builder usage within strategy pattern context"""
        from subforge.core.prp.base import BaseStrategy
        
        class TestStrategy(BaseStrategy):
            def generate(self, context):
                builder = PRPBuilder()
                return (
                    builder
                    .with_id(self.generate_prp_id("test"))
                    .with_type(PRPType.FACTORY_ANALYSIS)
                    .with_title("Strategy Generated")
                    .with_context_package(context["context_package"])
                    .with_execution_prompt("Strategy prompt")
                    .build()
                )
            
            def get_required_context_keys(self):
                return ["context_package"]
        
        # Use strategy with builder
        import tempfile
        from pathlib import Path
        
        with tempfile.TemporaryDirectory() as tmpdir:
            strategy = TestStrategy(Path(tmpdir))
            context = {"context_package": Mock(spec=ContextPackage)}
            
            prp = strategy.generate(context)
            
            assert prp.title == "Strategy Generated"
            assert "test_" in prp.id


class TestPRPBuilderEdgeCases:
    """Edge case tests for PRP Builder"""
    
    def test_builder_memory_efficiency(self):
        """Test that builder doesn't leak memory between builds"""
        import sys
        
        builder = PRPBuilder()
        context = Mock(spec=ContextPackage)
        
        # Build first PRP with large data
        large_data = {"data": ["item"] * 1000}
        
        prp1 = (
            builder
            .with_id("memory-1")
            .with_type(PRPType.FACTORY_ANALYSIS)
            .with_title("Memory Test 1")
            .with_context_package(context)
            .with_execution_prompt("Test")
            .with_output_specification(large_data)
            .build()
        )
        
        # Get reference count before second build
        ref_count_before = sys.getrefcount(large_data)
        
        # Build second PRP
        prp2 = (
            builder
            .with_id("memory-2")
            .with_type(PRPType.FACTORY_GENERATION)
            .with_title("Memory Test 2")
            .with_context_package(context)
            .with_execution_prompt("Test")
            .build()
        )
        
        # Reference count should not increase (builder cleared the reference)
        ref_count_after = sys.getrefcount(large_data)
        assert ref_count_after <= ref_count_before + 1  # Allow small variance
        
        # Second PRP should not have the large data
        assert prp2.output_specification == {}
    
    def test_builder_concurrent_usage(self):
        """Test that multiple builders can be used concurrently"""
        import concurrent.futures
        
        def build_prp(builder_id):
            builder = PRPBuilder()
            context = Mock(spec=ContextPackage)
            
            return (
                builder
                .with_id(f"concurrent-{builder_id}")
                .with_type(PRPType.FACTORY_ANALYSIS)
                .with_title(f"Concurrent {builder_id}")
                .with_context_package(context)
                .with_execution_prompt(f"Prompt {builder_id}")
                .build()
            )
        
        # Build PRPs concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(build_prp, i) for i in range(10)]
            prps = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # All PRPs should be unique
        assert len(prps) == 10
        ids = [prp.id for prp in prps]
        assert len(set(ids)) == 10


# Run tests with pytest
if __name__ == "__main__":
    pytest.main([__file__, "-v"])