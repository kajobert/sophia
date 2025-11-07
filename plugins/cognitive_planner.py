import logging
import json
import re
import os
from plugins.base_plugin import BasePlugin, PluginType
from core.context import SharedContext

logger = logging.getLogger(__name__)


def _extract_json_from_text(text: str):
    """
    ENHANCED: Aggressively extract JSON from text with multiple fallback strategies.
    
    Returns a parsed Python object on success, or None on failure.

    Strategy:
    1. Try direct json.loads(text)
    2. Strip markdown code blocks (```json, ```)
    3. Search for balanced JSON array `[...]` or object `{...}` blocks
    4. Auto-fix common LLM errors (missing closing brackets, trailing commas)
    5. Last resort: single quote replacement
    """
    if not text:
        return None

    # 1) direct parse
    try:
        return json.loads(text)
    except Exception:
        pass
    
    # 2) Strip markdown code blocks
    text_clean = text.strip()
    if text_clean.startswith("```"):
        # Remove opening ```json or ```
        text_clean = re.sub(r'^```(?:json)?\s*', '', text_clean)
        # Remove closing ```
        text_clean = re.sub(r'```\s*$', '', text_clean)
        text_clean = text_clean.strip()
        try:
            return json.loads(text_clean)
        except Exception:
            pass
    
    # 3) Auto-fix common LLM errors
    text_fixed = text_clean
    
    # Fix missing closing bracket for arrays
    if text_fixed.count('[') > text_fixed.count(']'):
        open_count = text_fixed.count('[') - text_fixed.count(']')
        # Add missing closing brackets
        text_fixed = text_fixed.rstrip() + (']' * open_count)
        logger.info(f"✅ Auto-fixed {open_count} missing ]")
        try:
            return json.loads(text_fixed)
        except Exception:
            pass
    
    # Fix missing closing brace for objects
    if text_fixed.count('{') > text_fixed.count('}'):
        open_count = text_fixed.count('{') - text_fixed.count('}')
        text_fixed = text_fixed.rstrip() + ('}' * open_count)
        logger.info(f"✅ Auto-fixed {open_count} missing }}")
        try:
            return json.loads(text_fixed)
        except Exception:
            pass
    
    # Remove trailing commas before ] or }
    text_fixed = re.sub(r',\s*]', ']', text_fixed)
    text_fixed = re.sub(r',\s*}', '}', text_fixed)
    try:
        return json.loads(text_fixed)
    except Exception:
        pass

    # 4) collect balanced blocks for arrays or objects and attempt to parse them all
    candidates = []
    for start_char, end_char in ("[", "]"), ("{", "}"):
        idx = text.find(start_char)
        while idx != -1:
            depth = 0
            in_string = False
            escape = False
            for i in range(idx, len(text)):
                ch = text[i]
                if ch == '"' and not escape:
                    in_string = not in_string
                if ch == '\\' and not escape:
                    escape = True
                    continue
                else:
                    escape = False

                if not in_string:
                    if ch == start_char:
                        depth += 1
                    elif ch == end_char:
                        depth -= 1
                        if depth == 0:
                            candidate = text[idx : i + 1]
                            candidates.append(candidate)
                            break
            idx = text.find(start_char, idx + 1)

    # Try parsing candidates and pick the most useful one:
    parsed_candidates = []
    for cand in candidates:
        try:
            parsed = json.loads(cand)
            parsed_candidates.append((cand, parsed))
        except Exception:
            # try naive single->double quote replacement as last resort
            try:
                fixed = cand.replace("'", '"')
                parsed = json.loads(fixed)
                parsed_candidates.append((cand, parsed))
            except Exception:
                continue

    # Prefer dicts with 'plan' key, then lists, then longest parsed candidate
    for cand, parsed in parsed_candidates:
        if isinstance(parsed, dict) and parsed.get("plan"):
            return parsed

    for cand, parsed in parsed_candidates:
        if isinstance(parsed, list):
            return parsed

    if parsed_candidates:
        # return the longest parsed text as a last resort
        parsed_candidates.sort(key=lambda x: len(x[0]), reverse=True)
        return parsed_candidates[0][1]

    return None
def _validate_plan(plan):
    """Validate plan structure: list of objects with required keys and types.
    Returns (bool, reason)
    """
    if not isinstance(plan, list):
        return False, "Plan is not a JSON array"
    for idx, item in enumerate(plan):
        if not isinstance(item, dict):
            return False, f"Step {idx} is not an object"
        for k in ("tool_name", "method_name", "arguments"):
            if k not in item:
                return False, f"Step {idx} missing required key: {k}"
        if not isinstance(item.get("tool_name"), str):
            return False, f"Step {idx} 'tool_name' must be a string"
        if not isinstance(item.get("method_name"), str):
            return False, f"Step {idx} 'method_name' must be a string"
        if not isinstance(item.get("arguments"), dict):
            return False, f"Step {idx} 'arguments' must be an object"
    return True, ""


class Planner(BasePlugin):
    """A cognitive plugin that creates a plan based on user input."""

    @property
    def name(self) -> str:
        return "cognitive_planner"

    @property
    def plugin_type(self) -> PluginType:
        return PluginType.COGNITIVE

    @property
    def version(self) -> str:
        return "1.0.0"

    def setup(self, config: dict) -> None:
        """This plugin requires the LLM tool to function."""
        self.prompt_template = ""
        offline_mode = config.get("offline_mode", False)
        
        # Use simplified prompt in offline mode (smaller context for 8B models)
        prompt_file = "config/prompts/planner_offline_prompt.txt" if offline_mode else "config/prompts/planner_prompt_template.txt"
        
        try:
            with open(prompt_file, "r") as f:
                self.prompt_template = f.read()
            if offline_mode:
                logger.info("Using simplified offline planner prompt")
        except FileNotFoundError:
            logger.error(
                f"Planner prompt template not found: {prompt_file}",
                extra={"plugin_name": "cognitive_planner"},
            )
            self.prompt_template = "Create a plan. Available tools: {tool_list}"

        self.plugins = config.get("all_plugins", {})
        # Use local LLM in offline mode, cloud LLM otherwise
        offline_mode = config.get("offline_mode", False)
        if offline_mode:
            self.llm_tool = self.plugins.get("tool_local_llm")
            if self.llm_tool:
                logger.info("Planner using tool_local_llm (offline mode)")
        else:
            self.llm_tool = self.plugins.get("tool_llm")
            if self.llm_tool:
                logger.info("Planner using tool_llm (cloud mode)")
        
        if not self.llm_tool:
            logger.error(
                "Planner plugin requires an LLM tool (tool_local_llm or tool_llm) to be available.",
                extra={"plugin_name": "cognitive_planner"},
            )

    async def execute(self, context: SharedContext) -> SharedContext:
        """
        Takes user input and generates a plan by instructing the LLM to call a
        predefined function. Implements fallback logic: retries plan generation
        up to `max_retries` times if extraction fails, and sets a planner_failed
        flag if all attempts fail.
        """
        # Number of attempts to ask the LLM to produce a valid JSON plan.
        # We try once + max_retries repair attempts (total attempts = max_retries+1)
        max_retries = 3
        attempt = 0
        plan_data = []
        last_llm_message = None
        last_exception = None

        # Respect global local-only flag unless payload explicitly allows cloud
        force_local = os.getenv("SOPHIA_FORCE_LOCAL_ONLY", "false").lower() == "true"
        allow_cloud_payload = False
        try:
            allow_cloud_payload = bool(context.payload.get("allow_cloud", False))
        except Exception:
            allow_cloud_payload = False

        if force_local and not allow_cloud_payload and context.payload.get("origin") != "user_input":
            context.offline_mode = True

        # Select LLM based on offline mode (runtime decision)
        if context.offline_mode:
            llm_tool = self.plugins.get("tool_local_llm")
            if not llm_tool:
                context.logger.error(
                    "Offline mode enabled but tool_local_llm not available!",
                    extra={"plugin_name": "cognitive_planner"}
                )
                context.payload["plan"] = []
                context.payload["planner_failed"] = True
                return context
            context.logger.info(
                "🔒 Planner using local LLM (offline mode)",
                extra={"plugin_name": "cognitive_planner"}
            )
        else:
            llm_tool = self.llm_tool
            context.logger.debug(
                "☁️ Planner using cloud LLM (online mode)",
                extra={"plugin_name": "cognitive_planner"}
            )

        if not context.user_input or not llm_tool:
            return context

        # --- Dynamically discover available tools ---
        available_tools = []
        if context.offline_mode:
            essential_tool_names = {
                "tool_local_llm",
                "tool_code_workspace",
                "tool_file_system",
                "tool_datetime",
                "tool_terminal",
            }
        else:
            essential_tool_names = None

        for plugin in self.plugins.values():
            if essential_tool_names and plugin.name not in essential_tool_names:
                continue
            if plugin.name == "tool_langfuse":
                continue
            if hasattr(plugin, "get_tool_definitions"):
                for tool_def in plugin.get_tool_definitions():
                    func = tool_def.get("function", {})
                    if "name" in func and "description" in func:
                        tool_string = (
                            f"- tool_name: '{plugin.name}', "
                            f"method_name: '{func['name']}', "
                            f"description: '{func['description']}'"
                        )
                        available_tools.append(tool_string)

        tool_list_str = "\n".join(available_tools)
        tool_description = self.prompt_template.format(
            tool_list=tool_list_str, user_input=context.user_input
        )

        planner_tool = [
            {
                "type": "function",
                "function": {
                    "name": "create_plan",
                    "description": tool_description,
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "plan": {
                                "type": "array",
                                "description": "An array of tool call objects.",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "tool_name": {"type": "string"},
                                        "method_name": {"type": "string"},
                                        "arguments": {"type": "object"},
                                    },
                                    "required": ["tool_name", "method_name", "arguments"],
                                },
                            }
                        },
                        "required": ["plan"],
                    },
                },
            }
        ]

        prompt = f"User Request: {context.user_input}"

        # Strong, explicit system instruction to force JSON-only output.
        strict_instructions = (
            "You are a planner. You MUST output ONLY a JSON array (no surrounding text, no explanation),\n"
            "where each item is an object with keys: 'tool_name' (string), 'method_name' (string), and 'arguments' (object).\n"
            "Example (one item):\n"
            "[{\n"
            "  \"tool_name\": \"tool_file_system\",\n"
            "  \"method_name\": \"write_file\",\n"
            "  \"arguments\": {\"path\": \"scripts/x.py\", \"content\": \"print(\\\"hi\\\")\"}\n"
            "}]\n"
            "Output exactly the JSON array and nothing else. If you cannot produce the schema, return an empty array: []"
        )

        planning_context = SharedContext(
            session_id=context.session_id,
            current_state="PLANNING",
            logger=context.logger,
            user_input=prompt,
            history=[],
            payload=context.payload.copy(),
        )
        planning_context.payload["tools"] = planner_tool
        planning_context.payload["tool_choice"] = "auto"
        # Loop: try initial planning + repair attempts. If the LLM output isn't valid JSON matching
        # the schema, we retry and provide the last output as context so the model can correct itself.
        while attempt <= max_retries:
            try:
                # Build history fresh each attempt, injecting strict system instruction.
                planning_context.history = [
                    {"role": "system", "content": strict_instructions},
                    {"role": "user", "content": prompt},
                ]

                if attempt > 0 and last_llm_message:
                    # Provide the previous invalid output and a short hint to correct it.
                    planning_context.history.append(
                        {"role": "user", "content": "Previous output was invalid JSON: \n" + str(last_llm_message) + "\n\nPlease output only the JSON array as described."}
                    )

                planned_context = await llm_tool.execute(context=planning_context)
                llm_message = planned_context.payload.get("llm_response")
                last_llm_message = llm_message
                context.logger.info(
                    f"Raw LLM response received in planner (attempt {attempt+1}): {llm_message}",
                    extra={"plugin_name": "cognitive_planner"},
                )
                plan_data = []
                # Normalize various LLM response shapes used in tests and runtimes
                tool_calls = None
                # 1) Ollama / tool-call converted responses: list of objects with .function
                if isinstance(llm_message, list) and len(llm_message) > 0 and hasattr(llm_message[0], "function"):
                    tool_calls = llm_message
                # 2) Some test helpers attach .tool_calls to a MagicMock
                elif hasattr(llm_message, "tool_calls"):
                    tool_calls = llm_message.tool_calls

                if tool_calls:
                    tool_call = tool_calls[0]
                    if getattr(tool_call, "function", None) and getattr(tool_call.function, "name", None) == "create_plan":
                        arguments = getattr(tool_call.function, "arguments", None)
                        if isinstance(arguments, dict):
                            plan_str = arguments.get("plan", "[]")
                            if isinstance(plan_str, str):
                                if plan_str and not plan_str.strip().endswith("]"):
                                    logger.warning(f"⚠️ Incomplete JSON: {plan_str[:80]}...")
                                    if plan_str.count("[") > plan_str.count("]"):
                                        plan_str = plan_str.rstrip() + "}]"
                                        logger.info("✅ Auto-fixed incomplete JSON")
                                plan_data = json.loads(plan_str)
                            else:
                                plan_data = plan_str
                        else:
                            try:
                                plan_data = json.loads(arguments).get("plan", [])
                            except Exception:
                                plan_data = []
                    else:
                        # Direct tool call list: convert tool_calls -> plan entries
                        plan_data = []
                        for tc in tool_calls:
                            fn = getattr(tc.function, "name", "")
                            # Split into plugin and method if possible
                            if "." in fn:
                                plugin_name, method_name = fn.split(".", 1)
                            else:
                                plugin_name = fn
                                method_name = ""
                            raw_args = getattr(tc.function, "arguments", None)
                            parsed_args = {}
                            if isinstance(raw_args, str):
                                try:
                                    parsed_args = json.loads(raw_args)
                                except Exception:
                                    parsed_args = {}
                            elif isinstance(raw_args, dict):
                                parsed_args = raw_args
                            plan_data.append(
                                {
                                    "tool_name": plugin_name,
                                    "method_name": method_name,
                                    "arguments": parsed_args,
                                }
                            )
                else:
                    # Fallback: extract plan from free-form string content
                    response_text = getattr(llm_message, "content", None)
                    if response_text is None:
                        response_text = str(llm_message)

                    parsed = _extract_json_from_text(response_text)
                    # Aggressive fallback: try to find the first balanced JSON array
                    # in the raw response string (handles double-encoded plan strings).
                    if parsed is None and isinstance(response_text, str):
                        s = response_text
                        parsed = None
                        start = s.find("[")
                        while start != -1 and parsed is None:
                            depth = 0
                            in_string = False
                            escape = False
                            for i in range(start, len(s)):
                                ch = s[i]
                                if ch == '"' and not escape:
                                    in_string = not in_string
                                if ch == '\\' and not escape:
                                    escape = True
                                    continue
                                else:
                                    escape = False

                                if not in_string:
                                    if ch == '[':
                                        depth += 1
                                    elif ch == ']':
                                        depth -= 1
                                        if depth == 0:
                                            candidate = s[start : i + 1]
                                            try:
                                                parsed = json.loads(candidate)
                                                break
                                            except Exception:
                                                parsed = None
                                                break
                            start = s.find("[", start + 1)
                    # If we recovered a parsed array but the items use alternate arg names,
                    # try to normalize common variants (e.g., 'file_path' or 'filename' -> 'path').
                    if parsed is not None and isinstance(parsed, list):
                        normalized = []
                        for item in parsed:
                            if not isinstance(item, dict):
                                normalized.append(item)
                                continue
                            args = item.get("arguments")
                            if isinstance(args, str):
                                try:
                                    args = json.loads(args)
                                except Exception:
                                    args = {"raw": args}

                            if isinstance(args, dict):
                                # common alternate keys mapping
                                if "file_path" in args and "path" not in args:
                                    args["path"] = args.pop("file_path")
                                if "filename" in args and "path" not in args:
                                    args["path"] = args.pop("filename")
                                # ensure only simple content (avoid complex escaping)
                                if "content" in args and not isinstance(args["content"], str):
                                    args["content"] = str(args["content"])

                            item["arguments"] = args
                            normalized.append(item)
                        parsed = normalized
                    if isinstance(parsed, list):
                        plan_data = parsed
                    elif isinstance(parsed, dict) and parsed.get("plan"):
                        plan_data = parsed.get("plan")
                # (duplicate fallback removed)

                if plan_data:
                    context.payload["plan"] = plan_data
                    context.payload["planner_failed"] = False
                    return context
                else:
                    context.logger.warning(
                        f"No valid plan found in LLM response (attempt {attempt+1}). Retrying...",
                        extra={"plugin_name": "cognitive_planner"},
                    )
            except (json.JSONDecodeError, AttributeError, ValueError, TypeError) as e:
                last_exception = e
                context.logger.error(
                    f"Failed to decode/process plan from LLM response (attempt {attempt+1}): {e}\nResponse was: {last_llm_message}",
                    exc_info=True,
                    extra={"plugin_name": "cognitive_planner"},
                )
            attempt += 1

        # All retries failed
        context.logger.error(
            f"Planner failed to generate a plan after {max_retries+1} attempts.",
            extra={"plugin_name": "cognitive_planner"},
        )
        context.payload["plan"] = []
        context.payload["planner_failed"] = True
        context.payload["planner_error_message"] = (
            f"Planner failed after {max_retries+1} attempts. Last exception: {last_exception}"
            if last_exception else "Planner failed to generate a plan."
        )
        return context
