def setup_otel(app):
    """Optional OpenTelemetry hook. The runtime remains functional without telemetry extras."""
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        FastAPIInstrumentor.instrument_app(app)
        return True
    except Exception:
        return False
