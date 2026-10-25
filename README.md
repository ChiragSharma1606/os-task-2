# Operating Systems Synchronization Simulations

This repository contains four live synchronization simulations implemented using Java concurrency mechanisms and Python visualizations.

## Simulations

1. **Readers-Writers using Monitor** — demonstrates coordination between readers and writers using monitor-style synchronization.
2. **Dining Philosophers using Semaphore** — demonstrates fork sharing and synchronization using semaphores.
3. **Dining Philosophers using Monitor** — demonstrates monitor-style synchronization with Java's `synchronized`, `wait()`, and `notifyAll()`.
4. **Readers-Writers using Semaphore** — demonstrates concurrent readers and exclusive writers using semaphores.

## Repository Structure

```text
os-task-2/
├── simulations/
│   ├── readers_writers_monitor.py
│   ├── dining_philosophers_semaphore.py
│   ├── dining_philosophers_monitor.py
│   └── readers_writers_semaphore.py
├── docs/
├── screenshots/
└── README.md
```

## Requirements

- Python 3
- Java JDK (includes `java` and `javac`)
- Python packages: `matplotlib` and `ipython`
- Jupyter Notebook or Google Colab is recommended because the scripts use live display updates.

## Setup

Install the Python packages:

```bash
pip install matplotlib ipython
```

Install a Java JDK if it is not already installed. Confirm both Java commands are available:

```bash
java -version
javac -version
```

In Google Colab, if Java is missing, run:

```bash
!apt-get update -qq && !apt-get install -y openjdk-21-jdk-headless
```

## Running the Simulations

Run a script from a Python notebook or a compatible Python environment. For example:

```python
%run simulations/readers_writers_monitor.py
```

Replace the filename with any of the other three scripts to run a different simulation.

The scripts compile their embedded Java source code and then run the Java simulation while Python displays the changing process states.

> **Note:** These scripts were written for notebook-style live visualization. They use paths under `/content/`, so a local environment may require adapting those paths.

## Concepts Demonstrated

- Mutual exclusion
- Thread synchronization
- Concurrent readers and exclusive writers
- Semaphore-based coordination
- Monitor-style synchronization
- Shared resources and race-condition prevention

## Screenshots

Simulation screenshots will be added to the `screenshots/` directory.

## Author

**Name:** Chirag Sharma

Add your course, class, or institution details here if required.
