# PX4 Setup

A solução envolve duas etapas principais:
1. Rodar o Micro-ROS Agent em um contêiner Docker no Raspberry Pi.
2. Configurar o PX4 para enviar os dados para a porta serial correta.


## 1 - Rodar o Micro-ROS Agent

O docker-compose.yml já está configurado para rodar o Micro-ROS Agent. Para iniciar o serviço, navegue até a pasta `ros2/` e execute:

```
docker-compose up
```

Isso iniciará o contêiner `micro_ros_agent`, que escutará na porta serial `/dev/ttyAMA0` com baudrate 921600.
Certifique-se de que o Raspberry Pi tenha permissão para acessar a porta serial.
E certifique-se que a porta está correta (pode ser diferente dependendo do hardware).

## 2 - Configurar o PX4

1. Conecte sua Pixhawk ao computador via USB e abra o QGroundControl.
2. Vá para a seção de Parameters (geralmente no ícone "Q" > Vehicle Setup > Parameters).
3. Procure e configure os três parâmetros abaixo. Este exemplo assume que você conectou o Raspberry Pi na porta TELEM2 da Pixhawk. Se usou outra porta (como TELEM1), apenas ajuste o número correspondente.
   - Habilitar o Cliente Micro-ROS: Este parâmetro diz ao PX4 qual porta serial usar para a ponte ROS2.
      - Parâmetro: UXRCE_DDS_CFG
      - Valor: Selecione TELEM2 no menu dropdown.
   - Configurar o Baud Rate: Deve ser idêntico ao valor usado no comando do Docker (921600).
      - Parâmetro: SER_TEL2_BAUD
      - Valor: 921600 8N1
   - Desabilitar o MAVLink na Mesma Porta: Para evitar conflitos, o serviço padrão de telemetria MAVLink precisa ser desativado na porta que o Micro-ROS irá usar.
      - Parâmetro: MAV_2_CONFIG
      - Valor: Selecione Disabled no menu.
Após alterar os parâmetros, reinicie a controladora de voo para que as mudanças tenham efeito.

## 3 - Verificar a Conexão

Com os contêineres rodando e o PX4 configurado, você pode verificar se os tópicos ROS2 estão sendo publicados.
1. Abra um novo terminal no seu Raspberry Pi.
2. Liste os contêineres em execução para encontrar o nome do contêiner da sua aplicação:
```Bash
docker ps
```
1. Execute um terminal dentro do seu contêiner.
```Bash
docker exec -it aas_gateway bash
```
Dentro do contêiner, ative o ambiente ROS2 e liste os tópicos:
```Bash
# Ative seu workspace ROS2 ou a instalação base
source /opt/ros/humble/setup.bash

# Liste todos os tópicos ROS2 disponíveis
ros2 topic list
```

Você deverá ver uma lista de tópicos começando com /fmu/out/. Isso confirma que a ponte está funcionando. Exemplos:
/fmu/out/vehicle_odometry
/fmu/out/vehicle_status

Para ver os dados sendo publicados em tempo real, use o comando ros2 topic echo. Por exemplo, para ver os dados de odometria do veículo:
```Bash
ros2 topic echo /fmu/out/vehicle_odometry
```
Se você vir mensagens sendo publicadas, então a configuração foi bem-sucedida!

---
Outras verificações possiveis

### Verifique os Logs do Contêiner do Agente
Os logs do micro-ros-agent dirão se ele conseguiu se conectar à porta serial e se está recebendo dados.
No terminal do Raspberry Pi, execute um dos comandos abaixo:
```Bash
docker-compose logs micro-ros-agent
```

O que procurar nos logs:
- Sucesso: Mensagens como [...][UXRCSession::new] session created, client_key, session established ou create publisher indicam que a comunicação com o PX4 foi bem-sucedida.
- Erro: Mensagens com Error, failed to connect, timeout ou No such file or directory (se a porta serial estiver errada) indicam um problema de conexão ou configuração.


