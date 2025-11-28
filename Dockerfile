FROM nvidia/cuda:12.6.0-devel-ubuntu22.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set working directory
WORKDIR /app

# Clone SAM3 repository
RUN git clone https://github.com/facebookresearch/sam3.git sam3

# Change to sam3 directory
WORKDIR /app/sam3

# Patch pyproject.toml to allow Python >= 3.10 (resolves numpy conflict)
RUN sed -i 's/requires-python = ">=3.8"/requires-python = ">=3.10"/' pyproject.toml

# Create virtual environment with explicit Python version
RUN uv venv --python 3.12

# Activate virtual environment
ENV VIRTUAL_ENV=/app/sam3/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Install PyTorch with CUDA 12.6 support
RUN uv pip install torch==2.7.0 torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126

# Install SAM3 and dependencies
RUN uv pip install -e ".[notebooks]"

# Copy inference script
COPY run_inference.py .

# Create results directory
RUN mkdir -p results

# Default command (keep container running)
CMD ["/bin/bash"]
