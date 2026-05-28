# 科学数据源许可与合规矩阵 (Data Source License Matrix)

本文件覆盖商业版（Pro / 企业版）中所有可能访问外部网络的数据源；其中**开源免费版**仅包含 PubMed 与 RCSB PDB 两条。Science Skills 只提供自动化查询工具，不拥有第三方数据库数据版权；用户仍需遵守对应数据库、论文、预印本、模型服务和 API 的条款。

## 1. 数据源许可与合规矩阵一览

| 数据源 ID | 官方/主服务地址 | 镜像/替代源 | 覆盖技能 | 主要许可 / 使用条款 | 核心限制与合规注意事项 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| <code>alphafold</code> | <code>https://alphafold.ebi.ac.uk</code><br>Download: <code>https://alphafold.ebi.ac.uk/files/</code> | 无通用镜像；可通过 <code>SCIENCE_PROXY</code> 或企业 profile 配置 | <code>alphafold_database_fetch_and_analyze</code> | 数据库/服务自有条款；第三方数据可能另有许可证 | 遵守 EMBL-EBI AlphaFold 数据使用与引用要求。 |
| <code>alphagenome</code> | <code>https://deepmind.google.com/science/alphagenome/</code><br>Download: <code>https://storage.googleapis.com/alphagenome/reference/gencode/</code> | 无通用镜像；可通过 <code>SCIENCE_PROXY</code> 或企业 profile 配置 | <code>alphagenome_single_variant_analysis</code> | 数据库/服务自有条款；第三方数据可能另有许可证 | 遵守 AlphaGenome 服务、Google Cloud Storage 文件和模型使用条款。 |
| <code>arxiv</code> | <code>http://export.arxiv.org/api/query</code><br>Download: <code>https://arxiv.org/pdf/</code> | <code>https://export.arxiv.org/e-print/</code> | <code>literature_search_arxiv</code> | 论文级许可证各不相同；API 需礼貌访问 | 遵守 arXiv API 使用政策和论文原始许可证。 |
| <code>biorxiv</code> | <code>https://api.biorxiv.org</code> | <code>https://www.biorxiv.org</code> | <code>literature_search_biorxiv</code> | 预印本版权归作者/平台条款约束 | 遵守 bioRxiv/medRxiv API 与预印本版权条款。 |
| <code>chembl</code> | <code>https://www.ebi.ac.uk/chembl/api/data</code> | 无通用镜像；可通过 <code>SCIENCE_PROXY</code> 或企业 profile 配置 | <code>chembl_database</code> | 数据库/服务自有条款；第三方数据可能另有许可证 | 遵守 ChEMBL/EMBL-EBI 使用条款，注意第三方化合物数据来源。 |
| <code>clinicaltrials</code> | <code>https://clinicaltrials.gov/api/v2</code> | 无通用镜像；可通过 <code>SCIENCE_PROXY</code> 或企业 profile 配置 | <code>clinical_trials_database</code> | 数据库/服务自有条款；第三方数据可能另有许可证 | 遵守 ClinicalTrials.gov 使用政策，结果解释需保留 NCT ID。 |
| <code>clinvar</code> | <code>https://eutils.ncbi.nlm.nih.gov/entrez/eutils/</code> | <code>https://www.ncbi.nlm.nih.gov/clinvar/</code> | <code>clinvar_database</code> | 数据库/服务自有条款；第三方数据可能另有许可证 | 遵守 NCBI/ClinVar 使用政策，保留 Variation ID、RCV/VCV/HGVS 标识。 |
| <code>dbsnp</code> | <code>https://api.ncbi.nlm.nih.gov/variation/v0/</code> | <code>https://eutils.ncbi.nlm.nih.gov/entrez/eutils/</code> | <code>dbsnp_database</code> | 数据库/服务自有条款；第三方数据可能另有许可证 | 遵守 NCBI/dbSNP 使用政策，保留 rsID 与基因组版本。 |
| <code>ebi_ols</code> | <code>https://www.ebi.ac.uk/ols4/api</code> | 无通用镜像；可通过 <code>SCIENCE_PROXY</code> 或企业 profile 配置 | <code>embl_ebi_ols</code> | 数据库/服务自有条款；第三方数据可能另有许可证 | 遵守 EMBL-EBI OLS 与具体本体许可证，保留 ontology term IRI。 |
| <code>encode</code> | <code>https://www.encodeproject.org</code> | <code>https://screen-v2.wenglab.org</code><br><code>https://factorbook.api.wenglab.org/graphql</code> | <code>encode_ccres_database</code> | 数据库/服务自有条款；第三方数据可能另有许可证 | 遵守 ENCODE/SCREEN/Factorbook 数据使用和引用要求。 |
| <code>ensembl</code> | <code>https://rest.ensembl.org</code> | <code>https://grch37.rest.ensembl.org</code> | <code>ensembl_database</code> | 数据库/服务自有条款；第三方数据可能另有许可证 | 遵守 Ensembl REST 使用政策，保留 ENSG/ENST/ENSP 和 assembly 信息。 |
| <code>europepmc</code> | <code>https://www.ebi.ac.uk/europepmc/webservices/rest/</code> | <code>https://europepmc.org</code> | <code>literature_search_europepmc</code><br><code>pubmed_database</code> | 数据库/服务自有条款；第三方数据可能另有许可证 | 遵守 Europe PMC 使用条款；全文许可因论文而异。 |
| <code>foldseek</code> | <code>https://search.foldseek.com</code> | 无通用镜像；可通过 <code>SCIENCE_PROXY</code> 或企业 profile 配置 | <code>foldseek_structural_search</code> | 数据库/服务自有条款；第三方数据可能另有许可证 | 遵守 Foldseek 服务使用政策；避免高频批量提交。 |
| <code>gnomad</code> | <code>https://gnomad.broadinstitute.org/api</code> | 无通用镜像；可通过 <code>SCIENCE_PROXY</code> 或企业 profile 配置 | <code>gnomad_database</code> | gnomAD 数据使用政策和引用要求 | 遵守 gnomAD 数据使用政策，保留数据集版本和群体频率上下文。 |
| <code>gtex</code> | <code>https://gtexportal.org/api/v2</code> | 无通用镜像；可通过 <code>SCIENCE_PROXY</code> 或企业 profile 配置 | <code>gtex_database</code> | GTEx 使用条款和引用要求 | 遵守 GTEx Portal 使用和引用要求，保留组织与版本信息。 |
| <code>hpa</code> | <code>https://www.proteinatlas.org/api</code><br>Download: <code>https://www.proteinatlas.org/search/download/</code> | <code>https://v25.proteinatlas.org</code> | <code>human_protein_atlas_database</code> | Human Protein Atlas 自有许可，通常要求署名且限制再分发 | 遵守 Human Protein Atlas 许可和署名要求。 |
| <code>interpro</code> | <code>https://www.ebi.ac.uk/interpro/api</code> | 无通用镜像；可通过 <code>SCIENCE_PROXY</code> 或企业 profile 配置 | <code>interpro_database</code> | 数据库/服务自有条款；第三方数据可能另有许可证 | 遵守 InterPro/EMBL-EBI 使用条款，保留 accession 和 member database 信息。 |
| <code>jaspar</code> | <code>https://jaspar.elixir.no/api/v1</code> | 无通用镜像；可通过 <code>SCIENCE_PROXY</code> 或企业 profile 配置 | <code>jaspar_database</code> | 数据库/服务自有条款；第三方数据可能另有许可证 | 遵守 JASPAR 使用和引用要求，保留 matrix ID 与版本。 |
| <code>ncbi_sequence</code> | <code>https://eutils.ncbi.nlm.nih.gov/entrez/eutils/</code> | 无通用镜像；可通过 <code>SCIENCE_PROXY</code> 或企业 profile 配置 | <code>ncbi_sequence_fetch</code> | 数据库/服务自有条款；第三方数据可能另有许可证 | 遵守 NCBI 序列数据库使用政策，保留 accession、版本和数据库名称。 |
| <code>openalex</code> | <code>https://api.openalex.org</code><br>Download: <code>https://content.openalex.org</code> | 无通用镜像；可通过 <code>SCIENCE_PROXY</code> 或企业 profile 配置 | <code>literature_search_openalex</code> | CC0 1.0；Polite Pool 要求 mailto 标识 | 遵守 OpenAlex CC0 许可、Polite Pool mailto 要求和 API Key 使用条款。 |
| <code>openfda</code> | <code>https://api.fda.gov</code> | 无通用镜像；可通过 <code>SCIENCE_PROXY</code> 或企业 profile 配置 | <code>openfda_database</code> | 数据库/服务自有条款；第三方数据可能另有许可证 | 遵守 openFDA 使用政策，注意 FDA 数据免责声明。 |
| <code>opentargets</code> | <code>https://api.platform.opentargets.org/api/v4/graphql</code> | 无通用镜像；可通过 <code>SCIENCE_PROXY</code> 或企业 profile 配置 | <code>opentargets_database</code> | 数据库/服务自有条款；第三方数据可能另有许可证 | 遵守 Open Targets Platform 数据许可和引用要求。 |
| <code>pdb</code> | <code>https://data.rcsb.org</code><br>Download: <code>https://files.rcsb.org/download/</code> | <code>https://www.ebi.ac.uk/pdbe/</code> | <code>pdb_database</code> | CC0 1.0；学术引用为社区规范 | 遵守 RCSB PDB / wwPDB 数据使用和署名要求。 |
| <code>protein_msa</code> | <code>https://www.ebi.ac.uk/Tools/services/rest/clustalo/</code> | 无通用镜像；可通过 <code>SCIENCE_PROXY</code> 或企业 profile 配置 | <code>protein_sequence_msa</code> | 数据库/服务自有条款；第三方数据可能另有许可证 | 遵守 EMBL-EBI Job Dispatcher 使用条款，避免高频提交。 |
| <code>protein_similarity</code> | <code>https://www.ebi.ac.uk/Tools/services/rest/ncbiblast</code> | <code>https://api.colabfold.com</code> | <code>protein_sequence_similarity_search</code> | 数据库/服务自有条款；第三方数据可能另有许可证 | 遵守 EMBL-EBI BLAST 与 ColabFold/MMseqs2 服务使用政策。 |
| <code>pubchem</code> | <code>https://pubchem.ncbi.nlm.nih.gov</code> | <code>https://www.ebi.ac.uk/chembl/</code> | <code>pubchem_database</code> | 数据库/服务自有条款；第三方数据可能另有许可证 | 遵守 PubChem PUG-REST 使用政策和 NCBI 访问限制。 |
| <code>pubmed</code> | <code>https://eutils.ncbi.nlm.nih.gov</code> | <code>https://www.ebi.ac.uk/europepmc/webservices/rest/</code> | <code>pubmed_database</code> | 数据库/服务自有条款；第三方数据可能另有许可证 | 遵守 NCBI E-utilities 使用政策、速率限制和引用要求。 |
| <code>quickgo</code> | <code>https://www.ebi.ac.uk/QuickGO/services</code> | 无通用镜像；可通过 <code>SCIENCE_PROXY</code> 或企业 profile 配置 | <code>quickgo_database</code> | 数据库/服务自有条款；第三方数据可能另有许可证 | 遵守 QuickGO/ECO 使用条款，保留 GO/ECO accession。 |
| <code>reactome</code> | <code>https://reactome.org/ContentService</code> | <code>https://reactome.org/AnalysisService</code> | <code>reactome_database</code> | CC BY 4.0 | 遵守 Reactome 许可和引用要求，保留 pathway stable ID。 |
| <code>string</code> | <code>https://string-db.org/api</code> | 无通用镜像；可通过 <code>SCIENCE_PROXY</code> 或企业 profile 配置 | <code>string_database</code> | 数据库/服务自有条款；第三方数据可能另有许可证 | 遵守 STRING 许可、引用和调用频率要求。 |
| <code>ucsc</code> | <code>https://api.genome.ucsc.edu</code> | <code>https://genome.ucsc.edu/cgi-bin</code> | <code>ucsc_conservation_and_tfbs</code> | 数据库/服务自有条款；第三方数据可能另有许可证 | 遵守 UCSC Genome Browser 使用条件，保留 genome/db 和 track 信息。 |
| <code>unibind</code> | <code>https://unibind.uio.no/api</code> | 无通用镜像；可通过 <code>SCIENCE_PROXY</code> 或企业 profile 配置 | <code>unibind_database</code> | 数据库/服务自有条款；第三方数据可能另有许可证 | 遵守 UniBind 使用与引用要求，保留 TF、dataset 与坐标版本。 |
| <code>uniprot</code> | <code>https://rest.uniprot.org</code> | 无通用镜像；可通过 <code>SCIENCE_PROXY</code> 或企业 profile 配置 | <code>alphafold_database_fetch_and_analyze</code><br><code>protein_sequence_similarity_search</code><br><code>uniprot_database</code> | CC BY 4.0 | 遵守 UniProt 使用条款并保留 accession 等标识。 |

## 2. 分发红线

- 不把 API 查询源和大文件下载镜像混为一谈；网络 profile 中的镜像仅在明确标注 <code>download_only</code> 时用于下载路径。
- 不宣传规避第三方数据库速率限制、账号限制或商业使用条款。
- 不把网络失败静默伪装成成功；fallback 到替代源时必须在输出中说明实际来源。
- OpenAlex 请求必须提供 <code>OPENALEX_MAILTO</code> 或 <code>OPENALEX_API_KEY</code> 中至少一种身份配置；不得静默匿名大量抓取。
- 保留上游 Apache-2.0 代码许可证头和 CC-BY 4.0 文本署名要求。
