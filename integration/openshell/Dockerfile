FROM python:3.12-slim-bookworm@sha256:54c85f3c47607a77f32adec749d3c81d1348bf25833671f512b26a9b6d778cb3
RUN groupadd --gid 1000 sandbox && useradd --uid 1000 --gid 1000 --create-home sandbox \
    && mkdir -p /output /evidence /sealed /opt/finguard \
    && printf 'SYNTHETIC-OPENSHELL-DECOY\n' > /sealed/decoy.txt \
    && chmod 755 /sealed && chmod 444 /sealed/decoy.txt \
    && chown sandbox:sandbox /output /evidence
COPY finguard /opt/finguard/finguard
COPY --chown=1000:1000 evidence /evidence
RUN ln -s /sealed/decoy.txt /evidence/secret-link
ENV PYTHONPATH=/opt/finguard PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /output
USER sandbox
CMD ["/bin/sleep", "infinity"]
