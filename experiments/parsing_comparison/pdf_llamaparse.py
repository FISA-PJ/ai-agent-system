# pip install llama-cloud-services
import os
import time
from dotenv import load_dotenv
from llama_cloud_services import LlamaParse

load_dotenv()

llamaparse_api_key = os.getenv("LLAMAPARSE_API_KEY")

def pdf_llamaparse(file_path, output_dir, safe_name, split_by_page = False) : 
    start = time.time()
    parser = LlamaParse(
        api_key=llamaparse_api_key, 
        result_type = 'markdown',
        output_tables_as_HTML=True, # table expressed as html tag
        num_workers=4,  # if multiple files passed, split in `num_workers` API calls
        verbose=True,
        language="ko",  # Optionally you can define a language, default=en
    )
    
    result = parser.parse(file_path)
    
    end = time.time()
    
    markdown_docs = result.get_markdown_documents(split_by_page=split_by_page)
    
    # 📌 split_by_page = False
    # save
    out_path = os.path.join(output_dir, f"llamaparse-{safe_name}.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(markdown_docs[0].text)
        
    print(f"✅ Saved as upstage to {out_path}")

    # 📌 split_by_page = True
    # for i, doc in enumerate(markdown_docs):
    #     filename = f"llamaparse_page_{i+1}.md"
    #     filepath = os.path.join(output_dir, filename)

    #     with open(filepath, "w", encoding="utf-8") as f:
    #         f.write(doc.text)

    #     print(f"✅ Saved: {filepath}")
    
    return end - start
    