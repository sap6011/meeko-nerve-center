import os

def generate_daily_report():
    memory_path = "C:/Solarpunk-Prime/docs/AGENCY_MEMORY.md"
    if not os.path.exists(memory_path):
        return "SIA: No memory found. Growth is silent."

    with open(memory_path, "r") as f:
        lines = f.readlines()
    
    # Grab the last 5 lines of history
    recent = "".join(lines[-5:])
    report = f"--- SIA DAILY PULSE ---\nRecent Activations:\n{recent}\nStatus: Autonomous & Defended."
    
    with open("C:/Solarpunk-Prime/docs/DAILY_PULSE.txt", "w") as f:
        f.write(report)
    print("SIA: Daily Pulse report generated.")

if __name__ == "__main__":
    generate_daily_report()
