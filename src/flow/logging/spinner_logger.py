import contextlib
import logging
import time
from typing import Optional, List

from rich.console import Console
from rich.progress import BarColumn
from rich.progress import Progress
from rich.progress import SpinnerColumn
from rich.progress import TextColumn


class SpinnerLogHandler(logging.Handler):
    """
    A custom logging handler that intercepts log records and displays them
    via an active SpinnerLogger progress if available. Otherwise, logs are
    buffered until a spinner is active.
    """

    def __init__(self, spinner_logger: "SpinnerLogger", level=logging.INFO):
        super().__init__(level=level)
        self.spinner_logger = spinner_logger

    def emit(self, record: logging.LogRecord) -> None:
        msg = self.format(record)
        self.spinner_logger.handle_external_log(msg, level=record.levelno)


class SpinnerLogger:
    """Provides fancy logging with spinners and progress displays."""

    def __init__(self, logger: logging.Logger, spinner_delay: float = 0.1):
        """Initializes the SpinnerLogger.

        Args:
            logger: A logger instance used for logging events.
            spinner_delay: The delay between spinner updates, in seconds.
        """
        self.logger = logger
        self.spinner_delay = spinner_delay
        self._spinner_active = False
        self._console: Optional[Console] = None
        self._progress: Optional[Progress] = None
        self._task_id: Optional[int] = None

        # Buffer logs when spinner isn't active
        self._log_buffer: List[str] = []

        # For ephemeral sub-steps
        self._sub_steps_enabled: bool = False
        self._sub_steps: List[str] = []

    def create_log_handler(self, level=logging.INFO) -> SpinnerLogHandler:
        """
        Creates and returns a custom log handler that can intercept logs and
        redirect them to this SpinnerLogger.
        """
        return SpinnerLogHandler(self, level=level)

    def handle_external_log(self, message: str, level: int = logging.INFO) -> None:
        """
        Handles external log messages from attached loggers.
        """
        if self._spinner_active and self._progress and self._task_id is not None:
            self.update_sub_step(message)
        else:
            self._log_buffer.append(message)

        # You can also record them as standard logs if you wish
        if level == logging.ERROR:
            self.logger.error(message)
        elif level == logging.WARNING:
            self.logger.warning(message)
        elif level == logging.DEBUG:
            self.logger.debug(message)
        else:
            self.logger.info(message)

    @contextlib.contextmanager
    def spinner(
        self,
        message: str,
        enable_sub_steps: bool = False,
        persist_messages: bool = True,
    ):
        """
        Context manager to display a spinner until exiting the context.

        Args:
            message: The message to display alongside the spinner.
            enable_sub_steps: If True, ephemeral logs become sub-steps.
            persist_messages: If True, sub-steps get logged again at the end.
        """
        if self._spinner_active:
            self.logger.debug("[spinner] Already active, reusing for: %s", message)
            self.update_text(message)
            yield
        else:
            self._spinner_active = True
            self._sub_steps_enabled = enable_sub_steps
            self._sub_steps.clear()
            self._console = Console()
            self._progress = Progress(
                SpinnerColumn(style="cyan"),
                TextColumn("[progress.description]{task.description}"),
                console=self._console,
                transient=True,
            )
            self._progress.start()
            self._task_id = self._progress.add_task(message, total=None)
            self.logger.info("[SPINNER START] %s", message)
            try:
                # Flush any buffered logs into sub-steps
                self._flush_buffer_to_spinner()
                yield
            finally:
                self._progress.update(self._task_id, total=1, completed=1)
                self._progress.stop()

                if persist_messages and self._sub_steps_enabled and self._sub_steps:
                    self.logger.info("--- Sub-steps for '%s' ---", message)
                    for step in self._sub_steps:
                        self.logger.info(" - %s", step)

                self.logger.info("[SPINNER END] %s", message)
                self._spinner_active = False
                self._sub_steps_enabled = False
                self._console = None
                self._progress = None
                self._task_id = None

    def _flush_buffer_to_spinner(self):
        for msg in self._log_buffer:
            self.update_sub_step(msg)
        self._log_buffer.clear()

    def update_text(self, message: str):
        """Updates the spinner text, or logs a message if no spinner is active.

        Args:
            message: The new message to display for the spinner.
        """
        if self._spinner_active and self._progress and self._task_id is not None:
            self._progress.update(self._task_id, description=message)
        self.logger.info("[SPINNER] %s", message)

    def update_sub_step(self, message: str):
        """Appends a sub-step or ephemeral message under the spinner."""
        if self._sub_steps_enabled:
            self._sub_steps.append(message)
        if self._progress and self._task_id is not None:
            self._progress.console.log(f"[sub-step] {message}")

    def progress_bar(self, message: str, total: int):
        """Displays a basic progress bar for multi-step tasks.

        Args:
            message: A description of the current progress being shown.
            total: The total number of steps in the task.
        """
        console = Console()
        with Progress(
            SpinnerColumn(style="green"),
            BarColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            task_id = progress.add_task(message, total=total)
            for i in range(total):
                time.sleep(0.1)  # Simulate work
                progress.update(task_id, advance=1)
                self.logger.info("[PROGRESS] Step %d/%d", i + 1, total)
            self.logger.info("[PROGRESS END] %s", message)

    def notify(self, message: str):
        """Logs a simple text notification.

        In a real implementation, this could add additional formatting, color, or
        ASCII art.

        Args:
            message: The notification message to log.
        """
        self.logger.info("[NOTIFY] %s", message)
