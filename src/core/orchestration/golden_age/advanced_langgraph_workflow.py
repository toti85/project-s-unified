"""
Project-S V2 - Advanced LangGraph Workflow System
-----------------------------------------------
MIGRATED FROM GOLDEN AGE VERSION (690 lines)
This module implements the Project-S LangGraph integration 
for multi-model operations and complex task processing.

Migration Date: June 29, 2025
Source: C:\project_s_agent\integrations\advanced_langgraph_workflow.py
Target: v2_architecture/core/orchestration/golden_age/advanced_langgraph_workflow.py
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Union, Literal
from enum import Enum
from datetime import datetime

# V2 Architecture imports - updated for new structure
try:
    from ...integrations.ai_models.model_manager import model_manager
    from ...core.state.persistent_state_manager import persistent_state_manager
except ImportError:
    # Fallback imports for development/testing
    try:
        from integrations.simplified_model_manager import model_manager
        from integrations.persistent_state_manager import persistent_state_manager
    except ImportError:
        model_manager = None
        persistent_state_manager = None
        logging.warning("Model manager and persistent state manager not available - running in limited mode")

logger = logging.getLogger(__name__)

try:
    from langgraph.graph import StateGraph, END
    LANGGRAPH_AVAILABLE = True
except ImportError:
    logger.warning("LangGraph nem elérhető. Telepítsd: pip install langgraph")
    LANGGRAPH_AVAILABLE = False

# State type
State = Dict[str, Any]

# Task types
class TaskType(str, Enum):
    PLANNING = "tervezés"
    CODING = "kódolás"
    DOCUMENTATION = "dokumentáció"
    DATA_ANALYSIS = "adatelemzés"
    CREATIVE = "kreatív_írás"
    TRANSLATION = "fordítás"
    SUMMARY = "összefoglalás"
    QUICK_RESPONSE = "gyors_válasz"
    UNKNOWN = "ismeretlen"

class AdvancedLangGraphWorkflow:
    """
    Advanced LangGraph workflow manager for multi-model and 
    multi-step task execution.
    
    *** GOLDEN AGE COMPONENT ***
    This is a migrated component from the Golden Age version 
    containing sophisticated workflow processing capabilities.
    """
    
    def __init__(self):
        """Initialize the advanced LangGraph workflow manager."""
        self.graph = None
        self.multi_step_graph = None
        self.multi_model_graph = None
        
        # Access to persistent state manager
        self.state_manager = persistent_state_manager
        
        if LANGGRAPH_AVAILABLE:
            self._setup_basic_graph()
            self._setup_multi_step_graph()
            self._setup_multi_model_graph()
            logger.info("✅ Advanced LangGraph workflow initialized (GOLDEN AGE COMPONENT)")
        else:
            logger.warning("❌ LangGraph not available, workflow initialization failed")
    
    def _setup_basic_graph(self):
        """Set up the basic state graph for simple tasks."""
        # State graph creation
        builder = StateGraph(State)
        
        # Node definitions
        def parse_input(state: State) -> State:
            """Parse input and identify task."""
            input_text = state.get("input", "")
            
            # Use model manager if available
            detected_type = "gyors_válasz"  # default
            if model_manager:
                try:
                    detected_type = model_manager.determine_task_type(input_text)
                except:
                    detected_type = "gyors_válasz"
            
            return {
                **state, 
                "parsed_input": {
                    "original": input_text,
                    "tokens": input_text.split(),
                    "detected_type": detected_type
                }
            }
            
        def process_with_model(state: State) -> State:
            """Select appropriate model and process task."""
            input_text = state.get("input", "")
            detected_type = state.get("parsed_input", {}).get("detected_type", "gyors_válasz")
            
            # Prepare model selection - async execution happens later
            suggested_model = "gpt-3.5-turbo"  # default
            if model_manager and hasattr(model_manager, 'ai_client'):
                try:
                    suggested_model = model_manager.ai_client.suggest_model_for_task(detected_type)
                except:
                    suggested_model = "gpt-3.5-turbo"
            
            return {
                **state, 
                "model_selection": {
                    "suggested_model": suggested_model,
                    "task_type": detected_type,
                    "ready_for_execution": True
                }
            }
            
        def prepare_response(state: State) -> State:
            """Prepare response and formatting."""
            input_text = state.get("input", "")
            model_data = state.get("model_selection", {})
            
            return {
                **state,
                "prepared_response": {
                    "input": input_text,
                    "selected_model": model_data.get("suggested_model", "gpt-3.5-turbo"),
                    "task_type": model_data.get("task_type", "gyors_válasz"),
                    "ready": True
                }
            }
        
        # Add nodes
        builder.add_node("parse_input", parse_input)
        builder.add_node("process_with_model", process_with_model)
        builder.add_node("prepare_response", prepare_response)
        
        # Add edges
        builder.add_edge("parse_input", "process_with_model")
        builder.add_edge("process_with_model", "prepare_response")
        builder.add_edge("prepare_response", END)
        
        # Set entry point
        builder.set_entry_point("parse_input")
        
        # Compile graph
        self.graph = builder.compile()
        logger.debug("✅ Basic LangGraph workflow created")
    
    def _setup_multi_step_graph(self):
        """Set up complex, multi-step workflow for complex tasks."""
        # State graph creation
        builder = StateGraph(State)
        
        # Node definitions
        def analyze_task(state: State) -> State:
            """Analyze and decompose the task."""
            input_text = state.get("input", "")
            
            # Identify task complexity and type
            task_complexity = "simple"  # Simple default
            subtasks = []
            
            # Simple heuristics for complexity estimation
            if len(input_text.split()) > 50:
                task_complexity = "complex"
                subtasks = ["planning", "execution", "verification"]
            elif "," in input_text or "és " in input_text or "majd " in input_text:
                # If there are comma-separated parts or "and"/"then" words, assume complexity
                task_complexity = "medium"
                subtasks = ["analysis", "execution"]
                
            return {
                **state, 
                "task_analysis": {
                    "complexity": task_complexity,
                    "subtasks": subtasks,
                    "current_step": 0
                }
            }
        
        def route_task(state: State) -> str:
            """Router function based on task complexity."""
            complexity = state.get("task_analysis", {}).get("complexity", "simple")
            
            if complexity == "complex":
                return "complex_workflow"
            elif complexity == "medium":
                return "medium_workflow"
            else:
                return "simple_workflow"
            
        def simple_workflow(state: State) -> State:
            """Execute simple task in one step."""
            return {**state, "workflow": "simple", "ready": True}
            
        def medium_workflow_step1(state: State) -> State:
            """Medium complexity task - first step."""
            return {**state, "workflow": "medium", "step": 1}
            
        def medium_workflow_step2(state: State) -> State:
            """Medium complexity task - second step."""
            return {**state, "workflow": "medium", "step": 2, "ready": True}
            
        def complex_workflow_step1(state: State) -> State:
            """Complex task - first step (planning)."""
            return {**state, "workflow": "complex", "step": 1}
            
        def complex_workflow_step2(state: State) -> State:
            """Complex task - second step (execution)."""
            return {**state, "workflow": "complex", "step": 2}
            
        def complex_workflow_step3(state: State) -> State:
            """Complex task - third step (verification)."""
            return {**state, "workflow": "complex", "step": 3, "ready": True}
            
        def prepare_final_response(state: State) -> State:
            """Prepare final response."""
            workflow = state.get("workflow", "simple")
            
            response_template = {
                "simple": "Egyszerű feladat végrehajtva.",
                "medium": "Közepes bonyolultságú feladat végrehajtva 2 lépésben.",
                "complex": "Komplex feladat végrehajtva 3 lépésben."
            }
            
            return {**state, "final_response": response_template.get(workflow, "Feladat végrehajtva."), "complete": True}
        
        # Add nodes
        builder.add_node("analyze_task", analyze_task)
        builder.add_node("simple_workflow", simple_workflow)
        builder.add_node("medium_workflow_step1", medium_workflow_step1)
        builder.add_node("medium_workflow_step2", medium_workflow_step2)
        builder.add_node("complex_workflow_step1", complex_workflow_step1)
        builder.add_node("complex_workflow_step2", complex_workflow_step2)
        builder.add_node("complex_workflow_step3", complex_workflow_step3)
        builder.add_node("prepare_final_response", prepare_final_response)
        
        # Add conditional router node
        builder.add_conditional_edges(
            "analyze_task",
            route_task,
            {
                "simple_workflow": "simple_workflow",
                "medium_workflow": "medium_workflow_step1",
                "complex_workflow": "complex_workflow_step1"
            }
        )
        
        # Additional edges
        builder.add_edge("simple_workflow", "prepare_final_response")
        builder.add_edge("medium_workflow_step1", "medium_workflow_step2")
        builder.add_edge("medium_workflow_step2", "prepare_final_response")
        builder.add_edge("complex_workflow_step1", "complex_workflow_step2")
        builder.add_edge("complex_workflow_step2", "complex_workflow_step3")
        builder.add_edge("complex_workflow_step3", "prepare_final_response")
        builder.add_edge("prepare_final_response", END)
        
        # Set entry point
        builder.set_entry_point("analyze_task")
        
        # Compile graph
        self.multi_step_graph = builder.compile()
        logger.debug("✅ Multi-step LangGraph workflow created")
    
    def _setup_multi_model_graph(self):
        """Set up multi-model workflow capable of using different AI models for different parts of the task."""
        # State graph creation
        builder = StateGraph(State)
        
        # Node definitions
        def analyze_request(state: State) -> State:
            """Analyze request and identify required models."""
            input_text = state.get("input", "")
            
            # Default model initialization
            planning_model = "gpt-4"  # For planning phase
            execution_model = "claude-3-sonnet"  # For execution
            verification_model = "gpt-3.5-turbo"  # For verification
            
            # Simple model identification based on input text
            if "használj" in input_text.lower() and "modell" in input_text.lower():
                # If explicit model specification in text
                if "gpt-4" in input_text.lower():
                    planning_model = "gpt-4"
                if "claude" in input_text.lower():
                    execution_model = "claude-3-opus" if "opus" in input_text.lower() else "claude-3-sonnet"
                if "helyi" in input_text.lower() or "ollama" in input_text.lower():
                    verification_model = "llama3"
            
            return {
                **state, 
                "multi_model": {
                    "planning_model": planning_model,
                    "execution_model": execution_model,
                    "verification_model": verification_model,
                    "current_phase": "planning"
                }
            }
            
        def route_phase(state: State) -> str:
            """Router based on current phase."""
            current_phase = state.get("multi_model", {}).get("current_phase", "planning")
            
            if current_phase == "planning":
                return "planning_phase"
            elif current_phase == "execution":
                return "execution_phase"
            elif current_phase == "verification":
                return "verification_phase"
            else:
                return "finalization"
                
        def planning_phase(state: State) -> State:
            """Planning phase with appropriate model."""
            planning_model = state.get("multi_model", {}).get("planning_model", "gpt-4")
            
            # Here we only prepare the planning phase - actual execution happens later
            return {
                **state, 
                "planning_result": {
                    "model": planning_model,
                    "status": "prepared",
                    "task": "Feladat tervezése"
                },
                "multi_model": {
                    **state.get("multi_model", {}),
                    "current_phase": "execution"
                }
            }
            
        def execution_phase(state: State) -> State:
            """Execution phase with appropriate model."""
            execution_model = state.get("multi_model", {}).get("execution_model", "claude-3-sonnet")
            
            # Here we only prepare the execution phase
            return {
                **state, 
                "execution_result": {
                    "model": execution_model,
                    "status": "prepared",
                    "task": "Feladat végrehajtása",
                    "planning_input": state.get("planning_result", {})
                },
                "multi_model": {
                    **state.get("multi_model", {}),
                    "current_phase": "verification"
                }
            }
            
        def verification_phase(state: State) -> State:
            """Verification phase with appropriate model."""
            verification_model = state.get("multi_model", {}).get("verification_model", "gpt-3.5-turbo")
            
            # Here we only prepare the verification phase
            return {
                **state, 
                "verification_result": {
                    "model": verification_model,
                    "status": "prepared",
                    "task": "Eredmény ellenőrzése",
                    "execution_input": state.get("execution_result", {})
                },
                "multi_model": {
                    **state.get("multi_model", {}),
                    "current_phase": "finalization"
                }
            }
            
        def finalization(state: State) -> State:
            """Summarize results."""
            # Summarize results from different phases
            return {
                **state,
                "final_result": {
                    "planning": state.get("planning_result", {}),
                    "execution": state.get("execution_result", {}),
                    "verification": state.get("verification_result", {}),
                    "status": "complete"
                }
            }
            
        # Add nodes
        builder.add_node("analyze_request", analyze_request)
        builder.add_node("planning_phase", planning_phase)
        builder.add_node("execution_phase", execution_phase)
        builder.add_node("verification_phase", verification_phase)
        builder.add_node("finalization", finalization)
        
        # Router and edges
        builder.add_conditional_edges(
            "analyze_request",
            route_phase,
            {
                "planning_phase": "planning_phase",
                "execution_phase": "execution_phase",
                "verification_phase": "verification_phase",
                "finalization": "finalization"
            }
        )
        
        builder.add_conditional_edges(
            "planning_phase",
            route_phase,
            {
                "planning_phase": "planning_phase",
                "execution_phase": "execution_phase",
                "verification_phase": "verification_phase",
                "finalization": "finalization"
            }
        )
        
        builder.add_conditional_edges(
            "execution_phase",
            route_phase,
            {
                "planning_phase": "planning_phase",
                "execution_phase": "execution_phase",
                "verification_phase": "verification_phase",
                "finalization": "finalization"
            }
        )
        
        builder.add_conditional_edges(
            "verification_phase",
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
        logger.debug("✅ Multi-model LangGraph workflow created")
    
    async def process_with_basic_graph(self, command: str) -> Dict[str, Any]:
        """Process command using basic LangGraph workflow."""
        if not LANGGRAPH_AVAILABLE or not self.graph:
            return {"error": "LangGraph not available"}
        
        try:
            # Create initial state
            initial_state = {"input": command}
            
            # Run on state graph
            logger.info(f"🔄 Processing command with basic LangGraph workflow: '{command}'")
            final_state = self.graph.invoke(initial_state)
            
            # Now that we have the suggested model, actually execute the task
            task_type = final_state.get("parsed_input", {}).get("detected_type", "gyors_válasz")
            selected_model = final_state.get("prepared_response", {}).get("selected_model", "gpt-3.5-turbo")
            
            # Actual AI execution
            if model_manager and hasattr(model_manager, 'execute_task_with_model'):
                try:
                    result = await model_manager.execute_task_with_model(
                        query=command,
                        system_message="Feldolgozd a felhasználó kérését a megadott modellel.",
                        model=selected_model,
                        task_type=task_type
                    )
                    final_state["result"] = result
                except Exception as e:
                    logger.warning(f"Model execution failed: {e}")
                    final_state["result"] = {"content": f"Model execution not available: {e}"}
            else:
                final_state["result"] = {"content": "Model manager not available - running in limited mode"}
            
            return final_state
            
        except Exception as e:
            logger.error(f"Error in LangGraph workflow: {e}")
            return {"error": str(e)}
    
    async def process_with_multi_step_graph(self, command: str) -> Dict[str, Any]:
        """Process command using multi-step LangGraph workflow."""
        if not LANGGRAPH_AVAILABLE or not self.multi_step_graph:
            return {"error": "LangGraph multi-step workflow not available"}
        
        try:
            # Create initial state
            initial_state = {"input": command}
            
            # Run on state graph
            logger.info(f"🔄 Processing command with multi-step LangGraph workflow: '{command}'")
            final_state = self.multi_step_graph.invoke(initial_state)
            
            workflow_type = final_state.get("workflow", "simple")
            final_response = final_state.get("final_response", "")
            
            # Only call AI for simple execution
            # Other workflow types would be called in multiple steps with custom handling
            if workflow_type == "simple" and model_manager and hasattr(model_manager, 'execute_task_with_tools'):
                try:
                    result = await model_manager.execute_task_with_tools(
                        query=command,
                        system_message="Egyszerű feladat végrehajtása. Használj megfelelő eszközöket a feladat teljesítéséhez."
                    )
                    final_state["ai_result"] = result
                except Exception as e:
                    logger.warning(f"Tool execution failed: {e}")
                    final_state["ai_result"] = {"content": f"Tool execution not available: {e}"}
            
            return final_state
            
        except Exception as e:
            logger.error(f"Error in multi-step LangGraph workflow: {e}")
            return {"error": str(e)}
    
    async def process_with_multi_model_graph(self, command: str) -> Dict[str, Any]:
        """Process command using multi-model LangGraph workflow."""
        if not LANGGRAPH_AVAILABLE or not self.multi_model_graph:
            return {"error": "LangGraph multi-model workflow not available"}
        
        try:
            # Create initial state
            initial_state = {"input": command}
            
            # Run on state graph
            logger.info(f"🔄 Processing command with multi-model LangGraph workflow: '{command}'")
            final_state = self.multi_model_graph.invoke(initial_state)
            
            # Only proceed with AI execution if model_manager is available
            if not model_manager or not hasattr(model_manager, 'execute_task_with_tools'):
                final_state["combined_result"] = {
                    "planning": "Model manager not available",
                    "execution": "Model manager not available", 
                    "verification": "Model manager not available",
                    "summary": "Running in limited mode - no AI execution available"
                }
                return final_state
            
            try:
                # Actual AI execution for each phase
                # 1. Planning
                planning_model = final_state.get("planning_result", {}).get("model", "gpt-4")
                planning_result = await model_manager.execute_task_with_tools(
                    query=f"Tervezési fázis a következő feladathoz: {command}",
                    system_message="Most a tervezési fázisban vagy. Készíts részletes tervet a feladat végrehajtásához.",
                    model=planning_model,
                    task_type="tervezés"
                )
                
                # 2. Execution
                execution_model = final_state.get("execution_result", {}).get("model", "claude-3-sonnet")
                planning_content = planning_result.get("content", "")
                execution_result = await model_manager.execute_task_with_tools(
                    query=f"Végrehajtási fázis. Terv: {planning_content}. Feladat: {command}",
                    system_message="Most a végrehajtási fázisban vagy. Hajtsd végre a tervet a feladat megoldásához.",
                    model=execution_model,
                    task_type="kódolás"
                )
                
                # 3. Verification
                verification_model = final_state.get("verification_result", {}).get("model", "gpt-3.5-turbo")
                execution_content = execution_result.get("content", "")
                verification_result = await model_manager.execute_task_with_tools(
                    query=f"Ellenőrzési fázis. Végrehajtás eredménye: {execution_content}. Eredeti feladat: {command}",
                    system_message="Most az ellenőrzési fázisban vagy. Értékeld a végrehajtás eredményét.",
                    model=verification_model,
                    task_type="összefoglalás"
                )
                
                # Summarize results
                final_state["planning_ai_result"] = planning_result
                final_state["execution_ai_result"] = execution_result
                final_state["verification_ai_result"] = verification_result
                
                # Combine phase results
                final_state["combined_result"] = {
                    "planning": planning_result.get("content", ""),
                    "execution": execution_result.get("content", ""),
                    "verification": verification_result.get("content", ""),
                    "summary": f"Task executed using multiple models:\n"
                              f"1. Planning: {planning_model}\n"
                              f"2. Execution: {execution_model}\n"
                              f"3. Verification: {verification_model}"
                }
                
            except Exception as e:
                logger.error(f"AI execution error in multi-model workflow: {e}")
                final_state["combined_result"] = {
                    "error": f"AI execution failed: {e}",
                    "summary": "Multi-model workflow setup completed but AI execution failed"
                }
            
            return final_state
            
        except Exception as e:
            logger.error(f"Error in multi-model LangGraph workflow: {e}")
            return {"error": str(e)}
    
    async def process_with_multi_model_graph_with_persistence(self, 
                                              command: str, 
                                              session_id: Optional[str] = None) -> Dict[str, Any]:
        """Process command with multi-model graph and persistent state preservation."""
        if not LANGGRAPH_AVAILABLE:
            return {"error": "LangGraph not available"}
        
        # Check or create session
        if not session_id:
            if self.state_manager and hasattr(self.state_manager, 'create_session'):
                try:
                    session_id = await self.state_manager.create_session({
                        "workflow_type": "multi_model"
                    })
                except:
                    session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            else:
                session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
        # Config ID for LangGraph
        config_id = "multi_model_workflow"
        
        # Check for previously saved state for this session
        saved_state = None
        if self.state_manager and hasattr(self.state_manager, 'load_langgraph_checkpoint'):
            try:
                saved_state = await self.state_manager.load_langgraph_checkpoint(session_id, config_id)
            except:
                saved_state = None
        
        initial_state = {}
        if saved_state:
            # If there's saved state, use it
            logger.info(f"✅ Previously saved state loaded from session: {session_id}")
            initial_state = saved_state
            
            # Add new input to existing state
            initial_state["input"] = command
            initial_state["last_command_timestamp"] = datetime.now().isoformat()
        else:
            # Otherwise create new initial state
            initial_state = {"input": command, "multi_model": {}}
        
        # Run graph with initial state
        events = []
        final_state = None
        
        try:
            # Use astream instead of stream for proper async iteration
            async for event in self.multi_model_graph.astream(initial_state):
                events.append(event)
                final_state = event  # The event contains the state
        except AttributeError:
            # Fallback: if astream is not available, use invoke
            try:
                final_state = await self.multi_model_graph.ainvoke(initial_state)
                events.append(final_state)
            except AttributeError:
                # Final fallback: synchronous invoke
                final_state = self.multi_model_graph.invoke(initial_state)
                events.append(final_state)
            
        if not final_state:
            return {"error": "Workflow did not return state"}
        
        # Save state for later continuation
        if self.state_manager and hasattr(self.state_manager, 'save_langgraph_checkpoint'):
            try:
                await self.state_manager.save_langgraph_checkpoint(session_id, config_id, final_state)
            except Exception as e:
                logger.warning(f"Failed to save checkpoint: {e}")
        
        # Complete processing - similar to process_with_multi_model_graph
        if model_manager and hasattr(model_manager, 'execute_task_with_tools'):
            try:
                # Execute each phase...
                planning_model = final_state.get("planning_result", {}).get("model", "gpt-4")
                planning_result = await model_manager.execute_task_with_tools(
                    query=f"Tervezési fázis a következő feladathoz: {command}",
                    model=planning_model,
                    task_type="tervezés"
                )
                
                # Return session result
                return {
                    "result": planning_result.get("content", "Planning phase completed"),
                    "models_used": {
                        "planning": planning_model,
                        "execution": final_state.get("execution_result", {}).get("model", "claude-3-sonnet"),
                        "verification": final_state.get("verification_result", {}).get("model", "gpt-3.5-turbo")
                    },
                    "session_id": session_id,
                    "workflow_events": events
                }
            except Exception as e:
                logger.error(f"AI execution failed in persistent workflow: {e}")
                return {
                    "result": f"Workflow prepared but AI execution failed: {e}",
                    "session_id": session_id,
                    "workflow_events": events
                }
        else:
            return {
                "result": "Workflow completed in limited mode - no AI execution available",
                "session_id": session_id,
                "workflow_events": events
            }


# Create a global instance for easy access
advanced_langgraph_workflow = AdvancedLangGraphWorkflow()
