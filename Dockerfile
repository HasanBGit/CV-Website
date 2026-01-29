# -----------------------------------------------------------------------------
# Stage 1: Build LaTeX environment with Roboto font
# -----------------------------------------------------------------------------
FROM python:3.11-slim AS latex-builder

ENV DEBIAN_FRONTEND=noninteractive

# Install minimal LaTeX (pdflatex; no XeTeX/Arabic)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    texlive-latex-base \
    texlive-latex-recommended \
    texlive-latex-extra \
    texlive-fonts-recommended \
    texlive-extra-utils \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install only Roboto font via tlmgr (small, not entire fonts-extra)
RUN tlmgr init-usertree 2>/dev/null || true \
    && tlmgr install roboto \
    && tlmgr path remove \
    && rm -rf /root/.texlive* /tmp/texlive* 2>/dev/null || true

# Copy user texmf (Roboto) to system path for runtime stage
RUN if [ -d /root/texmf ]; then \
      mkdir -p /usr/local/share/texmf && cp -r /root/texmf/. /usr/local/share/texmf/; \
      texhash /usr/local/share/texmf 2>/dev/null || true; \
      rm -rf /root/texmf; \
    fi

# -----------------------------------------------------------------------------
# Stage 2: Runtime image
# -----------------------------------------------------------------------------
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Install runtime LaTeX (pdflatex only)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    texlive-latex-base \
    texlive-latex-recommended \
    texlive-latex-extra \
    texlive-fonts-recommended \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy Roboto font tree from builder
COPY --from=latex-builder /usr/local/share/texmf /usr/local/share/texmf
RUN texhash /usr/local/share/texmf 2>/dev/null || true

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

EXPOSE 5000
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/ || exit 1

CMD ["python", "app.py"]
