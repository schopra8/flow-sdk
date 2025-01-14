import logging
from pathlib import Path
from typing import Dict, Generator, Optional, Type

import pytest

from flow.task_config.config_parser import ConfigModel, ConfigParser, ConfigParserError

logger = logging.getLogger(__name__)


@pytest.fixture(scope="module")
def test_configs(
    tmp_path_factory: pytest.TempPathFactory,
) -> Generator[Dict[str, Path], None, None]:
    """Generates test configuration files.

    Args:
        tmp_path_factory (pytest.TempPathFactory): Pytest fixture for creating a
            temporary directory.

    Yields:
        Dict[str, Path]: A dictionary mapping configuration file names to their
            respective paths.
    """
    logger.info("Setting up test configuration files.")
    configs: Dict[str, str] = {
        "valid.yaml": """
            name: flow-task
            task_management:
              num_instances: 1
              priority: standard
              utility_threshold_price: 4.24
            resources_specification:
              fcp_instance: fh1.ultra
              num_instances: 1
              gpu_type: h100-80gb
              num_gpus: 8
              intranode_interconnect: SXM
              internode_interconnect: 3200_IB
            ports:
              - 8080
              - 6006-6010
            ephemeral_storage_config:
              type: copy
              mounts:
                /remote/data_directory_name: /local/data_directory_name
                /remote/checkpoints_directory_name: /local/checkpoints_directory_name
            persistent_storage:
              mount_dir: /mount/dir/path
              attach:
                volume_name: my_volume
                region_id: us-west-2
              create:
                volume_name: new_volume
                region_id: us-west-2
                disk_interface: block
                size: 1000
            networking:
              dc_network_class: hi
            resources:
              vCPU: 16
              RAM: 64
            startup_script: |
              #!/bin/bash
              echo "Starting setup..."
              pip install -r requirements.txt
              echo "Setup complete."
            """,
        "missing_optional_fields.yaml": """
            name: flow-task
            resources_specification:
              fcp_instance: fh1.ultra
            startup_script: |
              #!/bin/bash
              echo "Starting setup..."
            """,
        "missing_required_fields.yaml": """
            task_management:
              priority: standard
            """,
        "invalid_data_types.yaml": """
            name: invalid-task
            task_management:
              num_instances: "three"  # Invalid data, should be an integer
            resources_specification:
              fcp_instance: "fh1.ultra"
            """,
        "malformed.yaml": """
            name flow-task
            task_management
              priority: standard
            """,
    }

    tmp_dir = tmp_path_factory.mktemp("configs")
    file_paths: Dict[str, Path] = {}

    for filename, content in configs.items():
        file_path = tmp_dir / filename
        with open(file_path, "w", encoding="utf-8") as file_handle:
            file_handle.write(content)
        file_paths[filename] = file_path

    yield file_paths


@pytest.mark.parametrize(
    "filename, expected_exception, expected_message",
    [
        ("valid.yaml", None, None),
        ("missing_required_fields.yaml", ConfigParserError, "name: Field required"),
        (
            "invalid_data_types.yaml",
            ConfigParserError,
            (
                "task_management -> num_instances: Input should be a valid integer, "
                "unable to parse string as an integer"
            ),
        ),
        ("malformed.yaml", ConfigParserError, "Failed to read configuration file"),
    ],
)
def test_config_parser(
    test_configs: Dict[str, Path],
    filename: str,
    expected_exception: Optional[Type[Exception]],
    expected_message: Optional[str],
) -> None:
    """Tests the ConfigParser against various configuration files.

    Args:
        test_configs (Dict[str, Path]): Dictionary mapping config filenames to their
            paths.
        filename (str): The name of the configuration file to test.
        expected_exception (Optional[Type[Exception]]): The expected exception type.
        expected_message (Optional[str]): The expected error message substring.
    """
    logger.info("Testing ConfigParser with file: %s", filename)
    file_path = test_configs[filename]
    if expected_exception:
        with pytest.raises(expected_exception) as exc_info:
            ConfigParser(str(file_path))
        assert expected_message in str(exc_info.value)
        logger.info("Expected exception occurred: %s", exc_info.value)
    else:
        parser = ConfigParser(str(file_path))
        assert isinstance(parser.config, ConfigModel)
        logger.info("ConfigParser successfully parsed the configuration.")


def test_getter_methods(test_configs: Dict[str, Path]) -> None:
    """Tests the getter methods of ConfigParser.

    Args:
        test_configs (Dict[str, Path]): Dictionary mapping config filenames to their
            paths.
    """
    logger.info("Testing getter methods.")
    file_path = test_configs["valid.yaml"]
    parser = ConfigParser(str(file_path))

    assert parser.get_task_name() == "flow-task"
    assert parser.get_task_management().priority == "standard"
    assert parser.get_task_management().utility_threshold_price == 4.24
    assert parser.get_task_management().num_instances == 1

    assert parser.get_resources_specification().fcp_instance == "fh1.ultra"
    assert parser.get_resources_specification().num_instances == 1

    assert len(parser.get_ports()) == 2
    port0 = parser.get_ports()[0]
    port1 = parser.get_ports()[1]
    assert port0.external == 8080
    assert port0.internal == 8080
    assert port1.external == "6006-6010"
    assert port1.internal == "6006-6010"

    assert parser.get_ephemeral_storage_config() is not None
    assert parser.get_persistent_storage() is not None
    assert parser.get_networking() is not None
    assert parser.get_resources() is not None
    assert 'echo "Starting setup..."' in parser.get_startup_script()

    logger.info("Getter methods returned correct values.")


def test_missing_optional_fields(test_configs: Dict[str, Path]) -> None:
    """Tests handling of missing optional fields in the configuration.

    Args:
        test_configs (Dict[str, Path]): Dictionary mapping config filenames to their
            paths.
    """
    logger.info("Testing missing optional fields.")
    file_path = test_configs["missing_optional_fields.yaml"]
    parser = ConfigParser(str(file_path))

    assert parser.get_task_name() == "flow-task"
    assert parser.get_task_management() is None
    assert parser.get_resources_specification().fcp_instance == "fh1.ultra"
    assert parser.get_ports() == []
    assert parser.get_ephemeral_storage_config() is None
    assert parser.get_persistent_storage() is None
    assert parser.get_networking() is None
    assert parser.get_resources() is None
    assert 'echo "Starting setup..."' in parser.get_startup_script()

    logger.info("Missing optional fields handled correctly.")


def test_validate_config_valid(test_configs: Dict[str, Path]) -> None:
    """Tests that a valid configuration file is validated successfully.

    Args:
        test_configs (Dict[str, Path]): Dictionary mapping config filenames to their
            paths.
    """
    logger.info("Testing validate_config with a valid configuration.")
    file_path = test_configs["valid.yaml"]
    parser = ConfigParser(str(file_path))
    assert isinstance(parser.config, ConfigModel)
    logger.info("Configuration validation passed.")


def test_validate_config_missing_required_fields(test_configs: Dict[str, Path]) -> None:
    """Tests validation failure for missing required fields in the configuration.

    Args:
        test_configs (Dict[str, Path]): Dictionary mapping config filenames to their
            paths.
    """
    logger.info("Testing validate_config with missing required fields.")
    file_path = test_configs["missing_required_fields.yaml"]
    with pytest.raises(ConfigParserError) as exc_info:
        ConfigParser(str(file_path))
    assert "name: Field required" in str(exc_info.value)
    logger.info("Validation correctly failed for missing required fields.")


def test_validate_config_invalid_data_types(test_configs: Dict[str, Path]) -> None:
    """Tests validation failure due to invalid data types in the configuration.

    Args:
        test_configs (Dict[str, Path]): Dictionary mapping config filenames to their
            paths.
    """
    logger.info("Testing validate_config with invalid data types.")
    file_path = test_configs["invalid_data_types.yaml"]
    with pytest.raises(ConfigParserError) as exc_info:
        ConfigParser(str(file_path))
    assert (
        "task_management -> num_instances: Input should be a valid integer, "
        "unable to parse string as an integer" in str(exc_info.value)
    )
    logger.info("Validation correctly failed for invalid data types.")
