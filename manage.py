#!/home/skerdi/.pyenv/versions/3.9.10/envs/venv/bin/python3
"""Django's command-line utility for administrative tasks."""
import os
import sys

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.django import DjangoInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


def main():
    """Run administrative tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bankgreen.settings")

    OTLP_GRPC_ENDPOINT = os.environ.get("OTLP_GRPC_ENDPOINT", "http://localhost:4317")

    resource = Resource(attributes={"service.name": "bank_green_django"})

    tracer = TracerProvider(resource=resource)
    trace.set_tracer_provider(tracer)

    otlp_exporter = OTLPSpanExporter(endpoint=OTLP_GRPC_ENDPOINT, insecure=True)
    span_processor = BatchSpanProcessor(otlp_exporter)

    trace.get_tracer_provider().add_span_processor(span_processor)

    DjangoInstrumentor().instrument(tracer_provider=tracer)

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
