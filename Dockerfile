# Runtime image for the tauargus CLI. The release workflow builds it with the
# manylinux wheel produced by the same run as the build context.
FROM python:3.12-slim
RUN --mount=type=bind,target=/wheels \
    pip install --no-cache-dir /wheels/pytauargus-*-cp312-*manylinux*_x86_64.whl
WORKDIR /work
ENTRYPOINT ["tauargus"]
