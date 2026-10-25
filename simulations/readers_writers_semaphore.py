import os, subprocess, shutil, math
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle
from IPython.display import display, clear_output

if shutil.which("javac") is None or shutil.which("java") is None:
    raise RuntimeError("Java is not installed. In Colab run: !apt-get update -qq && !apt-get install -y openjdk-21-jdk-headless")

# Java implementation: Readers-Writers using semaphores.
java_code = r"""
import java.util.concurrent.Semaphore;

public class ReadersWritersSemaphore {
    static final int READERS = 4;
    static final int WRITES = 3;
    static final Semaphore mutex = new Semaphore(1, true);
    static final Semaphore writeLock = new Semaphore(1, true);
    static int readCount = 0;
    static int sharedValue = 0;

    static synchronized void emit(String message) {
        System.out.println(message);
        System.out.flush();
    }

    static class Reader extends Thread {
        final int id;
        Reader(int id) { this.id = id; }

        public void run() {
            try {
                for (int round = 1; round <= 2; round++) {
                    mutex.acquire();
                    readCount++;
                    if (readCount == 1) writeLock.acquire();
                    emit("EVENT R" + id + " READING " + sharedValue + " " + round);
                    mutex.release();

                    Thread.sleep(600);

                    mutex.acquire();
                    readCount--;
                    if (readCount == 0) writeLock.release();
                    emit("EVENT R" + id + " READY " + sharedValue + " " + round);
                    mutex.release();
                    Thread.sleep(300);
                }
                emit("EVENT R" + id + " DONE 0 2");
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        }
    }

    static class Writer extends Thread {
        final int id;
        Writer(int id) { this.id = id; }

        public void run() {
            try {
                for (int round = 1; round <= WRITES; round++) {
                    writeLock.acquire();
                    emit("EVENT W" + id + " WRITING " + sharedValue + " " + round);
                    Thread.sleep(700);
                    sharedValue++;
                    emit("EVENT W" + id + " WROTE " + sharedValue + " " + round);
                    writeLock.release();
                    Thread.sleep(250);
                }
                emit("EVENT W" + id + " DONE " + sharedValue + " " + WRITES);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        }
    }

    public static void main(String[] args) throws InterruptedException {
        Thread[] threads = new Thread[READERS + 2];
        for (int i = 0; i < READERS; i++) {
            threads[i] = new Reader(i + 1);
            threads[i].start();
        }
        for (int i = 0; i < 2; i++) {
            threads[READERS + i] = new Writer(i + 1);
            threads[READERS + i].start();
        }
        for (Thread t : threads) t.join();
        emit("SIMULATION_FINISHED");
    }
}
"""

workdir = Path("/content/live_readers_writers_semaphore")
workdir.mkdir(parents=True, exist_ok=True)
source_file = workdir / "ReadersWritersSemaphore.java"
source_file.write_text(java_code)

compiled = subprocess.run(["javac", str(source_file)], cwd=str(workdir), capture_output=True, text=True)
if compiled.returncode != 0:
    print(compiled.stderr)
    raise RuntimeError("Java compilation failed.")

print("Compiled successfully. Starting live Readers-Writers semaphore simulation...")

reader_states = {i: "READY" for i in range(1, 5)}
writer_states = {i: "READY" for i in range(1, 3)}
shared_value = 0
recent_events = []
colors = {"READY": "#d9e2f3", "READING": "#8ecae6", "WRITING": "#90be6d",
          "WROTE": "#90be6d", "DONE": "#bdbdbd"}

def draw_live():
    clear_output(wait=True)
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 7)
    ax.axis("off")
    ax.set_title("Readers–Writers — LIVE Java Semaphore Simulation", fontsize=13, pad=12)

    ax.add_patch(Rectangle((3.7, 2.4), 2.6, 1.5, facecolor="#f6bd60", edgecolor="black", linewidth=1.5))
    ax.text(5, 3.15, f"SHARED DATA\nValue = {shared_value}", ha="center", va="center", fontsize=11, fontweight="bold")

    for i in range(1, 5):
        y = 5.7 - (i - 1) * 1.35
        state = reader_states[i]
        ax.add_patch(Circle((1.4, y), 0.42, facecolor=colors.get(state, "#d9e2f3"), edgecolor="black"))
        ax.text(1.4, y, f"R{i}\n{state}", ha="center", va="center", fontsize=8)
        if state == "READING":
            ax.annotate("", xy=(3.65, 3.15), xytext=(1.9, y),
                        arrowprops=dict(arrowstyle="->", lw=1.4))

    for i in range(1, 3):
        y = 5.1 - (i - 1) * 2.2
        state = writer_states[i]
        ax.add_patch(Rectangle((7.7, y - 0.38), 1.25, 0.76, facecolor=colors.get(state, "#d9e2f3"), edgecolor="black"))
        ax.text(8.325, y, f"W{i}\n{state}", ha="center", va="center", fontsize=8)
        if state == "WRITING":
            ax.annotate("", xy=(6.35, 3.15), xytext=(7.65, y),
                        arrowprops=dict(arrowstyle="->", lw=1.4))

    active_readers = sum(s == "READING" for s in reader_states.values())
    active_writers = sum(s == "WRITING" for s in writer_states.values())
    ax.text(5, 1.35, f"Active readers: {active_readers}     Active writers: {active_writers}",
            ha="center", va="center", fontsize=10)
    ax.text(5, 0.7, "Readers may overlap; a writer must have exclusive access.",
            ha="center", va="center", fontsize=9)
    display(fig)
    plt.close(fig)

process = subprocess.Popen(
    ["java", "-cp", str(workdir), "ReadersWritersSemaphore"],
    cwd=str(workdir), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    text=True, bufsize=1
)

for raw_line in process.stdout:
    line = raw_line.strip()
    if line.startswith("EVENT "):
        parts = line.split()
        who, state = parts[1], parts[2]
        value = int(parts[3])
        round_number = int(parts[4])
        shared_value = value
        if who.startswith("R"):
            reader_id = int(who[1:])
            reader_states[reader_id] = "READING" if state == "READING" else ("DONE" if state == "DONE" else "READY")
        elif who.startswith("W"):
            writer_id = int(who[1:])
            writer_states[writer_id] = "WRITING" if state == "WRITING" else ("DONE" if state == "DONE" else "READY")
        recent_events.append(f"{who}: {state}, shared value={value}, round={round_number}")
        recent_events = recent_events[-8:]
        draw_live()
        print("Recent Java events:")
        for event_text in recent_events:
            print(" •", event_text)
    elif line:
        print(line)

return_code = process.wait()
if return_code != 0:
    raise RuntimeError(f"Java program exited with code {return_code}")
print("\nSimulation completed successfully.")
