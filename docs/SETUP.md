# Zenkai-POML Quick Setup Guide

## 🚨 **IMPORTANT: Dependencies Required!**

Unlike basic ComfyUI nodes, Zenkai-POML requires additional Python packages for full functionality. **You must install dependencies** or many features won't work.

## 🚀 Automated Installation (Recommended)

### Option A: One-Command Setup
```bash
cd ComfyUI/custom_nodes/
mkdir Zenkai-POML
cd Zenkai-POML

# Download files (copy from artifacts)
# Then run automatic installer:
python install.py
```

### Option B: Manual Installation with Dependencies

1. **Create the folder structure:**
   ```bash
   mkdir -p "ComfyUI/custom_nodes/Zenkai-POML"
   cd "ComfyUI/custom_nodes/Zenkai-POML"
   ```

2. **Download the files:**
   - Copy `__init__.py` content → save as `__init__.py`
   - Copy `zenkai_poml.py` content → save as `zenkai_poml.py`
   - Copy `requirements.txt` content → save as `requirements.txt`
   - Copy `install.py` content → save as `install.py`

3. **Install dependencies (CRITICAL STEP):**
   ```bash
   # Full installation (all features)
   pip install -r requirements.txt
   
   # OR minimal installation (core features only)
   pip install poml pandas PyPDF2 Pillow requests jsonschema
   
   # OR absolute minimum (basic POML only)
   pip install poml
   ```

4. **Verify installation:**
   ```bash
   python install.py --check-only
   ```

5. **Restart ComfyUI:**
   - Close ComfyUI completely
   - Restart the application
   - Check console for: "🚀 Zenkai-POML nodes loaded successfully!"

## 📋 Dependency Levels Explained

| Installation | Command | Features Available |
|-------------|---------|-------------------|
| **🌟 Full** | `pip install -r requirements.txt` | ✅ All POML features<br>✅ Official SDK<br>✅ PDF/Excel processing<br>✅ Image handling<br>✅ External data<br>✅ Advanced validation |
| **⚖️ Standard** | `pip install poml pandas PyPDF2 Pillow requests` | ✅ Core POML<br>✅ Official SDK<br>✅ Basic file processing<br>❌ Advanced features |
| **🔧 Minimal** | `pip install poml` | ✅ Official POML SDK<br>❌ File processing<br>❌ Data integration |  
| **⚠️ Fallback** | No dependencies | ⚠️ Basic parsing only<br>❌ Most features disabled |

**Recommendation**: Use **Full** installation for best experience.

## ✅ Installation Verification

### Step 1: Check Node Availability
- Right-click in ComfyUI → Add Node
- Look for **Zenkai/POML** category
- Should see: `POML Processor` and `POML Template`

### Step 2: Test Basic Functionality  
1. **Add POML Processor node**
2. **Use default template:**
   ```xml
   <poml>
   <role>You are a helpful AI assistant.</role>
   <task>Test that POML processing works correctly.</task>
   <output-format>Respond with "POML is working!" if you understand.</output-format>
   </poml>
   ```
3. **Check rendered output** (should be clean, structured text)

### Step 3: Connect to OpenRouter
1. **Add OpenRouter node** (ensure you have this custom node)
2. **Connect:** `POML Processor` → `rendered_prompt` → `OpenRouter` → `text`
3. **Configure OpenRouter:**
   - Model: `anthropic/claude-3.5-sonnet-20241022`
   - API Key: `your-openrouter-key`
4. **Test the full pipeline**

## 🛠️ Troubleshooting Setup

### Problem: Nodes Don't Appear

**Check console output:**
```bash
# Look for error messages when starting ComfyUI
python main.py
```

**Common fixes:**
- Ensure files are in correct folder: `ComfyUI/custom_nodes/Zenkai-POML/`
- Check file permissions (must be readable)
- Verify Python syntax (no typos in copied code)
- Complete restart of ComfyUI (not just refresh)

### Problem: Import Errors

**Required Python modules:**
```python
import re          # Built-in ✅
import json        # Built-in ✅  
import xml.etree.ElementTree as ET  # Built-in ✅
import csv         # Built-in ✅
import io          # Built-in ✅
import os          # Built-in ✅
```

*All dependencies are Python built-ins - no pip install needed!*

### Problem: POML Parsing Fails

**Check POML syntax:**
- Must have `<poml>` root element
- Proper XML closing tags
- Valid variable JSON: `{"key": "value"}`

**Test with minimal example:**
```xml
<poml>
<role>Assistant</role>
<task>Help user</task>  
</poml>
```

## 🎯 Quick Start Workflows

### Workflow 1: Basic Enhancement
```
Text → POML Processor → OpenRouter → Output
```
**Use:** Convert plain prompts to structured POML

### Workflow 2: Template-Based
```
POML Template → POML Processor → OpenRouter → Analysis
```
**Use:** Consistent formatting for specific tasks

### Workflow 3: A/B Testing
```
Same Context → Multiple POML Styles → Compare Results
```
**Use:** Optimize prompt performance

## 📋 Configuration Checklist

### ComfyUI Setup
- [ ] ComfyUI installed and running
- [ ] Custom nodes folder accessible  
- [ ] Files copied to correct location
- [ ] ComfyUI restarted after installation

### Node Testing
- [ ] Zenkai/POML category visible
- [ ] POML Processor node loads
- [ ] POML Template node loads
- [ ] Basic POML parsing works
- [ ] Variables substitution works

### Integration Ready
- [ ] OpenRouter node installed
- [ ] API key configured
- [ ] Model selection working
- [ ] Full pipeline tested

## 🚀 Next Steps

### Learn POML Basics
1. **Try built-in templates** - Start with "Analysis" template
2. **Experiment with variables** - Use JSON context for dynamic content
3. **Test different render modes** - Compare standard vs optimized output

### Advanced Usage
1. **Create custom templates** - Build reusable patterns for your workflows
2. **Data integration** - Add tables and documents to prompts
3. **Multi-modal prompts** - Combine text, images, and structured data

### Community Resources
- **POML Documentation**: [microsoft.github.io/poml/latest/](https://microsoft.github.io/poml/latest/)
- **OpenRouter Models**: [openrouter.ai/models](https://openrouter.ai/models)
- **ComfyUI Community**: [reddit.com/r/comfyui](https://reddit.com/r/comfyui)

## 📞 Support

### Getting Help
1. **Check this README** - Most issues covered here
2. **GitHub Issues** - Report bugs or request features  
3. **ComfyUI Discord** - General ComfyUI support
4. **POML Discord** - POML-specific questions

### Common Issues & Solutions

| Problem | Solution |
|---------|----------|
| Nodes missing after install | Restart ComfyUI completely |
| POML syntax errors | Use debug mode to see parsing details |
| Variables not working | Check JSON format in variables input |
| Empty output | Ensure POML has role and task components |
| OpenRouter connection fails | Verify API key and model selection |

---

**🎉 You're ready to revolutionize your ComfyUI workflows with structured POML prompting!**

*Need help? The ComfyUI and POML communities are friendly and supportive. Don't hesitate to ask questions!*