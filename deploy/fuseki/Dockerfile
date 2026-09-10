FROM eclipse-temurin:21.0.8_9-jre-jammy

ARG JENA_VERSION=6.2.0
ENV FUSEKI_HOME=/opt/fuseki

RUN apt-get update \
    && apt-get install --no-install-recommends --yes ca-certificates curl tar \
    && rm -rf /var/lib/apt/lists/* \
    && curl --fail --silent --show-error --location \
       "https://archive.apache.org/dist/jena/binaries/apache-jena-fuseki-${JENA_VERSION}.tar.gz" \
       --output /tmp/fuseki.tar.gz \
    && mkdir --parents "${FUSEKI_HOME}" \
    && tar --extract --gzip --file /tmp/fuseki.tar.gz --strip-components=1 --directory "${FUSEKI_HOME}" \
    && rm /tmp/fuseki.tar.gz \
    && useradd --system --uid 10001 --home-dir "${FUSEKI_HOME}" fuseki \
    && mkdir --parents /fuseki-data \
    && chown --recursive fuseki:fuseki "${FUSEKI_HOME}" /fuseki-data

WORKDIR ${FUSEKI_HOME}
USER fuseki

EXPOSE 3030

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=5 \
  CMD curl --fail --silent http://127.0.0.1:3030/ > /dev/null

ENTRYPOINT ["/opt/fuseki/fuseki-server"]
CMD ["--loc=/fuseki-data", "--update", "/myDataset"]
