import datetime
import logging
from typing import List

from rich.table import Table

from .base_formatter import Formatter
from ..models.instance import Instance
from flow.models import Bid

DEFAULT_NUM = 5  # TODO(jaredquincy): Temporary default number for maximum rows.


class TableFormatter(Formatter):
    """
    Formatter for displaying status information in a table format.

    Attributes:
        max_rows (int): The maximum number of items (bids or instances) to display.
    """

    def __init__(self, max_rows: int = DEFAULT_NUM) -> None:
        """
        Initialize the TableFormatter with a specified maximum number of rows.

        Args:
            max_rows: The maximum number of rows to display for bids/instances.
        """
        super().__init__()
        self.max_rows = max_rows
        self.logger = logging.getLogger(__name__)
        self.logger.debug("TableFormatter initialized with max_rows=%d", max_rows)

    def format_status(self, bids: List[Bid], instances: List[Instance]) -> None:
        """
        Format and print bid and instance information to the console.

        Args:
            bids: A list of Bid objects.
            instances: A list of Instance objects.
        """
        self.logger.info(
            "Formatting status for %d bids and %d instances.", len(bids), len(instances)
        )
        self.format_bids(bids)
        self.format_instances(instances)

    def format_bids(self, bids: List[Bid]) -> None:
        """
        Format and print a table of bids to the console.

        Args:
            bids: A list of Bid objects.
        """
        if not bids:
            self.logger.info("No bids found to display.")
            self.console.print("\n \n No bids found.", style="bold yellow")
            return

        table = Table(
            title="Current Bids",
            title_style="bold",
            header_style="bold",
            border_style="dim",
        )
        table.add_column("Name", style="cyan")
        table.add_column("Type", style="green")
        table.add_column("Quantity", style="blue")
        table.add_column("Created", style="magenta")
        # table.add_column("Region", style="yellow") # TODO(jaredquincy): Add region to table.
        table.add_column("Status", style="red")

        displayed_bids = bids[: self.max_rows]

        for bid in displayed_bids:
            quantity_str = (
                str(bid.instance_quantity)
                if bid.instance_quantity is not None
                else "N/A"
            )
            created_str = bid.created_at or "N/A"
            # NEW: Pull region if available; fallback to "N/A"
            region_str = getattr(bid, "region", "N/A") or "N/A"

            table.add_row(
                bid.name or "N/A",
                bid.instance_type_id or "N/A",
                quantity_str,
                created_str,
                # region_str, # TODO(jaredquincy): Add region to table.
                bid.status or "N/A",
            )

        self.logger.debug("Displaying %d bid rows.", len(displayed_bids))
        self.console.print(table)

    def format_instances(self, instances: List[Instance]) -> None:
        """
        Format and print a table of instances to the console.

        Args:
            instances: A list of Instance objects.
        """
        if not instances:
            self.logger.info("No instances found to display.")
            self.console.print("No instances found.", style="bold yellow")
            return

        def _get_start_date(instance: Instance) -> datetime.datetime:
            """
            Safely retrieve the instance's start date or a minimum datetime if missing.

            Args:
                instance: The Instance object to retrieve the start date from.

            Returns:
                A datetime object representing the start date or datetime.min if none is available.
            """
            return instance.start_date or datetime.datetime.min

        # Sort instances by newest start date first
        instances_sorted = sorted(instances, key=_get_start_date, reverse=True)
        displayed_instances = instances_sorted[: self.max_rows]

        table = Table(
            title="Current Instances",
            title_style="bold",
            header_style="bold",
            border_style="dim",
        )
        table.add_column("Name", style="cyan")
        table.add_column("Type", style="green")
        table.add_column("Status", style="magenta")
        table.add_column("Created", style="blue")
        # table.add_column("Region", style="yellow") # TODO(jaredquincy): Add region to table.
        table.add_column("IP Address", style="cyan")
        table.add_column("Category", style="green")

        for instance in displayed_instances:
            if instance.start_date:
                created_str = instance.start_date.strftime("%Y-%m-%d %H:%M:%S")
            else:
                created_str = "N/A"

            table.add_row(
                instance.name or "N/A",
                getattr(instance, "instance_type_id", "Unknown") or "Unknown",
                instance.instance_status or "N/A",
                created_str,
                # getattr(instance, "region", "Unknown") or "Unknown", # TODO(jaredquincy): Add region to table.
                getattr(instance, "ip_address", "...") or "...",
                getattr(instance, "category", "N/A") or "N/A",
            )

        self.logger.debug("Displaying %d instance rows.", len(displayed_instances))
        self.console.print(table)
