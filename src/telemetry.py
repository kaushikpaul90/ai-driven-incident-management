import os
import logging

from azure.monitor.opentelemetry import configure_azure_monitor

_telemetry_initialized = False


def setup_telemetry():

    global _telemetry_initialized

    if _telemetry_initialized:
        return

    connection_string = os.getenv(
        "APPLICATIONINSIGHTS_CONNECTION_STRING"
    )

    if connection_string:

        configure_azure_monitor(
            connection_string=connection_string
        )

        logging.info(
            "Azure Application Insights initialized"
        )

        _telemetry_initialized = True