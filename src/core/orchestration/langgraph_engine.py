"""
Project-S v2 Architecture - LangGraph Workflow Engine
====================================================
Modern LangGraph-based workflow implementation that provides multiple
workflow types: basic, multi-step, and multi-model workflows.

This module migrates and enhances the original LangGraph functionality
with improved modularity, error handling, and integration capabilities.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Union, Literal, Callable
from enum import Enum
from datetime import datetime

from .base_workflow import BaseWorkflowEngine, WorkflowResult, WorkflowStatus, TaskComplexity, State

logger = logging.getLogger(__name__)

# LangGraph availability check
try:
    from langgraph.graph import StateGraph, END
    LANGGRAPH_AVAILABLE = True
    logger.info("LangGraph available - full workflow capabilities enabled")
except ImportError:
    logger.warning("LangGraph not available. Install with: pip install langgraph")
    LANGGRAPH_AVAILABLE = False

class TaskType(str, Enum):
    """Task type enumeration for workflow routing."""
    PLANNING = "tervezés"
    CODING = "kódolás"
    DOCUMENTATION = "dokumentáció"
    DATA_ANALYSIS = "adatelemzés"
    CREATIVE = "kreatív_írás"
    TRANSLATION = "fordítás"
    SUMMARY = "összefoglalás"
    QUICK_RESPONSE = "gyors_válasz"
    UNKNOWN = "ismeretlen"

class LangGraphWorkflowEngine(BaseWorkflowEngine[State]):
    """
    Advanced LangGraph workflow engine supporting multiple workflow patterns.
    
    Features:
    - Basic single-step workflows
    - Multi-step complex workflows 
    - Multi-model orchestration
    - Persistent state management
    - Error recovery and retry logic
    """
    
    def __init__(self, name: str = "langgraph_engine", config: Optional[Dict[str, Any]] = None):
        """
        Initialize the LangGraph workflow engine.
        
        Args:
            name: Engine identifier
            config: Configuration dictionary
        """
        super().__init__(name, config)
        
        # Workflow graphs
        self.basic_graph: Optional[Any] = None
        self.multi_step_graph: Optional[Any] = None
        self.multi_model_graph: Optional[Any] = None
        
        # External dependencies (will be injected)
        self.model_manager: Optional[Any] = None
        self.state_manager: Optional[Any] = None
        
        if LANGGRAPH_AVAILABLE:
            self._setup_workflows()
            logger.info(f"LangGraph workflow engine '{name}' initialized successfully")
        else:
            logger.warning(f"LangGraph workflow engine '{name}' initialized with limited functionality")
    
    def set_dependencies(self, model_manager: Any, state_manager: Any) -> None:
        """
        Inject external dependencies.
        
        Args:
            model_manager: Model management service
            state_manager: State management service
        """
        self.model_manager = model_manager
        self.state_manager = state_manager
        logger.info("Dependencies injected into LangGraph workflow engine")
    
    def _setup_workflows(self) -> None:
        """Set up all workflow graphs."""
        if not LANGGRAPH_AVAILABLE:
            return
            
        try:
            self._setup_basic_workflow()
            self._setup_multi_step_workflow()
            self._setup_multi_model_workflow()
            logger.info("All LangGraph workflows set up successfully")
        except Exception as e:
            logger.error(f"Error setting up workflows: {e}")
            raise
    
    def _setup_basic_workflow(self) -> None:
        """Set up basic single-step workflow graph."""
        if not LANGGRAPH_AVAILABLE:
            return
            
        builder = StateGraph(State)
        
        # Node definitions
        def parse_input(state: State) -> State:
            """Parse and analyze input."""
            input_text = state.get("input", "")
            task_type = self._determine_task_type(input_text)
            
            return {
                **state,
                "parsed_input": {
                    "original": input_text,
                    "tokens": input_text.split(),
                    "detected_type": task_type,
                    "complexity": self.get_complexity(input_text).value
                }
            }
        
        def select_model(state: State) -> State:
            """Select appropriate model for the task."""
            task_type = state.get("parsed_input", {}).get("detected_type", TaskType.QUICK_RESPONSE)
            suggested_model = self._suggest_model_for_task(task_type)
            
            return {
                **state,
                "model_selection": {
                    "suggested_model": suggested_model,
                    "task_type": task_type,
                    "ready_for_execution": True
                }
            }
        
        def prepare_response(state: State) -> State:
            """Prepare response structure."""
            return {
                **state,
                "prepared_response": {
                    "input": state.get("input", ""),
                    "selected_model": state.get("model_selection", {}).get("suggested_model", "gpt-3.5-turbo"),
                    "task_type": state.get("model_selection", {}).get("task_type", TaskType.QUICK_RESPONSE),
                    "ready": True,
                    "timestamp": datetime.now().isoformat()
                }
            }
        
        # Add nodes
        builder.add_node("parse_input", parse_input)
        builder.add_node("select_model", select_model)
        builder.add_node("prepare_response", prepare_response)
        
        # Add edges
        builder.add_edge("parse_input", "select_model")
        builder.add_edge("select_model", "prepare_response")
        builder.add_edge("prepare_response", END)
        
        # Set entry point
        builder.set_entry_point("parse_input")
        
        try:
            # Compile graph
            self.basic_graph = builder.compile()
            logger.debug("Basic workflow graph compiled successfully")
        except Exception as e:
            logger.error(f"Failed to compile basic workflow graph: {e}")
            # Create a simple fallback that just passes through the input
            self.basic_graph = None
    
    def _setup_multi_step_workflow(self) -> None:
        """Set up multi-step workflow for complex tasks."""
        if not LANGGRAPH_AVAILABLE:
            return
            
        builder = StateGraph(State)
        
        # Node definitions
        def analyze_task(state: State) -> State:
            """Analyze task complexity and break down into subtasks."""
            input_text = state.get("input", "")
            complexity = self.get_complexity(input_text)
            
            subtasks = []
            if complexity == TaskComplexity.COMPLEX:
                subtasks = ["planning", "execution", "verification"]
            elif complexity == TaskComplexity.MEDIUM:
                subtasks = ["analysis", "execution"]
            else:
                subtasks = ["simple_execution"]
            
            return {
                **state,
                "task_analysis": {
                    "complexity": complexity.value,
                    "subtasks": subtasks,
                    "current_step": 0,
                    "total_steps": len(subtasks)
                }
            }
        
        def route_task(state: State) -> str:
            """Route task based on complexity."""
            complexity = state.get("task_analysis", {}).get("complexity", "simple")
            
            route_map = {
                "complex": "complex_workflow",
                "medium": "medium_workflow",
                "simple": "simple_workflow"
            }
            
            return route_map.get(complexity, "simple_workflow")
        
        def simple_workflow(state: State) -> State:
            """Handle simple single-step tasks."""
            return {
                **state,
                "workflow_result": {
                    "type": "simple",
                    "status": "completed",
                    "ready": True
                }
            }
        
        def medium_workflow_step1(state: State) -> State:
            """Medium complexity - step 1."""
            return {
                **state,
                "workflow_result": {
                    "type": "medium",
                    "step": 1,
                    "status": "in_progress"
                }
            }
        
        def medium_workflow_step2(state: State) -> State:
            """Medium complexity - step 2."""
            return {
                **state,
                "workflow_result": {
                    "type": "medium",
                    "step": 2,
                    "status": "completed",
                    "ready": True
                }
            }
        
        def complex_workflow_step1(state: State) -> State:
            """Complex workflow - planning step."""
            return {
                **state,
                "workflow_result": {
                    "type": "complex",
                    "step": 1,
                    "phase": "planning",
                    "status": "in_progress"
                }
            }
        
        def complex_workflow_step2(state: State) -> State:
            """Complex workflow - execution step."""
            return {
                **state,
                "workflow_result": {
                    "type": "complex",
                    "step": 2,
                    "phase": "execution",
                    "status": "in_progress"
                }
            }
        
        def complex_workflow_step3(state: State) -> State:
            """Complex workflow - verification step."""
            return {
                **state,
                "workflow_result": {
                    "type": "complex",
                    "step": 3,
                    "phase": "verification",
                    "status": "completed",
                    "ready": True
                }
            }
        
        def finalize_result(state: State) -> State:
            """Finalize workflow result."""
            workflow_type = state.get("workflow_result", {}).get("type", "simple")
            
            return {
                **state,
                "final_result": {
                    "workflow_type": workflow_type,
                    "completed_at": datetime.now().isoformat(),
                    "status": "completed"
                }
            }
        
        # Add nodes
        builder.add_node("analyze_task", analyze_task)
        builder.add_node("simple_workflow", simple_workflow)
        builder.add_node("medium_workflow_step1", medium_workflow_step1)
        builder.add_node("medium_workflow_step2", medium_workflow_step2)
        builder.add_node("complex_workflow_step1", complex_workflow_step1)
        builder.add_node("complex_workflow_step2", complex_workflow_step2)
        builder.add_node("complex_workflow_step3", complex_workflow_step3)
        builder.add_node("finalize_result", finalize_result)
        
        # Add conditional routing
        builder.add_conditional_edges(
            "analyze_task",
            route_task,
            {
                "simple_workflow": "simple_workflow",
                "medium_workflow": "medium_workflow_step1",
                "complex_workflow": "complex_workflow_step1"
            }
        )
        
        # Add sequential edges
        builder.add_edge("simple_workflow", "finalize_result")
        builder.add_edge("medium_workflow_step1", "medium_workflow_step2")
        builder.add_edge("medium_workflow_step2", "finalize_result")
        builder.add_edge("complex_workflow_step1", "complex_workflow_step2")
        builder.add_edge("complex_workflow_step2", "complex_workflow_step3")
        builder.add_edge("complex_workflow_step3", "finalize_result")
        builder.add_edge("finalize_result", END)
        
        # Set entry point
        builder.set_entry_point("analyze_task")
        
        # Compile graph
        self.multi_step_graph = builder.compile()
        logger.debug("Multi-step workflow graph compiled successfully")
    
    def _setup_multi_model_workflow(self) -> None:
        """Set up multi-model workflow for advanced orchestration."""
        if not LANGGRAPH_AVAILABLE:
            return
            
        builder = StateGraph(State)
        
        # Node definitions
        def analyze_request(state: State) -> State:
            """Analyze request and select models for each phase."""
            input_text = state.get("input", "")
            
            # Default model selection
            models = {
                "planning_model": "gpt-4",
                "execution_model": "claude-3-sonnet", 
                "verification_model": "gpt-3.5-turbo",
                "current_phase": "planning"
            }
            
            # Custom model selection based on input
            if "gpt-4" in input_text.lower():
                models["planning_model"] = "gpt-4"
            if "claude" in input_text.lower():
                models["execution_model"] = "claude-3-opus" if "opus" in input_text.lower() else "claude-3-sonnet"
            if "local" in input_text.lower() or "ollama" in input_text.lower():
                models["verification_model"] = "llama3"
            
            return {
                **state,
                "multi_model": models
            }
        
        def route_phase(state: State) -> str:
            """Route to appropriate phase based on current state."""
            current_phase = state.get("multi_model", {}).get("current_phase", "planning")
            
            phase_map = {
                "planning": "planning_phase",
                "execution": "execution_phase", 
                "verification": "verification_phase",
                "finalization": "finalization"
            }
            
            return phase_map.get(current_phase, "finalization")
        
        def planning_phase(state: State) -> State:
            """Planning phase preparation."""
            return {
                **state,
                "planning_result": {
                    "model": state.get("multi_model", {}).get("planning_model", "gpt-4"),
                    "status": "prepared",
                    "phase": "planning"
                },
                "multi_model": {
                    **state.get("multi_model", {}),
                    "current_phase": "execution"
                }
            }
        
        def execution_phase(state: State) -> State:
            """Execution phase preparation."""
            return {
                **state,
                "execution_result": {
                    "model": state.get("multi_model", {}).get("execution_model", "claude-3-sonnet"),
                    "status": "prepared",
                    "phase": "execution",
                    "planning_input": state.get("planning_result", {})
                },
                "multi_model": {
                    **state.get("multi_model", {}),
                    "current_phase": "verification"
                }
            }
        
        def verification_phase(state: State) -> State:
            """Verification phase preparation."""
            return {
                **state,
                "verification_result": {
                    "model": state.get("multi_model", {}).get("verification_model", "gpt-3.5-turbo"),
                    "status": "prepared",
                    "phase": "verification",
                    "execution_input": state.get("execution_result", {})
                },
                "multi_model": {
                    **state.get("multi_model", {}),
                    "current_phase": "finalization"
                }
            }
        
        def finalization(state: State) -> State:
            """Finalize multi-model workflow results."""
            return {
                **state,
                "final_multi_model_result": {
                    "planning": state.get("planning_result", {}),
                    "execution": state.get("execution_result", {}),
                    "verification": state.get("verification_result", {}),
                    "status": "complete",
                    "completed_at": datetime.now().isoformat()
                }
            }
        
        # Add nodes
        builder.add_node("analyze_request", analyze_request)
        builder.add_node("planning_phase", planning_phase)
        builder.add_node("execution_phase", execution_phase)
        builder.add_node("verification_phase", verification_phase)
        builder.add_node("finalization", finalization)
        
        # Add conditional routing for all phases
        for phase_node in ["analyze_request", "planning_phase", "execution_phase", "verification_phase"]:
            builder.add_conditional_edges(
                phase_node,
                route_phase,
                {
                    "planning_phase": "planning_phase",
                    "execution_phase": "execution_phase",
                    "verification_phase": "verification_phase",
                    "finalization": "finalization"
                }
            )
        
        builder.add_edge("finalization", END)
        
        # Set entry point
        builder.set_entry_point("analyze_request")
        
        # Compile graph
        self.multi_model_graph = builder.compile()
        logger.debug("Multi-model workflow graph compiled successfully")
    
    def analyze_task(self, input_data: State) -> Dict[str, Any]:
        """
        Analyze input task to determine optimal execution strategy.
        
        Args:
            input_data: Input state to analyze
            
        Returns:
            Dict containing analysis results
        """
        input_text = input_data.get("input", "")
        task_type = self._determine_task_type(input_text)
        complexity = self.get_complexity(input_text)
        
        return {
            "task_type": task_type,
            "complexity": complexity,
            "word_count": len(input_text.split()),
            "suggested_workflow": self._suggest_workflow_type(complexity),
            "estimated_duration": self._estimate_duration(complexity),
            "requires_multi_model": self._requires_multi_model(input_text)
        }
    
    async def execute(self, input_data: State, workflow_type: str = "auto", **kwargs) -> WorkflowResult:
        """
        Execute workflow with the given input data.
        
        Args:
            input_data: Input state for execution
            workflow_type: Type of workflow to use ("basic", "multi_step", "multi_model", "auto")
            **kwargs: Additional execution parameters
            
        Returns:
            WorkflowResult: Execution result
        """
        if not LANGGRAPH_AVAILABLE:
            return WorkflowResult(
                status=WorkflowStatus.FAILED,
                data={},
                metadata={"error": "LangGraph not available"},
                execution_time=0.0,
                error="LangGraph not available"
            )
        
        start_time = datetime.now()
        self.start_execution()
        
        try:
            # Auto-select workflow type if needed
            if workflow_type == "auto":
                analysis = self.analyze_task(input_data)
                workflow_type = analysis["suggested_workflow"]
            
            # Execute appropriate workflow
            if workflow_type == "basic":
                result = await self._execute_basic_workflow(input_data, **kwargs)
            elif workflow_type == "multi_step":
                result = await self._execute_multi_step_workflow(input_data, **kwargs)
            elif workflow_type == "multi_model":
                result = await self._execute_multi_model_workflow(input_data, **kwargs)
            else:
                raise ValueError(f"Unknown workflow type: {workflow_type}")
            
            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Create result
            workflow_result = WorkflowResult(
                status=WorkflowStatus.COMPLETED,
                data=result,
                metadata={
                    "workflow_type": workflow_type,
                    "engine_name": self.name,
                    "langgraph_available": LANGGRAPH_AVAILABLE
                },
                execution_time=execution_time
            )
            
            self.complete_execution(workflow_result)
            return workflow_result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            error_msg = str(e)
            
            logger.error(f"Workflow execution failed: {error_msg}")
            
            workflow_result = WorkflowResult(
                status=WorkflowStatus.FAILED,
                data={},
                metadata={"workflow_type": workflow_type, "engine_name": self.name},
                execution_time=execution_time,
                error=error_msg
            )
            
            self.complete_execution(workflow_result)
            return workflow_result
    
    async def _execute_basic_workflow(self, input_data: State, **kwargs) -> Dict[str, Any]:
        """Execute basic workflow."""
        if not self.basic_graph:
            # Fallback execution when graph is not available
            logger.warning("Basic graph not available, using fallback execution")
            return self._fallback_basic_execution(input_data)
        
        try:
            # Run the graph
            result = self.basic_graph.invoke(input_data)
            
            # Execute with model manager if available
            if self.model_manager and result.get("prepared_response", {}).get("ready"):
                task_type = result["prepared_response"]["task_type"]
                selected_model = result["prepared_response"]["selected_model"]
                
                ai_result = await self.model_manager.execute_task_with_model(
                    query=input_data.get("input", ""),
                    system_message="Process the user request with the selected model.",
                    model=selected_model,
                    task_type=task_type
                )
                
                result["ai_result"] = ai_result
            
            return result
            
        except Exception as e:
            logger.warning(f"Graph execution failed, using fallback: {e}")
            return self._fallback_basic_execution(input_data)
    
    def _fallback_basic_execution(self, input_data: State) -> Dict[str, Any]:
        """Fallback execution when LangGraph fails."""
        input_text = input_data.get("input", "")
        task_type = self._determine_task_type(input_text)
        complexity = self.get_complexity(input_text)
        suggested_model = self._suggest_model_for_task(task_type)
        
        return {
            **input_data,
            "parsed_input": {
                "original": input_text,
                "tokens": input_text.split(),
                "detected_type": task_type,
                "complexity": complexity.value
            },
            "model_selection": {
                "suggested_model": suggested_model,
                "task_type": task_type,
                "ready_for_execution": True
            },
            "prepared_response": {
                "input": input_text,
                "selected_model": suggested_model,
                "task_type": task_type,
                "ready": True,
                "timestamp": datetime.now().isoformat(),
                "execution_mode": "fallback"
            }
        }
    
    async def _execute_multi_step_workflow(self, input_data: State, **kwargs) -> Dict[str, Any]:
        """Execute multi-step workflow."""
        if not self.multi_step_graph:
            logger.warning("Multi-step graph not available, using fallback execution")
            return self._fallback_multi_step_execution(input_data)
        
        try:
            # Run the graph
            result = self.multi_step_graph.invoke(input_data)
            
            # Execute with model manager for simple workflows
            if (self.model_manager and 
                result.get("workflow_result", {}).get("type") == "simple" and
                result.get("workflow_result", {}).get("ready")):
                
                ai_result = await self.model_manager.execute_task_with_tools(
                    query=input_data.get("input", ""),
                    system_message="Execute simple task with appropriate tools."
                )
                
                result["ai_result"] = ai_result
            
            return result
            
        except Exception as e:
            logger.warning(f"Multi-step graph execution failed, using fallback: {e}")
            return self._fallback_multi_step_execution(input_data)
    
    def _fallback_multi_step_execution(self, input_data: State) -> Dict[str, Any]:
        """Fallback execution for multi-step workflow."""
        input_text = input_data.get("input", "")
        complexity = self.get_complexity(input_text)
        
        subtasks = []
        if complexity == TaskComplexity.COMPLEX:
            subtasks = ["planning", "execution", "verification"]
            workflow_type = "complex"
        elif complexity == TaskComplexity.MEDIUM:
            subtasks = ["analysis", "execution"]
            workflow_type = "medium"
        else:
            subtasks = ["simple_execution"]
            workflow_type = "simple"
        
        return {
            **input_data,
            "task_analysis": {
                "complexity": complexity.value,
                "subtasks": subtasks,
                "current_step": 0,
                "total_steps": len(subtasks)
            },
            "workflow_result": {
                "type": workflow_type,
                "status": "completed",
                "ready": True,
                "execution_mode": "fallback"
            },
            "final_result": {
                "workflow_type": workflow_type,
                "completed_at": datetime.now().isoformat(),
                "status": "completed"
            }
        }
    
    async def _execute_multi_model_workflow(self, input_data: State, **kwargs) -> Dict[str, Any]:
        """Execute multi-model workflow."""
        if not self.multi_model_graph:
            logger.warning("Multi-model graph not available, using fallback execution")
            return self._fallback_multi_model_execution(input_data)
        
        try:
            # Run the graph
            result = self.multi_model_graph.invoke(input_data)
            
            # Execute each phase with model manager if available
            if self.model_manager:
                command = input_data.get("input", "")
                
                # Planning phase
                planning_model = result.get("planning_result", {}).get("model", "gpt-4")
                planning_result = await self.model_manager.execute_task_with_tools(
                    query=f"Planning phase for task: {command}",
                    system_message="You are in the planning phase. Create a detailed plan for task execution.",
                    model=planning_model,
                    task_type="tervezés"
                )
                
                # Execution phase
                execution_model = result.get("execution_result", {}).get("model", "claude-3-sonnet")
                planning_content = planning_result.get("content", "")
                execution_result = await self.model_manager.execute_task_with_tools(
                    query=f"Execution phase. Plan: {planning_content}. Task: {command}",
                    system_message="You are in the execution phase. Execute the plan using appropriate tools.",
                    model=execution_model,
                    task_type="kódolás"
                )
                
                # Verification phase
                verification_model = result.get("verification_result", {}).get("model", "gpt-3.5-turbo")
                execution_content = execution_result.get("content", "")
                verification_result = await self.model_manager.execute_task_with_tools(
                    query=f"Verification phase. Execution result: {execution_content}. Original task: {command}",
                    system_message="You are in the verification phase. Verify the execution results using tools.",
                    model=verification_model,
                    task_type="összefoglalás"
                )
                
                # Add AI results to the workflow result
                result.update({
                    "planning_ai_result": planning_result,
                    "execution_ai_result": execution_result,
                    "verification_ai_result": verification_result,
                    "combined_result": {
                        "planning": planning_result.get("content", ""),
                        "execution": execution_result.get("content", ""),
                        "verification": verification_result.get("content", ""),
                        "models_used": {
                            "planning": planning_model,
                            "execution": execution_model,
                            "verification": verification_model
                        }
                    }
                })
            
            return result
            
        except Exception as e:
            logger.warning(f"Multi-model graph execution failed, using fallback: {e}")
            return self._fallback_multi_model_execution(input_data)
    
    def _fallback_multi_model_execution(self, input_data: State) -> Dict[str, Any]:
        """Fallback execution for multi-model workflow."""
        input_text = input_data.get("input", "")
        
        # Default model selection
        models = {
            "planning_model": "gpt-4",
            "execution_model": "claude-3-sonnet", 
            "verification_model": "gpt-3.5-turbo",
            "current_phase": "finalization"
        }
        
        # Custom model selection based on input
        if "gpt-4" in input_text.lower():
            models["planning_model"] = "gpt-4"
        if "claude" in input_text.lower():
            models["execution_model"] = "claude-3-opus" if "opus" in input_text.lower() else "claude-3-sonnet"
        if "local" in input_text.lower() or "ollama" in input_text.lower():
            models["verification_model"] = "llama3"
        
        return {
            **input_data,
            "multi_model": models,
            "planning_result": {
                "model": models["planning_model"],
                "status": "prepared",
                "phase": "planning"
            },
            "execution_result": {
                "model": models["execution_model"],
                "status": "prepared",
                "phase": "execution"
            },
            "verification_result": {
                "model": models["verification_model"],
                "status": "prepared",
                "phase": "verification"
            },
            "final_multi_model_result": {
                "planning": {"model": models["planning_model"], "status": "prepared"},
                "execution": {"model": models["execution_model"], "status": "prepared"},
                "verification": {"model": models["verification_model"], "status": "prepared"},
                "status": "complete",
                "completed_at": datetime.now().isoformat(),
                "execution_mode": "fallback"
            }
        }
    
    def _determine_task_type(self, input_text: str) -> TaskType:
        """Determine task type from input text."""
        input_lower = input_text.lower()
        
        # Simple keyword-based task type detection
        if any(word in input_lower for word in ["kód", "program", "script", "függvény"]):
            return TaskType.CODING
        elif any(word in input_lower for word in ["dokumentum", "leírás", "dokumentáció"]):
            return TaskType.DOCUMENTATION
        elif any(word in input_lower for word in ["adat", "elemzés", "statisztika"]):
            return TaskType.DATA_ANALYSIS
        elif any(word in input_lower for word in ["fordítás", "translate"]):
            return TaskType.TRANSLATION
        elif any(word in input_lower for word in ["összefoglalás", "summarize"]):
            return TaskType.SUMMARY
        elif any(word in input_lower for word in ["terv", "tervezés", "plan"]):
            return TaskType.PLANNING
        elif any(word in input_lower for word in ["kreatív", "írás", "story"]):
            return TaskType.CREATIVE
        else:
            return TaskType.QUICK_RESPONSE
    
    def _suggest_model_for_task(self, task_type: TaskType) -> str:
        """Suggest best model for task type."""
        model_mapping = {
            TaskType.CODING: "claude-3-sonnet",
            TaskType.DOCUMENTATION: "gpt-4",
            TaskType.DATA_ANALYSIS: "gpt-4",
            TaskType.TRANSLATION: "gpt-3.5-turbo",
            TaskType.SUMMARY: "gpt-3.5-turbo",
            TaskType.PLANNING: "gpt-4",
            TaskType.CREATIVE: "claude-3-opus",
            TaskType.QUICK_RESPONSE: "gpt-3.5-turbo"
        }
        
        return model_mapping.get(task_type, "gpt-3.5-turbo")
    
    def _suggest_workflow_type(self, complexity: TaskComplexity) -> str:
        """Suggest workflow type based on complexity."""
        if complexity == TaskComplexity.COMPLEX:
            return "multi_model"
        elif complexity == TaskComplexity.MEDIUM:
            return "multi_step"
        else:
            return "basic"
    
    def _estimate_duration(self, complexity: TaskComplexity) -> str:
        """Estimate execution duration."""
        duration_map = {
            TaskComplexity.SIMPLE: "5-15 seconds",
            TaskComplexity.MEDIUM: "30-60 seconds", 
            TaskComplexity.COMPLEX: "1-3 minutes"
        }
        
        return duration_map.get(complexity, "Unknown")
    
    def _requires_multi_model(self, input_text: str) -> bool:
        """Determine if task requires multiple models."""
        multi_model_indicators = [
            "használj", "modell", "először", "majd", "azután",
            "tervezés", "végrehajtás", "ellenőrzés"
        ]
        
        return any(indicator in input_text.lower() for indicator in multi_model_indicators)
