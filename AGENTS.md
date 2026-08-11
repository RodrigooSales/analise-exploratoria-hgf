# AGENTS.md

## Projeto: Análise Exploratória de IMC e FINDRISC em Pacientes com Doenças Autoimunes

### Objetivo deste arquivo

Este documento define as regras científicas, estatísticas, técnicas e operacionais para o desenvolvimento da análise exploratória de dados em Python/Jupyter Notebooks a partir do arquivo sociodemográfico de pacientes de um hospital.

O estudo será desenvolvido com foco em publicação em congresso regional na área médica.

O agente responsável por implementar a análise deve seguir este arquivo como especificação principal do projeto.

---

# 1. Objetivo científico

O objetivo principal do estudo é investigar o perfil nutricional e o risco metabólico de pacientes com doenças autoimunes acompanhados no hospital, tendo como variáveis centrais:

- Índice de Massa Corporal (IMC);
- FINDRISC;
- características clínicas;
- características sociodemográficas.

A pergunta científica principal é:

> Existe associação entre o estado nutricional, avaliado pelo IMC, e o risco de desenvolvimento de diabetes mellitus tipo 2, avaliado pelo FINDRISC, em pacientes com doenças autoimunes?

Perguntas complementares:

1. Qual é o perfil de IMC da população estudada?
2. Qual é o perfil de risco pelo FINDRISC?
3. Qual é a prevalência de sobrepeso?
4. Qual é a prevalência de obesidade?
5. Qual é a prevalência de FINDRISC elevado?
6. Maiores valores de IMC estão associados a maiores valores de FINDRISC?
7. Variáveis clínicas e sociodemográficas apresentam associações exploratórias com IMC ou FINDRISC?

---

# 2. Definição da população

A análise principal deve considerar os pacientes com doenças autoimunes como **um único grupo**.

Não dividir a análise principal por diagnóstico específico.

Não utilizar como hipótese principal comparações entre:

- lúpus;
- artrite reumatoide;
- espondiloartrite;
- síndrome antifosfolípide;
- outras doenças autoimunes.

O diagnóstico específico deverá ser preservado e utilizado para caracterização descritiva da população.

A decisão de utilizar um único grupo tem como objetivo preservar o tamanho amostral e evitar análises inferenciais com subgrupos excessivamente pequenos.

---

# 3. Regra sobre diabetes previamente diagnosticado

Não excluir pacientes com base na possibilidade de diagnóstico prévio de diabetes.

Não criar análise de sensibilidade específica baseada em diabetes prévio.

Não estratificar a população com base nessa condição.

Não utilizar diabetes previamente diagnosticado como critério de inclusão ou exclusão da análise principal.

---

# 4. Estrutura do projeto

Utilizar a seguinte estrutura:

```text
estudo_autoimunes/
│
├── data/
│   ├── raw/
│   │   └── sociodemografico.csv
│   │
│   └── processed/
│       └── pacientes_clean.csv
│
├── notebooks/
│   ├── 00_data_audit.ipynb
│   ├── 01_data_cleaning.ipynb
│   ├── 02_population_description.ipynb
│   ├── 03_imc_analysis.ipynb
│   ├── 04_findrisc_analysis.ipynb
│   ├── 05_imc_findrisc_analysis.ipynb
│   ├── 06_secondary_analysis.ipynb
│   └── 07_tables_and_figures.ipynb
│
├── src/
│   ├── cleaning.py
│   ├── variables.py
│   ├── statistics.py
│   └── plots.py
│
├── outputs/
│   ├── figures/
│   └── tables/
│
├── requirements.txt
└── AGENTS.md
```

---

# 5. Princípio de reprodutibilidade

O arquivo original em `data/raw/` nunca deve ser alterado.

Todo tratamento deve gerar um novo arquivo processado.

Fluxo obrigatório:

```text
RAW DATA
   ↓
AUDITORIA
   ↓
LIMPEZA
   ↓
DATASET PROCESSADO
   ↓
EDA
   ↓
ANÁLISES
   ↓
TABELAS E FIGURAS
```

Toda transformação deve ser reproduzível por código.

Evitar qualquer correção manual diretamente no CSV.

---

# 6. Privacidade e proteção de dados

O banco contém informações clínicas sensíveis.

A coluna contendo nome do paciente não deve aparecer:

- em gráficos;
- em tabelas;
- em logs;
- em outputs;
- em mensagens de erro;
- em arquivos exportados;
- em notebooks de análise;
- em prints de DataFrames utilizados em apresentações.

Criar um identificador interno:

```text
patient_id
```

Exemplo:

```text
P001
P002
P003
...
```

Após a criação do identificador, remover o nome da versão analítica.

A versão processada utilizada nas análises deve ser anonimizada.

Nunca exibir dados individualizados que permitam reidentificação.

---

# 7. Notebook 00 — Auditoria do banco

Arquivo:

```text
notebooks/00_data_audit.ipynb
```

Objetivo:

> Determinar se o banco está consistente e adequado para análise.

Realizar obrigatoriamente:

```python
df.shape
df.info()
df.head()
df.tail()
df.isna().sum()
df.nunique()
df.duplicated().sum()
```

Avaliar:

- número de linhas;
- número de colunas;
- tipos de dados;
- linhas vazias;
- duplicatas;
- dados ausentes;
- variáveis numéricas armazenadas como texto;
- inconsistências de grafia;
- espaços antes/depois de textos;
- valores biologicamente implausíveis;
- variáveis completamente vazias.

Gerar relatório de auditoria.

---

# 8. Identificação da amostra real

O arquivo original possui aproximadamente 100 linhas, mas somente cerca de 75 correspondem a pacientes preenchidos.

O agente deve identificar programaticamente os registros válidos antes da análise.

Uma possível regra é:

```python
df = df[df["nome"].notna()].copy()
```

A regra definitiva deve ser validada pela estrutura real do banco.

O notebook deve registrar:

```text
Número de linhas do arquivo original
Número de registros excluídos por ausência de paciente
Número final de pacientes analisáveis
```

Nunca utilizar o total bruto de linhas do CSV como denominador epidemiológico.

---

# 9. Notebook 01 — Limpeza e padronização

Arquivo:

```text
notebooks/01_data_cleaning.ipynb
```

Responsabilidades:

- remover linhas vazias;
- anonimizar os pacientes;
- remover espaços extras;
- padronizar strings;
- converter variáveis numéricas;
- criar variáveis derivadas;
- validar faixas;
- padronizar diagnósticos;
- recalcular categorias de IMC;
- recalcular categorias de FINDRISC;
- salvar `pacientes_clean.csv`.

Nenhuma análise inferencial deve ser realizada nesse notebook.

---

# 10. Padronização do IMC

O banco possui valores potencialmente representados com vírgula ou ponto decimal.

Exemplos:

```text
28,5
27.06
38,74
32
```

Converter para valor numérico `float`.

Exemplo esperado:

```text
28.50
27.06
38.74
32.00
```

Não interpretar falha de conversão como zero.

Valores impossíveis devem virar `NaN` e gerar alerta de auditoria.

---

# 11. Classificação clínica do IMC

Criar a variável:

```text
imc_categoria
```

Utilizar as seguintes regras:

| IMC | Categoria |
|---|---|
| < 18,5 | Baixo peso |
| 18,5 a < 25 | Peso normal |
| 25 a < 30 | Sobrepeso |
| 30 a < 35 | Obesidade grau I |
| 35 a < 40 | Obesidade grau II |
| ≥ 40 | Obesidade grau III |

Implementação recomendada:

```python
def classificar_imc(imc):
    if pd.isna(imc):
        return pd.NA
    if imc < 18.5:
        return "Baixo peso"
    elif imc < 25:
        return "Peso normal"
    elif imc < 30:
        return "Sobrepeso"
    elif imc < 35:
        return "Obesidade grau I"
    elif imc < 40:
        return "Obesidade grau II"
    else:
        return "Obesidade grau III"
```

---

# 12. Indicadores derivados do IMC

Criar:

```text
excesso_peso
obesidade
```

Definições:

```python
excesso_peso = IMC >= 25
obesidade = IMC >= 30
```

Essas variáveis devem manter `NaN` quando o IMC original estiver ausente.

Nunca converter missing em `False`.

---

# 13. Extração do FINDRISC

O campo FINDRISC pode conter número + texto.

Exemplos:

```text
23 (Muito Alto Risco)
16 (Risco Moderado)
17 (Alto Risco)
```

Extrair apenas a pontuação numérica.

Criar:

```text
findrisc_score
```

A classificação textual originalmente digitada não deve ser utilizada como fonte final de verdade.

---

# 14. Classificação automática do FINDRISC

Criar:

```text
findrisc_categoria
```

Utilizar exclusivamente a pontuação numérica.

Regras:

| Pontuação | Categoria |
|---|---|
| < 7 | Baixo risco |
| 7–11 | Leve/moderado |
| 12–14 | Moderado |
| 15–20 | Alto |
| > 20 | Muito alto |

Implementação recomendada:

```python
def classificar_findrisc(score):
    if pd.isna(score):
        return pd.NA
    if score < 7:
        return "Baixo risco"
    elif score <= 11:
        return "Leve/moderado"
    elif score <= 14:
        return "Moderado"
    elif score <= 20:
        return "Alto"
    else:
        return "Muito alto"
```

A classificação recalculada deve prevalecer sobre o texto original.

---

# 15. Indicador de FINDRISC elevado

Criar:

```text
findrisc_alto
```

Definição:

```python
findrisc_alto = findrisc_score >= 15
```

Interpretação:

```text
False = FINDRISC < 15
True  = FINDRISC ≥ 15
```

O indicador representa as categorias:

```text
Alto + Muito alto
```

Manter `NaN` quando FINDRISC estiver ausente.

---

# 16. Padronização dos diagnósticos

Criar duas variáveis:

```text
diagnostico_original
diagnostico_padronizado
```

Nunca sobrescrever o diagnóstico original.

Executar:

- `strip()`;
- padronização de capitalização quando apropriado;
- normalização de grafias;
- mapeamento documentado.

Exemplos que podem necessitar normalização:

```text
Lúpus Eritematoso
Lúpus Eritematoso 
Lúpus Eritematoso, Fibromialgia
```

O agente deve manter uma tabela de mapeamento explícita.

---

# 17. Uso do diagnóstico na análise

O diagnóstico específico deverá ser usado inicialmente apenas para:

- caracterizar a amostra;
- apresentar distribuição de doenças;
- informar n e percentual.

Não realizar como análise principal:

```text
Lúpus × FINDRISC
Artrite reumatoide × FINDRISC
Espondiloartrite × FINDRISC
```

Não fragmentar a coorte para inferência principal.

---

# 18. Notebook 02 — Caracterização da população

Arquivo:

```text
notebooks/02_population_description.ipynb
```

Produzir a caracterização global da amostra.

## Variáveis sociodemográficas

Quando disponíveis:

- estado civil;
- escolaridade;
- renda familiar;
- ocupação.

## Variáveis clínicas

Quando disponíveis:

- diagnóstico;
- tempo de doença;
- uso de corticoide;
- uso de imunobiológico;
- comorbidades;
- tabagismo;
- etilismo;
- atividade física.

## Variáveis antropométricas

- IMC;
- categoria do IMC;
- circunferência abdominal;
- circunferência cervical.

## Variáveis metabólicas

- FINDRISC;
- categoria FINDRISC.

---

# 19. Estatística descritiva de variáveis quantitativas

Para cada variável quantitativa relevante calcular:

```text
n válido
média
moda
desvio-padrão
mediana
P25
P75
mínimo
máximo
```

Não escolher a medida de tendência central exclusivamente com base em teste automático de normalidade.

A distribuição deve ser avaliada visualmente e numericamente.

Para o texto científico:

- usar `média ± DP` quando adequado;
- usar `mediana [P25–P75]` quando adequado;
- manter ambos disponíveis na EDA.

---

# 20. Estatística descritiva de variáveis categóricas

Apresentar:

```text
n (%)
```

O denominador percentual deve ser o número de observações válidas daquela variável.

Nunca usar automaticamente o N total quando existirem dados ausentes.

Exemplo:

```text
Atividade física
Sim: n (%)
Não: n (%)
Missing: n
```

---

# 21. Dados ausentes

Missing data deve ser tratado como parte explícita da análise exploratória.

Gerar tabela contendo:

| Variável | N válido | N ausente | % ausente |
|---|---:|---:|---:|

Gerar também visualização de dados ausentes.

Variáveis com alto percentual de missing não devem automaticamente participar de análises inferenciais.

O agente deve informar claramente o N utilizado em cada análise.

Nunca imputar dados sem decisão metodológica explícita.

---

# 22. Notebook 03 — Análise exploratória do IMC

Arquivo:

```text
notebooks/03_imc_analysis.ipynb
```

Analisar o IMC como variável contínua.

Gerar:

- histograma;
- curva de densidade quando apropriada;
- boxplot;
- Q-Q plot.

Calcular:

```text
n
média
moda
desvio-padrão
mediana
P25
P75
mínimo
máximo
```

Investigar outliers.

Não remover outliers automaticamente.

---

# 23. Análise das categorias de IMC

Apresentar:

```text
Baixo peso
Peso normal
Sobrepeso
Obesidade grau I
Obesidade grau II
Obesidade grau III
```

Gerar gráfico de barras com:

```text
n
%
```

Dar destaque adicional a:

```text
IMC ≥ 25 → excesso de peso
IMC ≥ 30 → obesidade
```

Essas duas proporções são resultados epidemiológicos de interesse.

---

# 24. Notebook 04 — Análise exploratória do FINDRISC

Arquivo:

```text
notebooks/04_findrisc_analysis.ipynb
```

Analisar FINDRISC como variável numérica e categórica.

Para o escore contínuo gerar:

- histograma;
- boxplot;
- curva de densidade quando apropriada.

Calcular:

```text
n
média
moda
desvio-padrão
mediana
P25
P75
mínimo
máximo
```

Para as categorias apresentar:

```text
Baixo risco
Leve/moderado
Moderado
Alto
Muito alto
```

com `n (%)`.

---

# 25. Prevalência de FINDRISC elevado

Calcular especificamente:

```text
FINDRISC ≥ 15
```

Apresentar:

```text
n
%
IC95% da proporção, quando apropriado
```

O cálculo final deve utilizar apenas os pacientes com FINDRISC válido.

---

# 26. Notebook 05 — Relação IMC × FINDRISC

Arquivo:

```text
notebooks/05_imc_findrisc_analysis.ipynb
```

Essa é a análise principal do estudo.

Selecionar apenas pacientes com:

```text
IMC válido
E
FINDRISC válido
```

Registrar explicitamente o N da análise.

Gerar scatter plot:

```text
X = IMC
Y = FINDRISC
```

Cada ponto deve representar um paciente anonimizado.

Não colocar identificadores dos pacientes na figura.

---

# 27. Correlação de Spearman

Utilizar a correlação de Spearman como análise principal.

Implementação:

```python
from scipy.stats import spearmanr
```

Reportar:

```text
rho de Spearman
IC95%
p-valor
N
```

O intervalo de confiança deve ser obtido preferencialmente por bootstrap.

Recomendações:

- utilizar semente aleatória fixa;
- documentar número de reamostragens;
- utilizar pelo menos 5.000 reamostragens quando computacionalmente viável;
- preferir 10.000 para o resultado final.

Nunca reportar apenas p-valor.

---

# 28. Interpretação da correlação

A magnitude da associação deve ser interpretada com cautela.

O agente não deve tratar correlação como causalidade.

Evitar frases como:

```text
"O aumento do IMC causa aumento do FINDRISC."
```

Preferir:

```text
"Observou-se associação positiva entre IMC e FINDRISC."
```

ou:

```text
"Maiores valores de IMC estiveram associados a maiores escores FINDRISC."
```

---

# 29. Limitação estrutural: IMC compõe o FINDRISC

Esse é um ponto metodológico obrigatório.

O IMC faz parte da construção do próprio escore FINDRISC.

Portanto, existe acoplamento matemático entre as variáveis.

A associação observada entre IMC e FINDRISC é parcialmente esperada por construção do escore.

Essa questão:

- não invalida a análise;
- deve ser explicitada;
- impede tratar as variáveis como completamente independentes.

O resultado deve ser interpretado levando essa característica em consideração.

Esse ponto deverá aparecer posteriormente:

- nos métodos;
- na discussão;
- nas limitações.

---

# 30. Possibilidade futura: FINDRISC sem componente de IMC

Caso futuramente estejam disponíveis as respostas individuais de todos os componentes do FINDRISC, pode-se considerar uma análise complementar com:

```text
FINDRISC_sem_IMC
```

e investigar:

```text
IMC × FINDRISC_sem_IMC
```

Essa análise não deve ser realizada com o banco atual caso os componentes necessários não estejam disponíveis.

Nunca reconstruir ou inventar componentes ausentes.

---

# 31. Notebook 06 — Análises secundárias

Arquivo:

```text
notebooks/06_secondary_analysis.ipynb
```

Após a análise principal, podem ser realizadas análises exploratórias envolvendo:

## Corticoide

```text
uso de corticoide × IMC
uso de corticoide × FINDRISC
```

## Atividade física

```text
atividade física × IMC
atividade física × FINDRISC
```

## Imunobiológicos

```text
imunobiológico × IMC
imunobiológico × FINDRISC
```

## Outros fatores

Quando os dados forem suficientes:

- tabagismo;
- etilismo;
- renda;
- escolaridade;
- tempo de doença.

Todas essas análises devem ser explicitamente classificadas como:

```text
ANÁLISES EXPLORATÓRIAS SECUNDÁRIAS
```

Não devem substituir a hipótese principal.

---

# 32. Controle de múltiplas análises

O agente não deve realizar dezenas de testes estatísticos indiscriminadamente em busca de `p < 0,05`.

Toda análise deve ser classificada como:

```text
principal
secundária
exploratória
```

Se múltiplos testes relacionados forem realizados, considerar correção por múltiplas comparações quando metodologicamente apropriado.

Preferir Holm quando houver necessidade de ajuste.

---

# 33. Análises de sensibilidade

## Diagnósticos múltiplos

A análise principal utiliza todos os pacientes elegíveis.

Como análise de sensibilidade, pode-se comparar o resultado com pacientes que possuam apenas um diagnóstico autoimune registrado.

Objetivo:

> verificar se a associação IMC × FINDRISC permanece estável diante da composição clínica da amostra.

Não utilizar essa análise para escolher o resultado com menor p-valor.

## Outliers

Executar a análise principal com todos os dados válidos.

Valores extremos devem ser investigados.

Classificar como:

```text
erro de digitação
erro de transformação
valor biologicamente implausível
valor extremo verdadeiro
```

Um valor extremo verdadeiro não deve ser excluído apenas por ser extremo.

A exclusão só é permitida mediante justificativa objetiva e documentada.

Se houver exclusão válida, apresentar análise de sensibilidade.

---

# 34. Validação do N em cada análise

Nunca assumir que todas as análises possuem o mesmo N.

Exemplo esperado:

```text
Amostra total: 75

IMC válido: 73

FINDRISC válido: 74

IMC + FINDRISC válidos: 72
```

Esses números devem ser recalculados automaticamente após a limpeza.

Toda tabela inferencial deve apresentar o N efetivamente utilizado.

---

# 35. Testes de normalidade

Não implementar lógica automática do tipo:

```python
if shapiro_p > 0.05:
    usar_teste_parametrico()
else:
    usar_teste_nao_parametrico()
```

A decisão estatística deve considerar:

- natureza da variável;
- tamanho amostral;
- distribuição;
- outliers;
- relação esperada;
- adequação metodológica.

O teste de Shapiro-Wilk pode ser utilizado como informação auxiliar, mas não como único critério de decisão.

---

# 36. Tamanho de efeito e intervalo de confiança

Sempre que aplicável, reportar:

```text
estimativa
IC95%
tamanho de efeito
p-valor
N
```

Nunca produzir resultado científico final contendo somente:

```text
p = ...
```

A interpretação deve priorizar magnitude e incerteza do efeito.

---

# 37. Notebook 07 — Tabelas e figuras

Arquivo:

```text
notebooks/07_tables_and_figures.ipynb
```

Esse notebook não deve recalcular manualmente resultados.

Ele deve importar dados e resultados já processados pelos módulos/notebooks anteriores.

Objetivos:

- padronizar tabelas;
- padronizar figuras;
- exportar resultados;
- gerar materiais prontos para o artigo/resumo do congresso.

---

# 38. Tabela 1 — Caracterização da população

Título sugerido:

> Características sociodemográficas e clínicas dos pacientes com doenças autoimunes.

Incluir, conforme disponibilidade:

- diagnóstico;
- estado civil;
- escolaridade;
- renda;
- ocupação;
- atividade física;
- tabagismo;
- etilismo;
- uso de corticoide;
- imunobiológicos;
- tempo de doença;
- outras variáveis clínicas relevantes.

Variáveis categóricas:

```text
n (%)
```

Variáveis quantitativas:

```text
média ± DP
e/ou
mediana [P25–P75]
```

conforme distribuição.

---

# 39. Tabela 2 — Perfil antropométrico e risco metabólico

Título sugerido:

> Perfil antropométrico e risco metabólico dos pacientes com doenças autoimunes.

Estrutura recomendada:

| Variável | N válido | Média | Moda | Desvio-padrão | Mediana [P25–P75] | n (%) |
|---|---:|---:|---:|---:|---:|---:|
| IMC (kg/m²) | — | — | — | — | — | — |
| Excesso de peso (IMC ≥25) | — | — | — | — | — | — |
| Obesidade (IMC ≥30) | — | — | — | — | — | — |
| FINDRISC (pontos) | — | — | — | — | — | — |
| FINDRISC ≥15 | — | — | — | — | — | — |

Para IMC e FINDRISC calcular obrigatoriamente:

```text
N válido
média
moda
desvio-padrão
mediana
P25
P75
```

Para variáveis categóricas derivadas:

```text
Excesso de peso
Obesidade
FINDRISC ≥15
```

apresentar:

```text
n (%)
```

Não calcular média, moda ou desvio-padrão para essas variáveis categóricas como resultado clínico principal.

---

# 40. Tabela 3 — Associação entre IMC e FINDRISC

Título sugerido:

> Associação entre índice de massa corporal e escore FINDRISC.

Estrutura:

| N | rho de Spearman | IC95% | p-valor |
|---:|---:|---:|---:|

Opcionalmente incluir método de IC:

```text
Bootstrap, 10.000 reamostragens
```

---

# 41. Figuras principais

Priorizar poucas figuras de alta utilidade científica.

## Figura 1

Distribuição das categorias de IMC.

Preferência:

```text
gráfico de barras
```

Mostrar:

```text
n e/ou %
```

## Figura 2

Distribuição das categorias FINDRISC.

Preferência:

```text
gráfico de barras
```

## Figura 3

Relação IMC × FINDRISC.

Preferência:

```text
scatter plot
```

Adicionar:

- tendência visual quando apropriado;
- rho de Spearman;
- IC95%;
- N.

Não sugerir causalidade.

## Figura 4

Perfil geral de risco metabólico.

Pode apresentar:

- excesso de peso;
- obesidade;
- FINDRISC ≥15.

A construção deve priorizar legibilidade e utilidade para congresso.

---

# 42. Regras de visualização

Todos os gráficos devem:

- possuir título objetivo;
- possuir rótulos de eixos;
- utilizar unidades;
- evitar elementos decorativos desnecessários;
- possuir fontes legíveis;
- ser adequados para impressão;
- evitar excesso de categorias;
- ser exportados em alta resolução.

Preferir formatos:

```text
PNG para uso rápido
SVG ou PDF para publicação quando apropriado
```

Gerar versão mínima de:

```text
300 DPI
```

quando exportado como imagem raster.

---

# 43. Bibliotecas Python recomendadas

Dependências principais:

```text
pandas
numpy
scipy
statsmodels
matplotlib
seaborn
openpyxl
jupyter
ipykernel
```

Opcionalmente:

```text
missingno
pingouin
tabulate
```

O projeto deve evitar dependências desnecessárias.

---

# 44. Funções reutilizáveis

Sempre que uma transformação ou cálculo aparecer em mais de um notebook, mover para `src/`.

## cleaning.py

Exemplos:

```python
clean_numeric_column()
clean_text_column()
remove_empty_records()
create_patient_id()
```

## variables.py

Exemplos:

```python
classificar_imc()
classificar_findrisc()
create_excesso_peso()
create_obesidade()
create_findrisc_alto()
```

## statistics.py

Exemplos:

```python
descriptive_numeric()
descriptive_categorical()
spearman_with_bootstrap_ci()
missing_summary()
```

## plots.py

Exemplos:

```python
plot_imc_distribution()
plot_findrisc_distribution()
plot_imc_findrisc()
plot_missing_data()
```

---

# 45. Convenções de nomes

Usar nomes internos em `snake_case`.

Exemplos:

```text
imc
imc_categoria
excesso_peso
obesidade
findrisc_score
findrisc_categoria
findrisc_alto
diagnostico_original
diagnostico_padronizado
uso_corticoide
atividade_fisica
```

Evitar espaços e acentos em nomes de colunas processadas.

Os rótulos apresentados ao leitor podem utilizar português normal.

---

# 46. Células de notebook

Cada notebook deve seguir a estrutura:

```text
1. Objetivo
2. Importações
3. Configuração
4. Carregamento
5. Validações
6. Análise
7. Visualização
8. Conclusões daquele notebook
9. Outputs gerados
```

Não misturar limpeza pesada com inferência estatística.

---

# 47. Seeds e reprodutibilidade

Toda operação aleatória deve utilizar seed fixa.

Exemplo:

```python
RANDOM_STATE = 42
```

Inclui:

- bootstrap;
- reamostragem;
- qualquer procedimento estocástico.

Registrar versão do Python e principais bibliotecas.

---

# 48. Controle de qualidade antes da análise principal

Antes de executar `05_imc_findrisc_analysis.ipynb`, validar:

```text
[ ] linhas vazias removidas
[ ] pacientes anonimizados
[ ] IMC convertido para numérico
[ ] FINDRISC convertido para numérico
[ ] categorias de IMC recalculadas
[ ] categorias FINDRISC recalculadas
[ ] missing preservados corretamente
[ ] nenhuma ausência transformada em zero
[ ] nenhuma ausência transformada incorretamente em False
[ ] duplicatas avaliadas
[ ] outliers avaliados
[ ] N válido documentado
```

Se alguma condição falhar, interromper a análise principal.

---

# 49. Assertions recomendadas

Criar verificações programáticas.

Exemplos:

```python
assert df["patient_id"].is_unique
assert "nome" not in df.columns
assert df["imc"].dropna().dtype.kind in "fi"
assert df["findrisc_score"].dropna().between(0, 30).all()
```

A faixa FINDRISC deverá ser validada conforme o instrumento utilizado.

Não corrigir automaticamente um valor inválido sem registrar o motivo.

---

# 50. Relatório de qualidade do dataset

Gerar arquivo:

```text
outputs/tables/data_quality_report.csv
```

Contendo:

```text
variável
tipo original
tipo final
n válido
n missing
% missing
mínimo
máximo
n categorias
observações
```

Esse relatório não deve conter nomes de pacientes.

---

# 51. Outputs obrigatórios

Ao final do pipeline devem existir, no mínimo:

```text
data/processed/pacientes_clean.csv

outputs/tables/table_1_population.csv
outputs/tables/table_2_metabolic_profile.csv
outputs/tables/table_3_imc_findrisc.csv
outputs/tables/missing_data.csv
outputs/tables/data_quality_report.csv

outputs/figures/figure_1_imc_categories.png
outputs/figures/figure_2_findrisc_categories.png
outputs/figures/figure_3_imc_findrisc.png
outputs/figures/figure_4_metabolic_profile.png
```

Os nomes podem ser refinados, mas devem permanecer consistentes.

---

# 52. Interpretação científica

Evitar linguagem causal.

Evitar:

```text
"IMC aumenta o risco FINDRISC."
```

Preferir:

```text
"Maiores valores de IMC estiveram associados a maiores escores FINDRISC."
```

Evitar extrapolar resultados para:

```text
todos os pacientes com doenças autoimunes
população geral
todos os hospitais
```

O resultado descreve a amostra analisada.

---

# 53. Significância estatística

O limiar convencional pode ser:

```text
α = 0,05
```

Porém:

- não utilizar p-valor isoladamente;
- não transformar resultado não significativo em “ausência de associação”;
- interpretar IC95%;
- reportar magnitude;
- considerar tamanho amostral.

Não realizar `p-hacking`.

---

# 54. Moda

A moda deve ser calculada para IMC e FINDRISC conforme solicitado.

Quando houver múltiplas modas:

- não selecionar arbitrariamente uma única;
- registrar que a distribuição é multimodal;
- permitir apresentação de múltiplos valores quando necessário.

Quando todos os valores ocorrerem apenas uma vez e a moda não for informativa, isso deve ser registrado.

A moda é uma medida complementar e não deve substituir média ou mediana.

---

# 55. Dados laboratoriais com alta ausência

Variáveis laboratoriais devem ser avaliadas na auditoria.

Se apresentarem percentual muito elevado de missing:

- não utilizar como eixo principal;
- não realizar inferência com baixa base amostral sem justificativa;
- apresentar apenas de forma exploratória quando pertinente;
- informar N válido.

Nunca imputar exames laboratoriais ausentes apenas para aumentar N.

---

# 56. Diagnósticos pequenos

Diagnósticos com poucos pacientes devem permanecer na descrição global.

Não executar teste estatístico de comparação para grupos com N insuficiente apenas porque a variável existe.

A análise principal permanece com a coorte agrupada.

---

# 57. Comorbidades

Comorbidades podem ser descritas.

Caso estejam registradas em um campo de texto com múltiplas condições:

- preservar valor original;
- opcionalmente criar variáveis binárias por condição;
- documentar mapeamento;
- evitar explosão desnecessária de dezenas de testes.

---

# 58. Uso de corticoide

A variável uso recente ou prévio de corticoide poderá ser utilizada em análise secundária.

Linguagem permitida:

```text
"associação entre uso de corticoide e IMC"
```

Evitar:

```text
"efeito do corticoide sobre o IMC"
```

caso o desenho seja observacional/transversal.

---

# 59. Atividade física

Atividade física poderá ser analisada como variável secundária.

Toda comparação deve apresentar:

```text
N por grupo
estatística descritiva
tamanho de efeito quando aplicável
IC95% quando aplicável
p-valor
```

Evitar conclusões causais.

---

# 60. Desenho do estudo

Até que o protocolo confirme outra classificação, tratar a análise como compatível com estudo observacional de corte transversal.

A análise estatística deve refletir esse desenho.

Não utilizar linguagem longitudinal se os dados forem apenas de um momento de coleta.

---

# 61. Checklist científico antes de exportar resultados

Antes da geração final:

```text
[ ] objetivo principal respondido
[ ] população tratada como único grupo
[ ] diagnóstico usado apenas descritivamente na análise principal
[ ] dados anonimizados
[ ] IMC corretamente classificado
[ ] FINDRISC corretamente classificado
[ ] FINDRISC ≥15 calculado
[ ] excesso de peso calculado
[ ] obesidade calculada
[ ] missing reportado
[ ] média calculada
[ ] moda calculada
[ ] desvio-padrão calculado
[ ] mediana calculada
[ ] P25 e P75 calculados
[ ] Spearman executado
[ ] IC95% calculado
[ ] N da correlação reportado
[ ] limitação IMC/FINDRISC documentada
[ ] análises secundárias identificadas como exploratórias
[ ] nenhum nome de paciente em outputs
```

---

# 62. Fluxo final do projeto

```text
CSV ORIGINAL
     │
     ▼
[00] AUDITORIA
     │
     ├── pacientes válidos
     ├── duplicatas
     ├── inconsistências
     ├── tipos
     └── missing
     │
     ▼
[01] LIMPEZA
     │
     ├── anonimização
     ├── IMC
     ├── FINDRISC
     ├── diagnósticos
     └── variáveis derivadas
     │
     ▼
DATASET ANALÍTICO
     │
     ├───────────────────┐
     ▼                   ▼
[02] POPULAÇÃO       [03-04] EDA
     │                   │
     │              IMC / FINDRISC
     │                   │
     └────────┬──────────┘
              ▼
       [05] ANÁLISE PRINCIPAL
              │
              ▼
        IMC × FINDRISC
              │
              ▼
        Spearman + IC95%
              │
              ▼
       [06] SECUNDÁRIAS
              │
       ┌──────┼─────────┐
       ▼      ▼         ▼
 Corticoide  Ativ.    Outros
             física   fatores
              │
              ▼
       SENSIBILIDADE
              │
              ▼
       [07] OUTPUTS
              │
       ┌──────┴───────┐
       ▼              ▼
    TABELAS         FIGURAS
       │              │
       └──────┬───────┘
              ▼
            ARTIGO
```

---

# 63. Resultado científico esperado

O projeto deve permitir responder de forma objetiva:

1. Qual é o perfil sociodemográfico e clínico da população?
2. Qual é a distribuição do IMC?
3. Qual é a prevalência de excesso de peso?
4. Qual é a prevalência de obesidade?
5. Qual é a distribuição do FINDRISC?
6. Qual é a prevalência de FINDRISC ≥15?
7. Qual é a magnitude da associação entre IMC e FINDRISC?
8. Qual é a incerteza dessa estimativa?
9. Quais fatores clínicos apresentam associações exploratórias relevantes?
10. Quais são as principais limitações da análise?

---

# 64. Regra final para o agente

A prioridade do projeto é:

```text
correção científica
>
reprodutibilidade
>
transparência
>
qualidade das visualizações
>
significância estatística
```

Nunca modificar decisões metodológicas com o objetivo de obter significância estatística.

Nunca excluir dados válidos para melhorar resultados.

Nunca ocultar dados ausentes.

Nunca expor identidade de pacientes.

Nunca tratar associação como causalidade.

Toda decisão de limpeza, exclusão ou transformação deve ser documentada.

O objetivo não é encontrar um `p < 0,05`.

O objetivo é produzir uma análise exploratória confiável, transparente e defensável cientificamente para utilização em um artigo médico.
