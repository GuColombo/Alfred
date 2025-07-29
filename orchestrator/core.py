import asyncio
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
import uuid
from loguru import logger

from config.settings import ConfigManager
from memory.engine import MemoryEngine
from orchestrator.llm_router import LLMRouter
from tools.plugin_executor import PluginExecutor

@dataclass
class TaskContext:
    """Context for task execution."""
    task_id: str
    prompt: str
    model: str
    use_memory: bool
    enable_plugins: bool
    verbose: bool
    created_at: datetime
    metadata: Dict[str, Any]

class TaskOrchestrator:
    """Central orchestrator for Alfred's task execution."""
    
    def __init__(self, config: ConfigManager):
        self.config = config
        self.memory = MemoryEngine(config)
        self.llm_router = LLMRouter(config)
        self.plugin_executor = PluginExecutor(config)
        
        # Task tracking
        self.active_tasks: Dict[str, TaskContext] = {}
        self.completed_tasks: List[TaskContext] = []
        
        logger.info("Task orchestrator initialized")
    
    def execute_task(
        self,
        prompt: str,
        model: str = "auto",
        use_memory: bool = True,
        enable_plugins: bool = True,
        verbose: bool = False
    ) -> str:
        """Execute a task through the orchestrator."""
        
        # Create task context
        task_id = str(uuid.uuid4())
        context = TaskContext(
            task_id=task_id,
            prompt=prompt,
            model=model,
            use_memory=use_memory,
            enable_plugins=enable_plugins,
            verbose=verbose,
            created_at=datetime.now(),
            metadata={}
        )
        
        self.active_tasks[task_id] = context
        logger.info(f"Starting task {task_id}: {prompt[:100]}...")
        
        try:
            # Memory retrieval phase
            relevant_context = ""
            if use_memory:
                memories = self.memory.search(prompt, limit=5)
                if memories:
                    relevant_context = "\n".join([f"Memory {i+1}: {mem}" for i, mem in enumerate(memories)])
                    if verbose:
                        logger.info(f"Retrieved {len(memories)} relevant memories")
            
            # Model selection and routing
            selected_model = self.llm_router.select_model(model, prompt)
            if verbose:
                logger.info(f"Selected model: {selected_model}")
            
            # Enhanced prompt with context
            enhanced_prompt = self._build_enhanced_prompt(prompt, relevant_context, enable_plugins)
            
            # LLM execution
            response = self.llm_router.execute(selected_model, enhanced_prompt)
            
            # Plugin execution if needed
            if enable_plugins and self._requires_plugin_execution(response):
                plugin_result = self.plugin_executor.execute_from_response(response)
                if plugin_result:
                    response = f"{response}\n\nPlugin Execution Result:\n{plugin_result}"
            
            # Memory storage
            if use_memory:
                self.memory.store_interaction(prompt, response, context.metadata)
                if verbose:
                    logger.info("Stored interaction in memory")
            
            # Task completion
            context.metadata["status"] = "completed"
            context.metadata["response_length"] = len(response)
            context.metadata["model_used"] = selected_model
            
            self.completed_tasks.append(context)
            del self.active_tasks[task_id]
            
            logger.info(f"Task {task_id} completed successfully")
            return response
            
        except Exception as e:
            logger.error(f"Task {task_id} failed: {e}")
            context.metadata["status"] = "failed"
            context.metadata["error"] = str(e)
            self.completed_tasks.append(context)
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]
            raise
    
    def _build_enhanced_prompt(self, prompt: str, context: str, enable_plugins: bool) -> str:
        """Build enhanced prompt with context and capabilities."""
        enhanced = prompt
        
        if context:
            enhanced = f"Relevant context:\n{context}\n\nTask: {prompt}"
        
        if enable_plugins:
            plugin_list = self.plugin_executor.list_available_plugins()
            if plugin_list:
                enhanced += f"\n\nAvailable tools: {', '.join(plugin_list)}"
        
        return enhanced
    
    def _requires_plugin_execution(self, response: str) -> bool:
        """Determine if response requires plugin execution."""
        # Simple heuristic - look for tool invocation patterns
        tool_indicators = [
            "execute:", "run:", "tool:", "command:",
            "search:", "fetch:", "calculate:", "analyze:"
        ]
        return any(indicator in response.lower() for indicator in tool_indicators)
    
    def memory_search(self, query: str, limit: int = 10) -> List[str]:
        """Search memory for relevant information."""
        return self.memory.search(query, limit)
    
    def list_memories(self, limit: int = 10) -> List[str]:
        """List recent memories."""
        return self.memory.list_recent(limit)
    
    def clear_memory(self):
        """Clear all memory."""
        self.memory.clear()
    
    def memory_stats(self) -> str:
        """Get memory statistics."""
        stats = self.memory.get_stats()
        return f"Total memories: {stats.get('total', 0)}\nVector entries: {stats.get('vectors', 0)}\nGraph nodes: {stats.get('nodes', 0)}"
    
    def list_plugins(self) -> Dict[str, bool]:
        """List available plugins and their status."""
        return self.plugin_executor.list_plugins()
    
    def toggle_plugin(self, name: str, enabled: bool) -> bool:
        """Enable or disable a plugin."""
        return self.plugin_executor.toggle_plugin(name, enabled)
    
    def install_plugin(self, path: str) -> bool:
        """Install a plugin from path."""
        return self.plugin_executor.install_plugin(path)
    
    def get_status(self) -> str:
        """Get system status."""
        status_parts = [
            f"Active tasks: {len(self.active_tasks)}",
            f"Completed tasks: {len(self.completed_tasks)}",
            f"Memory status: {self.memory.is_healthy()}",
            f"LLM router status: {self.llm_router.get_status()}",
            f"Plugin executor status: {self.plugin_executor.get_status()}"
        ]
        return "\n".join(status_parts)