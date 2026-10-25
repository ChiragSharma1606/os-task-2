import os, subprocess, shutil, math, time
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from IPython.display import display, clear_output

# Check Java
if shutil.which("javac") is None or shutil.which("java") is None:
    raise RuntimeError("Java is not installed in this runtime. In Colab, run: !apt-get update -qq && apt-get install -y openjdk-21-jdk-headless")

# Create a fresh Java implementation: 4 philosophers synchronized with Semaphores.
java_code = r"""
import java.util.concurrent.Semaphore;

public class DiningPhilosophersSemaphore {
    static final int N = 4;
    static final int ROUNDS = 3;
    static final Semaphore[] forks = new Semaphore[N];

    static synchronized void event(int id, String state, int round) {
        System.out.println("EVENT P" + (id + 1) + " " + state + " " + round);
        System.out.flush();
    }

    static class Philosopher extends Thread {
        private final int id;
        Philosopher(int id) { this.id = id; }

        public void run() {
            int left = id;
            int right = (id + 1) % N;
            for (int round = 1; round <= ROUNDS; round++) {
                try {
                    event(id, "THINKING", round);
                    Thread.sleep(500);

                    event(id, "HUNGRY", round);
                    // Acquire forks in a fixed order to avoid circular wait.
                    int first = Math.min(left, right);
                    int second = Math.max(left, right);
                    forks[first].acquire();
                    forks[second].acquire();

                    event(id, "EATING", round);
                    Thread.sleep(700);

                    forks[second].release();
                    forks[first].release();
                    event(id, "THINKING", round);
                    Thread.sleep(250);
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                    return;
                }
            }
            event(id, "DONE", ROUNDS);
        }
    }

    public static void main(String[] args) throws InterruptedException {
        for (int i = 0; i < N; i++) forks[i] = new Semaphore(1, true);
        Thread[] philosophers = new Thread[N];
        for (int i = 0; i < N; i++) {
            philosophers[i] = new Philosopher(i);
            philosophers[i].start();
        }
        for (Thread philosopher : philosophers) philosopher.join();
        System.out.println("SIMULATION_FINISHED");
    }
}
"""

workdir = Path("/content/live_dining_philosophers")
workdir.mkdir(parents=True, exist_ok=True)
source_file = workdir / "DiningPhilosophersSemaphore.java"
source_file.write_text(java_code)

compiled = subprocess.run(
    ["javac", str(source_file)],
    cwd=str(workdir),
    capture_output=True,
    text=True
)
if compiled.returncode != 0:
    print(compiled.stderr)
    raise RuntimeError("Java compilation failed.")

print("Compiled successfully. Starting live Java semaphore simulation...")

# Live view: states and fork availability are updated from actual Java output.
states = ["READY"] * 4
rounds = [0] * 4
recent_events = []
colors = {"READY": "#d9e2f3", "THINKING": "#8ecae6",
          "HUNGRY": "#ffb703", "EATING": "#90be6d", "DONE": "#bdbdbd"}

def draw_live():
    clear_output(wait=True)
    fig, ax = plt.subplots(figsize=(7, 6))
    ax.set_xlim(-1.65, 1.65)
    ax.set_ylim(-1.55, 1.55)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("Dining Philosophers — LIVE Java Semaphore Simulation", fontsize=13, pad=15)

    # Draw four forks between adjacent philosophers. Forks are marked in use
    # when either adjacent philosopher is eating.
    positions = []
    for i in range(4):
        angle = math.pi / 2 + i * (2 * math.pi / 4)
        positions.append((math.cos(angle), math.sin(angle)))

    for i in range(4):
        x1, y1 = positions[i]
        x2, y2 = positions[(i + 1) % 4]
        fx, fy = (x1 + x2) / 2, (y1 + y2) / 2
        in_use = states[i] == "EATING" or states[(i + 1) % 4] == "EATING"
        ax.text(fx * 0.78, fy * 0.78, f"Fork {i+1}\n{'IN USE' if in_use else 'free'}",
                ha="center", va="center", fontsize=8,
                bbox=dict(boxstyle="round,pad=0.25",
                          facecolor="#f4a261" if in_use else "#eeeeee",
                          edgecolor="black"))

    for i, (x, y) in enumerate(positions):
        ax.add_patch(Circle((x, y), 0.29, facecolor=colors[states[i]], edgecolor="black", linewidth=1.5))
        ax.text(x, y, f"P{i+1}\n{states[i]}\nRound {rounds[i]}",
                ha="center", va="center", fontsize=8, fontweight="bold")

    ax.add_patch(Circle((0, 0), 0.32, facecolor="#f6bd60", edgecolor="black"))
    ax.text(0, 0, "SHARED\nTABLE", ha="center", va="center", fontsize=9, fontweight="bold")
    ax.text(0, -1.42, "Blue = Thinking   Orange = Hungry   Green = Eating   Gray = Done",
            ha="center", va="center", fontsize=8)
    display(fig)
    plt.close(fig)

process = subprocess.Popen(
    ["java", "-cp", str(workdir), "DiningPhilosophersSemaphore"],
    cwd=str(workdir),
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1
)

for raw_line in process.stdout:
    line = raw_line.strip()
    if line.startswith("EVENT "):
        parts = line.split()
        # Format: EVENT P1 STATE ROUND
        philosopher_index = int(parts[1][1:]) - 1
        state = parts[2]
        round_number = int(parts[3])
        states[philosopher_index] = state
        rounds[philosopher_index] = round_number
        recent_events.append(f"P{philosopher_index + 1}: {state} (round {round_number})")
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
