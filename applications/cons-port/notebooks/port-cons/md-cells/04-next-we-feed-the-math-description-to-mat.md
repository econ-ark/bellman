<!-- notebook cell 6 | id: e771cf0b -->
<!-- auto-extracted from solve_port_cons_ffp.ipynb -->

Next, we feed the math description to **matsya** to produce a `dolo-plus` stage YAML.  
Matsya is a RAG-backed LLM service: it retrieves relevant snippets from the BE-DDSL documentation, 
then asks a language model to translate the natural-language/LaTeX specification 
into strict `dolo-plus` syntax. The helper `matsya_translate` is a thin CLI wrapper
 — it takes a math description string, sends it to the Matsya endpoint, and returns 
 the generated YAML (or `None` if the service is unavailable).