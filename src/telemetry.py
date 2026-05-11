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

    if not connection_string:
        print("Application Insights connection string not found.")
        return

    configure_azure_monitor(
        connection_string=connection_string
    )

    logging.basicConfig(level=logging.INFO)

    _telemetry_initialized = True

    print("Application Insights telemetry initialized.")