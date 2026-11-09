# Roteiro de teste no Mac (≈ 5 minutos)

O suporte a macOS foi feito sem um Mac à mão. Os testes automáticos rodam em
Macs virtuais, mas só um Mac de verdade confirma o Bluetooth, as permissões e
o cursor. Se você tem um Mac, siga os passos e anote o resultado de cada um.

**Precisa de:** macOS 10.15 ou mais novo, Python 3.9+ (python.org ou
`brew install python`) e, se tiver, um Joy-Con, Pro Controller, DualSense ou
DualShock 4.

## 1. Instalar
Dê dois cliques em `installer/macos/Instalar.command`. Se o macOS bloquear,
clique com o botão direito → **Abrir**.

- [ ] A instalação terminou e o **autoteste** no final mostrou `TUDO OK`
      (a linha "permissões" pode aparecer como aviso; isso é esperado agora).
- [ ] O aplicativo **Capybara Lightgun** abriu e o ícone da mira apareceu na barra de menus.

## 2. Permissões
No aplicativo, clique em **⚠ Liberar permissões do macOS** e ative o
"Capybara Lightgun" em **Acessibilidade** e em **Monitoramento de Entrada**.
Encerre o aplicativo (menu da mira → Encerrar) e abra de novo.

- [ ] O aviso amarelo sumiu.
- [ ] Nas listas de permissões aparece "Capybara Lightgun" (e não "Python" ou "Terminal").
      Se aparecer "Python", anote, porque isso muda como o instalador cria o aplicativo.

## 3. Sem controle (mouse do sistema)
Aba **Controle** → Fonte da mira = **Mouse do sistema**.

- [ ] A mini-tela "Ao vivo" acompanha o mouse.
- [ ] **Estande de teste**: os cliques acertam os alvos e não contam em dobro.
- [ ] Botão direito no estande = "tiro fora da tela" (o cursor pisca no canto e volta).

## 4. Com controle (se tiver)
Pareie em Ajustes → Bluetooth. Fonte da mira = **Automático**.

- [ ] O topo mostra "light gun ativa" e o nome do controle; IMU ~ 60 a 250/s.
- [ ] Apoie o controle parado 1 s: "Giroscópio ok".
- [ ] **Calibrar** (centro + 4 cantos) termina com erro baixo.
- [ ] Ao apontar para os cantos da tela, **o cursor do Mac vai para os cantos**.
- [ ] Girar o pulso (sem mudar a direção) não mexe a mira.
- [ ] O gatilho (ZR / R2) clica; o coice vibra (DualSense/DS4 pelo SDL; Joy-Con pode não vibrar).
- [ ] No **Estande de teste**, acerta os alvos.

## 5. Reinício
- [ ] Depois de sair e entrar de novo na conta, o aplicativo abre sozinho na barra de menus.

## Como enviar o resultado
Copie a saída de:

    ~/Library/Application\ Support/CapybaraLightgun/venv/bin/python -m capybara_lightgun selftest

e o arquivo `~/Library/Application Support/capybara-lightgun/client.log`, e
diga quais caixas falharam.
