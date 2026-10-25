import os, re, subprocess, shutil, time
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle
from IPython.display import display, clear_output

# Compile the Java synchronization program.
source = r"""
import java.util.concurrent.ThreadLocalRandom;

public class ReadersWritersMonitor {
    static final Object monitor = new Object();
    static int readers = 0;
    static int sharedValue = 0;
    static boolean writerActive = false;
    static int waitingWriters = 0;

    static void emit(String msg) {
        System.out.println("EVENT " + msg);
        System.out.flush();
    }

    static void startRead(int id, int round) throws InterruptedException {
        synchronized (monitor) {
            while (writerActive || waitingWriters > 0) monitor.wait();
            readers++;
            emit("R" + id + " READING " + sharedValue + " " + round);
        }
    }

    static void endRead(int id, int round) {
        synchronized (monitor) {
            readers--;
            emit("R" + id + " READY " + sharedValue + " " + round);
            if (readers == 0) monitor.notifyAll();
        }
    }

    static void startWrite(int id, int round) throws InterruptedException {
        synchronized (monitor) {
            waitingWriters++;
            try {
                while (writerActive || readers > 0) monitor.wait();
                writerActive = true;
                emit("W" + id + " WRITING " + sharedValue + " " + round);
            } finally {
                waitingWriters--;
            }
        }
    }

    static void endWrite(int id, int round) {
        synchronized (monitor) {
            sharedValue++;
            emit("W" + id + " WROTE " + sharedValue + " " + round);
            writerActive = false;
            monitor.notifyAll();
        }
    }

    static class Reader extends Thread {
        int id;
        Reader(int id) { this.id = id; }
        public void run() {
            try {
                for (int r = 1; r <= 3; r++) {
                    Thread.sleep(ThreadLocalRandom.current().nextInt(250, 850));
                    startRead(id, r);
                    Thread.sleep(ThreadLocalRandom.current().nextInt(500, 1000));
                    endRead(id, r);
                }
            } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
        }
    }

    static class Writer extends Thread {
        int id;
        Writer(int id) { this.id = id; }
        public void run() {
            try {
                for (int r = 1; r <= 3; r++) {
                    Thread.sleep(ThreadLocalRandom.current().nextInt(400, 1000));
                    startWrite(id, r);
                    Thread.sleep(ThreadLocalRandom.current().nextInt(600, 1100));
                    endWrite(id, r);
                }
            } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
        }
    }

    public static void main(String[] args) throws Exception {
        Thread[] all = new Thread[6];
        for (int i = 0; i < 4; i++) all[i] = new Reader(i + 1);
        for (int i = 0; i < 2; i++) all[4 + i] = new Writer(i + 1);
        for (Thread t : all) t.start();
        for (Thread t : all) t.join();
        emit("DONE " + sharedValue);
    }
}
"""
with open("ReadersWritersMonitor.java", "w") as f:
    f.write(source)

if shutil.which("javac") is None:
    raise RuntimeError("Java compiler not found. In Colab, install Java with: !apt-get -qq install default-jdk")
subprocess.run(["javac", "ReadersWritersMonitor.java"], check=True)

proc = subprocess.Popen(
    ["java", "ReadersWritersMonitor"],
    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1
)

reader_states = {f"R{i}": "WAITING" for i in range(1, 5)}
writer_states = {f"W{i}": "WAITING" for i in range(1, 3)}
reader_values = {}
shared_value = 0
events = []
done = False

def draw_scene(message):
    clear_output(wait=True)
    fig, ax = plt.subplots(figsize=(10, 5.8))
    ax.set_xlim(0, 10); ax.set_ylim(0, 6); ax.axis("off")
    ax.set_title("Readers–Writers Problem | Java Monitor (wait/notifyAll)", fontsize=14, pad=12)

    # Shared resource
    ax.add_patch(Rectangle((3.65, 2.25), 2.7, 1.35, fill=False, linewidth=2))
    ax.text(5, 3.05, "SHARED DATA", ha="center", va="center", fontsize=12, weight="bold")
    ax.text(5, 2.58, f"Value: {shared_value}", ha="center", va="center", fontsize=12)

    # Readers left
    for i, x in enumerate([1.1, 2.15, 3.2], start=1):
        state = reader_states[f"R{i}"]
        color = "seagreen" if state == "READING" else "lightgray"
        ax.add_patch(Circle((x, 4.75), 0.38, facecolor=color, edgecolor="black"))
        ax.text(x, 4.75, f"R{i}", ha="center", va="center", fontsize=9, weight="bold")
        ax.text(x, 4.15, state, ha="center", va="center", fontsize=8)
    x=2.15
    state=reader_states["R4"]
    color="seagreen" if state=="READING" else "lightgray"
    ax.add_patch(Circle((x, 1.1), 0.38, facecolor=color, edgecolor="black"))
    ax.text(x, 1.1, "R4", ha="center", va="center", fontsize=9, weight="bold")
    ax.text(x, 0.5, state, ha="center", va="center", fontsize=8)

    # Writers right
    for i, y in enumerate([4.55, 1.45], start=1):
        state = writer_states[f"W{i}"]
        color = "tomato" if state == "WRITING" else "lightgray"
        ax.add_patch(Circle((8.1, y), 0.48, facecolor=color, edgecolor="black"))
        ax.text(8.1, y, f"W{i}", ha="center", va="center", fontsize=10, weight="bold")
        ax.text(8.1, y-0.72, state, ha="center", va="center", fontsize=9)

    active_readers = sum(v == "READING" for v in reader_states.values())
    active_writers = sum(v == "WRITING" for v in writer_states.values())
    ax.text(5, 4.7, f"Active readers: {active_readers}", ha="center", fontsize=10)
    ax.text(5, 4.25, f"Active writers: {active_writers}", ha="center", fontsize=10)
    ax.text(5, 0.3, message[:120], ha="center", va="center", fontsize=9, wrap=True)
    plt.tight_layout()
    display(fig)
    plt.close(fig)

draw_scene("Starting Java monitor simulation…")
for line in proc.stdout:
    line = line.strip()
    if not line.startswith("EVENT "):
        continue
    event = line[6:]
    events.append(event)
    parts = event.split()
    if not parts:
        continue
    who = parts[0]
    if who.startswith("R") and who[1:].isdigit():
        if len(parts) >= 4:
            action = parts[1]
            if action == "READING":
                reader_states[who] = "READING"
                reader_values[who] = parts[2]
            elif action == "READY":
                reader_states[who] = "DONE"
    elif who.startswith("W") and who[1:].isdigit():
        if len(parts) >= 4:
            action = parts[1]
            if action == "WRITING":
                writer_states[who] = "WRITING"
            elif action == "WROTE":
                writer_states[who] = "DONE"
                try: shared_value = int(parts[2])
                except ValueError: pass
    elif who == "DONE":
        try: shared_value = int(parts[1])
        except (IndexError, ValueError): pass
    draw_scene(event)
    time.sleep(0.12)

stderr = proc.stderr.read()
return_code = proc.wait()
if return_code != 0:
    print("Java error:", stderr)
else:
    print("Simulation finished. Final shared value:", shared_value)
    print("Java events captured:", len(events))
