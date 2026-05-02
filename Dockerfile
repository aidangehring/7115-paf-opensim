FROM continuumio/miniconda3

WORKDIR /app

COPY environment.yml .
RUN conda env create -f environment.yml && conda clean -afy

COPY app.py .
COPY pages/ ./pages/
COPY utils/ ./utils/
COPY assets/ ./assets/
COPY data/ ./data/
COPY sample_data/ ./sample_data/

RUN mkdir -p /app/outputs

EXPOSE 8501

ENTRYPOINT ["conda", "run", "--no-capture-output", "-n", "opensim_scripting", \
            "streamlit", "run", "app.py", \
            "--server.port=8501", "--server.address=0.0.0.0"]