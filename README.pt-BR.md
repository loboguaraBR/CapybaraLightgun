# Capybara Lightgun

[English](README.md) · **Português (Brasil)**

O Capybara Lightgun transforma **qualquer dispositivo com giroscópio** num
**apontador absoluto**: uma light gun que mira para onde você aponta
fisicamente. Funciona no **Linux**, no **Windows** e no **macOS**
(experimental). Quem não tiver um dispositivo com giroscópio pode usar o
**mouse do sistema**.

> **Foco no giroscópio, sem preferência por dispositivo.** O projeto trata do
> giroscópio como sensor, não de uma marca ou produto. Ele lê velocidade
> angular e aceleração de qualquer dispositivo que as exponha pelo sistema
> operacional (hoje, controles de videogame; amanhã, outros dispositivos com
> IMU) e as transforma numa mira calibrada e fisicamente fiel. Os nomes de
> dispositivos citados aqui só indicam o que já foi visto funcionando. Não
> são preferência nem recomendação.

> 🤖 **Gerado com o Claude.** Este projeto (código, testes, instaladores,
> documentação e traduções) foi **gerado com o assistente de inteligência
> artificial Claude, da Anthropic**, sob a direção do autor do projeto, que o
> testou e publicou. Software gerado por IA pode conter erros: revise antes de
> confiar nele. A Anthropic não tem relação com este projeto.

> ⚖️ **Uso por sua conta e risco.** O software é fornecido **no estado em que
> se encontra, sem nenhuma garantia**. **Quem usa, modifica ou distribui o
> software é o único responsável por esse uso.** O autor não controla e não se
> responsabiliza pela forma como terceiros o utilizam. Leia o
> [aviso legal completo](AVISO-LEGAL.md).

**Documentação:** [Guia de instalação (Linux · Windows · macOS)](docs/INSTALACAO.md) ·
[Aviso legal](AVISO-LEGAL.md) · [Licença](LICENSE) ·
[Guia completo de uso](docs/GUIA-pt-BR.md)

---

## Sumário

- [Por que este projeto existe](#por-que-este-projeto-existe)
- [O que ele faz](#o-que-ele-faz)
- [Como funciona](#como-funciona)
- [Entradas, saídas e sistemas suportados](#entradas-saídas-e-sistemas-suportados)
- [Instalação](#instalação)
- [Usando o aplicativo](#usando-o-aplicativo)
- [Para desenvolvedores: uma bancada de testes de giroscópio](#para-desenvolvedores-uma-bancada-de-testes-de-giroscópio)
- [Estrutura do projeto e testes](#estrutura-do-projeto-e-testes)
- [Idiomas](#idiomas)
- [Licença (MIT): o que significa](#licença-mit-o-que-significa)
- [Isenção de responsabilidade e avisos legais](#isenção-de-responsabilidade-e-avisos-legais) · texto completo: [AVISO-LEGAL.md](AVISO-LEGAL.md)

---

## Por que este projeto existe

O Capybara Lightgun é um projeto **pessoal, educacional e sem fins
lucrativos**, criado para:

1. **Ajudar desenvolvedores a testar rapidamente recursos de giroscópio.**
   Quem desenvolve um aplicativo, jogo, emulador, ferramenta de
   acessibilidade ou protótipo de pesquisa com movimento ou mira por
   giroscópio pode usar o projeto como uma bancada de testes pronta. Ele lê
   dados reais da IMU, calcula a orientação, projeta na tela e entrega tudo
   como eventos padrão de mouse/ponteiro, que o seu aplicativo já entende.
   Não é preciso escrever um driver antes.
2. **Tornar acessível a mira estilo light gun** com equipamentos que as
   pessoas já têm, em telas modernas, onde as light guns de TV de tubo não
   funcionam mais.
3. **Compartilhar as técnicas abertamente** (fusão de sensores, calibração
   por transformação projetiva, suavização de baixa latência) para que outras
   pessoas aprendam e melhorem.

O projeto **não** tem o objetivo de gerar lucro, competir com qualquer
produto ou prejudicar ninguém. Por isso ele é distribuído sob a licença
permissiva **MIT** (veja abaixo).

## O que ele faz

- **Mira absoluta:** o cursor vai exatamente para onde o dispositivo aponta,
  como numa light gun de verdade, e não como um "mouse por giroscópio"
  relativo. Girar o pulso não mexe a mira.
- **Calibração:** mire no centro e nos 4 cantos da tela. O mapeamento é uma
  homografia, então a mira continua correta mesmo com você fora do eixo da
  tela ou com a tela inclinada.
- **Movimento suave e com pouco atraso:** o cursor é atualizado num ritmo
  fixo (250 Hz por padrão), interpolado pelo relógio do próprio sensor. Isso
  esconde as rajadas e travadas do Bluetooth. Um filtro adaptativo ("One
  Euro") tira o tremor da mão sem atrasar os movimentos rápidos.
- **Tiro estabilizado:** o tiro usa a posição da mira de alguns milissegundos
  antes do aperto, para o tranco do dedo não desviar.
- **Controle da deriva:** o erro do giroscópio é medido de novo sempre que o
  dispositivo fica parado, e há um botão para recentrar.
- **Dois modos de saída:**
  - **Só light gun (driver)**, só no Linux: um dispositivo virtual de light
    gun separado, que a área de trabalho ignora. O cursor e o touchpad ficam
    livres, e os emuladores que leem os dispositivos direto (como o RetroArch
    com o driver `udev`) usam a arma.
  - **Mouse do sistema:** move o cursor de verdade e funciona com qualquer
    coisa. Devolve o cursor sozinho enquanto você usa o touchpad ou o mouse.
- **Extras de light gun:** recarregar apontando para fora da tela (opcional),
  recarregar com um tranco (opcional), tiro automático, teclas do teclado em
  qualquer botão, vibração como "coice", mira desenhada na tela e perfis por
  jogo que trocam sozinhos conforme a janela ativa.
- **Aplicativo de janela:** ícone na bandeja ou barra de menus, visualização
  ao vivo, calibração e estande de teste em tela cheia, em 6 idiomas.
- **Funciona também sem giroscópio:** com o **mouse do sistema** como fonte,
  quem não tem um dispositivo com giroscópio ainda ganha os recursos de light
  gun (recarregar, tiro automático, teclas, mira na tela, perfis).

## Como funciona

```
giroscópio + acelerômetro ──► orientação (filtro Mahony, corrigido pela gravidade)
        │
        ▼
direção do cano ──► interseção raio/plano ──► homografia calibrada ──► (x, y) na tela
        │                                                                 │
        ▼                                                                 ▼
 filtro One Euro + interpolação em ritmo fixo                saída de ponteiro absoluto
                                          (uinput no Linux · SendInput no Windows · Quartz no macOS)
```

- Os eixos dos sensores de cada família de dispositivos são convertidos para
  uma convenção interna única (X = cano, Y = esquerda, Z = cima). O código
  específico de cada dispositivo se limita a ler o sensor; todo o resto é
  compartilhado.
- Sem magnetômetro não existe referência absoluta para o eixo horizontal. Por
  isso a deriva horizontal é tratada com a estimativa automática do erro do
  giroscópio e com o botão de recentrar.

## Entradas, saídas e sistemas suportados

**Entradas (fontes da mira)**, escolhidas automaticamente ou no aplicativo:

| Fonte | Como é lida | Observações |
|---|---|---|
| Joy-Con / Pro Controller (Nintendo Switch) | Driver do kernel Linux (`hid-nintendo`, evdev) · HID direto nos outros sistemas | Caminho mais testado |
| DualSense (PS5) / DualShock 4 (PS4) | Driver do kernel Linux · SDL | Aponte a frente do controle para a tela |
| Outros controles com giroscópio | SDL (API genérica de sensores) | Ex.: Steam Deck/Controller, modelos 8BitDo com giroscópio |
| Mouse do sistema | Posição e botões do cursor do sistema | Para quem não tem dispositivo com giroscópio |

Controles sem giroscópio, como a maioria dos controles de Xbox comuns, não
conseguem mirar. O aplicativo avisa e sugere o mouse.

**Saídas:** dispositivo virtual de light gun (Linux), mouse do sistema
(Linux, Windows, macOS), modo "mouse giroscópio" relativo e teclas do
teclado.

**Sistemas:** Linux (X11; testado), Windows (implementado, ainda não validado
em hardware real) e macOS (experimental; veja
[`docs/TESTE-MAC.md`](docs/TESTE-MAC.md)). Os testes automáticos rodam em
Linux, Windows e macOS.

## Instalação

> 📘 **Passo a passo para cada sistema** (requisitos, pareamento, permissões,
> configuração de emuladores, solução de problemas, atualização e
> desinstalação): **[docs/INSTALACAO.md](docs/INSTALACAO.md)**. Abaixo, a
> versão resumida.

Precisa do Python 3.9 ou mais novo. Cada instalador cria o próprio ambiente
isolado e não mexe no Python do sistema.

**Linux**
```bash
./installer/linux/install.sh
```
Pode pedir sua senha uma vez, para instalar uma regra udev (permissão de
acesso aos dispositivos) e ajustar o BlueZ (`ClassicBondedOnly=false`), o que
controles como o Joy-Con exigem. Veja as
[mudanças feitas no seu sistema](#mudanças-feitas-no-seu-sistema).

**Windows:** dois cliques em `installer\windows\Instalar.bat`. Não precisa de
administrador e instala o Python pelo `winget` se faltar.

**macOS (experimental):** dois cliques em `installer/macos/Instalar.command`.
Depois, libere o aplicativo em *Ajustes do Sistema → Privacidade e Segurança
→ Acessibilidade* e *Monitoramento de Entrada*.

Todos os instaladores criam um atalho no menu e fazem o aplicativo abrir no
login, minimizado na bandeja. Os desinstaladores vêm junto. O guia completo de
uso, com o passo a passo de cada emulador e a tabela de ajustes, está em
[`docs/GUIA-pt-BR.md`](docs/GUIA-pt-BR.md).

## Usando o aplicativo

1. Deixe o dispositivo parado por ~1 s (o giroscópio fica **ok**).
2. Clique em **Calibrar**, mire no centro e nos 4 cantos e aperte o gatilho.
3. Escolha o modo: **Só light gun (driver)** ou **Mouse do sistema**.
4. Teste no **Estande de teste** (tela cheia, com estatística de acertos).

A aba **Ajuda** explica como configurar os emuladores (RetroArch, MAME,
Dolphin, DuckStation/PCSX2) e traz dicas de precisão. Pela linha de comando:

```bash
capybara-lightgun gui            # o aplicativo (também: --tray)
capybara-lightgun run --dry-run  # desenha a mira no terminal, sem mexer no mouse
capybara-lightgun calibrate      # calibração pelo terminal
capybara-lightgun buttons        # mostra o nome dos botões apertados
capybara-lightgun devices        # lista os dispositivos detectados
capybara-lightgun selftest       # confere o sistema sem precisar de dispositivo
capybara-lightgun sim            # estande de tiro (pygame)
```

## Para desenvolvedores: uma bancada de testes de giroscópio

Formas de usar o Capybara Lightgun no desenvolvimento de recursos de
giroscópio ou de ponteiro:

- **Alimentar o seu aplicativo com mira por giroscópio de verdade, sem
  escrever driver.** O seu aplicativo só recebe eventos de mouse/ponteiro
  absoluto (ou lê o dispositivo virtual, no Linux).
- **Inspecionar o comportamento do sensor:** a visualização ao vivo mostra
  lado a lado a mira filtrada e a mira crua, sem filtro. O
  `run --dry-run` desenha a mira no terminal.
- **Testar os seus próprios algoritmos:** a fusão (`fusion.py`), a geometria
  e a calibração (`geometry.py`), os filtros (`filters.py`) e o pipeline
  (`engine.py`) são pequenos, documentados e cobertos por testes que simulam
  uma arma física diante de uma tela.
- **Adicionar um dispositivo novo:** escreva uma fonte de entrada que gere
  `ImuSample` (giroscópio em °/s, acelerômetro em g, dt) e `ButtonState`, na
  convenção de eixos interna. Todo o resto (calibração, suavização, saídas e
  aplicativo) funciona sem mudanças.

## Estrutura do projeto e testes

```
src/capybara_lightgun/
  fusion.py, geometry.py, filters.py   fusão de sensores, projeção/homografia, One Euro
  engine.py                            pipeline: IMU → mira → ponteiro + botões
  calibration.py                       calibração centro + 4 cantos
  inputs/                              evdev (Linux), HID direto, SDL, mouse do sistema
  outputs/                             uinput, SendInput, Quartz, console
  client.py, gui.py, gui_fields.py     aplicativo residente (Qt) e ajustes
  i18n.py, locales/                    traduções
  selftest.py, simulator.py            autoteste e estande de tiro (pygame)
installer/                             instaladores Linux, Windows e macOS
tests/                                 testes (pytest)
```

```bash
python -m venv .venv && .venv/bin/pip install -e '.[dev,sim]'
.venv/bin/pytest
```

## Idiomas

A interface está em inglês (padrão), português (Brasil), espanhol, francês,
alemão e chinês simplificado. O seletor **🌐 Language** fica sempre em
inglês, para voltar com facilidade se alguém escolher um idioma por engano.
Para adicionar um idioma, copie um arquivo em
`src/capybara_lightgun/locales/`, traduza, registre em `i18n.py` e rode os
testes. O `tests/test_i18n.py` aponta qualquer texto que faltar.

---

## Licença (MIT): o que significa

Este projeto é licenciado sob a **Licença MIT** (veja [`LICENSE`](LICENSE)). Em
palavras simples (o texto que vale juridicamente é o do arquivo `LICENSE`, em
inglês):

- **Você pode** usar, copiar, modificar, mesclar, publicar, distribuir,
  sublicenciar e vender cópias do software, para qualquer finalidade,
  inclusive comercial.
- **Com uma condição:** manter o aviso de direitos autorais e o texto da
  licença em todas as cópias ou partes substanciais do software.
- **Sem garantia:** o software é fornecido "no estado em que se encontra"
  ("as is"), sem garantia de nenhum tipo, expressa ou implícita, incluindo
  comerciabilidade, adequação a uma finalidade específica e não violação.
- **Sem responsabilidade:** os autores e titulares dos direitos não
  respondem por qualquer reclamação, dano ou outra responsabilidade
  decorrente do software ou do seu uso.

**Por que MIT?** O objetivo é permitir que qualquer pessoa, principalmente
desenvolvedores, estude, teste, reutilize e melhore estas técnicas de
giroscópio com o mínimo de barreiras. A **intenção do autor de não buscar
lucro** é uma declaração de propósito. Ela **não** acrescenta restrições à
licença.

## Isenção de responsabilidade e avisos legais

> O aviso completo, que é o que vale, está em **[AVISO-LEGAL.md](AVISO-LEGAL.md)**
> (inglês: [DISCLAIMER.md](DISCLAIMER.md)). Ele trata, entre outros pontos,
> do uso de IA (Claude) para gerar o projeto e do fato de que **cada usuário é
> o único responsável pela forma como usa o software**. A seção abaixo é um
> resumo.

*Esta seção é informativa e não constitui aconselhamento jurídico. As leis
variam de país para país. Em caso de dúvida jurídica, consulte um
profissional qualificado. Nada aqui restringe ou amplia a
[`LICENSE`](LICENSE); se houver diferença, prevalece a `LICENSE`.*

### Sem garantia, uso por sua conta e risco
Na máxima extensão permitida pela legislação aplicável, o software é
fornecido **"no estado em que se encontra"**, sem garantias de qualquer tipo.
Os autores e colaboradores **não se responsabilizam** por danos diretos ou
indiretos, perda de dados, danos a hardware ou software, lesões, lucros
cessantes, banimento de contas ou qualquer outra consequência de instalar,
usar, modificar ou distribuir este software. A decisão de usar e a forma de
uso são suas, assim como a responsabilidade por elas.

### Finalidade e uso pretendido
O Capybara Lightgun é uma ferramenta não comercial, educacional e de
desenvolvimento, voltada à **interoperabilidade**: permite que dispositivos
que você possui funcionem como dispositivos apontadores no seu próprio
computador. Ele **não se destina** a trapaças, obtenção de vantagem indevida,
burla de restrições ou prejuízo a pessoas, sistemas ou empresas, e não deve
ser usado para isso.

### Sem afiliação; marcas registradas
Este é um projeto **independente**. Não é afiliado, patrocinado ou endossado
pela Nintendo, Sony Interactive Entertainment, Microsoft, Valve, 8BitDo,
Apple ou qualquer outra empresa. *Nintendo Switch, Joy-Con, PlayStation,
DualSense, DualShock, Xbox, Steam, Steam Deck, macOS, Windows* e outros nomes
são marcas de seus respectivos titulares. Eles aparecem aqui **apenas para
indicar compatibilidade** (uso nominativo). Citar um dispositivo não é uma
recomendação, e nenhum dispositivo é preferido: o foco do projeto é o
**giroscópio** como sensor.

### Sem conteúdo proprietário, sem burla de proteções
O projeto **não contém** código, firmware, chaves de criptografia, BIOS,
ROMs, jogos ou outro material protegido por direitos autorais de fabricantes
de dispositivos ou de jogos. Ele usa apenas **interfaces públicas dos
sistemas operacionais** (evdev/uinput, HID, SDL, Win32, Quartz) e formatos de
relatório de dispositivos documentados publicamente ou pela comunidade, para
fins de interoperabilidade. Ele **não modifica** o firmware dos dispositivos
e **não contorna** proteções contra cópia, DRM ou qualquer outra medida
técnica de proteção.

### Jogos, emuladores e serviços online
O Capybara Lightgun não fornece jogos nem ROMs e não aponta onde obtê-los. Se
você o usar com emuladores, **é sua responsabilidade** ter cópias legítimas e
cumprir as licenças e leis aplicáveis. A emulação de dispositivos de entrada
pode **violar os termos de uso** de jogos online ou competitivos, ou acionar
sistemas antitrapaça. Não use onde isso não for permitido. Os autores não se
responsabilizam por suspensões de contas ou outras penalidades.

### Mudanças feitas no seu sistema
Os instaladores são transparentes, atuam no nível do usuário e podem ser
revertidos. Dependendo do sistema, eles podem:
- **Linux:** adicionar uma regra udev
  (`/etc/udev/rules.d/70-capybara-lightgun.rules`) que dá ao usuário logado
  acesso aos controles suportados e ao `/dev/uinput`; carregar os módulos
  `uinput` e `hid-nintendo`; ajustar `ClassicBondedOnly=false` em
  `/etc/bluetooth/input.conf`, com cópia de segurança. **Atenção:** esse
  ajuste permite que dispositivos de entrada Bluetooth se conectem sem
  "bonding". Controles como o Joy-Con precisam disso, mas o ajuste afrouxa um
  pouco um padrão de segurança do BlueZ. Avalie se você está num ambiente
  sensível; para desfazer, restaure a cópia de segurança.
- **Todos os sistemas:** criar um ambiente Python isolado, um atalho no menu
  e a abertura automática no login. Os desinstaladores removem tudo isso (seus
  ajustes são mantidos).
- **macOS:** pedir as permissões de Acessibilidade e Monitoramento de
  Entrada.

Leia os scripts em `installer/` e `scripts/` antes de executá-los.

### Privacidade
O aplicativo **não faz nenhuma conexão de rede** e **não coleta dados de
uso**. Configurações, calibração e registros ficam só no seu computador. A
troca automática de perfil, que é opcional, lê localmente o **título ou a
classe da janela ativa**, apenas para comparar com as palavras que você
configurou. Essa informação nunca é armazenada nem enviada a lugar algum.

### Segurança física
Você vai movimentar um objeto no ar: use a **alça de pulso**, mantenha espaço
livre ao seu redor e longe de outras pessoas, segure o dispositivo com firmeza
e faça pausas. A vibração é opcional.

### Software de terceiros
O Capybara Lightgun depende de pacotes de terceiros que têm **licenças
próprias**, entre eles PyQt5 (GPL v3 ou comercial), Qt, SDL2 e PySDL2 (zlib e
domínio público), pygame (LGPL), python-evdev / evdev-binary (BSD) e hidapi
(BSD/GPL/original). Os instaladores baixam esses pacotes do PyPI. A Licença
MIT deste projeto cobre apenas o código do próprio projeto. Quem **redistribuir
um pacote** que inclua esses componentes (por exemplo, um executável
empacotado) precisa cumprir também as licenças deles, em especial os termos da
GPL do PyQt5.

### Contribuições
Ao contribuir, você concorda que a sua contribuição será licenciada sob a
mesma Licença MIT e declara que tem o direito de enviá-la.

---

Copyright (c) 2026 loboguaraBR. Licenciado sob a [Licença MIT](LICENSE).
