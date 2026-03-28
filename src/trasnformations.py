import os
import textwrap
# ─────────────────────────────────────────────
# T1 — Presentation
# ─────────────────────────────────────────────
def generate_web_interface(name):
    path = f'skeleton/{name}'
    os.makedirs(path, exist_ok=True)

    # index.html
    with open(os.path.join(path, 'index.html'), 'w') as f:
        f.write(textwrap.dedent(f"""
            <!DOCTYPE html>
            <html>
            <head><title>{name} — Passenger Portal</title></head>
            <body>
                <h1>ERTMS Passenger Portal</h1>
                <p>Component: {name}</p>
            </body>
            </html>
        """))

    # Dockerfile
    with open(os.path.join(path, 'Dockerfile'), 'w') as f:
        f.write(textwrap.dedent("""
            FROM nginx:alpine
            COPY index.html /usr/share/nginx/html/index.html
        """))


def generate_operator_ui(name):
    path = f'skeleton/{name}'
    os.makedirs(path, exist_ok=True)

    # dashboard.html
    with open(os.path.join(path, 'dashboard.html'), 'w') as f:
        f.write(textwrap.dedent(f"""
            <!DOCTYPE html>
            <html>
            <head><title>{name} — Operator Dashboard</title></head>
            <body>
                <h1>ERTMS Operator Dashboard</h1>
                <p>Component: {name}</p>
                <p>Status: Monitoring active routes...</p>
            </body>
            </html>
        """))

    # Dockerfile
    with open(os.path.join(path, 'Dockerfile'), 'w') as f:
        f.write(textwrap.dedent("""
            FROM nginx:alpine
            COPY dashboard.html /usr/share/nginx/html/index.html
        """))


def generate_driver_ui(name):
    path = f'skeleton/{name}'
    os.makedirs(path, exist_ok=True)

    # driver.html
    with open(os.path.join(path, 'driver.html'), 'w') as f:
        f.write(textwrap.dedent(f"""
            <!DOCTYPE html>
            <html>
            <head><title>{name} — Driver Interface</title></head>
            <body>
                <h1>ERTMS Driver Interface</h1>
                <p>Component: {name}</p>
                <p>Movement Authority: PENDING</p>
            </body>
            </html>
        """))

    # Dockerfile
    with open(os.path.join(path, 'Dockerfile'), 'w') as f:
        f.write(textwrap.dedent("""
            FROM nginx:alpine
            COPY driver.html /usr/share/nginx/html/index.html
        """))
# ─────────────────────────────────────────────
# T2 — Communication
# ─────────────────────────────────────────────
def generate_api_gateway(name):
    path = f'skeleton/{name}'
    os.makedirs(path, exist_ok=True)

    # app.py
    with open(os.path.join(path, 'app.py'), 'w') as f:
        f.write(textwrap.dedent(f"""
            from flask import Flask, request, jsonify
            import requests

            app = Flask(__name__)

            ROUTES = {{
                '/passengers': 'http://passengers-ms:80',
                '/routes': 'http://routes-ms:80',
                '/trains': 'http://trains-ms:80',
                '/position': 'http://position-time-ms:80',
                '/tickets': 'http://tickets-ms:80',
                '/authority': 'http://mas:80',
            }}

            @app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
            def gateway(path):
                for prefix, target in ROUTES.items():
                    if ('/' + path).startswith(prefix):
                        url = target + '/' + path
                        resp = requests.request(
                            method=request.method,
                            url=url,
                            json=request.get_json(silent=True)
                        )
                        return jsonify(resp.json()), resp.status_code

                return jsonify(error='Route not found'), 404

            if __name__ == '__main__':
                app.run(host='0.0.0.0', port=80)
        """))

    # Dockerfile
    with open(os.path.join(path, 'Dockerfile'), 'w') as f:
        f.write(textwrap.dedent("""
            FROM python:3.11-slim
            WORKDIR /app
            COPY . .
            RUN pip install flask requests
            CMD ["python", "app.py"]
        """))
# ─────────────────────────────────────────────
# T3 — Logic
# ─────────────────────────────────────────────
def generate_microservice(name, database=None):
    path = f'skeleton/{name}'
    os.makedirs(path, exist_ok=True)

    db_host = database if database else f'{name}-db'

    # app.py
    with open(os.path.join(path, 'app.py'), 'w') as f:
        f.write(textwrap.dedent(f"""
            from flask import Flask, jsonify, request
            import mysql.connector

            app = Flask(__name__)

            def get_conn():
                return mysql.connector.connect(
                    host='{db_host}',
                    user='root',
                    password='root',
                    database='{db_host}'
                )

            @app.route('/health')
            def health():
                return jsonify(status='ok', service='{name}')

            @app.route('/records')
            def get_records():
                conn = get_conn()
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM records")
                rows = cursor.fetchall()
                cursor.close()
                conn.close()
                return jsonify(records=rows)

            @app.route('/records', methods=['POST'])
            def create_record():
                data = request.json
                conn = get_conn()
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO records (name) VALUES (%s)",
                    (data.get('name', 'unknown'),)
                )
                conn.commit()
                cursor.close()
                conn.close()
                return jsonify(status='created'), 201

            if __name__ == '__main__':
                app.run(host='0.0.0.0', port=80)
        """))

    # Dockerfile
    with open(os.path.join(path, 'Dockerfile'), 'w') as f:
        f.write(textwrap.dedent("""
            FROM python:3.11-slim
            WORKDIR /app
            COPY . .
            RUN pip install flask mysql-connector-python
            CMD ["python", "app.py"]
        """))


def generate_authority_service(name):
    path = f'skeleton/{name}'
    os.makedirs(path, exist_ok=True)

    # app.py
    with open(os.path.join(path, 'app.py'), 'w') as f:
        f.write(textwrap.dedent(f"""
            from flask import Flask, jsonify, request

            app = Flask(__name__)

            @app.route('/health')
            def health():
                return jsonify(status='ok', service='{name}')

            @app.route('/authority', methods=['POST'])
            def request_authority():
                data = request.json
                train_id = data.get('train_id')
                corridor = data.get('corridor')

                # Placeholder: real logic would query position-time-ms and routes-ms
                granted = True

                return jsonify(
                    train_id=train_id,
                    corridor=corridor,
                    movement_authority='GRANTED' if granted else 'DENIED'
                )

            if __name__ == '__main__':
                app.run(host='0.0.0.0', port=80)
        """))

    # Dockerfile
    with open(os.path.join(path, 'Dockerfile'), 'w') as f:
        f.write(textwrap.dedent("""
            FROM python:3.11-slim
            WORKDIR /app
            COPY . .
            RUN pip install flask
            CMD ["python", "app.py"]
        """))

# ─────────────────────────────────────────────
# T4 — Data
# ─────────────────────────────────────────────
def generate_database(name):
    path = f'skeleton/{name}'
    os.makedirs(path, exist_ok=True)

    with open(os.path.join(path, 'init.sql'), 'w') as f:
        f.write(textwrap.dedent(f"""
            CREATE TABLE IF NOT EXISTS records (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL
            );
        """))


def generate_data_lake(name):
    path = f'skeleton/{name}'
    os.makedirs(path, exist_ok=True)

    # README con descripción del Data Lake
    with open(os.path.join(path, 'README.md'), 'w') as f:
        f.write(textwrap.dedent(f"""
            # {name} — ERTMS Data Lake
            Aggregated operational and historical data lake.

            ## Schemas
            - operational/ : real-time ingestion from position-time-ms
            - historical/ : archived train movement records
            - audit/ : movement authority logs
        """))

    # Script de ingestión
    with open(os.path.join(path, 'ingest.py'), 'w') as f:
        f.write(textwrap.dedent(f"""
            # Placeholder ingestion script for the ERTMS Data Lake ({name})

            import json
            import datetime

            def ingest(event: dict):
                record = {{
                    'timestamp': datetime.datetime.utcnow().isoformat(),
                    'payload': event
                }}
                print(json.dumps(record))

            if __name__ == '__main__':
                ingest({{
                    'train_id': 'T-001',
                    'position': '48.8566,2.3522',
                    'speed_kmh': 220
                }})
        """))

# ─────────────────────────────────────────────
# T5 — Physical
# ─────────────────────────────────────────────
def generate_onboard_unit(name):
    path = f'skeleton/{name}'
    os.makedirs(path, exist_ok=True)

    with open(os.path.join(path, 'obu.py'), 'w') as f:
        f.write(textwrap.dedent(f"""
            # Onboard Unit ({name}) — ERTMS T5
            # Simulates the main computing unit aboard the train.

            import time
            import random

            def read_sensors():
                return {{
                    'speed_kmh': round(random.uniform(0, 300), 1),
                    'position': f"{{random.uniform(40, 55):.4f}}, {{random.uniform(-5, 25):.4f}}"
                }}

            def send_to_ground(data):
                print(f'[OBU {name}] Sending to ground control: {{data}}')

            def receive_command(cmd):
                print(f'[OBU {name}] Command received: {{cmd}}')
                if cmd.get('action') == 'BRAKE':
                    apply_brake(cmd.get('intensity', 1.0))

            def apply_brake(intensity):
                print(f'[OBU {name}] Applying brake at intensity {{intensity}}')

            if __name__ == '__main__':
                while True:
                    data = read_sensors()
                    send_to_ground(data)
                    time.sleep(1)
        """))

def generate_sensor(name):
    path = f'skeleton/{name}'
    os.makedirs(path, exist_ok=True)

    with open(os.path.join(path, 'sensor.py'), 'w') as f:
        f.write(textwrap.dedent(f"""
            # Train Sensor ({name}) — ERTMS T5
            # Simulates speed, position, and physical condition detection.

            import random
            import time

            def read():
                return {{
                    'speed_kmh': round(random.uniform(0, 300), 1),
                    'position': f"{{random.uniform(40, 55):.4f}}, {{random.uniform(-5, 25):.4f}}",
                    'door_closed': random.choice([True, True, True, False]),
                    'pantograph': 'UP'
                }}

            if __name__ == '__main__':
                while True:
                    print(f'[SENSOR {name}]', read())
                    time.sleep(0.5)
        """))

import time, random

import random
import time

def read():
    return {
        'speed_kmh': round(random.uniform(0, 300), 1),
        'position': f"{random.uniform(40, 55):.4f}, {random.uniform(-5, 25):.4f}",
        'door_closed': random.choice([True, True, True, False]),
        'pantograph': 'UP'
    }

if __name__ == '__main__':
    name = "SENSOR-01"  # puedes parametrizar este valor
    while True:
        print(f'[SENSOR {name}]', read())
        time.sleep(0.5)

def generate_actuator(name):
    path = f'skeleton/{name}'
    os.makedirs(path, exist_ok=True)

    with open(os.path.join(path, 'actuator.py'), 'w') as f:
        f.write(textwrap.dedent(f"""
            # Brake Actuator ({name}) — ERTMS T5
            # Receives control commands and acts on the physical train.

            def execute(command):
                action = command.get('action')
                intensity = command.get('intensity', 1.0)

                if action == 'BRAKE':
                    print(f'[ACTUATOR {name}] Emergency brake — intensity {{intensity}}')
                elif action == 'RELEASE':
                    print(f'[ACTUATOR {name}] Brake released')
                else:
                    print(f'[ACTUATOR {name}] Unknown command: {{action}}')

            if __name__ == '__main__':
                execute({{'action': 'BRAKE', 'intensity': 0.8}})
        """))

def generate_balise(name):
    path = f'skeleton/{name}'
    os.makedirs(path, exist_ok=True)

    with open(os.path.join(path, 'balise.py'), 'w') as f:
        f.write(textwrap.dedent(f"""
            # Balise ({name}) — ERTMS T5
            # Track-side transponder transmitting position reference data to passing trains.

            BALISE_ID = '{name}'
            POSITION_M = 12500  # metres from reference point

            def transmit():
                return {{
                    'balise_id': BALISE_ID,
                    'position_m': POSITION_M,
                    'track_id': 'CORRIDOR-A',
                    'signal': 'EUROBALISE-STM'
                }}

            if __name__ == '__main__':
                print('[BALISE]', transmit())
        """))

# ─────────────────────────────────────────────
# docker-compose
# ─────────────────────────────────────────────
TIER_ORDER = {
'data': 0,
'physical': 1,
'logic': 2,
'communication':3,
'presentation': 4,
}
DB_IMAGES = {'database', 'data_lake'}

def generate_docker_compose(components):
    """components: { name: (tier, type) }"""
    path = 'skeleton/'
    os.makedirs(path, exist_ok=True)

    sorted_items = sorted(
        components.items(),
        key=lambda kv: TIER_ORDER.get(kv[1][0], 5)
    )

    db_names = [n for n, (t, ct) in sorted_items if ct == 'database']

    with open(os.path.join(path, 'docker-compose.yml'), 'w') as f:
        f.write("services:\n")

        for i, (name, (tier, ctype)) in enumerate(sorted_items):
            port = 8000 + i
            f.write(f"  {name}:\n")

            if ctype == 'database':
                f.write("    image: mysql:8\n")
                f.write("    environment:\n")
                f.write("      - MYSQL_ROOT_PASSWORD=root\n")
                f.write(f"      - MYSQL_DATABASE={name}\n")
                f.write("    volumes:\n")
                f.write(f"      - ./{name}/init.sql:/docker-entrypoint-initdb.d/init.sql\n")
                f.write("    ports:\n")
                f.write("      - '3306:3306'\n")

            elif ctype == 'data_lake':
                f.write("    image: python:3.11-slim\n")
                f.write(f"    volumes:\n      - ./{name}:/app\n")
                f.write("    working_dir: /app\n")
                f.write("    command: python ingest.py\n")

            elif ctype in {'onboard_unit', 'sensor', 'actuator', 'balise'}:
                f.write("    image: python:3.11-slim\n")
                script = {
                    'onboard_unit': 'obu.py',
                    'sensor': 'sensor.py',
                    'actuator': 'actuator.py',
                    'balise': 'balise.py',
                }[ctype]
                f.write(f"    volumes:\n      - ./{name}:/app\n")
                f.write("    working_dir: /app\n")
                f.write(f"    command: python {script}\n")

            else:
                # microservice, api_gateway, authority_service, web UIs
                f.write(f"    build: ./{name}\n")
                f.write(f"    ports:\n      - '{port}:80'\n")

                if ctype == 'microservice' and db_names:
                    f.write("    depends_on:\n")
                    for db in db_names:
                        f.write(f"      - {db}\n")

        f.write("\nnetworks:\n  default:\n    driver: bridge\n")
# ─────────────────────────────────────────────
# Dispatcher
# ─────────────────────────────────────────────
GENERATORS = {
'web_interface': generate_web_interface,
'operator_ui': generate_operator_ui,
'driver_ui': generate_driver_ui,
'api_gateway': generate_api_gateway,
'microservice': generate_microservice,
'authority_service':generate_authority_service,
'database': generate_database,
'data_lake': generate_data_lake,
'onboard_unit': generate_onboard_unit,
'sensor': generate_sensor,
'actuator': generate_actuator,
'balise': generate_balise,
}

def apply_transformations(model):
    components = {}  # name -> (tier, type)
    db_map = {}      # microservice_name -> database_name (heuristic: shared prefix)

    # First pass: collect all components
    for e in model.elements:
        if e.__class__.__name__ == 'Component':
            components[e.name] = (e.tier, e.type)

    # Second pass: link microservices to their databases by name prefix
    db_names = [n for n, (t, ct) in components.items() if ct == 'database']
    for name, (tier, ctype) in components.items():
        if ctype == 'microservice':
            for db in db_names:
                if db.replace('-db', '').replace('_db', '') in name:
                    db_map[name] = db
                    break

    # Generate skeletons
    for name, (tier, ctype) in components.items():
        gen = GENERATORS.get(ctype)
        if gen:
            if ctype == 'microservice':
                gen(name, database=db_map.get(name))
            else:
                gen(name)

    generate_docker_compose(components)