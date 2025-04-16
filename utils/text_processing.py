import re
from typing import List, Tuple
def highlight_key_sections(text: str) -> str:
    """
    Identify and highlight key sections in the text.
    Returns HTML with highlighted sections.
    """
    # Split text into paragraphs
    paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
    
    # Simple heuristic to identify important paragraphs
    important_paragraphs = []
    for para in paragraphs:
        # Check for headings (all caps or followed by colon)
        if (para.isupper() and len(para.split()) < 10) or ':' in para[:50]:
            important_paragraphs.append((para, "heading"))
        # Check for dense information (numbers, bullet points, etc.)
        elif (len(re.findall(r'\d+', para)) > 3 or 
              any(c in para for c in ['•', '- ', '* '])):
            important_paragraphs.append((para, "key_info"))
        # Check for conclusion-like phrases
        elif any(phrase in para.lower() for phrase in 
                ['conclusion', 'summary', 'key findings', 'recommendation']):
            important_paragraphs.append((para, "conclusion"))
    
    # Convert to HTML with highlights
    html_content = []
    for para, para_type in important_paragraphs:
        if para_type == "heading":
            html_content.append(f'<h3 style="color: #2b5876; background-color: #f0f8ff; padding: 8px; border-radius: 5px;">{para}</h3>')
        elif para_type == "key_info":
            html_content.append(f'<p style="background-color: #f8f9fa; border-left: 4px solid #4285f4; padding: 10px; margin: 10px 0;">{para}</p>')
        elif para_type == "conclusion":
            html_content.append(f'<p style="background-color: #fcf8e3; border: 1px solid #faebcc; padding: 10px; border-radius: 5px;">{para}</p>')
    
    # Add non-highlighted paragraphs
    highlighted_paras = {para for para, _ in important_paragraphs}
    for para in paragraphs:
        if para not in highlighted_paras:
            html_content.append(f'<p>{para}</p>')
    
    # Generate the final HTML
    html_output = '<div style="font-family: Arial, sans-serif;">\n'
    html_output += '\n'.join(html_content)
    html_output += '\n</div>'
    
    return html_output