import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))
from agrisaathi.agents.orchestrator import build_orchestrator
root_agent = build_orchestrator()
