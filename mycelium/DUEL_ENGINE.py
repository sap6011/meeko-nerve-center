import time
import subprocess
import os

def duel_functions(func_name, version_a, version_b):
    results = {}
    for version, code in [('A', version_a), ('B', version_b)]:
        test_file = f'data/temp_duel_{version}.py'
        # Wrap the scavenged code in a performance timer
        test_wrapper = f"""
import time
import json
from pathlib import Path

DATA = Path("data")
DATA.mkdir(exist_ok=True)
{code}
start = time.perf_counter()
try:
    {func_name}()
    print(f"SUCCESS:{{time.perf_counter() - start}}")
except Exception as e:
    print(f"FAILURE:{{e}}")
"""
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_wrapper)
        
        try:
            proc = subprocess.run(['python', test_file], capture_output=True, text=True, timeout=5)
            output = proc.stdout.strip()
            if "SUCCESS" in output:
                results[version] = float(output.split(':')[1])
            else:
                results[version] = float('inf')
        except:
            results[version] = float('inf')
        finally:
            if os.path.exists(test_file): os.remove(test_file)

    winner = 'A' if results.get('A', float('inf')) <= results.get('B', float('inf')) else 'B'
    print(f"🏆 Duel for {func_name}: Version {winner} won ({results[winner]:.6f}s)")
    return version_a if winner == 'A' else version_b

if __name__ == "__main__":
    print("⚖️ Duel Engine: Standing by for arbitration.")


# -- LIVE_WIRE topology connector --
def _wire_state():
    _r = json.loads((DATA / "knowledge_graph.json").read_text()) if (DATA / "knowledge_graph.json").exists() else {}
    (DATA / "duel_engine_state.json").write_text(json.dumps({"last_run": __import__("datetime").datetime.now().isoformat(), "status": "wired"}, indent=2))
