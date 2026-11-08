# lightgun-joypad

Transforma um **Joy-Con** ou **Pro Controller** do Nintendo Switch numa
**light gun absoluta**, no **Linux** e no **Windows**, usando o giroscópio e o
acelerômetro do controle.

Absoluta quer dizer que a mira vai **para onde o cano aponta**, como uma arma
de verdade, e não "arrasta" o cursor como um mouse. Se você mirar no canto
superior esquerdo da TV, a mira vai para o canto superior esquerdo, mesmo de
olhos fechados e sem cursor na tela.

## Como funciona

```
giroscópio + acelerômetro ──► orientação 3D (filtro Mahony, ~200 amostras/s)
        │
        ▼
direção do cano ──► interseção com um plano ──► homografia calibrada ──► (x, y) da tela
        │                                                                    │
        ▼                                                                    ▼
 filtro One Euro (tira o tremor sem atrasar)                mouse ABSOLUTO virtual
                                                (uinput no Linux / SendInput no Windows)
```

- **Mira física**: a direção do cano é projetada como um raio. Visto de um ponto
  fixo, a relação entre esse raio e a tela real é exatamente uma *homografia*.
  Por isso a calibração por **centro + 4 cantos** fica correta mesmo com você
  fora do eixo da TV, sentado mais baixo, com a TV inclinada etc.
- **Girar o pulso não mexe a mira**: o roll é descartado porque a mira é
  calculada pela gravidade, como numa arma real.
- **Fluidez**: usa as 3 amostras de IMU de cada pacote (~5 ms cada), com o
  tempo do próprio sensor. O filtro **One Euro** segura a mira quando você está
  parado e sai do caminho nos movimentos rápidos.
- **Tranco do gatilho**: ao atirar, o clique usa a posição de 25 ms antes e
  congela a mira por 60 ms, para o tranco do dedo não desviar o tiro.
- **Deriva**: o Switch não tem bússola, então o yaw (esquerda/direita) pode
  escorregar com o tempo. Duas coisas resolvem:
  1. o bias do giroscópio é medido sozinho sempre que o controle fica
     **apoiado parado** por ~1 s (por exemplo, na mesa entre as fases);
  2. o botão **recentrar** (Y / ← por padrão): mire no centro da tela e aperte.
  Para cima/baixo não deriva, porque a gravidade corrige.

## Instalação

### Linux

```bash
./installer/linux/install.sh
```

O instalador:
- ajusta o Bluetooth para aceitar o Joy-Con e as permissões (pede a senha 1 vez);
- cria um ambiente Python próprio em `~/.local/share/lightgun-joypad`;
- cria o aplicativo **Light Gun Joypad** no menu e o faz abrir sozinho, na
  bandeja do sistema, quando você entra no Linux;
- cria também o atalho do **Simulador**.

Desinstalar: `~/.local/share/lightgun-joypad/uninstall.sh`.

> **O Joy-Con conecta no Bluetooth mas as luzes ficam piscando?** O BlueZ
> rejeita controles sem *bonding* (`Rejected connection from !bonded device`).
> O instalador já corrige; para corrigir à parte:
> `sudo ./scripts/fix-linux-joycon.sh` e aperte um botão do Joy-Con.

### Windows

1. Pareie o Joy-Con ou Pro Controller em *Configurações → Bluetooth*
   (segure o botão de sync até as luzes correrem).
2. Dê dois cliques em `installer\windows\Instalar.bat`.

O instalador não precisa de administrador. Se faltar o Python, ele instala
pelo `winget`. Depois cria os atalhos no Menu Iniciar e na Área de Trabalho,
põe o aplicativo para abrir com o Windows (na bandeja) e registra o programa em
*Aplicativos instalados*, de onde dá para desinstalar.

> Feche o Steam (ou desative o "Switch Pro Configuration Support"), o BetterJoy
> e o DS4Windows: eles disputam o controle.

## O aplicativo

**Light Gun Joypad** é um programa de janela próprio (Qt), que funciona sem
navegador e sem internet. Fechar a janela não encerra o programa: ele continua
na **bandeja** (o ícone da mira perto do relógio). Pelo menu da bandeja dá para
pausar, recentrar, calibrar, trocar de perfil ou encerrar. A cor do ícone
mostra o estado: verde = ativa, amarelo = pausada ou giroscópio sem calibrar,
cinza = sem controle. Tudo o que você muda vale na hora.

### Os dois modos (botões no topo da janela)

| Modo | O que acontece | Use com |
|---|---|---|
| **🎯 Só light gun (driver)**, padrão no Linux | Cria o dispositivo "Joypad Light Gun (driver)", que a área de trabalho **ignora**: o cursor e o touchpad ficam livres. | RetroArch com driver de entrada **udev** (Light Gun → dispositivo "Joypad Light Gun (driver)") |
| **🖱 Mouse do sistema** | A arma move o cursor. Se você mexer no touchpad ou no mouse, a arma **cede** o cursor por alguns segundos e retoma quando você atira. | Qualquer jogo/emulador (MAME, Dolphin, jogos de PC) |

No Windows só existe o modo mouse: um dispositivo de light gun separado
precisaria de um driver de kernel.

- **Ao vivo:** mira em tempo real (a bolinha cinza é a mira sem filtro),
  botões apertados, estado do giroscópio e da calibração.
- **Calibrar:** em tela cheia, mire no centro e nos 4 cantos e aperte o ZR.
- **Estande de teste:** alvos em tela cheia usando o mouse de verdade, para
  testar o caminho completo. **H** esconde a mira.
- **Mira:** sensibilidade X/Y, ajuste fino do ponto de impacto, estabilidade
  parada, resposta a movimentos rápidos e trava de micro-movimento.
- **Tiro:** compensação do tranco, congelamento após o tiro, velocidade do tiro
  automático e para onde vai o "tiro fora da tela".
- **Botões:** cada botão do controle pode virar gatilho, tiro automático,
  recarregar, clique esquerdo/direito/do meio, recentrar, pausar ou qualquer
  tecla do teclado. A linha do botão acende quando você o aperta.
- **Saída:** modo *light gun* (absoluto) ou *mouse giroscópio* (relativo, para
  jogos de PC que não aceitam mouse absoluto), área da tela e monitor.
- **Sensor:** correção pela gravidade, auto-correção da deriva e tamanho/distância
  da tela.
- **Perfis:** um por jogo, criados a partir de modelos prontos: Padrão, MAME,
  Arcade tiro rápido, Precisão e Mouse giroscópio.

Com a mira ativa, a light gun controla o cursor. Para usar o mouse normal,
aperte **HOME** no controle (pausa/retoma).

## Uso

```bash
lightgun-joypad gui            # aplicativo (janela + bandeja); --tray inicia escondido
lightgun-joypad calibrate      # calibração pelo terminal
lightgun-joypad run            # light gun sem painel
lightgun-joypad run --dry-run  # NÃO mexe no mouse: desenha a mira no terminal
lightgun-joypad sim            # simulador: estande de tiro em tela cheia
lightgun-joypad buttons        # mostra o nome de cada botão apertado
lightgun-joypad devices        # lista os controles detectados
lightgun-joypad init-config    # cria o arquivo de config para editar
```

Depois de instalado, o comando é `lightgun-joypad`. No Windows, rode
`%LOCALAPPDATA%\LightGunJoypad\venv\Scripts\lightgun-joypad`.

### Simulador (testar sem emulador)

`lightgun-joypad sim` abre um estande de tiro em tela cheia que usa o mesmo
processamento do modo real, mas desenha a mira na janela em vez de mexer no
mouse. Não precisa de `/dev/uinput`.

- Alvos aparecem aleatoriamente; o placar mostra acertos e o **erro médio em
  pixels**. A bolinha cinza é a mira crua (sem filtro), para comparar.
- **C** calibra na própria tela (centro + 4 cantos) e salva a calibração.
- **H** esconde a mira: atire às cegas e veja onde o tiro caiu.
- **Y** (no controle) ou **R** recentra; **T** liga/desliga o rastro; **N** zera o placar.
- Sem controle conectado, o mouse faz o papel da arma.
- `--windowed 1280x720` abre em janela; `--display 1` abre no 2º monitor.

### Calibração (terminal, sem precisar ver cursor)

1. Apoie o controle parado (mede o bias do giroscópio).
2. Segure como arma, **na posição em que vai jogar**.
3. Mire no **centro**, aperte o gatilho; depois nos 4 **cantos** da área de
   imagem do jogo.

O programa mostra o campo de visão medido e o erro residual. A calibração é
salva em `~/.config/lightgun-joypad/calibration.json` (Windows:
`%APPDATA%\lightgun-joypad\`).

Sem calibração, a geometria é calculada pelo tamanho da tela e pela distância
(`screen` na config; o padrão é uma TV de 55" a 2 m).

### Toda vez que começar a jogar

Mire no centro e aperte **recentrar** (Y ou ←). Se a mira escorregar no meio do
jogo, faça de novo; leva meio segundo.

### Botões padrão

| Botão (Joy-Con R / L)  | Ação                                              |
|------------------------|---------------------------------------------------|
| ZR / ZL                | **gatilho** (clique esquerdo)                     |
| R / L                  | **tiro fora da tela** (recarregar)                |
| A / →                  | clique direito                                    |
| B / ↓                  | clique do meio                                    |
| Y / ←                  | **recentrar** (mirando no centro)                 |
| X / ↑                  | tecla `1` (start P1 no MAME)                      |
| + / −                  | tecla `5` (ficha no MAME)                         |
| SL / SR                | `enter` / `esc`                                   |
| HOME / Captura         | pausar/retomar a mira (para usar o mouse real)    |

Edite com `init-config`. As ações são `trigger`, `offscreen_shot`,
`mouse_left`, `mouse_right`, `mouse_middle`, `recenter`, `toggle` e
`key:<tecla>` (letras, números, `enter`, `esc`, `space`, `tab`, setas, `f1`–`f12`,
`shift`, `ctrl`, `alt`). Também dá para usar nomes crus do evdev
(`"BTN_TR2": "trigger"`); veja os nomes com `lightgun-joypad buttons`.

## Ajustes finos (`config.json`)

| Chave                        | Efeito                                                         |
|------------------------------|----------------------------------------------------------------|
| `smoothing.min_cutoff`       | menor = mira mais firme parada (mais "pesada")                 |
| `smoothing.beta`             | maior = menos atraso em movimentos rápidos                     |
| `shot.lookback_ms` / `freeze_ms` | compensação do tranco do gatilho                          |
| `fusion.kp`                  | quão rápido a gravidade corrige a inclinação                   |
| `region` / `monitor`         | limitar a mira a um monitor ou janela (`monitor` só no Windows) |
| `offscreen_position`         | para onde vai o "tiro fora da tela"                            |
| `grab`                       | Linux: esconde o controle do emulador como gamepad             |

Exemplo de config completa: [`config.example.json`](config.example.json).

## Emuladores

O sistema vê um **mouse absoluto**, então funciona com qualquer jogo/emulador
que aceite mouse como light gun:

- **RetroArch**: *Configurações → Entrada → Portas → Tipo de dispositivo:
  Light Gun* (driver de entrada `udev` no Linux, `raw`/`dinput` no Windows).
  Associe *Gun Trigger* ao clique esquerdo e *Gun Reload* ao direito, ou use o
  `offscreen_shot`.
- **MAME**: `-lightgun -lightgun_device mouse`. Com `-offscreen_reload`, o 2º botão recarrega.
- **Dolphin/PCSX2/DuckStation**: mapeie o ponteiro para o mouse.

Em tela cheia com vários monitores, use `monitor` (Windows) ou `region`.

## Desenvolvimento

```bash
python3 -m venv .venv && .venv/bin/pip install -e '.[dev]'
.venv/bin/pytest
```

Os testes simulam uma arma física a 2 m de uma TV de 55" e conferem que ela
acerta alvos conhecidos: com roll, com jogador fora do eixo, com direção
inicial desconhecida + recentrar, com bias e ruído no giroscópio, e com a
compensação do tranco do gatilho.

```
src/lightgun_joypad/
  fusion.py        Mahony + estimador de bias do giroscópio
  geometry.py      projeção do raio + homografia
  filters.py       One Euro 2D
  engine.py        pipeline IMU -> mira -> mouse/botões
  calibration.py   calibração guiada (centro + 4 cantos)
  client.py        núcleo do cliente residente (thread do controle, perfis, calibração)
  gui.py           aplicativo Qt: janela de configuração, bandeja, calibração e estande
  simulator.py     estande de tiro (pygame)
  inputs/          linux_evdev (hid-nintendo) e switch_hid (hidapi, protocolo cru)
  outputs/         linux_uinput, windows_sendinput, console (--dry-run)
```

### Limitações

- Sem bússola no controle, o yaw sempre precisa de um ponto de referência
  (recentrar). O bias automático deixa a deriva bem lenta, mas não zero.
- Se você **andar** pela sala depois de calibrar, a mira desalinha; com o
  jogador parado no lugar calibrado, a geometria é exata.
- O backend `hidapi` lê os dados crus com escala padrão (`gyro_dps_per_lsb`).
  Erro de escala é absorvido pela calibração, mas, se a mira "correr" mais ou
  menos que o cano, ajuste esse valor.
