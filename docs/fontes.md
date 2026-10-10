# Fontes locais — diagnóstico de 10/10/2026

Dados ficam em ../Dados, fora do repositório do projeto: cerca de 2,21 GB. Censo 2015–2024 com CSV de cursos/IES e dicionários; Trajetória 2015–2024 com XLSX e dicionário DOCX; CPC 2015–2019 e 2021–2023. Não foram localizados Enade 2025 das licenciaturas, população municipal IBGE de 18–24 anos ou geometrias.

Trajetória: nomes técnicos na linha 9; arquivo identificado como coorte 2015. Coluna técnica TADA, apesar do rótulo visual TDAN. Ordem das colunas difere do dicionário. Censo 2021/2022/2023/2024: 200/200/202/223 colunas, cabeçalhos lidos com separador ; e latin-1. Confirmar cada edição durante a ingestão.

Na Etapa 1 não houve validação integral das linhas, chaves ou hashes. Na Etapa 3, a Trajetória e os Censos de cursos 2021–2024 foram lidos integralmente, com validação estrutural do recorte MT, hashes, reconciliação e relatórios. Consulte validacao.md para resultados e limitações; não há indicadores aprovados. Arquivos XLS antigos precisarão de leitor adicional ou conversão documentada; não estão cobertos por openpyxl. Arquivos temporários iniciados por ~$ são excluídos da descoberta de fontes.

Os contratos de cursos de 2021–2024 foram confrontados com a aba cadastro_cursos de cada dicionário local; todas as colunas desses quatro CSVs foram encontradas. O cadastro de IES de 2021 tem três campos não localizados na aba consultada: CO_PROJETO, CO_LOCAL_OFERTA e NO_LOCAL_OFERTA. Sua ingestão depende de revisão própria.

A dimensão geográfica do Censo é determinante: TP_DIMENSAO distingue presencial Brasil, EAD Brasil, EAD agregado Brasil e EAD exterior. Cursos EAD se repetem por município. Os dados nacionais e municipais não podem ser somados indiscriminadamente. Na edição 2022, registros nacionais/exteriores podem apresentar UF 0.
