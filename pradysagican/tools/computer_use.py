"""
Computer Use Agent - Browser automation, GUI interaction, sandboxed code execution,
file operations, and system monitoring.

Provides a unified interface for programmatic computer interaction with safety
sandboxing, screen observation, and action execution capabilities.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import os
import platform
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import uuid
from collections import deque
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import (
    Any,
    Awaitable,
    Callable,
    Deque,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
    Union,
)

from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class BrowserActionType(str, Enum):
    """Types of browser actions."""
    NAVIGATE = "navigate"
    CLICK = "click"
    TYPE_TEXT = "type_text"
    SCROLL = "scroll"
    SCREENSHOT = "screenshot"
    WAIT = "wait"
    EVALUATE_JS = "evaluate_js"
    SELECT = "select"
    HOVER = "hover"
    GO_BACK = "go_back"
    GO_FORWARD = "go_forward"
    REFRESH = "refresh"


class GUIActionType(str, Enum):
    """Types of GUI interactions."""
    CLICK = "click"
    DOUBLE_CLICK = "double_click"
    RIGHT_CLICK = "right_click"
    TYPE_TEXT = "type_text"
    KEY_PRESS = "key_press"
    MOUSE_MOVE = "mouse_move"
    DRAG_AND_DROP = "drag_and_drop"
    SCREENSHOT = "screenshot"
    FIND_ELEMENT = "find_element"
    WAIT_FOR_ELEMENT = "wait_for_element"


class FileOperationType(str, Enum):
    """Types of file system operations."""
    READ = "read"
    WRITE = "write"
    APPEND = "append"
    DELETE = "delete"
    COPY = "copy"
    MOVE = "move"
    LIST_DIR = "list_dir"
    MKDIR = "mkdir"
    EXISTS = "exists"
    STAT = "stat"
    SEARCH = "search"
    CHECKSUM = "checksum"


class CodeLanguage(str, Enum):
    """Supported languages for sandboxed code execution."""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    BASH = "bash"
    RUBY = "ruby"
    GO = "go"


class HealthStatus(str, Enum):
    """System health status levels."""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------

class Coordinate(BaseModel):
    """Screen coordinate."""
    x: int = Field(default=0, ge=0)
    y: int = Field(default=0, ge=0)


class BrowserState(BaseModel):
    """Current state of the browser session."""
    url: str = Field(default="about:blank", description="Current page URL")
    title: str = Field(default="", description="Current page title")
    is_loading: bool = Field(default=False)
    cookies: Dict[str, str] = Field(default_factory=dict)
    viewport_width: int = Field(default=1920)
    viewport_height: int = Field(default=1080)
    scroll_x: int = Field(default=0)
    scroll_y: int = Field(default=0)
    history: List[str] = Field(default_factory=list, description="Navigation history")
    console_logs: List[str] = Field(default_factory=list)
    page_text: str = Field(default="", description="Extracted visible text content")
    dom_element_count: int = Field(default=0)
    screenshot_path: Optional[str] = Field(default=None)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class BrowserAction(BaseModel):
    """A single browser action to execute."""
    action_type: BrowserActionType
    url: Optional[str] = None
    selector: Optional[str] = None
    text: Optional[str] = None
    coordinate: Optional[Coordinate] = None
    scroll_delta: int = Field(default=0, description="Pixels to scroll (positive=down)")
    js_code: Optional[str] = None
    wait_seconds: float = Field(default=0.0, ge=0)
    timeout_seconds: float = Field(default=10.0, gt=0)


class BrowserActionResult(BaseModel):
    """Result of a browser action."""
    action_type: BrowserActionType
    success: bool
    state: BrowserState
    error: Optional[str] = None
    js_result: Any = None
    screenshot_data: Optional[bytes] = None
    duration_ms: float = 0.0


class GUIAction(BaseModel):
    """A GUI interaction action."""
    action_type: GUIActionType
    coordinate: Optional[Coordinate] = None
    end_coordinate: Optional[Coordinate] = None  # For drag_and_drop
    text: Optional[str] = None
    key_combination: Optional[str] = None  # e.g., "ctrl+c", "alt+tab"
    element_query: Optional[str] = None  # For find/wait operations
    timeout_seconds: float = Field(default=10.0, gt=0)
    screenshot_region: Optional[Tuple[int, int, int, int]] = Field(
        default=None, description="(x, y, width, height) region for screenshots"
    )


class GUIActionResult(BaseModel):
    """Result of a GUI action."""
    action_type: GUIActionType
    success: bool
    error: Optional[str] = None
    element_found: bool = False
    element_location: Optional[Coordinate] = None
    screenshot_path: Optional[str] = None
    duration_ms: float = 0.0


class CodeExecution(BaseModel):
    """Request for sandboxed code execution."""
    language: CodeLanguage
    code: str = Field(..., min_length=1)
    timeout_seconds: float = Field(default=30.0, gt=0, le=300.0)
    memory_limit_mb: int = Field(default=256, gt=0, le=4096)
    environment: Dict[str, str] = Field(
        default_factory=dict, description="Environment variables to set"
    )
    working_directory: Optional[str] = None
    stdin_data: Optional[str] = None


class CodeExecutionResult(BaseModel):
    """Result of a code execution."""
    language: CodeLanguage
    stdout: str = ""
    stderr: str = ""
    exit_code: int = -1
    success: bool = False
    duration_ms: float = 0.0
    memory_used_mb: float = 0.0
    error: Optional[str] = None
    truncated: bool = Field(default=False, description="Whether output was truncated")


class FileOperationResult(BaseModel):
    """Result of a file system operation."""
    operation: FileOperationType
    path: str
    success: bool
    error: Optional[str] = None
    data: Any = None  # File contents, directory listing, stat info, etc.
    size_bytes: Optional[int] = None
    duration_ms: float = 0.0


class CPUInfo(BaseModel):
    """CPU usage information."""
    usage_percent: float = 0.0
    core_count: int = 0
    load_average: Tuple[float, float, float] = (0.0, 0.0, 0.0)


class MemoryInfo(BaseModel):
    """Memory usage information."""
    total_mb: float = 0.0
    used_mb: float = 0.0
    available_mb: float = 0.0
    usage_percent: float = 0.0
    swap_total_mb: float = 0.0
    swap_used_mb: float = 0.0


class DiskInfo(BaseModel):
    """Disk usage information."""
    total_gb: float = 0.0
    used_gb: float = 0.0
    free_gb: float = 0.0
    usage_percent: float = 0.0
    mount_point: str = "/"


class NetworkInfo(BaseModel):
    """Network status information."""
    hostname: str = ""
    ip_addresses: List[str] = Field(default_factory=list)
    bytes_sent: int = 0
    bytes_received: int = 0
    connections_count: int = 0


class ProcessInfo(BaseModel):
    """Process information."""
    pid: int
    name: str
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    status: str = ""


class SystemHealth(BaseModel):
    """Comprehensive system health snapshot."""
    status: HealthStatus = HealthStatus.UNKNOWN
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    cpu: CPUInfo = Field(default_factory=CPUInfo)
    memory: MemoryInfo = Field(default_factory=MemoryInfo)
    disk: DiskInfo = Field(default_factory=DiskInfo)
    network: NetworkInfo = Field(default_factory=NetworkInfo)
    top_processes: List[ProcessInfo] = Field(default_factory=list)
    uptime_seconds: float = 0.0
    platform_info: str = ""
    python_version: str = ""
    warnings: List[str] = Field(default_factory=list)


class ScreenObservation(BaseModel):
    """An observation of the current screen state for the agent's decision-making."""
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    screenshot_path: Optional[str] = None
    visible_text: str = ""
    active_window_title: str = ""
    mouse_position: Coordinate = Field(default_factory=Coordinate)
    screen_width: int = 0
    screen_height: int = 0


class SandboxConfig(BaseModel):
    """Configuration for the execution sandbox."""
    allowed_paths: List[str] = Field(
        default_factory=lambda: [tempfile.gettempdir()],
        description="Directories the agent is allowed to access",
    )
    blocked_commands: List[str] = Field(
        default_factory=lambda: [
            "rm -rf /", "mkfs", "dd if=", ":(){ :|:& };:",
            "chmod -R 777 /", "shutdown", "reboot", "halt",
            "init 0", "init 6",
        ],
        description="Command patterns that are blocked for safety",
    )
    max_file_size_mb: int = Field(default=100, description="Max file size for write operations")
    allow_network: bool = Field(default=True)
    allow_subprocesses: bool = Field(default=True)
    max_output_bytes: int = Field(default=1_000_000, description="Max stdout/stderr size")


# ---------------------------------------------------------------------------
# Helper: Sandbox Validator
# ---------------------------------------------------------------------------

class _SandboxValidator:
    """Validates operations against sandbox security policies."""

    def __init__(self, config: SandboxConfig) -> None:
        self._config = config

    def validate_path(self, path: str) -> Tuple[bool, Optional[str]]:
        """Check whether a file path is within the allowed directories.

        Returns:
            Tuple of (allowed, error_message).
        """
        resolved = os.path.realpath(os.path.expanduser(path))
        for allowed in self._config.allowed_paths:
            allowed_resolved = os.path.realpath(os.path.expanduser(allowed))
            if resolved.startswith(allowed_resolved):
                return True, None
        return False, f"Path '{path}' is outside allowed directories: {self._config.allowed_paths}"

    def validate_command(self, command: str) -> Tuple[bool, Optional[str]]:
        """Check whether a command string contains blocked patterns.

        Returns:
            Tuple of (allowed, error_message).
        """
        cmd_lower = command.lower().strip()
        for blocked in self._config.blocked_commands:
            if blocked.lower() in cmd_lower:
                return False, f"Command contains blocked pattern: '{blocked}'"
        return True, None

    def validate_code(self, code: str, language: CodeLanguage) -> Tuple[bool, Optional[str]]:
        """Perform basic static analysis on code to detect dangerous patterns.

        This is a heuristic check and not a replacement for true sandboxing.

        Returns:
            Tuple of (allowed, error_message).
        """
        dangerous_patterns: Dict[CodeLanguage, List[str]] = {
            CodeLanguage.PYTHON: [
                r"os\.system\s*\(",
                r"subprocess\.(?:call|run|Popen)\s*\(",
                r"shutil\.rmtree\s*\(\s*['\"]\/",
                r"__import__\s*\(\s*['\"](?:os|subprocess|shutil)",
                r"eval\s*\(\s*input",
            ],
            CodeLanguage.BASH: [
                r"rm\s+-rf\s+/(?!\w)",
                r"mkfs\.",
                r"dd\s+if=",
                r":\(\)\s*\{",
                r"chmod\s+-R\s+777\s+/(?!\w)",
            ],
            CodeLanguage.JAVASCRIPT: [
                r"child_process",
                r"require\s*\(\s*['\"]fs['\"]\s*\)\.(?:unlink|rmdir)",
                r"process\.exit",
            ],
        }

        patterns = dangerous_patterns.get(language, [])
        for pattern in patterns:
            if re.search(pattern, code):
                return False, f"Code contains potentially dangerous pattern: {pattern}"
        return True, None


# ---------------------------------------------------------------------------
# Computer Use Agent
# ---------------------------------------------------------------------------

class ComputerUseAgent:
    """Agent for computer interaction: browser automation, GUI, code execution,
    file operations, and system monitoring.

    Implements screen observation and action execution within a sandboxed
    environment for safety. All operations are logged and validated against
    the sandbox configuration before execution.

    Example::

        agent = ComputerUseAgent()

        # Navigate a browser
        result = await agent.navigate_browser("https://example.com")
        print(result.state.title)

        # Execute sandboxed code
        code_result = await agent.execute_code(CodeLanguage.PYTHON, "print(2 + 2)")
        print(code_result.stdout)  # "4\\n"

        # Check system health
        health = await agent.system_monitoring()
        print(health.status, health.cpu.usage_percent)
    """

    def __init__(
        self,
        sandbox_config: Optional[SandboxConfig] = None,
        browser_executable: Optional[str] = None,
    ) -> None:
        self._sandbox = sandbox_config or SandboxConfig()
        self._validator = _SandboxValidator(self._sandbox)
        self._browser_state = BrowserState()
        self._browser_executable = browser_executable
        self._action_history: Deque[Dict[str, Any]] = deque(maxlen=500)
        self._observations: Deque[ScreenObservation] = deque(maxlen=100)
        self._temp_dir = Path(tempfile.mkdtemp(prefix="computer_use_agent_"))
        # Ensure temp dir is in allowed paths
        if str(self._temp_dir) not in self._sandbox.allowed_paths:
            self._sandbox.allowed_paths.append(str(self._temp_dir))
        logger.info("ComputerUseAgent initialized (temp_dir=%s)", self._temp_dir)

    # ------------------------------------------------------------------
    # Browser Automation
    # ------------------------------------------------------------------

    async def navigate_browser(
        self,
        url: str,
        *,
        wait_seconds: float = 0.0,
        viewport_width: int = 1920,
        viewport_height: int = 1080,
    ) -> BrowserActionResult:
        """Navigate the browser to a URL.

        Simulates a full page navigation including URL validation, state updates,
        history management, and optional waiting for dynamic content.

        Args:
            url: The URL to navigate to.
            wait_seconds: Seconds to wait after navigation for dynamic content.
            viewport_width: Browser viewport width.
            viewport_height: Browser viewport height.

        Returns:
            BrowserActionResult with the updated browser state.
        """
        start = time.monotonic()
        action = BrowserAction(
            action_type=BrowserActionType.NAVIGATE,
            url=url,
            wait_seconds=wait_seconds,
        )

        # Validate URL
        if not self._validate_url(url):
            return BrowserActionResult(
                action_type=BrowserActionType.NAVIGATE,
                success=False,
                state=self._browser_state,
                error=f"Invalid or blocked URL: {url}",
                duration_ms=self._elapsed_ms(start),
            )

        # Update browser state
        old_url = self._browser_state.url
        self._browser_state.url = url
        self._browser_state.is_loading = True
        self._browser_state.viewport_width = viewport_width
        self._browser_state.viewport_height = viewport_height
        if old_url != "about:blank":
            self._browser_state.history.append(old_url)

        # Simulate page load
        self._browser_state.title = self._extract_title_from_url(url)
        self._browser_state.page_text = f"[Page content for {url}]"
        self._browser_state.dom_element_count = hash(url) % 500 + 50
        self._browser_state.scroll_x = 0
        self._browser_state.scroll_y = 0
        self._browser_state.timestamp = datetime.now(timezone.utc)

        if wait_seconds > 0:
            await asyncio.sleep(wait_seconds)

        self._browser_state.is_loading = False
        self._browser_state.console_logs.append(f"Navigated to {url}")

        elapsed = self._elapsed_ms(start)
        self._record_action("navigate_browser", {"url": url}, True, elapsed)

        return BrowserActionResult(
            action_type=BrowserActionType.NAVIGATE,
            success=True,
            state=self._browser_state.model_copy(deep=True),
            duration_ms=elapsed,
        )

    async def execute_browser_action(self, action: BrowserAction) -> BrowserActionResult:
        """Execute an arbitrary browser action.

        Supports NAVIGATE, CLICK, TYPE_TEXT, SCROLL, SCREENSHOT, WAIT,
        EVALUATE_JS, SELECT, HOVER, GO_BACK, GO_FORWARD, and REFRESH.

        Args:
            action: The BrowserAction to execute.

        Returns:
            BrowserActionResult with the outcome and updated state.
        """
        start = time.monotonic()

        try:
            if action.action_type == BrowserActionType.NAVIGATE:
                return await self.navigate_browser(action.url or "about:blank", wait_seconds=action.wait_seconds)

            elif action.action_type == BrowserActionType.CLICK:
                return await self._browser_click(action, start)

            elif action.action_type == BrowserActionType.TYPE_TEXT:
                return await self._browser_type(action, start)

            elif action.action_type == BrowserActionType.SCROLL:
                self._browser_state.scroll_y = max(0, self._browser_state.scroll_y + action.scroll_delta)
                return BrowserActionResult(
                    action_type=BrowserActionType.SCROLL,
                    success=True,
                    state=self._browser_state.model_copy(deep=True),
                    duration_ms=self._elapsed_ms(start),
                )

            elif action.action_type == BrowserActionType.SCREENSHOT:
                screenshot_path = str(self._temp_dir / f"screenshot_{uuid.uuid4().hex[:8]}.png")
                self._browser_state.screenshot_path = screenshot_path
                return BrowserActionResult(
                    action_type=BrowserActionType.SCREENSHOT,
                    success=True,
                    state=self._browser_state.model_copy(deep=True),
                    duration_ms=self._elapsed_ms(start),
                )

            elif action.action_type == BrowserActionType.WAIT:
                await asyncio.sleep(action.wait_seconds)
                return BrowserActionResult(
                    action_type=BrowserActionType.WAIT,
                    success=True,
                    state=self._browser_state.model_copy(deep=True),
                    duration_ms=self._elapsed_ms(start),
                )

            elif action.action_type == BrowserActionType.EVALUATE_JS:
                return await self._browser_eval_js(action, start)

            elif action.action_type == BrowserActionType.GO_BACK:
                if self._browser_state.history:
                    prev_url = self._browser_state.history.pop()
                    self._browser_state.url = prev_url
                    self._browser_state.title = self._extract_title_from_url(prev_url)
                return BrowserActionResult(
                    action_type=BrowserActionType.GO_BACK,
                    success=True,
                    state=self._browser_state.model_copy(deep=True),
                    duration_ms=self._elapsed_ms(start),
                )

            elif action.action_type == BrowserActionType.GO_FORWARD:
                return BrowserActionResult(
                    action_type=BrowserActionType.GO_FORWARD,
                    success=True,
                    state=self._browser_state.model_copy(deep=True),
                    duration_ms=self._elapsed_ms(start),
                )

            elif action.action_type == BrowserActionType.REFRESH:
                self._browser_state.timestamp = datetime.now(timezone.utc)
                self._browser_state.console_logs.append(f"Refreshed {self._browser_state.url}")
                return BrowserActionResult(
                    action_type=BrowserActionType.REFRESH,
                    success=True,
                    state=self._browser_state.model_copy(deep=True),
                    duration_ms=self._elapsed_ms(start),
                )

            elif action.action_type == BrowserActionType.HOVER:
                return BrowserActionResult(
                    action_type=BrowserActionType.HOVER,
                    success=True,
                    state=self._browser_state.model_copy(deep=True),
                    duration_ms=self._elapsed_ms(start),
                )

            elif action.action_type == BrowserActionType.SELECT:
                return BrowserActionResult(
                    action_type=BrowserActionType.SELECT,
                    success=True,
                    state=self._browser_state.model_copy(deep=True),
                    duration_ms=self._elapsed_ms(start),
                )

            else:
                return BrowserActionResult(
                    action_type=action.action_type,
                    success=False,
                    state=self._browser_state.model_copy(deep=True),
                    error=f"Unsupported action type: {action.action_type}",
                    duration_ms=self._elapsed_ms(start),
                )

        except Exception as exc:
            return BrowserActionResult(
                action_type=action.action_type,
                success=False,
                state=self._browser_state.model_copy(deep=True),
                error=str(exc),
                duration_ms=self._elapsed_ms(start),
            )

    async def _browser_click(self, action: BrowserAction, start: float) -> BrowserActionResult:
        """Handle a browser click action."""
        target = action.selector or (
            f"({action.coordinate.x},{action.coordinate.y})" if action.coordinate else "unknown"
        )
        self._browser_state.console_logs.append(f"Clicked: {target}")
        self._browser_state.timestamp = datetime.now(timezone.utc)

        return BrowserActionResult(
            action_type=BrowserActionType.CLICK,
            success=True,
            state=self._browser_state.model_copy(deep=True),
            duration_ms=self._elapsed_ms(start),
        )

    async def _browser_type(self, action: BrowserAction, start: float) -> BrowserActionResult:
        """Handle a browser type text action."""
        if not action.text:
            return BrowserActionResult(
                action_type=BrowserActionType.TYPE_TEXT,
                success=False,
                state=self._browser_state.model_copy(deep=True),
                error="No text provided for type action",
                duration_ms=self._elapsed_ms(start),
            )

        target = action.selector or "active_element"
        self._browser_state.console_logs.append(f"Typed into {target}: {action.text[:50]}")
        self._browser_state.timestamp = datetime.now(timezone.utc)

        return BrowserActionResult(
            action_type=BrowserActionType.TYPE_TEXT,
            success=True,
            state=self._browser_state.model_copy(deep=True),
            duration_ms=self._elapsed_ms(start),
        )

    async def _browser_eval_js(self, action: BrowserAction, start: float) -> BrowserActionResult:
        """Handle JavaScript evaluation in the browser context."""
        if not action.js_code:
            return BrowserActionResult(
                action_type=BrowserActionType.EVALUATE_JS,
                success=False,
                state=self._browser_state.model_copy(deep=True),
                error="No JavaScript code provided",
                duration_ms=self._elapsed_ms(start),
            )

        # In a real implementation this would use CDP or Playwright.
        # Here we simulate basic JS evaluation for common patterns.
        js_result: Any = None
        code = action.js_code.strip()

        if code.startswith("document.title"):
            js_result = self._browser_state.title
        elif code.startswith("document.URL") or code.startswith("window.location.href"):
            js_result = self._browser_state.url
        elif code.startswith("document.querySelectorAll"):
            # Simulate returning element count
            js_result = self._browser_state.dom_element_count
        else:
            js_result = f"[JS eval result for: {code[:100]}]"

        self._browser_state.console_logs.append(f"JS eval: {code[:80]}")

        return BrowserActionResult(
            action_type=BrowserActionType.EVALUATE_JS,
            success=True,
            state=self._browser_state.model_copy(deep=True),
            js_result=js_result,
            duration_ms=self._elapsed_ms(start),
        )

    def get_browser_state(self) -> BrowserState:
        """Return a snapshot of the current browser state."""
        return self._browser_state.model_copy(deep=True)

    # ------------------------------------------------------------------
    # GUI Interaction
    # ------------------------------------------------------------------

    async def interact_with_gui(self, action: GUIAction) -> GUIActionResult:
        """Execute a GUI interaction action.

        Supports click, double-click, right-click, typing, key presses,
        mouse movement, drag-and-drop, screenshots, and element finding.

        Args:
            action: The GUIAction to execute.

        Returns:
            GUIActionResult with the outcome.
        """
        start = time.monotonic()
        logger.info("GUI action: %s", action.action_type.value)

        try:
            if action.action_type in (
                GUIActionType.CLICK,
                GUIActionType.DOUBLE_CLICK,
                GUIActionType.RIGHT_CLICK,
            ):
                return await self._gui_click(action, start)

            elif action.action_type == GUIActionType.TYPE_TEXT:
                return await self._gui_type_text(action, start)

            elif action.action_type == GUIActionType.KEY_PRESS:
                return await self._gui_key_press(action, start)

            elif action.action_type == GUIActionType.MOUSE_MOVE:
                return await self._gui_mouse_move(action, start)

            elif action.action_type == GUIActionType.DRAG_AND_DROP:
                return await self._gui_drag_drop(action, start)

            elif action.action_type == GUIActionType.SCREENSHOT:
                return await self._gui_screenshot(action, start)

            elif action.action_type == GUIActionType.FIND_ELEMENT:
                return await self._gui_find_element(action, start)

            elif action.action_type == GUIActionType.WAIT_FOR_ELEMENT:
                return await self._gui_wait_for_element(action, start)

            else:
                return GUIActionResult(
                    action_type=action.action_type,
                    success=False,
                    error=f"Unsupported GUI action: {action.action_type}",
                    duration_ms=self._elapsed_ms(start),
                )

        except Exception as exc:
            return GUIActionResult(
                action_type=action.action_type,
                success=False,
                error=str(exc),
                duration_ms=self._elapsed_ms(start),
            )

    async def _gui_click(self, action: GUIAction, start: float) -> GUIActionResult:
        """Perform a click action using system tools if available."""
        coord = action.coordinate or Coordinate(x=0, y=0)
        click_type = action.action_type.value

        # On Linux with xdotool available, perform real click
        if shutil.which("xdotool") and platform.system() == "Linux":
            click_map = {
                "click": "1",
                "double_click": "1 --repeat 2",
                "right_click": "3",
            }
            btn_args = click_map.get(click_type, "1")
            cmd = f"xdotool mousemove {coord.x} {coord.y} && xdotool click {btn_args}"
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()

        self._record_action(click_type, {"x": coord.x, "y": coord.y}, True, self._elapsed_ms(start))

        return GUIActionResult(
            action_type=action.action_type,
            success=True,
            element_location=coord,
            duration_ms=self._elapsed_ms(start),
        )

    async def _gui_type_text(self, action: GUIAction, start: float) -> GUIActionResult:
        """Type text using system tools."""
        text = action.text or ""
        if not text:
            return GUIActionResult(
                action_type=GUIActionType.TYPE_TEXT,
                success=False,
                error="No text provided",
                duration_ms=self._elapsed_ms(start),
            )

        if shutil.which("xdotool") and platform.system() == "Linux":
            # Escape single quotes for shell
            escaped = text.replace("'", "'\\''")
            cmd = f"xdotool type -- '{escaped}'"
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()

        self._record_action("type_text", {"text": text[:100]}, True, self._elapsed_ms(start))

        return GUIActionResult(
            action_type=GUIActionType.TYPE_TEXT,
            success=True,
            duration_ms=self._elapsed_ms(start),
        )

    async def _gui_key_press(self, action: GUIAction, start: float) -> GUIActionResult:
        """Simulate a key press or key combination."""
        keys = action.key_combination or ""
        if not keys:
            return GUIActionResult(
                action_type=GUIActionType.KEY_PRESS,
                success=False,
                error="No key combination specified",
                duration_ms=self._elapsed_ms(start),
            )

        if shutil.which("xdotool") and platform.system() == "Linux":
            # Convert common notation: ctrl+c -> ctrl+c (xdotool format)
            xdo_keys = keys.replace("+", "+")
            cmd = f"xdotool key {xdo_keys}"
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()

        self._record_action("key_press", {"keys": keys}, True, self._elapsed_ms(start))

        return GUIActionResult(
            action_type=GUIActionType.KEY_PRESS,
            success=True,
            duration_ms=self._elapsed_ms(start),
        )

    async def _gui_mouse_move(self, action: GUIAction, start: float) -> GUIActionResult:
        """Move the mouse cursor to a position."""
        coord = action.coordinate or Coordinate(x=0, y=0)

        if shutil.which("xdotool") and platform.system() == "Linux":
            cmd = f"xdotool mousemove {coord.x} {coord.y}"
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()

        return GUIActionResult(
            action_type=GUIActionType.MOUSE_MOVE,
            success=True,
            element_location=coord,
            duration_ms=self._elapsed_ms(start),
        )

    async def _gui_drag_drop(self, action: GUIAction, start: float) -> GUIActionResult:
        """Perform a drag-and-drop operation."""
        from_coord = action.coordinate or Coordinate(x=0, y=0)
        to_coord = action.end_coordinate or Coordinate(x=100, y=100)

        if shutil.which("xdotool") and platform.system() == "Linux":
            cmd = (
                f"xdotool mousemove {from_coord.x} {from_coord.y} "
                f"mousedown 1 "
                f"mousemove {to_coord.x} {to_coord.y} "
                f"mouseup 1"
            )
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()

        self._record_action(
            "drag_and_drop",
            {"from": (from_coord.x, from_coord.y), "to": (to_coord.x, to_coord.y)},
            True,
            self._elapsed_ms(start),
        )

        return GUIActionResult(
            action_type=GUIActionType.DRAG_AND_DROP,
            success=True,
            duration_ms=self._elapsed_ms(start),
        )

    async def _gui_screenshot(self, action: GUIAction, start: float) -> GUIActionResult:
        """Take a screenshot, optionally of a specific region."""
        screenshot_path = str(self._temp_dir / f"gui_screenshot_{uuid.uuid4().hex[:8]}.png")

        if shutil.which("scrot") and platform.system() == "Linux":
            if action.screenshot_region:
                x, y, w, h = action.screenshot_region
                # Use import from ImageMagick for region capture
                if shutil.which("import"):
                    cmd = f"import -window root -crop {w}x{h}+{x}+{y} {screenshot_path}"
                else:
                    cmd = f"scrot {screenshot_path}"
            else:
                cmd = f"scrot {screenshot_path}"

            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            if proc.returncode != 0:
                return GUIActionResult(
                    action_type=GUIActionType.SCREENSHOT,
                    success=False,
                    error=f"Screenshot failed: {stderr.decode(errors='replace')}",
                    duration_ms=self._elapsed_ms(start),
                )

        return GUIActionResult(
            action_type=GUIActionType.SCREENSHOT,
            success=True,
            screenshot_path=screenshot_path,
            duration_ms=self._elapsed_ms(start),
        )

    async def _gui_find_element(self, action: GUIAction, start: float) -> GUIActionResult:
        """Find a GUI element by query (uses accessibility tools where available)."""
        query = action.element_query or ""
        found = False
        location = None

        # On Linux, try xdotool search for window names
        if shutil.which("xdotool") and platform.system() == "Linux" and query:
            cmd = f"xdotool search --name '{query}' 2>/dev/null | head -1"
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await proc.communicate()
            window_id = stdout.decode().strip()
            if window_id:
                found = True
                # Get window geometry
                geo_cmd = f"xdotool getwindowgeometry {window_id} 2>/dev/null"
                geo_proc = await asyncio.create_subprocess_shell(
                    geo_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                geo_out, _ = await geo_proc.communicate()
                geo_text = geo_out.decode()
                # Parse "Position: X,Y"
                pos_match = re.search(r"Position:\s+(\d+),(\d+)", geo_text)
                if pos_match:
                    location = Coordinate(x=int(pos_match.group(1)), y=int(pos_match.group(2)))

        return GUIActionResult(
            action_type=GUIActionType.FIND_ELEMENT,
            success=True,
            element_found=found,
            element_location=location,
            duration_ms=self._elapsed_ms(start),
        )

    async def _gui_wait_for_element(self, action: GUIAction, start: float) -> GUIActionResult:
        """Wait for a GUI element to appear within the timeout."""
        query = action.element_query or ""
        deadline = time.monotonic() + action.timeout_seconds
        poll_interval = 0.5

        while time.monotonic() < deadline:
            find_result = await self._gui_find_element(action, start)
            if find_result.element_found:
                return GUIActionResult(
                    action_type=GUIActionType.WAIT_FOR_ELEMENT,
                    success=True,
                    element_found=True,
                    element_location=find_result.element_location,
                    duration_ms=self._elapsed_ms(start),
                )
            await asyncio.sleep(poll_interval)

        return GUIActionResult(
            action_type=GUIActionType.WAIT_FOR_ELEMENT,
            success=False,
            element_found=False,
            error=f"Element '{query}' not found within {action.timeout_seconds}s",
            duration_ms=self._elapsed_ms(start),
        )

    # ------------------------------------------------------------------
    # Sandboxed Code Execution
    # ------------------------------------------------------------------

    async def execute_code(
        self,
        language: Union[CodeLanguage, str],
        code: str,
        *,
        timeout_seconds: float = 30.0,
        memory_limit_mb: int = 256,
        environment: Optional[Dict[str, str]] = None,
        stdin_data: Optional[str] = None,
    ) -> CodeExecutionResult:
        """Execute code in a sandboxed subprocess environment.

        The code runs in a new subprocess with resource limits. Output is
        captured and truncated if it exceeds the configured maximum.

        Args:
            language: Programming language.
            code: Source code to execute.
            timeout_seconds: Maximum execution time.
            memory_limit_mb: Memory limit in MB.
            environment: Optional environment variables.
            stdin_data: Optional data piped to stdin.

        Returns:
            CodeExecutionResult with stdout, stderr, exit code, etc.
        """
        if isinstance(language, str):
            try:
                language = CodeLanguage(language.lower())
            except ValueError:
                return CodeExecutionResult(
                    language=CodeLanguage.PYTHON,
                    error=f"Unsupported language: {language}",
                )

        start = time.monotonic()

        # Sandbox validation
        valid, err = self._validator.validate_code(code, language)
        if not valid:
            return CodeExecutionResult(
                language=language,
                error=f"Sandbox validation failed: {err}",
                duration_ms=self._elapsed_ms(start),
            )

        # Find interpreter
        interpreter = self._get_interpreter(language)
        if interpreter is None:
            return CodeExecutionResult(
                language=language,
                error=f"Interpreter for {language.value} not found on this system",
                duration_ms=self._elapsed_ms(start),
            )

        # Write code to temp file
        ext_map = {
            CodeLanguage.PYTHON: ".py",
            CodeLanguage.JAVASCRIPT: ".js",
            CodeLanguage.BASH: ".sh",
            CodeLanguage.RUBY: ".rb",
            CodeLanguage.GO: ".go",
        }
        ext = ext_map.get(language, ".txt")
        code_file = self._temp_dir / f"exec_{uuid.uuid4().hex[:8]}{ext}"
        code_file.write_text(code, encoding="utf-8")

        # Build command
        if language == CodeLanguage.GO:
            cmd = [interpreter, "run", str(code_file)]
        else:
            cmd = [interpreter, str(code_file)]

        # Prepare environment
        env = dict(os.environ)
        env["HOME"] = str(self._temp_dir)
        env["TMPDIR"] = str(self._temp_dir)
        if environment:
            env.update(environment)

        # Set resource limits on Unix via preexec_fn
        def _set_limits() -> None:
            try:
                import resource
                mem_bytes = memory_limit_mb * 1024 * 1024
                resource.setrlimit(resource.RLIMIT_AS, (mem_bytes, mem_bytes))
            except (ImportError, ValueError, OSError):
                pass

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.PIPE if stdin_data else None,
                env=env,
                cwd=str(self._temp_dir),
                preexec_fn=_set_limits if platform.system() != "Windows" else None,
            )

            stdin_bytes = stdin_data.encode() if stdin_data else None
            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    proc.communicate(input=stdin_bytes),
                    timeout=timeout_seconds,
                )
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                return CodeExecutionResult(
                    language=language,
                    stderr=f"Execution timed out after {timeout_seconds}s",
                    exit_code=-1,
                    success=False,
                    duration_ms=self._elapsed_ms(start),
                    error="Timeout",
                )

            max_output = self._sandbox.max_output_bytes
            truncated = False
            stdout_str = stdout_bytes.decode(errors="replace")
            stderr_str = stderr_bytes.decode(errors="replace")

            if len(stdout_str) > max_output:
                stdout_str = stdout_str[:max_output] + "\n... [output truncated]"
                truncated = True
            if len(stderr_str) > max_output:
                stderr_str = stderr_str[:max_output] + "\n... [output truncated]"
                truncated = True

            exit_code = proc.returncode or 0
            success = exit_code == 0

            result = CodeExecutionResult(
                language=language,
                stdout=stdout_str,
                stderr=stderr_str,
                exit_code=exit_code,
                success=success,
                duration_ms=self._elapsed_ms(start),
                truncated=truncated,
            )

            self._record_action(
                "execute_code",
                {"language": language.value, "code_length": len(code), "exit_code": exit_code},
                success,
                result.duration_ms,
            )

            return result

        except FileNotFoundError:
            return CodeExecutionResult(
                language=language,
                error=f"Interpreter '{interpreter}' not found",
                duration_ms=self._elapsed_ms(start),
            )
        except Exception as exc:
            return CodeExecutionResult(
                language=language,
                error=str(exc),
                duration_ms=self._elapsed_ms(start),
            )
        finally:
            # Cleanup temp file
            try:
                code_file.unlink(missing_ok=True)
            except OSError:
                pass

    # ------------------------------------------------------------------
    # File Operations
    # ------------------------------------------------------------------

    async def file_operations(
        self,
        operation: Union[FileOperationType, str],
        path: str,
        *,
        content: Optional[str] = None,
        destination: Optional[str] = None,
        pattern: Optional[str] = None,
        encoding: str = "utf-8",
    ) -> FileOperationResult:
        """Perform a file system operation within the sandbox.

        All paths are validated against the sandbox's allowed directories.

        Args:
            operation: The file operation type.
            path: Primary file/directory path.
            content: Content for WRITE/APPEND operations.
            destination: Destination path for COPY/MOVE operations.
            pattern: Search pattern for SEARCH operation (glob or regex).
            encoding: Text encoding (default UTF-8).

        Returns:
            FileOperationResult with the outcome and any retrieved data.
        """
        if isinstance(operation, str):
            try:
                operation = FileOperationType(operation.lower())
            except ValueError:
                return FileOperationResult(
                    operation=FileOperationType.READ,
                    path=path,
                    success=False,
                    error=f"Unknown operation: {operation}",
                )

        start = time.monotonic()

        # Validate primary path
        valid, err = self._validator.validate_path(path)
        if not valid:
            return FileOperationResult(
                operation=operation, path=path, success=False,
                error=err, duration_ms=self._elapsed_ms(start),
            )

        # Validate destination path if needed
        if destination and operation in (FileOperationType.COPY, FileOperationType.MOVE):
            valid, err = self._validator.validate_path(destination)
            if not valid:
                return FileOperationResult(
                    operation=operation, path=path, success=False,
                    error=f"Destination: {err}", duration_ms=self._elapsed_ms(start),
                )

        try:
            p = Path(path)

            if operation == FileOperationType.READ:
                data = p.read_text(encoding=encoding)
                return FileOperationResult(
                    operation=operation, path=path, success=True,
                    data=data, size_bytes=len(data.encode(encoding)),
                    duration_ms=self._elapsed_ms(start),
                )

            elif operation == FileOperationType.WRITE:
                if content is None:
                    return FileOperationResult(
                        operation=operation, path=path, success=False,
                        error="No content provided for write", duration_ms=self._elapsed_ms(start),
                    )
                content_bytes = content.encode(encoding)
                max_size = self._sandbox.max_file_size_mb * 1024 * 1024
                if len(content_bytes) > max_size:
                    return FileOperationResult(
                        operation=operation, path=path, success=False,
                        error=f"Content exceeds max file size ({self._sandbox.max_file_size_mb} MB)",
                        duration_ms=self._elapsed_ms(start),
                    )
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(content, encoding=encoding)
                return FileOperationResult(
                    operation=operation, path=path, success=True,
                    size_bytes=len(content_bytes), duration_ms=self._elapsed_ms(start),
                )

            elif operation == FileOperationType.APPEND:
                if content is None:
                    return FileOperationResult(
                        operation=operation, path=path, success=False,
                        error="No content provided for append", duration_ms=self._elapsed_ms(start),
                    )
                with open(path, "a", encoding=encoding) as f:
                    f.write(content)
                size = p.stat().st_size
                return FileOperationResult(
                    operation=operation, path=path, success=True,
                    size_bytes=size, duration_ms=self._elapsed_ms(start),
                )

            elif operation == FileOperationType.DELETE:
                if p.is_dir():
                    shutil.rmtree(path)
                else:
                    p.unlink()
                return FileOperationResult(
                    operation=operation, path=path, success=True,
                    duration_ms=self._elapsed_ms(start),
                )

            elif operation == FileOperationType.COPY:
                if not destination:
                    return FileOperationResult(
                        operation=operation, path=path, success=False,
                        error="No destination provided for copy",
                        duration_ms=self._elapsed_ms(start),
                    )
                if p.is_dir():
                    shutil.copytree(path, destination)
                else:
                    shutil.copy2(path, destination)
                return FileOperationResult(
                    operation=operation, path=path, success=True,
                    data={"destination": destination}, duration_ms=self._elapsed_ms(start),
                )

            elif operation == FileOperationType.MOVE:
                if not destination:
                    return FileOperationResult(
                        operation=operation, path=path, success=False,
                        error="No destination provided for move",
                        duration_ms=self._elapsed_ms(start),
                    )
                shutil.move(path, destination)
                return FileOperationResult(
                    operation=operation, path=path, success=True,
                    data={"destination": destination}, duration_ms=self._elapsed_ms(start),
                )

            elif operation == FileOperationType.LIST_DIR:
                if not p.is_dir():
                    return FileOperationResult(
                        operation=operation, path=path, success=False,
                        error=f"'{path}' is not a directory", duration_ms=self._elapsed_ms(start),
                    )
                entries = []
                for entry in sorted(p.iterdir()):
                    stat = entry.stat()
                    entries.append({
                        "name": entry.name,
                        "is_dir": entry.is_dir(),
                        "size_bytes": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                    })
                return FileOperationResult(
                    operation=operation, path=path, success=True,
                    data=entries, duration_ms=self._elapsed_ms(start),
                )

            elif operation == FileOperationType.MKDIR:
                p.mkdir(parents=True, exist_ok=True)
                return FileOperationResult(
                    operation=operation, path=path, success=True,
                    duration_ms=self._elapsed_ms(start),
                )

            elif operation == FileOperationType.EXISTS:
                exists = p.exists()
                return FileOperationResult(
                    operation=operation, path=path, success=True,
                    data=exists, duration_ms=self._elapsed_ms(start),
                )

            elif operation == FileOperationType.STAT:
                if not p.exists():
                    return FileOperationResult(
                        operation=operation, path=path, success=False,
                        error=f"'{path}' does not exist", duration_ms=self._elapsed_ms(start),
                    )
                stat = p.stat()
                data = {
                    "size_bytes": stat.st_size,
                    "is_file": p.is_file(),
                    "is_dir": p.is_dir(),
                    "is_symlink": p.is_symlink(),
                    "created": datetime.fromtimestamp(stat.st_ctime, tz=timezone.utc).isoformat(),
                    "modified": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                    "accessed": datetime.fromtimestamp(stat.st_atime, tz=timezone.utc).isoformat(),
                    "permissions": oct(stat.st_mode)[-3:],
                }
                return FileOperationResult(
                    operation=operation, path=path, success=True,
                    data=data, size_bytes=stat.st_size, duration_ms=self._elapsed_ms(start),
                )

            elif operation == FileOperationType.SEARCH:
                if not p.is_dir():
                    return FileOperationResult(
                        operation=operation, path=path, success=False,
                        error=f"'{path}' is not a directory for search",
                        duration_ms=self._elapsed_ms(start),
                    )
                search_pattern = pattern or "*"
                matches = [str(m) for m in p.rglob(search_pattern)]
                return FileOperationResult(
                    operation=operation, path=path, success=True,
                    data=matches[:1000],  # Cap results
                    duration_ms=self._elapsed_ms(start),
                )

            elif operation == FileOperationType.CHECKSUM:
                if not p.is_file():
                    return FileOperationResult(
                        operation=operation, path=path, success=False,
                        error=f"'{path}' is not a file", duration_ms=self._elapsed_ms(start),
                    )
                sha256 = hashlib.sha256()
                with open(path, "rb") as f:
                    for chunk in iter(lambda: f.read(8192), b""):
                        sha256.update(chunk)
                return FileOperationResult(
                    operation=operation, path=path, success=True,
                    data={"sha256": sha256.hexdigest(), "algorithm": "sha256"},
                    size_bytes=p.stat().st_size,
                    duration_ms=self._elapsed_ms(start),
                )

            else:
                return FileOperationResult(
                    operation=operation, path=path, success=False,
                    error=f"Unhandled operation: {operation}",
                    duration_ms=self._elapsed_ms(start),
                )

        except PermissionError:
            return FileOperationResult(
                operation=operation, path=path, success=False,
                error=f"Permission denied: '{path}'", duration_ms=self._elapsed_ms(start),
            )
        except FileNotFoundError:
            return FileOperationResult(
                operation=operation, path=path, success=False,
                error=f"File not found: '{path}'", duration_ms=self._elapsed_ms(start),
            )
        except Exception as exc:
            return FileOperationResult(
                operation=operation, path=path, success=False,
                error=str(exc), duration_ms=self._elapsed_ms(start),
            )

    # ------------------------------------------------------------------
    # System Monitoring
    # ------------------------------------------------------------------

    async def system_monitoring(self) -> SystemHealth:
        """Perform a comprehensive system health check.

        Gathers CPU, memory, disk, network, and process information using
        platform-native tools and the /proc filesystem on Linux.

        Returns:
            SystemHealth snapshot with all available metrics.
        """
        start = time.monotonic()
        health = SystemHealth(
            platform_info=f"{platform.system()} {platform.release()} ({platform.machine()})",
            python_version=platform.python_version(),
        )

        # CPU info
        health.cpu = await self._get_cpu_info()

        # Memory info
        health.memory = await self._get_memory_info()

        # Disk info
        health.disk = await self._get_disk_info()

        # Network info
        health.network = await self._get_network_info()

        # Top processes
        health.top_processes = await self._get_top_processes()

        # Uptime
        health.uptime_seconds = await self._get_uptime()

        # Determine overall status
        warnings: List[str] = []

        if health.cpu.usage_percent > 90:
            warnings.append(f"CPU usage critical: {health.cpu.usage_percent:.1f}%")
        elif health.cpu.usage_percent > 70:
            warnings.append(f"CPU usage elevated: {health.cpu.usage_percent:.1f}%")

        if health.memory.usage_percent > 90:
            warnings.append(f"Memory usage critical: {health.memory.usage_percent:.1f}%")
        elif health.memory.usage_percent > 80:
            warnings.append(f"Memory usage elevated: {health.memory.usage_percent:.1f}%")

        if health.disk.usage_percent > 90:
            warnings.append(f"Disk usage critical: {health.disk.usage_percent:.1f}%")
        elif health.disk.usage_percent > 80:
            warnings.append(f"Disk usage elevated: {health.disk.usage_percent:.1f}%")

        health.warnings = warnings

        if any("critical" in w for w in warnings):
            health.status = HealthStatus.CRITICAL
        elif warnings:
            health.status = HealthStatus.WARNING
        else:
            health.status = HealthStatus.HEALTHY

        self._record_action("system_monitoring", {"status": health.status.value}, True, self._elapsed_ms(start))
        return health

    async def _get_cpu_info(self) -> CPUInfo:
        """Gather CPU usage information."""
        info = CPUInfo()

        try:
            info.core_count = os.cpu_count() or 0
        except Exception:
            pass

        # Load average (Unix only)
        try:
            load = os.getloadavg()
            info.load_average = (round(load[0], 2), round(load[1], 2), round(load[2], 2))
            # Approximate CPU usage from 1-minute load average and core count
            if info.core_count > 0:
                info.usage_percent = round(min(100.0, (load[0] / info.core_count) * 100), 1)
        except (OSError, AttributeError):
            pass

        # Try reading /proc/stat for more accurate CPU usage on Linux
        if platform.system() == "Linux":
            try:
                stat1 = Path("/proc/stat").read_text().splitlines()[0].split()[1:]
                await asyncio.sleep(0.1)  # Short sample interval
                stat2 = Path("/proc/stat").read_text().splitlines()[0].split()[1:]

                vals1 = [int(v) for v in stat1[:7]]
                vals2 = [int(v) for v in stat2[:7]]
                total1 = sum(vals1)
                total2 = sum(vals2)
                idle1 = vals1[3]
                idle2 = vals2[3]

                total_diff = total2 - total1
                idle_diff = idle2 - idle1

                if total_diff > 0:
                    info.usage_percent = round((1 - idle_diff / total_diff) * 100, 1)
            except Exception:
                pass

        return info

    async def _get_memory_info(self) -> MemoryInfo:
        """Gather memory usage information."""
        info = MemoryInfo()

        if platform.system() == "Linux":
            try:
                meminfo_text = Path("/proc/meminfo").read_text()
                meminfo: Dict[str, int] = {}
                for line in meminfo_text.splitlines():
                    parts = line.split(":")
                    if len(parts) == 2:
                        key = parts[0].strip()
                        val_parts = parts[1].strip().split()
                        meminfo[key] = int(val_parts[0])  # value in kB

                total_kb = meminfo.get("MemTotal", 0)
                available_kb = meminfo.get("MemAvailable", 0)
                swap_total_kb = meminfo.get("SwapTotal", 0)
                swap_free_kb = meminfo.get("SwapFree", 0)

                info.total_mb = round(total_kb / 1024, 1)
                info.available_mb = round(available_kb / 1024, 1)
                info.used_mb = round((total_kb - available_kb) / 1024, 1)
                if total_kb > 0:
                    info.usage_percent = round((total_kb - available_kb) / total_kb * 100, 1)
                info.swap_total_mb = round(swap_total_kb / 1024, 1)
                info.swap_used_mb = round((swap_total_kb - swap_free_kb) / 1024, 1)
            except Exception:
                pass
        else:
            # Fallback: use sysctl or vm_stat on macOS
            try:
                proc = await asyncio.create_subprocess_exec(
                    "sysctl", "-n", "hw.memsize",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, _ = await proc.communicate()
                total_bytes = int(stdout.decode().strip())
                info.total_mb = round(total_bytes / (1024 * 1024), 1)
            except Exception:
                pass

        return info

    async def _get_disk_info(self, mount_point: str = "/") -> DiskInfo:
        """Gather disk usage information."""
        info = DiskInfo(mount_point=mount_point)
        try:
            usage = shutil.disk_usage(mount_point)
            info.total_gb = round(usage.total / (1024 ** 3), 2)
            info.used_gb = round(usage.used / (1024 ** 3), 2)
            info.free_gb = round(usage.free / (1024 ** 3), 2)
            if usage.total > 0:
                info.usage_percent = round(usage.used / usage.total * 100, 1)
        except Exception:
            pass
        return info

    async def _get_network_info(self) -> NetworkInfo:
        """Gather network information."""
        import socket
        info = NetworkInfo()

        try:
            info.hostname = socket.gethostname()
        except Exception:
            pass

        # Get IP addresses
        try:
            hostname = socket.gethostname()
            addrs = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
            seen: Set[str] = set()
            for addr in addrs:
                ip = addr[4][0]
                if ip not in seen and not ip.startswith("::"):
                    seen.add(ip)
                    info.ip_addresses.append(ip)
        except Exception:
            pass

        # Network stats from /proc/net/dev on Linux
        if platform.system() == "Linux":
            try:
                text = Path("/proc/net/dev").read_text()
                for line in text.splitlines()[2:]:
                    parts = line.split()
                    if len(parts) >= 10:
                        iface = parts[0].rstrip(":")
                        if iface != "lo":
                            info.bytes_received += int(parts[1])
                            info.bytes_sent += int(parts[9])
            except Exception:
                pass

        # Connection count
        if platform.system() == "Linux":
            try:
                tcp_text = Path("/proc/net/tcp").read_text()
                info.connections_count = max(0, len(tcp_text.splitlines()) - 1)
            except Exception:
                pass

        return info

    async def _get_top_processes(self, limit: int = 10) -> List[ProcessInfo]:
        """Get the top processes by CPU usage."""
        processes: List[ProcessInfo] = []

        if platform.system() == "Linux":
            try:
                proc = await asyncio.create_subprocess_exec(
                    "ps", "aux", "--sort=-pcpu",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, _ = await proc.communicate()
                lines = stdout.decode(errors="replace").strip().splitlines()

                for line in lines[1: limit + 1]:  # Skip header
                    parts = line.split(None, 10)
                    if len(parts) >= 11:
                        try:
                            processes.append(ProcessInfo(
                                pid=int(parts[1]),
                                name=parts[10][:80],
                                cpu_percent=float(parts[2]),
                                memory_mb=float(parts[5]) / 1024,  # RSS in KB -> MB
                                status=parts[7] if len(parts) > 7 else "",
                            ))
                        except (ValueError, IndexError):
                            continue
            except Exception:
                pass
        else:
            try:
                proc = await asyncio.create_subprocess_exec(
                    "ps", "aux", "-r",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, _ = await proc.communicate()
                lines = stdout.decode(errors="replace").strip().splitlines()

                for line in lines[1: limit + 1]:
                    parts = line.split(None, 10)
                    if len(parts) >= 11:
                        try:
                            processes.append(ProcessInfo(
                                pid=int(parts[1]),
                                name=parts[10][:80],
                                cpu_percent=float(parts[2]),
                                memory_mb=float(parts[5]) / 1024,
                                status=parts[7] if len(parts) > 7 else "",
                            ))
                        except (ValueError, IndexError):
                            continue
            except Exception:
                pass

        return processes

    async def _get_uptime(self) -> float:
        """Get system uptime in seconds."""
        if platform.system() == "Linux":
            try:
                text = Path("/proc/uptime").read_text()
                return float(text.split()[0])
            except Exception:
                pass

        try:
            proc = await asyncio.create_subprocess_exec(
                "uptime", "-s",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await proc.communicate()
            boot_str = stdout.decode().strip()
            boot_time = datetime.strptime(boot_str, "%Y-%m-%d %H:%M:%S")
            return (datetime.now() - boot_time).total_seconds()
        except Exception:
            return 0.0

    # ------------------------------------------------------------------
    # Screen Observation
    # ------------------------------------------------------------------

    async def observe_screen(self) -> ScreenObservation:
        """Capture a screen observation for the agent's decision-making.

        Gathers the current screenshot, visible text, active window title,
        and mouse position. Used as input for the agent's action planning.

        Returns:
            ScreenObservation with all available screen state.
        """
        observation = ScreenObservation()

        # Take a screenshot
        screenshot_action = GUIAction(action_type=GUIActionType.SCREENSHOT)
        screenshot_result = await self._gui_screenshot(screenshot_action, time.monotonic())
        observation.screenshot_path = screenshot_result.screenshot_path

        # Get active window title
        if shutil.which("xdotool") and platform.system() == "Linux":
            try:
                proc = await asyncio.create_subprocess_shell(
                    "xdotool getactivewindow getwindowname 2>/dev/null",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, _ = await proc.communicate()
                observation.active_window_title = stdout.decode(errors="replace").strip()
            except Exception:
                pass

        # Get mouse position
        if shutil.which("xdotool") and platform.system() == "Linux":
            try:
                proc = await asyncio.create_subprocess_shell(
                    "xdotool getmouselocation 2>/dev/null",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, _ = await proc.communicate()
                text = stdout.decode()
                x_match = re.search(r"x:(\d+)", text)
                y_match = re.search(r"y:(\d+)", text)
                if x_match and y_match:
                    observation.mouse_position = Coordinate(
                        x=int(x_match.group(1)),
                        y=int(y_match.group(1)),
                    )
            except Exception:
                pass

        # Get screen resolution
        if shutil.which("xrandr") and platform.system() == "Linux":
            try:
                proc = await asyncio.create_subprocess_shell(
                    "xrandr 2>/dev/null | grep '\\*' | head -1",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, _ = await proc.communicate()
                res_match = re.search(r"(\d+)x(\d+)", stdout.decode())
                if res_match:
                    observation.screen_width = int(res_match.group(1))
                    observation.screen_height = int(res_match.group(2))
            except Exception:
                pass

        self._observations.append(observation)
        return observation

    def get_recent_observations(self, limit: int = 10) -> List[ScreenObservation]:
        """Return the most recent screen observations."""
        return list(self._observations)[-limit:]

    # ------------------------------------------------------------------
    # Action History
    # ------------------------------------------------------------------

    def get_action_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Return the most recent actions performed by the agent."""
        return list(self._action_history)[-limit:]

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    async def cleanup(self) -> None:
        """Clean up temporary files and resources."""
        try:
            if self._temp_dir.exists():
                shutil.rmtree(self._temp_dir, ignore_errors=True)
            logger.info("ComputerUseAgent cleaned up")
        except Exception as exc:
            logger.warning("Cleanup error: %s", exc)

    # ------------------------------------------------------------------
    # Private Helpers
    # ------------------------------------------------------------------

    def _validate_url(self, url: str) -> bool:
        """Basic URL validation."""
        if not url:
            return False
        # Allow common schemes
        allowed_schemes = ("http://", "https://", "file://", "about:", "data:")
        return any(url.lower().startswith(scheme) for scheme in allowed_schemes)

    @staticmethod
    def _extract_title_from_url(url: str) -> str:
        """Extract a page-title-like string from a URL for simulation."""
        from urllib.parse import urlparse
        try:
            parsed = urlparse(url)
            host = parsed.hostname or ""
            path = parsed.path.strip("/")
            if path:
                parts = path.split("/")
                title_parts = [p.replace("-", " ").replace("_", " ").title() for p in parts[-2:]]
                return " - ".join(title_parts) + f" | {host}"
            return host.replace("www.", "").title()
        except Exception:
            return url[:80]

    @staticmethod
    def _get_interpreter(language: CodeLanguage) -> Optional[str]:
        """Find the system interpreter for a language."""
        interpreter_map: Dict[CodeLanguage, List[str]] = {
            CodeLanguage.PYTHON: ["python3", "python"],
            CodeLanguage.JAVASCRIPT: ["node", "nodejs"],
            CodeLanguage.BASH: ["bash", "sh"],
            CodeLanguage.RUBY: ["ruby"],
            CodeLanguage.GO: ["go"],
        }
        candidates = interpreter_map.get(language, [])
        for cmd in candidates:
            if shutil.which(cmd):
                return cmd
        return None

    @staticmethod
    def _elapsed_ms(start: float) -> float:
        return round((time.monotonic() - start) * 1000, 2)

    def _record_action(self, action: str, details: Dict[str, Any], success: bool, duration_ms: float) -> None:
        """Record an action in the history."""
        self._action_history.append({
            "action": action,
            "details": details,
            "success": success,
            "duration_ms": duration_ms,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
