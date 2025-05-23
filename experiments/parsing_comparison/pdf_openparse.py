# pip install openparse
import os
import time
import openparse

# conda activate 003_teest 
def pdf_openparse(file_path, output_dir, safe_name) :
    start = time.time()
    parser = openparse.DocumentParser()
    parsed_docs = parser.parse(file_path)
    
    end = time.time()
    text_list = []
    for node in parsed_docs.nodes :
        if hasattr(node, 'text') :
            text_list.append(node.text)
    text = '\n'.join(text_list)
    
    out_path = os.path.join(output_dir, f"openparse-{safe_name}.md")
    with open(out_path, 'w', encoding='utf-8') as f:
         f.write(text)
    
    print(f"✅ Saved as upstage to {out_path}")
    
    return end - start