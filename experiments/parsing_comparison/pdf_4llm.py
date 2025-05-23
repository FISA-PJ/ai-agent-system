# pip install -U langchain-pymupdf4llm
import os 
import time
import pymupdf4llm
import pathlib

def pdf4llm(file_path, output_dir, safe_name) :
    start = time.time()
    ## w/ llamaindex
    # llama_reader = pymupdf4llm.LlamaMarkdownReader()
    # llama_docs = llama_reader.load_data(file_path)
    
    # w/o llamaindex
    llama_docs = pymupdf4llm.to_markdown(file_path)
    end = time.time()
    
    # save 
    out_path = os.path.join(output_dir, f"pdf4llm-woLlama-{safe_name}.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(llama_docs)
    print(f"✅ Saved as pdf4llm to {out_path}")

    return end - start