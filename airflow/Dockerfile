# FROM apache/airflow:2.8.4

# # Switch to root to install system packages
# USER root

# # Update package lists and install basic dependencies
# RUN apt-get update && apt-get install -y \
#     wget \
#     gnupg \
#     unzip \
#     curl \
#     xvfb \
#     fonts-liberation \
#     libappindicator3-1 \
#     libasound2 \
#     libatk-bridge2.0-0 \
#     libdrm2 \
#     libgtk-3-0 \
#     libnspr4 \
#     libnss3 \
#     libxss1 \
#     libxtst6 \
#     xdg-utils \
#     libxrandr2 \
#     libasound2 \
#     libpangocairo-1.0-0 \
#     libatk1.0-0 \
#     libcairo-gobject2 \
#     libgtk-3-0 \
#     libgdk-pixbuf2.0-0 \
#     && rm -rf /var/lib/apt/lists/*

# # Add Google Chrome repository and install Chrome
# RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
#     && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
#     && apt-get update \
#     && apt-get install -y google-chrome-stable \
#     && rm -rf /var/lib/apt/lists/*

# # Install ChromeDriver
# RUN CHROMEDRIVER_VERSION=$(curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE) && \
#     wget -N http://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip -P /tmp/ && \
#     unzip /tmp/chromedriver_linux64.zip -d /tmp/ && \
#     rm /tmp/chromedriver_linux64.zip && \
#     chown root:root /tmp/chromedriver && \
#     chmod 755 /tmp/chromedriver && \
#     mv /tmp/chromedriver /usr/bin/chromedriver

# # Create symlinks for Chrome (only if it doesn't exist)
# RUN if [ ! -f /usr/bin/google-chrome ]; then \
#         ln -s /usr/bin/google-chrome-stable /usr/bin/google-chrome; \
#     fi

# # Create the entrypoint wrapper script with proper error handling
# RUN printf '#!/bin/bash\n# Start Xvfb in the background\nXvfb :99 -screen 0 1024x768x24 > /dev/null 2>&1 &\n# Execute the original command\nexec "$@"\n' > /usr/local/bin/entrypoint-wrapper.sh

# # Make the script executable
# RUN chmod +x /usr/local/bin/entrypoint-wrapper.sh

# # Verify the script was created correctly
# RUN ls -la /usr/local/bin/entrypoint-wrapper.sh && cat /usr/local/bin/entrypoint-wrapper.sh

# # Switch back to airflow user
# USER airflow

# # Copy and install Python requirements
# COPY requirements.txt .
# RUN pip install -r requirements.txt

# # Set environment variables
# ENV DISPLAY=:99
# ENV CHROME_BIN=/usr/bin/google-chrome
# ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

# # Use the wrapper script as entrypoint
# ENTRYPOINT ["/usr/local/bin/entrypoint-wrapper.sh", "/entrypoint"]
# CMD ["--help"]

FROM apache/airflow:2.8.4

# Switch to root to install system packages
USER root

# Install required system packages and dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    xvfb \
    fonts-liberation \
    libappindicator3-1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libxss1 \
    libxtst6 \
    xdg-utils \
    libxrandr2 \
    libpangocairo-1.0-0 \
    libcairo-gobject2 \
    libgdk-pixbuf2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Add Google Chrome repository and install Chrome
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Install ChromeDriver v138.0.7204.49 (matching Chrome version)
RUN CHROMEDRIVER_VERSION=138.0.7204.49 && \
    wget -q https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/${CHROMEDRIVER_VERSION}/linux64/chromedriver-linux64.zip -O /tmp/chromedriver.zip && \
    unzip /tmp/chromedriver.zip -d /tmp/ && \
    mv /tmp/chromedriver-linux64/chromedriver /usr/bin/chromedriver && \
    chmod +x /usr/bin/chromedriver && \
    rm -rf /tmp/chromedriver*

# Create symlink for Google Chrome if necessary
RUN if [ ! -f /usr/bin/google-chrome ]; then \
        ln -s /usr/bin/google-chrome-stable /usr/bin/google-chrome; \
    fi

# Create Xvfb entrypoint wrapper
RUN printf '#!/bin/bash\nXvfb :99 -screen 0 1024x768x24 > /dev/null 2>&1 &\nexec "$@"\n' > /usr/local/bin/entrypoint-wrapper.sh && \
    chmod +x /usr/local/bin/entrypoint-wrapper.sh

# Switch back to airflow user
USER airflow

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Set environment variables
ENV DISPLAY=:99
ENV CHROME_BIN=/usr/bin/google-chrome
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

# Set entrypoint
ENTRYPOINT ["/usr/local/bin/entrypoint-wrapper.sh", "/entrypoint"]
CMD ["--help"]
