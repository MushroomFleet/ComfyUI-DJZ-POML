"""
Zenkai-POML: Prompt Orchestration Markup Language for ComfyUI

A custom ComfyUI node that brings Microsoft's POML capabilities to visual AI workflows.
Converts structured POML markup into optimized prompts for LLMs via OpenRouter/Sonnet 4.

Dependencies: See requirements.txt for full list
Core requirements: poml, pandas, PyPDF2, Pillow, requests, jsonschema

Author: Zenkai Labs  
License: MIT
Version: 1.0.0
"""

import re
import json
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import ParseError
import csv
import io
import os
from typing import Dict, Any, List, Tuple, Optional
import warnings

# Handle optional dependencies gracefully
DEPENDENCIES_AVAILABLE = {}

try:
    import poml
    DEPENDENCIES_AVAILABLE['poml'] = True
    print("✅ Official POML SDK loaded")
except ImportError:
    DEPENDENCIES_AVAILABLE['poml'] = False
    warnings.warn("⚠️ Official POML SDK not available. Using fallback parser.")

try:
    import pandas as pd
    DEPENDENCIES_AVAILABLE['pandas'] = True
except ImportError:
    DEPENDENCIES_AVAILABLE['pandas'] = False
    warnings.warn("⚠️ pandas not available. Advanced table processing disabled.")

try:
    from PIL import Image
    DEPENDENCIES_AVAILABLE['pillow'] = True
except ImportError:
    DEPENDENCIES_AVAILABLE['pillow'] = False
    warnings.warn("⚠️ Pillow not available. Image processing limited.")

try:
    import PyPDF2
    DEPENDENCIES_AVAILABLE['pypdf2'] = True
except ImportError:
    DEPENDENCIES_AVAILABLE['pypdf2'] = False
    warnings.warn("⚠️ PyPDF2 not available. PDF processing disabled.")

try:
    import requests
    DEPENDENCIES_AVAILABLE['requests'] = True
except ImportError:
    DEPENDENCIES_AVAILABLE['requests'] = False
    warnings.warn("⚠️ requests not available. External data fetching disabled.")

try:
    import jsonschema
    DEPENDENCIES_AVAILABLE['jsonschema'] = True
except ImportError:
    DEPENDENCIES_AVAILABLE['jsonschema'] = False
    warnings.warn("⚠️ jsonschema not available. JSON validation disabled.")

class POMLParser:
    """Enhanced POML parser that uses official SDK when available"""
    
    def __init__(self):
        self.variables = {}
        self.use_official_sdk = DEPENDENCIES_AVAILABLE.get('poml', False)
        
        # Note: Official POML SDK uses poml.poml() function, not a Parser class
    
    def parse(self, poml_text: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Parse POML markup and return structured data"""
        if context is None:
            context = {}
        
        self.variables.update(context)
        
        # Try official POML SDK first
        if self.use_official_sdk:
            try:
                return self._parse_with_official_sdk(poml_text, context)
            except Exception as e:
                warnings.warn(f"Official POML SDK failed: {e}. Falling back to custom parser.")
        
        # Fallback to custom parser
        return self._parse_with_fallback(poml_text, context)
    
    def _parse_with_official_sdk(self, poml_text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Use official POML SDK for parsing"""
        try:
            # Use official POML function
            result = poml.poml(poml_text, context=context, format="pydantic")
            
            # Extract role and task from messages if available
            role = ""
            task = ""
            examples = []
            output_format = ""
            
            # Parse messages to extract structured components
            if hasattr(result, 'messages') and result.messages:
                for message in result.messages:
                    if hasattr(message, 'speaker') and hasattr(message, 'content'):
                        content = str(message.content)
                        
                        # Try to extract role and task from system/human messages
                        if message.speaker == 'system':
                            if not role and 'role' in content.lower():
                                role = content
                            elif not task:
                                task = content
                        elif message.speaker == 'human' and not task:
                            task = content
            
            # If we couldn't extract role/task from messages, try raw parsing
            if not role or not task:
                # Fall back to basic text extraction
                if not role:
                    role = "AI Assistant"
                if not task:
                    task = "Help the user with their request"
            
            # Convert to our expected format
            return {
                'role': role,
                'task': task,
                'examples': examples,
                'output_format': output_format,
                'documents': [],
                'tables': [],
                'images': [],
                'variables': self.variables,
                'sdk_used': 'official',
                'raw_elements': [],
                'original_result': result  # Store original for debugging
            }
        except Exception as e:
            raise Exception(f"Official POML SDK parsing error: {e}")
    
    def _parse_with_fallback(self, poml_text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback custom parser implementation"""
        try:
            # Clean up the POML text
            cleaned_poml = self._preprocess_poml(poml_text)
            
            # Parse as XML
            root = ET.fromstring(cleaned_poml)
            
            # Extract components
            parsed_data = {
                'role': '',
                'task': '',
                'examples': [],
                'output_format': '',
                'documents': [],
                'tables': [],
                'images': [],
                'variables': self.variables,
                'sdk_used': 'fallback',
                'raw_elements': []
            }
            
            # Process all child elements
            for element in root:
                self._process_element(element, parsed_data)
            
            return parsed_data
            
        except ParseError as e:
            return {
                'error': f"POML parsing error: {str(e)}",
                'role': 'Assistant',
                'task': 'Help the user',
                'examples': [],
                'output_format': '',
                'documents': [],
                'tables': [],
                'images': [],
                'variables': {},
                'sdk_used': 'error',
                'raw_elements': []
            }
    
    def _preprocess_poml(self, poml_text: str) -> str:
        """Clean and prepare POML text for XML parsing"""
        # Ensure we have a root element
        if not poml_text.strip().startswith('<poml>'):
            poml_text = f"<poml>{poml_text}</poml>"
        
        # Handle self-closing tags
        poml_text = re.sub(r'<(\w+[^>]*)/>', r'<\1></\1>', poml_text)
        
        # Escape any unescaped special characters in text content
        # This is a simple approach - in production you'd want more robust handling
        return poml_text
    
    def _process_element(self, element: ET.Element, parsed_data: Dict[str, Any]) -> None:
        """Process individual POML elements"""
        tag = element.tag.lower()
        text = element.text or ""
        
        # Substitute variables in text
        text = self._substitute_variables(text)
        
        if tag == 'role':
            parsed_data['role'] = text.strip()
            
        elif tag == 'task':
            parsed_data['task'] = text.strip()
            
        elif tag == 'output-format' or tag == 'output_format':
            parsed_data['output_format'] = text.strip()
            
        elif tag == 'example':
            example = self._process_example(element)
            if example:
                parsed_data['examples'].append(example)
                
        elif tag == 'document':
            doc_info = self._process_document(element)
            parsed_data['documents'].append(doc_info)
            
        elif tag == 'table':
            table_info = self._process_table(element)
            parsed_data['tables'].append(table_info)
            
        elif tag == 'img' or tag == 'image':
            img_info = {
                'src': element.get('src', ''),
                'alt': element.get('alt', ''),
                'title': element.get('title', 'Image')
            }
            parsed_data['images'].append(img_info)
            
        elif tag == 'let':
            var_name = element.get('name')
            var_value = element.get('value', text.strip())
            if var_name:
                self.variables[var_name] = self._substitute_variables(var_value)
                
        # Store raw element for advanced processing
        parsed_data['raw_elements'].append({
            'tag': tag,
            'text': text,
            'attributes': element.attrib,
            'children': [child.tag for child in element]
        })
    
    def _process_example(self, element: ET.Element) -> Optional[Dict[str, str]]:
        """Process example elements"""
        example = {'input': '', 'output': ''}
        
        for child in element:
            child_tag = child.tag.lower()
            child_text = (child.text or "").strip()
            child_text = self._substitute_variables(child_text)
            
            if child_tag == 'input':
                example['input'] = child_text
            elif child_tag in ['output', 'o']:
                example['output'] = child_text
        
        # If no child elements, use element text as input
        if not example['input'] and not example['output'] and element.text:
            example['input'] = self._substitute_variables(element.text.strip())
            
        return example if (example['input'] or example['output']) else None
    
    def _process_table(self, element: ET.Element) -> Dict[str, Any]:
        """Process table elements with enhanced data handling"""
        table_info = {
            'title': element.get('title', 'Table'),
            'src': element.get('src', ''),
            'headers': [],
            'rows': [],
            'content': ''
        }
        
        # If external source is specified
        if table_info['src'] and os.path.exists(table_info['src']):
            try:
                content = self._load_table_from_file(table_info['src'])
                table_info['content'] = content
                return table_info
            except Exception as e:
                table_info['content'] = f"Error loading table from {table_info['src']}: {e}"
                return table_info
        
        # Process embedded table structure
        thead = element.find('thead')
        tbody = element.find('tbody')
        
        if thead is not None:
            header_row = thead.find('tr')
            if header_row is not None:
                table_info['headers'] = [th.text or '' for th in header_row.findall('th')]
        
        if tbody is not None:
            for row in tbody.findall('tr'):
                row_data = [td.text or '' for td in row.findall('td')]
                table_info['rows'].append(row_data)
        
        # Generate text representation
        if table_info['headers'] or table_info['rows']:
            lines = []
            if table_info['headers']:
                lines.append(' | '.join(table_info['headers']))
                lines.append('-' * len(lines[0]))
            for row in table_info['rows']:
                lines.append(' | '.join(str(cell) for cell in row))
            table_info['content'] = '\n'.join(lines)
        
        return table_info
    
    def _load_table_from_file(self, file_path: str) -> str:
        """Load table data from external files"""
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.csv':
            return self._load_csv_file(file_path)
        elif file_ext in ['.xlsx', '.xls']:
            return self._load_excel_file(file_path)
        else:
            # Try as plain text
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
    
    def _load_csv_file(self, file_path: str) -> str:
        """Load and format CSV file"""
        if DEPENDENCIES_AVAILABLE.get('pandas', False):
            # Use pandas for robust CSV processing
            try:
                df = pd.read_csv(file_path)
                return df.to_string(index=False)
            except Exception as e:
                warnings.warn(f"Pandas CSV processing failed: {e}. Using built-in csv module.")
        
        # Fallback to built-in csv module
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                rows = list(reader)
                if rows:
                    headers = rows[0]
                    data_rows = rows[1:]
                    
                    lines = [' | '.join(headers)]
                    lines.append('-' * len(lines[0]))
                    for row in data_rows:
                        lines.append(' | '.join(str(cell) for cell in row))
                    return '\n'.join(lines)
                return "Empty CSV file"
        except Exception as e:
            return f"Error loading CSV: {e}"
    
    def _load_excel_file(self, file_path: str) -> str:
        """Load and format Excel file"""
        if not DEPENDENCIES_AVAILABLE.get('openpyxl', False):
            return f"Excel processing requires openpyxl. Install with: pip install openpyxl"
        
        try:
            if DEPENDENCIES_AVAILABLE.get('pandas', False):
                df = pd.read_excel(file_path)
                return df.to_string(index=False)
            else:
                # Manual openpyxl processing
                import openpyxl
                workbook = openpyxl.load_workbook(file_path)
                sheet = workbook.active
                
                rows = []
                for row in sheet.iter_rows(values_only=True):
                    rows.append([str(cell) if cell is not None else '' for cell in row])
                
                if rows:
                    lines = [' | '.join(rows[0])]  # Headers
                    lines.append('-' * len(lines[0]))
                    for row in rows[1:]:
                        lines.append(' | '.join(row))
                    return '\n'.join(lines)
                return "Empty Excel file"
                
        except Exception as e:
            return f"Error loading Excel file: {e}"
    
    def _process_document(self, element: ET.Element) -> Dict[str, Any]:
        """Process document elements with file loading"""
        doc_info = {
            'src': element.get('src', ''),
            'title': element.get('title', 'Document'),
            'content': element.text or ""
        }
        
        # Load external document if source specified
        if doc_info['src'] and os.path.exists(doc_info['src']):
            try:
                doc_info['content'] = self._load_document_from_file(doc_info['src'])
            except Exception as e:
                doc_info['content'] = f"Error loading document: {e}"
        
        return doc_info
    
    def _load_document_from_file(self, file_path: str) -> str:
        """Load document content from various file types"""
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.pdf':
            return self._load_pdf_file(file_path)
        else:
            # Plain text files
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except UnicodeDecodeError:
                # Try different encoding
                with open(file_path, 'r', encoding='latin-1') as f:
                    return f.read()
    
    def _load_pdf_file(self, file_path: str) -> str:
        """Load and extract text from PDF files"""
        if not DEPENDENCIES_AVAILABLE.get('pypdf2', False):
            return f"PDF processing requires PyPDF2. Install with: pip install PyPDF2"
        
        try:
            import PyPDF2
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                text_parts = []
                for page in reader.pages:
                    text_parts.append(page.extract_text())
                return '\n\n'.join(text_parts)
        except Exception as e:
            return f"Error loading PDF: {e}"
    
    def _validate_json_context(self, json_str: str) -> Tuple[bool, Dict[str, Any], str]:
        """Validate JSON context with schema validation if available"""
        try:
            data = json.loads(json_str) if json_str.strip() else {}
            
            # Optional schema validation
            if DEPENDENCIES_AVAILABLE.get('jsonschema', False):
                # Basic schema for template variables
                schema = {
                    "type": "object",
                    "properties": {},
                    "additionalProperties": True
                }
                try:
                    jsonschema.validate(data, schema)
                except Exception as validation_error:
                    return False, {}, f"JSON schema validation failed: {validation_error}"
            
            return True, data, "Valid JSON"
            
        except json.JSONDecodeError as e:
            return False, {}, f"Invalid JSON: {e}"
    
    def _substitute_variables(self, text: str) -> str:
        """Substitute {{ variable }} patterns with values"""
        def replace_var(match):
            var_name = match.group(1).strip()
            return str(self.variables.get(var_name, f"{{{{{var_name}}}}}"))
        
        return re.sub(r'\{\{\s*([^}]+)\s*\}\}', replace_var, text)
    
    def render(self, parsed_data: Dict[str, Any], style: str = "standard") -> str:
        """Render parsed POML to plain text prompt"""
        parts = []
        
        # Role section
        if parsed_data.get('role'):
            if style == "optimized":
                parts.append(f"Role: {parsed_data['role']}")
            else:
                parts.append(parsed_data['role'])
        
        # Task section  
        if parsed_data.get('task'):
            if style == "optimized":
                parts.append(f"Task: {parsed_data['task']}")
            else:
                parts.append(parsed_data['task'])
        
        # Examples section
        if parsed_data.get('examples'):
            if style == "optimized":
                parts.append("Examples:")
            for i, example in enumerate(parsed_data['examples'], 1):
                if example['input'] and example['output']:
                    parts.append(f"Example {i}:")
                    parts.append(f"Input: {example['input']}")
                    parts.append(f"Output: {example['output']}")
                elif example['input']:
                    parts.append(f"Example {i}: {example['input']}")
        
        # Documents
        for doc in parsed_data.get('documents', []):
            if doc['content']:
                parts.append(f"Document - {doc['title']}:")
                parts.append(doc['content'])
        
        # Tables
        for table in parsed_data.get('tables', []):
            if table['content']:
                parts.append(f"Table - {table['title']}:")
                parts.append(table['content'])
        
        # Images (as alt text descriptions)
        for img in parsed_data.get('images', []):
            if img['alt']:
                parts.append(f"Image - {img['title']}: {img['alt']}")
        
        # Output format
        if parsed_data.get('output_format'):
            if style == "optimized":
                parts.append(f"Output Format: {parsed_data['output_format']}")
            else:
                parts.append(parsed_data['output_format'])
        
        # Join all parts
        if style == "debug":
            return "\n\n=== DEBUG MODE ===\n" + "\n\n".join(f"[{i}] {part}" for i, part in enumerate(parts, 1))
        else:
            return "\n\n".join(parts)


class ZenkaiPOMLProcessor:
    """
    ComfyUI Node: POML Processor
    
    Converts structured POML markup into rendered prompts for LLM processing
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "poml_template": ("STRING", {
                    "multiline": True, 
                    "default": '''<poml>
<role>You are a helpful AI assistant.</role>
<task>Assist the user with their request in a clear and helpful manner.</task>
<output-format>Provide a well-structured, informative response.</output-format>
</poml>'''
                }),
                "render_mode": (["standard", "optimized", "debug"], {"default": "standard"}),
            },
            "optional": {
                "variables_json": ("STRING", {
                    "multiline": True, 
                    "default": '{"user_name": "User", "topic": "AI"}',
                    "tooltip": "JSON object with template variables"
                }),
                "max_length": ("INT", {"default": 0, "min": 0, "max": 8000, "step": 100}),
            }
        }
    
    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("rendered_prompt", "metadata")
    FUNCTION = "process_poml"
    CATEGORY = "Zenkai/POML"
    
    def process_poml(self, poml_template: str, render_mode: str = "standard", 
                    variables_json: str = "{}", max_length: int = 0) -> Tuple[str, str]:
        """Process POML template and return rendered prompt"""
        
        # Validate and parse variables
        json_valid, variables, json_error = self._validate_json_context(variables_json)
        if not json_valid:
            error_prompt = f"JSON Variables Error: {json_error}\n\nFallback prompt active."
            metadata = json.dumps({"error": json_error, "mode": render_mode})
            return (error_prompt, metadata)
        
        # Initialize parser
        parser = POMLParser()
        
        # Parse POML
        parsed_data = parser.parse(poml_template, variables)
        
        # Check for errors
        if 'error' in parsed_data:
            error_prompt = f"POML Error: {parsed_data['error']}\n\nFallback: {parsed_data['role']} - {parsed_data['task']}"
            metadata = json.dumps({
                "error": parsed_data['error'], 
                "mode": render_mode,
                "dependencies": DEPENDENCIES_AVAILABLE
            })
            return (error_prompt, metadata)
        
        # Render to text
        rendered_prompt = parser.render(parsed_data, render_mode)
        
        # Apply length limit if specified
        if max_length > 0 and len(rendered_prompt) > max_length:
            rendered_prompt = rendered_prompt[:max_length] + "..."
        
        # Generate comprehensive metadata
        metadata = {
            "mode": render_mode,
            "sdk_used": parsed_data.get('sdk_used', 'unknown'),
            "components_found": {
                "role": bool(parsed_data.get('role')),
                "task": bool(parsed_data.get('task')),
                "examples": len(parsed_data.get('examples', [])),
                "documents": len(parsed_data.get('documents', [])),
                "tables": len(parsed_data.get('tables', [])),
                "images": len(parsed_data.get('images', [])),
                "output_format": bool(parsed_data.get('output_format'))
            },
            "variables_used": list(parsed_data.get('variables', {}).keys()),
            "prompt_length": len(rendered_prompt),
            "dependencies_status": DEPENDENCIES_AVAILABLE,
            "features_available": {
                "official_poml_sdk": DEPENDENCIES_AVAILABLE.get('poml', False),
                "advanced_tables": DEPENDENCIES_AVAILABLE.get('pandas', False),
                "pdf_processing": DEPENDENCIES_AVAILABLE.get('pypdf2', False),
                "image_processing": DEPENDENCIES_AVAILABLE.get('pillow', False),
                "external_data": DEPENDENCIES_AVAILABLE.get('requests', False),
                "json_validation": DEPENDENCIES_AVAILABLE.get('jsonschema', False)
            }
        }
        
        return (rendered_prompt, json.dumps(metadata, indent=2))
    
    def _validate_json_context(self, json_str: str) -> Tuple[bool, Dict[str, Any], str]:
        """Validate JSON context - moved to parser but kept for compatibility"""
        parser = POMLParser()
        return parser._validate_json_context(json_str)


class ZenkaiPOMLTemplate:
    """
    ComfyUI Node: POML Template Library
    
    Provides pre-built POML templates for common use cases
    """
    
    TEMPLATES = {
        "Analysis": '''<poml>
<role>You are an experienced analyst specializing in {{ analysis_type }}.</role>
<task>Analyze the provided {{ data_type }} and provide comprehensive insights.</task>
<example>
  <input>Sales data showing quarterly trends</input>
  <output>Key findings: Growth of 15% in Q3, seasonal patterns observed, recommendations for Q4 strategy.</output>
</example>
<output-format>Structure your analysis with: Summary, Key Findings, Insights, Recommendations.</output-format>
</poml>''',
        
        "Creative Writing": '''<poml>
<role>You are a creative writer with expertise in {{ genre }}.</role>
<task>Create {{ content_type }} based on the theme: {{ theme }}.</task>
<output-format style="tone: {{ tone }}; length: {{ length }}">
Write in an engaging {{ style }} style suitable for {{ audience }}.
</output-format>
</poml>''',
        
        "Technical Documentation": '''<poml>
<role>You are a technical writer specializing in {{ domain }}.</role>
<task>Create clear documentation for {{ subject }}.</task>
<output-format>
Use structured format with:
- Overview
- Key concepts  
- Step-by-step instructions
- Examples
- Troubleshooting tips
</output-format>
</poml>''',
        
        "Customer Support": '''<poml>
<role>You are a {{ company }} customer support specialist.</role>
<task>Help the customer with their {{ issue_type }} inquiry.</task>
<example>
  <input>How do I reset my password?</input>
  <output>I'll help you reset your password. Here are the steps: 1) Go to login page, 2) Click "Forgot Password", 3) Enter your email...</output>
</example>
<output-format style="tone: helpful; format: step-by-step">
Provide clear, actionable guidance with empathy.
</output-format>
</poml>''',
        
        "Data Analysis": '''<poml>
<role>You are a data scientist with expertise in {{ field }}.</role>
<task>Analyze the dataset and identify {{ analysis_focus }}.</task>
<table title="{{ dataset_name }}">
{{ table_data }}
</table>
<output-format style="format: executive-summary">
Present findings with statistical significance, trends, and actionable recommendations.
</output-format>
</poml>'''
    }
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "template_name": (list(cls.TEMPLATES.keys()), {"default": "Analysis"}),
            },
            "optional": {
                "template_variables": ("STRING", {
                    "multiline": True,
                    "default": '{"analysis_type": "business intelligence", "data_type": "quarterly reports"}',
                    "tooltip": "JSON with template-specific variables"
                }),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("poml_template",)
    FUNCTION = "get_template"
    CATEGORY = "Zenkai/POML"
    
    def get_template(self, template_name: str, template_variables: str = "{}") -> Tuple[str]:
        """Get a pre-built POML template with variable substitution"""
        
        template = self.TEMPLATES.get(template_name, self.TEMPLATES["Analysis"])
        
        # Apply any variable substitutions to template
        try:
            variables = json.loads(template_variables) if template_variables.strip() else {}
            parser = POMLParser()
            parser.variables = variables
            template = parser._substitute_variables(template)
        except json.JSONDecodeError:
            pass  # Use template as-is if variables are invalid
        
        return (template,)


# ComfyUI Node Registration
NODE_CLASS_MAPPINGS = {
    "ZenkaiPOMLProcessor": ZenkaiPOMLProcessor,
    "ZenkaiPOMLTemplate": ZenkaiPOMLTemplate,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ZenkaiPOMLProcessor": "POML Processor",
    "ZenkaiPOMLTemplate": "POML Template",
}
