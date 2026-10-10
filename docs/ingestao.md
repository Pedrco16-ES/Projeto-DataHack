# Ingestão local — Etapa 3

Esta etapa produz tabelas administrativas tratadas, não indicadores públicos nem cargas PostgreSQL. Os originais permanecem em `../Dados`. Cada lote concluído fica em `data/processed/<batch_id>/`, ignorado pelo Git.

## Execução

Dentro de Projeto-DataHack, use o Python do venv:

```powershell
.\venv\Scripts\python.exe -m src.ingestion preview "..\Dados\indicadores_trajetoria_es_2015_2024\indicadores_trajetoria_educacao_superior_2015_2024.xlsx" --source trajetoria --edition 2024
.\venv\Scripts\python.exe -m src.ingestion process "..\Dados\indicadores_trajetoria_es_2015_2024\indicadores_trajetoria_educacao_superior_2015_2024.xlsx" --source trajetoria --edition 2024
.\venv\Scripts\python.exe -m src.ingestion process "..\Dados\microdados_censo_da_educacao_superior_2024\dados\MICRODADOS_CADASTRO_CURSOS_2024.CSV" --source censo_curso --edition 2024 --chunksize 25000
```

`preview` informa leiaute e colunas sem imprimir registros no terminal. A amostra pode ser visualizada na interface local:

```powershell
.\venv\Scripts\python.exe -m streamlit run admin.py --server.address=127.0.0.1
```

Selecione fonte, edição e arquivo, visualize a amostra, confirme a revisão e processe. O modo Disco local evita limites de upload. A interface não tem autenticação e não deve ser hospedada nem exposta na rede: contém dados sem supressão. O dashboard público será implementado separadamente.

CSV: cabeçalho nas primeiras 20 linhas, delimitador detectado e UTF-8 ou latin-1; `--encoding` e `--separator` permitem decisão explícita no processamento. Leitura pandas em blocos. XLSX: prévia com pandas.read_excel e processamento com openpyxl read_only + DataFrames por bloco, evitando carregar a planilha nacional inteira. `--sheet` seleciona aba; sem seleção, somente arquivos com uma aba são aceitos. JSON: lista de objetos tabulares, até 50 MB. ZIP: membro selecionado com `--member` quando há vários arquivos; cópia temporária controlada, sem extração dos caminhos fornecidos pelo arquivo, com limites de tamanho e compressão. XLS e ODS não são suportados nesta etapa.

## Contratos e granularidade

`src/ingestion/contracts/` registra contratos específicos do Censo de cursos 2021–2024 e da Trajetória edição 2024, com hash e caminho relativo do dicionário. As colunas dos quatro Censos foram confrontadas com seus respectivos dicionários locais. Colunas adicionais não reconhecidas bloqueiam a carga. A ausência de colunas obrigatórias bloqueia a carga; opcionais ausentes são listadas no relatório e não são fabricadas.

Trajetória: cabeçalho técnico na linha 9; chave candidata `(CO_IES, CO_CURSO, NU_ANO_INGRESSO, NU_ANO_REFERENCIA)`. Todos os anos de referência são preservados. `ANOS_DESDE_INGRESSO` é apenas a diferença calendárica referência menos ingresso, não uma convenção aprovada de horizonte.

Censo de cursos: chave candidata `(NU_ANO_CENSO, CO_IES, CO_CURSO, TP_DIMENSAO, CO_MUNICIPIO)` no recorte MT. O dicionário define dimensão 1 como presencial Brasil, 2 como EAD Brasil, 3 como EAD com dados somente no nível Brasil e 4 como EAD no exterior. Não somar observações nacionais e municipais. Não usar curso/ano como chave única para a base municipal EAD.

A unicidade é verificada dentro de cada lote. A consolidação entre arquivos, a chave definitiva da tabela PostgreSQL e a cobertura de junções pertencem à Etapa 4 e às análises seguintes.

Cadastro de IES não é importado nesta etapa: a edição 2021 contém CO_PROJETO, CO_LOCAL_OFERTA e NO_LOCAL_OFERTA não encontrados na aba do dicionário consultada; a granularidade precisa de revisão antes de um contrato próprio. Nenhuma coluna ambígua será mapeada automaticamente.

## Tratamento e reconciliação

- Preserva códigos como texto, inclusive zeros à esquerda existentes na fonte. Não inventa zeros perdidos em células originalmente numéricas.
- Remove espaços externos, padroniza cabeçalhos e reconhece vazio e ponto como ausentes. Não preenche valores ausentes com zero.
- Separa outros estados e registros sem alocação geográfica. UF não identificável sem dimensão que justifique a ausência vai para rejeição.
- No Censo 2022, UF 0 não é convertida para uma UF válida: dimensões 3/4 justificam exclusão por ausência de alocação estadual; dimensão 2 sem UF fica em rejeição para revisão.
- Valida os registros de MT: chaves, códigos, município, edição/período, modalidade, dimensão, contagens inteiras não negativas e taxas entre 0 e 100.
- Identifica todas as ocorrências de chaves repetidas no lote e as separa para revisão, inclusive quando cruzam blocos. Não escolhe automaticamente um registro vencedor.
- Reporta ausências e extremos. Outliers IQR são sinais para revisão; não causam exclusão. Não há agregação ou cálculo de taxas nesta etapa.
- Exige `recebidas = aceitas + rejeitadas + excluídas` antes de concluir o lote.

Somente o recorte MT é materializado para validação global de duplicidades e perfil; o consumo de memória final cresce com esse recorte, não é estritamente constante. Os registros de outros estados não recebem validação numérica completa.

## Rastreabilidade e arquivos

O SHA-256 do original, contrato, código e decisões define o identificador do lote. O original é verificado novamente ao final. Arquivos parciais ficam em diretório temporário; somente lotes completos são disponibilizados. Repetir o mesmo arquivo e decisões reutiliza o lote após conferir os hashes das saídas. Mudanças no contrato, código ou decisões criam outro lote; não substituem o anterior.

- `accepted.csv`: recorte MT tratado, UTF-8, sem aprovação analítica/pública.
- `rejected.csv`: registros rejeitados com motivos; erros de tipo preservam o conteúdo original. Rejeições por duplicidade são registradas na representação já normalizada.
- `excluded.csv`: número do registro e motivo de exclusão territorial; os demais campos continuam no original.
- `report.json`: contagens, hashes, chave, leiaute, ausências, perfil, alertas e decisão de mapeamento.

`_record_number` é a posição do registro de dados, iniciando em 1 após o cabeçalho. Não é necessariamente o número de linha física do CSV, pois campos podem conter quebras de linha. Ausentes nos CSVs tratados são representados por campo vazio; leitura posterior deve preservar os códigos como texto.

Os downloads administrativos CSV/XLSX neutralizam texto que possa ser interpretado como fórmula. Os CSVs internos do pipeline preservam os valores e não devem ser abertos como planilhas não confiáveis. Nenhum desses mecanismos substitui a supressão de pequenas células exigida para o dashboard público.

## Mapeamento manual

O arquivo JSON de mapeamento contém, por exemplo, `{"CODIGO_CURSO_ORIGEM": "CO_CURSO"}`. Use apenas após verificar a definição no dicionário:

```powershell
.\venv\Scripts\python.exe -m src.ingestion process "arquivo.csv" --source censo_curso --edition 2024 --mapping "mapeamento.json" --confirm-mapping --mapping-reason "Definição confrontada com o dicionário da edição"
```

Sem confirmação e justificativa, o mapeamento é rejeitado. Não inserir dados pessoais ou credenciais na justificativa.

## Próxima etapa

A Etapa 4 precisa das tabelas tratadas e dos relatórios de qualidade aqui produzidos. Antes de carregar, revisar rejeições, confirmar contratos/chaves e preparar migrations e transações. Um lote tratado não é automaticamente aprovado para persistência definitiva ou publicação.
