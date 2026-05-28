# Chinese Scientific Query Policy

本策略用于把中文科研问题转换为数据库可执行参数，再把英文结果解释回中文。目标不是界面翻译，而是减少错误工具调用和错误数据库参数。

## 查询前

- 识别用户语言；包含中文时不要把原文直接传给需要英文参数的 API。
- 先抽取科研实体：疾病、基因、蛋白、药物、物种、变异、文献类型、时间范围。
- 优先转成数据库可理解的英文术语、标准 ID 或检索语法。
- PubMed 查询优先使用 MeSH、Title/Abstract 关键词、Boolean 逻辑、Publication Type 和 Date - Publication。
- 如果实体无法可靠规范化，使用保守英文关键词 fallback，并在结果解释中说明不确定性。

## 查询后

- 保留 PMID、DOI、MeSH、UniProt Accession、PDB ID、CID 等英文标识符。
- 英文标题和摘要应以中文总结，但不得编造数据库没有返回的结论。
- 网络失败、0 结果、拼写歧义和术语不确定必须显式说明。

## PubMed MVP

- `skills/pubmed_database/scripts/pubmed_query_normalizer.py` 提供第一版规则化中文到 PubMed query 转换。
- `search_pubmed` 会在收到中文 query 时自动调用规范化层。
- `normalize_pubmed_query` 可在不访问网络的情况下预览转换结果，适合调试中文输入。

## UniProt MVP

- `skills/uniprot_database/scripts/uniprot_query_normalizer.py` 提供中文到 UniProt query 转换。
- `search_proteins`、`get_count`、`stream_results` 会在收到中文 query 时自动调用规范化层。
- `normalize_uniprot_query` 可在不访问网络的情况下预览转换结果，适合调试中文输入。

## PDB MVP

- `skills/pdb_database/scripts/pdb_query_normalizer.py` 提供中文到 PDB query 转换。
- `search_pdb.py` 在收到中文 query（无论是结构化 JSON 还是自由文本）时自动解析并递归转换叶子节点，或打包为 full_text 全文检索。
- 支持 `normalize` 子命令进行转换预览。

## PubChem MVP

- `skills/pubchem_database/scripts/pubchem_query_normalizer.py` 提供中文化学/药物名词到英文的转换。
- 在 `pubchem_api.py` 的 `resolve` 接口中对 `name` 进行拦截转换。
- 支持 `normalize` 子命令进行转换预览，并对单字 "水" 进行了防误匹配边界过滤保护。

## OpenAlex MVP

- `skills/literature_search_openalex/scripts/openalex_query_normalizer.py` 提供中文学术名词到英文的转换。
- 在 `openalex_cli.py` 的 `resolve`（`args.query`）和 `filter`（`args.search`）接口中拦截转换。
- 支持 `normalize` 子命令进行转换预览，自动过滤学术停用词和修饰词并保留非中文 token。

## Ensembl MVP

- `skills/ensembl_database/scripts/ensembl_query_normalizer.py` 提供中文基因查询到 Ensembl symbol/species 的转换。
- `ensembl_api.py` 的 `resolve-gene` 和 `canonical-tss` 会在收到中文 gene query 时自动规范化 gene symbol，并识别人类/小鼠物种提示。
- 规范化层保守处理基因 token，不确定时不会编造 ENSG/ENST/ENSP ID。

## ChEMBL MVP

- `skills/chembl_database/scripts/chembl_query_normalizer.py` 提供常见中文药物名和活性概念到 ChEMBL search query 的转换。
- `chembl_api.py` 的可搜索 endpoint（如 `molecule`、`target`、`activity`）会在 `--search` 输入包含中文时先规范化。
- 目前优先覆盖常见药物名和 `inhibitor`/`agonist`/`antagonist`/`target` 等检索概念。

## ClinVar MVP

- `skills/clinvar_database/scripts/clinvar_query_normalizer.py` 提供中文临床变异问题到 NCBI Entrez query 的转换。
- `ClinVarClient.count_variants` 和 `ClinVarClient.search_variants` 会把中文输入转换为 `GENE[gene]`、疾病英文词和 `clinical_significance` 条件。
- 结果解释必须保留 ClinVar Variation ID、RCV/VCV、HGVS 等英文标识符。

## dbSNP MVP

- `skills/dbsnp_database/scripts/dbsnp_query_normalizer.py` 提供 rsID 与 HGVS token 抽取。
- `dbsnp_cli.py` 的 rsID 查询和 HGVS 解析入口会从中文句子中提取 `rs...` 或 HGVS 表达式。
- 未识别到标准 token 时保留原输入，由 dbSNP 脚本返回明确错误，不静默猜测变异。

## gnomAD MVP

- `skills/gnomad_database/scripts/gnomad_query_normalizer.py` 提供中文 gene query 到 gnomAD gene symbol/consequence 的转换。
- `search_variants.py` 会规范化 gene symbol，并在未显式传入 consequence 时识别中文“错义”或 LoF 类提示。
- `get_gene_constraint.py` 会规范化 gene symbol，用于中文约束指标查询。

## AlphaFold MVP

- `skills/alphafold_database_fetch_and_analyze/scripts/alphafold_query_normalizer.py` 提供 UniProt accession 抽取和少量高置信别名映射。
- `fetch_structure.py` 会从中文输入中提取 UniProt accession；目前仅对 `TP53`/`P53` 等明确别名做保守映射。
- 对普通蛋白中文名仍应优先要求用户提供 UniProt Accession，避免下载错误结构。
