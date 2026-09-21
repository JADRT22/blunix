# Soberix (Português)

> [!NOTE]
> Este é o README secundário. O principal, em inglês, está aqui:
> **[README.md](README.md)** 🇬🇧

**Soberix** é um gerenciador estilo Bloxstrap para Linux, construído sobre o
[Sober](https://sober.vinegarhq.org/) — o runtime da VinegarHQ que roda o
cliente Android do Roblox nativamente no Linux, sem Wine.

> **[🌐 Site oficial](https://jadrt22.github.io/soberix/)** — visão geral, screenshots e FAQ.

O Sober faz o trabalho pesado (rodar o Roblox). O Soberix apenas o *gerencia*:
configurações, FastFlags, mods e backups — assim como o Bloxstrap faz para o
cliente Windows.

> **Aviso importante sobre FastFlags:** desde 30/09/2025 a Roblox usa uma
> *allowlist* de FastFlags — flags fora da lista são **ignoradas** pelo cliente.
> O Soberix trabalha apenas com flags da allowlist conhecida.
> Referência: https://vinegarhq.org/Sober/Configuration/TipsAndTricks.html

## Por que não é um "Bloxstrap de verdade" para Linux?

- **Bloxstrap é Windows-only** (WPF/.NET) e depende de mecanismos do Windows
  (registro, `ClientSettings/ClientAppSettings.json`, pasta `Modifications/`).
- No Linux, a base correta é o **Sober** (Flatpak `org.vinegarhq.Sober`), que
  roda o cliente **Android** do Roblox nativamente — "faster than on Windows",
  segundo a própria página do Flathub.
- O Sober é fechado e distribuído exclusivamente via Flatpak; a integração
  correta é via `config.json` e `asset_overlay`, documentados pela VinegarHQ.

## Funcionalidades

- **Verificação de ambiente**: Flatpak, Sober instalado, arquitetura x86_64,
  SSE4.1/SSE4.2 (obrigatórios), GPU com Vulkan.
- **Editor de configuração** com todos os campos oficiais do Sober
  (`discord_rpc_enabled`, `server_location_indicator_enabled`, `close_on_leave`,
  `enable_gamemode`, `enable_hidpi`, `touch_mode`, `graphics_optimization_mode`,
  `use_opengl`, `use_console_experience`, `enable_mobile_home_screen`,
  `allow_gamepad_permission`, `use_libsecret`).
- **Editor de FastFlags** restrito à allowlist, com botão **Recomendado** em
  3 níveis — **Leve** (muda pouco), **Médio** (equilibrado) e **Completo
  (muda muito)** — cada um explicando o que altera antes de aplicar.
- **Gerenciador de mods** via `asset_overlay`: instala mods `.zip` mantendo a
  estrutura de pastas exigida (espelha `content/…` do base.apk), lista e
  remove mods instalados.
- **Jogos recentes e favoritos**: chips na tela inicial para rejogar com 1 clique
  (`soberix games` no CLI).
- **Checagem de atualização**: consulta as Releases do GitHub e oferece o download
  quando há versão nova.
- **Backups**: snapshot completo da config (`config.json` + fflags) com
  restore e histórico automático antes de qualquer escrita.
- **CLI completa** e **GUI GTK4** com abas (Geral, FastFlags, Mods, Backups).

## Download (jeito fácil)

Baixe o AppImage mais recente na página de **[Releases](https://github.com/JADRT22/soberix/releases/latest)**:

1. Baixe **`Soberix-<versão>-x86_64.AppImage`**
2. Clique com botão direito → **Propriedades → Permitir executar** (só na 1ª vez)
3. Dê duplo clique → janela abre com um botão grande **🎮 JOGAR**
4. Opcional: cole o número ou link de um jogo e clique **Abrir jogo**

> Toda versão nova é gerada automaticamente pela CI do GitHub — igual ao
> Bloxstrap, que publica as releases dele por GitHub Actions. Para atualizar,
> basta baixar o AppImage novo e substituir o antigo (suas configurações,
> flags e mods ficam em `~/.local/share`/`~/.local/state` e não são tocadas).

## Rodar do código (para quem gosta de mexer 🔧)

```bash
git clone https://github.com/JADRT22/soberix.git
cd soberix
python3 -m soberix            # GUI
python3 -m soberix doctor     # CLI (não precisa de GTK)
```

Ou gere seu próprio AppImage: `./tools/build-appimage.sh`

Para o ícone ficar no menu de aplicativos:

```bash
./Soberix-*-x86_64.AppImage install-menu
```

A janela mostra **"Tudo pronto! ✅"** quando o ambiente está OK. Se faltar
algo, aparece o problema em português simples, e os **detalhes técnicos**
ficam escondidos atrás de um botão.

> O AppImage usa o Python 3 + GTK 4 do sistema (presentes em qualquer distro
> com desktop). Precisa do **Sober instalado** — se não estiver, o app avisa
> com o comando pronto para copiar.

### CLI amigável

```bash
soberix play              # abre o Roblox
soberix play 2753915549   # abre um jogo pelo número
soberix play "https://www.roblox.com/games/2753915549/Brookhaven-RP"   # link do site
soberix play --profile light|medium|full   # aliases em inglês (ou leve/medio/completo)
```

## Requisitos

- Linux x86_64 com SSE4.1 e SSE4.2 (`grep -o sse4_1 /proc/cpuinfo`)
- [Flatpak](https://flatpak.org/) configurado com o Flathub
- Sober instalado: `flatpak install flathub org.vinegarhq.Sober`
- Python 3.11+ com PyGObject (GTK 4) para a GUI
  - Arch/CachyOS: `sudo pacman -S python-gobject gtk4`
  - Debian/Ubuntu: `sudo apt install python3-gi gir1.2-gtk-4.0`

## Instalação (a partir do código)

```bash
cd ~/Projetos/soberix
./tools/build-appimage.sh         # gera Soberix-<versão>-x86_64.AppImage
./Soberix-*-x86_64.AppImage install-menu
```

Ou apenas use sem instalar:

```bash
python3 -m soberix            # GUI
python3 -m soberix --help     # CLI
```

## Uso (avançado)

### CLI

```bash
soberix doctor                       # verifica o ambiente
soberix play 2753915549              # modo simples: joga (nº, link ou nada)
soberix install-menu                 # atalho no menu de aplicativos
soberix config show                  # mostra a config atual do Sober
soberix config set close_on_leave true
soberix config set touch_mode fake-off
soberix fflags list                  # flags da allowlist
soberix fflags set FIntDebugForceMSAASamples 4
soberix fflags preset performance    # aplica preset
soberix mods list                    # mods instalados no asset_overlay
soberix mods install meumod.zip      # instala um mod
soberix mods remove ArrowCursor.png  # remove por caminho relativo
soberix status                       # jogo/servidor detectado nos logs do Sober
soberix rejoin                       # reentra no último servidor
soberix servers                      # servidores visitados
soberix backup create                # cria backup
soberix backup list                  # lista backups
soberix backup restore <arquivo>     # restaura
soberix launch                       # abre o Roblox (Sober)
soberix launch --place 123456789     # abre uma experience
```

### GUI

```bash
python3 -m soberix
```

Abas: **Início** (botão JOGAR ROBLOX + status), **Config** (opções do Sober),
**FastFlags** (allowlist + presets), **Mods** (asset_overlay),
**Backups** (criar/restaurar).

## Como o Soberix modifica o Sober

| Recurso        | Mecanismo                                                       |
|----------------|-----------------------------------------------------------------|
| Config/Fflags  | `~/.var/app/org.vinegarhq.Sober/config/sober/config.json`       |
| Mods           | `~/.var/app/org.vinegarhq.Sober/data/sober/asset_overlay/`      |
| Backups        | `~/.local/share/soberix/backups/`                              |
| Logs           | `~/.local/state/soberix/soberix.log`                          |

O Sober só lê a config no boot: após mudar algo, feche o Roblox e abra de novo
(vale para FastFlags e mods).

## Segurança e privacidade

- Não faz download de binários; mods vêm de arquivos `.zip` que **você** fornece.
- Nunca lê nem transmite o cookie de sessão do Roblox (`cookies`, `state`).
- Backup inclui apenas `config.json`.
- Sem telemetria. Código 100% aberto.

## Avisos legais

- Soberix **não é afiliado** à Roblox Corporation nem à VinegarHQ.
- Uso de clientes não oficiais pode, em tese, violar os ToS da Roblox. A
  VinegarHQ declara que o uso normal do Sober "muito raramente" gera moderação;
  use por sua conta e risco.
- Não use para: multi-instance, bots, exploits. O Sober bloqueia multi-instance
  por design e a Roblox considera a prática maliciosa.

## Limitações conhecidas

- **FastFlags**: somente a allowlist pós-30/09/2025 funciona. O Soberix valida
  contra ela, mas a Roblox pode alterar a lista a qualquer momento.
- **Studio**: o Sober não roda o Roblox Studio. Para Studio no Linux, use o
  Vinegar (via Wine) — fora do escopo do Soberix.
- **Multi-instance**: não suportado (nem pelo Sober, nem aqui).

## Licença

MIT.
