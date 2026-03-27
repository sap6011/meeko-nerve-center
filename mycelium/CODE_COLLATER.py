import os
import re

def collate_legacy_logic():
    """DISABLED: SWARM_TOOLBOX v3 is now a clean engine registry.
    CODE_COLLATER's regex-based extraction produced broken triple-quote
    cascades in the 8000-line output. The new SWARM_TOOLBOX uses AST
    parsing to build a live registry instead of concatenating raw code.
    """
    print("CODE_COLLATER: Disabled. SWARM_TOOLBOX v3 uses AST-based registry now.")
    print("  Run: python mycelium/SWARM_TOOLBOX.py  to update the registry.")

if __name__ == "__main__":
    collate_legacy_logic()
