# Guia de instalação

[English](INSTALL.md) · **Português (Brasil)**

Este guia explica, passo a passo, como instalar, configurar, atualizar e
remover o **Capybara Lightgun** no **Linux**, no **Windows** e no **macOS**.

> Antes de instalar, leia o [aviso legal](../AVISO-LEGAL.md). Ao instalar ou
> usar o software, você aceita que o usa **por sua conta e risco** e que
> **só você é responsável** pela forma como o usa.

---

## Sumário

1. [Antes de começar (todos os sistemas)](#1-antes-de-começar-todos-os-sistemas)
2. [Linux](#2-linux)
3. [Windows](#3-windows)
4. [macOS (experimental)](#4-macos-experimental)
5. [Pareando o dispositivo](#5-pareando-o-dispositivo)
6. [Primeiro uso: calibração e teste](#6-primeiro-uso-calibração-e-teste)
7. [Configurando emuladores e jogos](#7-configurando-emuladores-e-jogos)
8. [Solução de problemas](#8-solução-de-problemas)
9. [Atualizando](#9-atualizando)
10. [Desinstalando](#10-desinstalando)
11. [Instalação manual (desenvolvedores)](#11-instalação-manual-desenvolvedores)
12. [Onde ficam os arquivos](#12-onde-ficam-os-arquivos)

---

## 1. Antes de começar (todos os sistemas)

**Você precisa de:**
- Um computador com **Linux**, **Windows 10/11** ou **macOS 10.15+**.
- **Python 3.9 ou mais novo.** No Windows, o instalador instala para você.
- **Internet durante a instalação**, para baixar os pacotes Python. Depois
  disso o aplicativo funciona sem internet e nunca se conecta à rede.
- **Uma fonte de mira:**
  - qualquer dispositivo com **giroscópio** que o sistema consiga ler (por
    exemplo Joy-Con, Pro Controller, DualSense, DualShock 4, Steam
    Deck/Controller, alguns modelos 8BitDo), ou
  - só o **mouse do sistema**, se você não tiver um dispositivo com
    giroscópio. A maioria dos controles de Xbox comuns não tem giroscópio.

**Baixe o projeto**, de um destes jeitos:
- **ZIP:** abra <https://github.com/loboguaraBR/CapybaraLightgun>,
  clique em **Code → Download ZIP** e extraia numa pasta que você vá manter
  (os instaladores copiam o que precisam, mas manter a pasta facilita as
  atualizações).
- **Git:**
  ```bash
  git clone https://github.com/loboguaraBR/CapybaraLightgun.git
  cd CapybaraLightgun
  ```

**Feche outros programas de controle** que possam disputar o dispositivo:
Steam (ou desative o Steam Input para aquele controle), BetterJoy,
DS4Windows, reWASD, joycond e semelhantes.

---

## 2. Linux

Testado no Ubuntu/Linux Mint com X11. Deve funcionar em outras distribuições
com kernel recente (5.16+ para controles Nintendo) e BlueZ.

### 2.1 Instalar

```bash
cd CapybaraLightgun
./installer/linux/install.sh
```

O que o instalador faz:
1. **Pede sua senha uma vez** (sudo), só se precisar, para:
   - instalar a regra udev `/etc/udev/rules.d/70-capybara-lightgun.rules`,
     que dá ao usuário logado acesso aos controles suportados e ao
     `/dev/uinput` sem root;
   - carregar os módulos do kernel `uinput` e `hid-nintendo`;
   - ajustar `ClassicBondedOnly=false` em `/etc/bluetooth/input.conf`, com
     cópia de segurança. Controles como o Joy-Con precisam disso para
     conectar. O ajuste afrouxa um pouco um padrão de segurança do BlueZ;
     veja o [aviso legal](../AVISO-LEGAL.md).
2. Cria um **ambiente Python isolado** em `~/.local/share/capybara-lightgun`
   (o Python do sistema não é alterado). Se faltar o `python3-venv`, ele baixa
   o `get-pip` oficial em vez de pedir para instalar pacotes.
3. Instala o comando `capybara-lightgun` em `~/.local/bin`.
4. Coloca o **Capybara Lightgun** (e o **Simulador**) no menu de aplicativos
   e faz o aplicativo abrir minimizado na bandeja quando você entra no
   sistema.
5. Abre o aplicativo.

Você pode revisar tudo antes: `installer/linux/install.sh` e
`scripts/fix-linux-joycon.sh`.

### 2.2 Depois de instalar

- **Reconecte o controle** (desligue e ligue, ou pareie de novo) para as
  novas permissões valerem.
- Se o comando `capybara-lightgun` não for encontrado no terminal, saia e
  entre de novo na sessão (para o `~/.local/bin` entrar no `PATH`).

### 2.3 Observações do Linux

- **Dois modos de saída:** *Só light gun (driver)* cria uma light gun
  virtual que a área de trabalho ignora, então cursor e touchpad ficam livres
  (feito para o RetroArch com o driver de entrada `udev`). *Mouse do sistema*
  move o cursor de verdade e funciona com qualquer jogo.
- **Wayland:** a saída da arma funciona, mas ler o mouse do sistema como
  fonte de mira, a mira desenhada na tela e a troca automática de perfil
  precisam do **X11**.

---

## 3. Windows

> Situação: implementado e coberto pelos testes automáticos, mas **ainda não
> validado com controles reais no Windows**. Relate os problemas que
> encontrar.

### 3.1 Instalar

1. Baixe e extraia o projeto (veja a [seção 1](#1-antes-de-começar-todos-os-sistemas)).
2. Abra a pasta `installer\windows` e **dê dois cliques em `Instalar.bat`**.
   - Se o SmartScreen mostrar "O Windows protegeu o computador", clique em
     **Mais informações → Executar assim mesmo**. O script é texto puro; dá
     para abrir no Bloco de Notas e revisar antes.
3. O instalador:
   - procura o Python 3.9+ ou instala o Python 3.12 para o seu usuário pelo
     `winget` (não precisa de administrador);
   - cria um ambiente isolado em `%LOCALAPPDATA%\CapybaraLightgun`;
   - instala o programa e as dependências (hidapi, PyQt5, SDL2, pygame);
   - cria atalhos no **Menu Iniciar** e na **Área de Trabalho**, e um atalho
     em **Inicializar** para o aplicativo abrir na bandeja quando você entrar
     no Windows;
   - registra o aplicativo em **Configurações → Aplicativos** (para
     desinstalar por lá);
   - abre o aplicativo.

Se o `winget` não existir, instale o Python por <https://www.python.org/downloads/>,
**marque "Add python.exe to PATH"** e rode o `Instalar.bat` de novo.

### 3.2 Observações do Windows

- No Windows só existe a saída **Mouse do sistema**. Um dispositivo de light
  gun separado precisaria de um driver de kernel.
- Feche a **Steam** (ou desative o Steam Input para o controle), o
  **BetterJoy** e o **DS4Windows**: eles disputam o controle.
- A opção "Aumentar precisão do ponteiro" do Windows só afeta o modo *Mouse
  giroscópio (relativo)*, não a light gun absoluta.

---

## 4. macOS (experimental)

> Situação: **experimental**. Implementado e coberto por testes automáticos
> em Macs (Apple Silicon e Intel), mas ainda não validado num Mac de verdade
> com controles. A lista de verificação em [`TESTE-MAC.md`](TESTE-MAC.md)
> ajuda a relatar o resultado.

### 4.1 Instalar

1. Instale o **Python 3.9+** por <https://www.python.org/downloads/macos/> ou
   pelo Homebrew (`brew install python`).
2. Baixe e extraia o projeto.
3. No Finder, abra `installer/macos` e **dê dois cliques em
   `Instalar.command`**. Se o macOS bloquear, clique com o **botão direito →
   Abrir → Abrir**.
4. O instalador:
   - cria um ambiente isolado em
     `~/Library/Application Support/CapybaraLightgun`;
   - cria o aplicativo **`~/Applications/Capybara Lightgun.app`**, com ícone;
   - faz o aplicativo abrir no login (ícone na barra de menus), por um
     LaunchAgent;
   - roda um autoteste e abre o aplicativo.

### 4.2 Permissões (obrigatórias)

O macOS pede duas permissões. Sem elas a arma não move o cursor nem lê o
controle:

1. No aplicativo, clique no botão amarelo **⚠ Liberar permissões do macOS**
   (ou abra *Ajustes do Sistema → Privacidade e Segurança*).
2. Ative o **Capybara Lightgun** em **Acessibilidade** e em **Monitoramento
   de Entrada**.
3. **Encerre** o aplicativo (ícone da barra de menus → Encerrar) e abra de
   novo.

### 4.3 Observações do macOS
- No macOS só existe a saída **Mouse do sistema**.
- Controles Nintendo são lidos por HID; PlayStation e outros, pelo SDL.

---

## 5. Pareando o dispositivo

Pareie pelas configurações de Bluetooth do sistema (ou conecte por USB,
quando o dispositivo permitir). Antes, coloque o dispositivo em **modo de
pareamento**:

| Dispositivo | Modo de pareamento | Como segurar como arma |
|---|---|---|
| Joy-Con (E ou D) | Segure o botãozinho de **sync** no trilho até as luzes correrem de um lado para o outro | Em pé, como pistola, com o gatilho (ZR/ZL) sob o indicador |
| Pro Controller | Segure o botão de **sync** na borda de cima | Aponte a borda de cima (gatilhos) para a tela |
| DualSense (PS5) | Segure **Create + PS** até a barra de luz piscar rápido | Aponte a frente (lado da barra de luz) para a tela |
| DualShock 4 (PS4) | Segure **Share + PS** até a barra de luz piscar rápido | Aponte a frente para a tela |
| Steam Deck / outros com giroscópio | Veja o manual do fabricante | Aponte a frente para a tela |
| Mouse do sistema | Nada a parear | — |

**Dica do Linux:** se o Joy-Con conectar mas as luzes **continuarem
piscando**, falta o ajuste do BlueZ. Rode `sudo ./scripts/fix-linux-joycon.sh`
e aperte um botão do Joy-Con.

---

## 6. Primeiro uso: calibração e teste

1. Abra o **Capybara Lightgun** (menu de aplicativos, Menu Iniciar,
   Aplicativos ou ícone da bandeja).
2. Se quiser, escolha o idioma em **🌐 Language**, no topo. Esse rótulo fica
   sempre em inglês, para você sempre achar o caminho de volta.
3. Na aba **Controle**, deixe a fonte da mira em **Automático** ou escolha o
   seu dispositivo (ou **Mouse do sistema**).
4. **Deixe o dispositivo parado** na mesa por ~1 s, até aparecer
   *Giroscópio: ok*.
5. Clique em **🎯 Calibrar**. Segurando como vai jogar, mire no **centro** e
   depois nos **4 cantos**, apertando o gatilho em cada alvo. O resultado
   mostra o erro (abaixo de 1% é ótimo).
6. Clique em **🔫 Estande de teste** e atire nos alvos. **H** esconde a mira,
   um bom jeito de conferir se ela segue para onde você aponta. **ESC** sai.
7. Se durante o jogo a mira escorregar para o lado: aponte para o **centro**
   da tela e aperte **Y** (□ no PlayStation).

---

## 7. Configurando emuladores e jogos

| Programa | Modo no Capybara Lightgun | Ajuste no programa |
|---|---|---|
| **RetroArch** (Linux) | *Só light gun (driver)* | Configurações → Drivers → Entrada = `udev`; Porta 1 → Tipo de dispositivo = *Light Gun*, Índice do mouse = *Capybara Lightgun (driver)* |
| **RetroArch** (Windows/macOS) | *Mouse do sistema* | Porta 1 → Tipo de dispositivo = *Light Gun* (mouse) |
| **MAME** | *Mouse do sistema* | `-lightgun -lightgun_device mouse` (e `-offscreen_reload` para recarregar com o 2º botão) |
| **Dolphin** (Wii) | *Mouse do sistema* | Wii Remote → Apontar = cursor do mouse |
| **DuckStation / PCSX2** (GunCon) | *Mouse do sistema* | Controle = GunCon, mira pelo mouse |
| Jogos de PC sem mouse absoluto | *Mouse giroscópio (relativo)* (aba Saída) | Mira normal pelo mouse |

Crie um **perfil** por jogo na aba *Perfis*. Escreva palavras da janela do
jogo (ex.: `retroarch`, `mame`) para o perfil trocar sozinho.

### Zapper do NES no RetroArch (core FCEUmm)

Testado no Linux (X11) com RetroArch 1.22:

1. No Capybara Lightgun, use a saída **Mouse do sistema**. Assim o driver de
   entrada padrão do RetroArch (`x`) já enxerga a arma. O modo *Só light gun
   (driver)* fica invisível para esse driver.
2. *Menu rápido → Controles → Controles da porta 2 → Tipo de dispositivo* =
   **Zapper**. O Duck Hunt e a maioria dos jogos de Zapper só leem a
   **porta 2**: na porta 1 a mira aparece, mas o tiro não sai.
3. *Configurações → Entrada → Controles da porta 2 → Índice do mouse* = **0**.
   O driver `x` só atende o mouse 0: com outro índice a mira nem aparece.
4. *Menu rápido → Opções do núcleo → Zapper Mode* = **Crosshair light gun**
   (`fceumm_zapper_mode = "clightgun"`). O modo *Mouse* usa movimento relativo
   e a mira desalinha.
5. O gatilho é o clique esquerdo (`input_player2_gun_trigger_mbtn = "1"`, o
   padrão). No Capybara, confira na aba *Botões* que o botão que você usa como
   gatilho está em *Gatilho*.

Feche o RetroArch antes de editar o `retroarch.cfg` à mão, porque ele grava as
configurações ao sair.

---

## 8. Solução de problemas

| Problema | O que fazer |
|---|---|
| "Nenhum controle encontrado" | Confira se está pareado e conectado; feche Steam/BetterJoy/DS4Windows; clique em **Reconectar**. No Linux, rode `capybara-lightgun devices`. |
| Luzes do Joy-Con piscando sem parar (Linux) | `sudo ./scripts/fix-linux-joycon.sh` e aperte um botão do Joy-Con. |
| Bluetooth desligou depois do ajuste (alguns notebooks) | `rfkill unblock bluetooth` e `bluetoothctl power on`, depois pareie de novo. |
| Mensagem "sem giroscópio" | Esse controle não tem giroscópio (ex.: Xbox comum). Use a fonte **Mouse do sistema**. |
| Mira escorrega devagar para o lado | Deixe o dispositivo parado 1 s (auto-correção) ou aperte **Y** mirando no centro. |
| Mira treme parada | Diminua *Estabilidade parado* ou ligue a *Trava de micro-movimento* (aba Mira). |
| Cursor anda aos trancos | Aumente *Suavidade do movimento* para 20–25 ms (aba Mira); aproxime o dispositivo do computador. |
| O tiro desvia ao apertar o gatilho | Aumente a *Compensação do tranco* (aba Tiro). |
| O cursor disputa com o touchpad | Use *Só light gun (driver)* (Linux) ou mantenha *Ceder ao touchpad/mouse* ligado. |
| macOS: nada se mexe | Libere **Acessibilidade** e **Monitoramento de Entrada** e abra o aplicativo de novo. |
| Escolheu um idioma por engano | Procure **🌐 Language** no topo (sempre em inglês) e escolha *Português (Brasil)* ou *English*. |

**Conferir o sistema sem dispositivo nenhum:**
```bash
capybara-lightgun selftest
```
No Windows, rode
`%LOCALAPPDATA%\CapybaraLightgun\venv\Scripts\capybara-lightgun selftest`. No
macOS,
`~/Library/Application\ Support/CapybaraLightgun/venv/bin/capybara-lightgun selftest`.

O registro do aplicativo é o `client.log`, na [pasta de configurações](#12-onde-ficam-os-arquivos).

---

## 9. Atualizando

Baixe a versão nova (ZIP ou `git pull`) e **rode o instalador de novo**.
Ajustes, perfis, calibração e idioma são mantidos.

---

## 10. Desinstalando

| Sistema | Como |
|---|---|
| Linux | `~/.local/share/capybara-lightgun/uninstall.sh` |
| Windows | *Configurações → Aplicativos → Capybara Lightgun → Desinstalar*, ou `installer\windows\Desinstalar.bat` |
| macOS | `~/Library/Application\ Support/CapybaraLightgun/uninstall.sh` |

Os seus ajustes são mantidos; apague a [pasta de configurações](#12-onde-ficam-os-arquivos)
para removê-los também. No Linux, as mudanças no sistema podem ser desfeitas
com `sudo rm /etc/udev/rules.d/70-capybara-lightgun.rules
/etc/modules-load.d/capybara-lightgun.conf` e restaurando o
`/etc/bluetooth/input.conf` a partir da cópia de segurança
(`input.conf.bak-lightgun`).

---

## 11. Instalação manual (desenvolvedores)

```bash
git clone https://github.com/loboguaraBR/CapybaraLightgun.git
cd CapybaraLightgun
python3 -m venv .venv
.venv/bin/pip install -e '.[dev,sim]'     # Windows: .venv\Scripts\pip install -e ".[dev,sim]"
.venv/bin/pytest                           # testes
.venv/bin/capybara-lightgun selftest       # verificação do sistema
.venv/bin/capybara-lightgun gui            # abre o aplicativo
```

No Linux, o acesso aos dispositivos ainda precisa da regra udev
(`sudo ./scripts/fix-linux-joycon.sh`).

---

## 12. Onde ficam os arquivos

| | Programa | Ajustes, calibração, idioma, registro |
|---|---|---|
| Linux | `~/.local/share/capybara-lightgun` | `~/.config/capybara-lightgun` |
| Windows | `%LOCALAPPDATA%\CapybaraLightgun` | `%APPDATA%\capybara-lightgun` |
| macOS | `~/Library/Application Support/CapybaraLightgun` e `~/Applications/Capybara Lightgun.app` | `~/Library/Application Support/capybara-lightgun` |
