import os, subprocess, shutil, math
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from IPython.display import display, clear_output

if shutil.which("javac") is None or shutil.which("java") is None:
    raise RuntimeError("Java is not installed. In Colab run: !apt-get update -qq && !apt-get install -y openjdk-21-jdk-headless")

# Java implementation: monitor-style synchronization using synchronized methods and wait/notify.
java_code = r"""
public class DiningPhilosophersMonitor {
    static final int N = 4;
    static final int ROUNDS = 3;
    static final int THINKING = 0, HUNGRY = 1, EATING = 2;
    static final String[] LABELS = {"THINKING", "HUNGRY", "EATING"};
    static final int[] state = new int[N];

    static class Table {
        synchronized void takeForks(int i, int round) throws InterruptedException {
            state[i] = HUNGRY;
            emit(i, "HUNGRY", round);
            while (state[left(i)] == EATING || state[right(i)] == EATING) {
                wait();
            }
            state[i] = EATING;
            emit(i, "EATING", round);
        }

        synchronized void putForks(int i, int round) {
            state[i] = THINKING;
            emit(i, "THINKING", round);
            notifyAll();
        }

        int left(int i) { return (i + N - 1) % N; }
        int right(int i) { return (i + 1) % N; }
    }

    static final Table table = new Table();

    static synchronized void emit(int i, String stateName, int round) {
        System.out.println("EVENT P" + (i + 1) + " " + stateName + " " + round);
        System.out.flush();
    }

    static class Philosopher extends Thread {
        final int id;
        Philosopher(int id) { this.id = id; }

        public void run() {
            for (int round = 1; round <= ROUNDS; round++) {
                try {
                    emit(id, "THINKING", round);
                    Thread.sleep(450);
                    table.takeForks(id, round);
                    Thread.sleep(650);
                    table.putForks(id, round);
                    Thread.sleep(250);
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                    return;
                }
            }
            emit(id, "DONE", ROUNDS);
        }
    }

    public static void main(String[] args) throws InterruptedException {
        Thread[] philosophers = new Thread[N];
        for (int i = 0; i < N; i++) {
            philosophers[i] = new Philosopher(i);
            philosophers[i].start();
        }
        for (Thread p : philosophers) p.join();
        System.out.println("SIMULATION_FINISHED");
    }
}
"""

workdir = Path("/content/live_dining_philosophers_monitor")
workdir.mkdir(parents=True, exist_ok=True)
source_file = workdir / "DiningPhilosophersMonitor.java"
source_file.write_text(java_code)

compiled = subprocess.run(
    ["javac", str(source_file)],
    cwd=str(workdir), capture_output=True, text=True
)
if compiled.returncode != 0:
    print(compiled.stderr)
    raise RuntimeError("Java compilation failed.")

print("Compiled successfully. Starting live Java monitor simulation...")

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
    ax.set_title("Dining Philosophers — LIVE Java Monitor Simulation", fontsize=13, pad=15)

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
                ha="center", va="center", fontsize=8)

    ax.add_patch(Circle((0, 0), 0.32, facecolor="#f6bd60", edgecolor="black"))
    ax.text(0, 0, "MONITOR\nTABLE", ha="center", va="center", fontsize=9, fontweight="bold")
    ax.text(0, -1.42, "Blue = Thinking   Orange = Hungry   Green = Eating   Gray = Done",
            ha="center", va="center", fontsize=8)
    display(fig)
    plt.close(fig)

process = subprocess.Popen(
    ["java", "-cp", str(workdir), "DiningPhilosophersMonitor"],
    cwd=str(workdir), stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT, text=True, bufsize=1
)

for raw_line in process.stdout:
    line = raw_line.strip()
    if line.startswith("EVENT "):
        parts = line.split()
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
