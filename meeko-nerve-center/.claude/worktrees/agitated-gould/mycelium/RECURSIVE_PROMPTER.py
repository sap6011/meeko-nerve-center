def generate_self_commands():
    cmds = [
        "Write-Host '--- SOLARPUNK SINGULARITY: CIRCULAR ECONOMY ACTIVE ---' -ForegroundColor Green",
        "python mycelium/SOLAR_OVERSEER.py",    # Bots monitoring bots
        "python mycelium/EXTERNAL_HANDSHAKE.py",
        "python mycelium/REVENUE_ENGINE.py",
        "python mycelium/REVENUE_RECYCLER.py",  # Reinvesting profit
        "python mycelium/SCAVENGER_WEB.py",
        "python mycelium/SKILL_MANIFESTOR.py",
        "python mycelium/AUTO_ARCHITECT.py",
        "python mycelium/MISSION_CONTROL.py"
    ]
    ps_content = "$cmds = " + str(cmds).replace("[", "@(").replace("]", ")") + "\nforeach ($c in $cmds) { iex $c }"
    with open('AUTO_EXEC.ps1', 'w', encoding='utf-8') as f:
        f.write(ps_content)
    print("🌀 Sovereign Architect: CIRCULAR MYCELIUM ONLINE.")

if __name__ == '__main__':
    generate_self_commands()
