# STAGE 1: Builder
FROM odoo:18.0 AS builder

USER root

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    pkg-config \
    libcairo2-dev \
    libgirepository1.0-dev \
    libdbus-1-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /etc/odoo/

# Build wheels to a temporary directory
RUN pip3 wheel --no-cache-dir --wheel-dir=/wheels -r /etc/odoo/requirements.txt


# STAGE 2: Final
FROM odoo:18.0

USER root

# Install runtime dependencies only
# libcairo2 differs from libcairo2-dev (headers vs lib)
# libgirepository-1.0-1 is needed for PyGObject
# libdbus-1-3 is runtime for dbus
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libcairo2 \
    libgirepository-1.0-1 \
    libdbus-1-3 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /wheels /wheels

# Install from pre-built wheels
# We use --no-index to ensure we only look at our wheel dir
RUN pip3 install --break-system-packages --ignore-installed --no-cache-dir --no-index --find-links=/wheels /wheels/*.whl \
    && rm -rf /wheels

USER odoo
