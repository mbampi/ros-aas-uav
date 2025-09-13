
# Experimento no Laboratório — Plano e Execução

Este documento combina o plano de testes e as instruções de execução para validar o AAS Gateway em hardware físico (UAVs). Ele contém objetivo, configuração, cenários de teste, passos para executar os componentes e instruções para coleta de métricas.

## 1 - Objetivo

Medir a latência ponta a ponta (end-to-end) e o consumo de recursos computacionais embarcados do middleware AAS Gateway em um UAV físico. Demonstrar a capacidade do sistema de gerenciar dados de múltiplos UAVs simultaneamente, reforçando o argumento de interoperabilidade.

## 2 - Visão Geral do Experimento

Componentes principais:
- Servidor OPC UA (executando na Estação de Controle / GCS)
- AAS Gateway (ROS 2 node, executando no companion computer do UAV)

Pastas de interesse para coleta de dados:
- `opcua_server/metrics/` (no servidor OPC UA)
- `ros2/logs/` (no computador de bordo)

## 3 - Configuração de Hardware e Software

Hardware recomendado:
- Drones: 2 drones baseados em PX4
- Companion Computer: Raspberry Pi ou similar (um por drone)
- Estação de Controle (GCS): notebook para executar o Servidor OPC UA

Software:
- Repositório: `ros-aas-uav`
- AAS Gateway: pacote ROS2 dentro de `ros2/src/aas_ros2_gateway`
- Servidor OPC UA: `opcua_server/`

## 4 - Servidor OPC UA (Estação de Controle)

O Servidor OPC UA ficará no GCS escutando na porta 4840.

### Pré-requisitos

- Python 3.6 ou superior
- pip
- virtualenv

### Execução (no diretório `opcua_server`)

1. Crie e ative um ambiente virtual:

```bash
python3 -m venv venv
source venv/bin/activate
```

2. Instale dependências e execute:

```bash
pip install -r requirements.txt
python3 opcua_server.py
```

O servidor criará a pasta `opcua_server/metrics/` com os logs/métricas de interesse.

## 5 - Companion Computer (AAS Gateway + Resource Monitor)

### Pré-requisitos

- Docker e Docker Compose

No companion board vamos executar o AAS Gateway (ROS2 node) e o Resource Monitor.

### Arquivos de configuração principais

- `ros2/src/aas_ros2_gateway/config/params.yaml`
   - Contém parâmetros do gateway. Ajuste `opcua_endpoint` para apontar ao servidor OPC UA do GCS.
   - Para mais logs, defina `debug_enabled: true`.
- `ros2/src/aas_ros2_gateway/config/map.yaml`
   - Mapeia tópicos ROS2 para propriedades AAS. Use `ros2 topic list` para descobrir tópicos disponíveis.

### Rodar o AAS Gateway (recomendado com Docker)

No diretório `ros2`:

```bash
cd ros2
docker-compose up --build
```

Observação: a primeira execução pode demorar por causa da instalação de `px4_msgs`. Em execuções seguintes, basta `docker-compose up`.

Logs esperados:

```
Created 15 topic subscriptions
AAS Gateway initialization complete!
aas_gateway node has been started.
```

## 6 - Cenários de Teste

### Cenário A — Desempenho com um Drone

Objetivo: medir latência ponta a ponta e uso de CPU/memória do AAS Gateway em voo estacionário ou baixa velocidade.

Dados: publique telemetria essencial (ex.: atitude, posição GPS, estado da bateria). Três tópicos são suficientes. Exemplo:

- `/px4_1/fmu/out/battery_status` -> remaining
- `/px4_1/fmu/out/vehicle_attitude` -> q
- `/px4_1/fmu/out/vehicle_gps_position` -> eph / satellites_used

Medição: executar por 15 minutos.

### Cenário B — Interoperabilidade com Dois Drones

Objetivo: validar recebimento e distinção de dados de dois UAVs diferentes no Servidor OPC UA.

Ação: ligue ambos os drones (podem ficar sobre a mesa). Cada drone roda sua instância do AAS Gateway. Verifique no Servidor OPC UA que dados de ambos aparecem separadamente.

## 7 - Métricas e Coleta de Dados

Pastas a coletar após cada cenário:

- `opcua_server/metrics/` (Servidor OPC UA)
- `ros2/logs/` (Companion computer / AAS Gateway)

Essas pastas contêm dados brutos de latência, eventos e uso de recursos.

## 8 - Registro Visual e Documentação

Recomenda-se capturar:

- Fotos do setup experimental (drones, companion computer, GCS)
- Screenshots de terminais importantes (logs do gateway, saída do resource monitor)
- Screenshot/ gravação da interface do cliente OPC UA mostrando dados em tempo real

## 9 - Checklist rápido para executar o experimento

- [ ] Preparar hardware (2 drones + GCS)
- [ ] Iniciar Servidor OPC UA no GCS (`opcua_server`)
- [ ] Ajustar `params.yaml` para `opcua_endpoint` correto
- [ ] Iniciar AAS Gateway em cada companion computer (Docker)
- [ ] Iniciar Resource Monitor em cada companion computer
- [ ] Executar Cenário A (15 min) e coletar pastas
- [ ] Executar Cenário B (15 min) e coletar pastas
- [ ] Copiar `opcua_server/metrics/`, `ros2/logs/` para armazenamento

Documentos de referência:
- `opcua_server/README.md` e `ros2/src/aas_ros2_gateway/README.md`
