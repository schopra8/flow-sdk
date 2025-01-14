from typing import List

from flow.task_config.config_parser import Port


def parse_ports(port_list: List[Port]) -> List[int]:
    """Parses a list of Port objects into integer port numbers.

    Args:
        port_list: A list of Port objects to parse.

    Returns:
        A list of integer port numbers extracted from the Port objects.

    Raises:
        ValueError: If an invalid port value or range is encountered.
    """
    parsed_ports: List[int] = []
    for port_item in port_list:
        port_value = port_item.port
        if isinstance(port_value, int):
            parsed_ports.append(port_value)
        elif isinstance(port_value, str):
            if "-" in port_value:
                try:
                    start_port_str, end_port_str = port_value.split("-")
                    start_port = int(start_port_str.strip())
                    end_port = int(end_port_str.strip())
                    if start_port > end_port:
                        raise ValueError(
                            f"Invalid port range: {port_value} "
                            "(start port is greater than end port)"
                        )
                    parsed_ports.extend(range(start_port, end_port + 1))
                except ValueError as exc:
                    raise ValueError(f"Invalid port range: {port_value}") from exc
            else:
                try:
                    parsed_ports.append(int(port_value.strip()))
                except ValueError as exc:
                    raise ValueError(f"Invalid port value: {port_value}") from exc
        else:
            raise ValueError(f"Invalid port value: {port_value}")
    return parsed_ports
