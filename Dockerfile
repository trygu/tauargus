# Runtime image for the tauargus CLI. The release workflow builds it with the
# manylinux wheels produced by the same run as the build context.
FROM python:3.12-slim
ARG TARGETARCH
RUN --mount=type=bind,target=/wheels \
    case "$TARGETARCH" in arm64) A=aarch64;; *) A=x86_64;; esac; \
    pip install --no-cache-dir /wheels/pytauargus-*-cp312-*manylinux*_${A}.whl
WORKDIR /work
ENTRYPOINT ["tauargus"]
