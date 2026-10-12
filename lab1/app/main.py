import os
import time
import random
import logging
from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse
from pythonjsonlogger import jsonlogger

# Инициализация Prometheus метрик
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP Requests', ['method', 'endpoint', 'http_status'])
ERROR_COUNT = Counter('http_errors_total', 'Total HTTP Errors', ['method', 'endpoint', 'http_status'])
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'HTTP Request Latency', ['method', 'endpoint'])

# Настройка OpenTelemetry для трейсинга
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

# Настраиваем трассировку
provider = TracerProvider()
processor = BatchSpanProcessor(OTLPSpanExporter(endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://jaeger:4317")))
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)
tracer = trace.get_tracer(__name__)

# Настройка структурированных JSON-логов
logger = logging.getLogger("service-logger")
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter('%(levelname)s %(message)s %(asctime)s')
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)

app = FastAPI()

# Middleware для сбора метрик RED и логирования trace_id
@app.middleware("http")
async def monitor_requests(request: Request, call_next):
    if request.url.path == "/metrics":
        return await call_next(request)
        
    start_time = time.time()
    method = request.method
    endpoint = request.url.path
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    status_code = str(response.status_code)
    
    # Записываем метрики
    REQUEST_COUNT.labels(method=method, endpoint=endpoint, http_status=status_code).inc()
    REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(duration)
    if response.status_code >= 500:
        ERROR_COUNT.labels(method=method, endpoint=endpoint, http_status=status_code).inc()
        
    # Извлекаем текущий trace_id для связывания логов и трейсов
    current_span = trace.get_current_span()
    trace_id = format(current_span.get_span_context().trace_id, '032x') if current_span else "0"
    
    logger.info("Request processed", extra={
        "trace_id": trace_id,
        "method": method,
        "endpoint": endpoint,
        "status": status_code,
        "duration": duration
    })
    
    return response

# Веб-интерфейс с кнопками для генерации событий
@app.get("/", response_class=HTMLResponse)
async def index():
    return """
    <html>
        <head><title>Monitoring Lab</title></head>
        <body style="font-family: Arial, sans-serif; text-align: center; margin-top: 50px;">
            <h1>Управление нагрузкой сервиса</h1>
            <div style="margin: 20px;"><button onclick="fetch('/error')" style="padding: 10px 20px; background-color: red; color: white; cursor: pointer;">Создать ошибку</button></div>
            <div style="margin: 20px;"><button onclick="fetch('/delay')" style="padding: 10px 20px; background-color: orange; color: white; cursor: pointer;">Создать задержку</button></div>
            <div style="margin: 20px;"><button onclick="fetch('/load')" style="padding: 10px 20px; background-color: green; color: white; cursor: pointer;">Нагрузка (RPS)</button></div>
            <p>Открой <a href="/metrics" target="_blank">/metrics</a> чтобы увидеть сырые метрики.</p>
        </body>
    </html>
    """

@app.get("/error")
async def make_error():
    current_span = trace.get_current_span()
    current_span.set_status(trace.StatusCode.ERROR, "Искусственная ошибка 500")
    logger.error("Спровоцирована ошибка 500", extra={
        "trace_id": format(current_span.get_span_context().trace_id, '032x')
    })
    return Response(content="Внутренняя ошибка сервера", status_code=500)

@app.get("/delay")
async def make_delay():
    # Создаем вложенный спан (slow-dependency) по требованию Части 4
    with tracer.start_as_current_span("slow-dependency") as child_span:
        sleep_time = random.uniform(1.0, 3.0)
        child_span.set_attribute("delay.duration_seconds", sleep_time)
        time.sleep(sleep_time)
    return {"status": "delayed", "sleep_time": sleep_time}

@app.get("/load")
async def make_load():
    # Имитируем пачку запросов для мгновенного скачка RPS
    for _ in range(20):
        REQUEST_COUNT.labels(method="GET", endpoint="/internal-load", http_status="200").inc()
    return {"status": "load_generated", "requests": 20}

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

# Автоматическое инструментирование входящих запросов
FastAPIInstrumentor.instrument_app(app)
