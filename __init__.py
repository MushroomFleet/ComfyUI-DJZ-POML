"""
Zenkai-POML Custom Nodes for ComfyUI
Brings Microsoft's POML (Prompt Orchestration Markup Language) to ComfyUI workflows

Installation:
1. Place this folder in ComfyUI/custom_nodes/
2. Restart ComfyUI
3. Nodes will appear under Zenkai/POML category

Author: Zenkai Labs
License: MIT
Version: 1.0.0
"""

from .zenkai_poml import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

# Export for ComfyUI
__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']

# Node mappings for ComfyUI registration
WEB_DIRECTORY = "./web"

print("🚀 Zenkai-POML nodes loaded successfully!")
print("📝 Nodes available: POML Processor, POML Template")
print("📁 Category: Zenkai/POML")