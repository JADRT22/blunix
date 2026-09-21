<p align="center">
  <img src="data/com.github.fernando.soberix.png" alt="Logo do Soberix" width="120">
</p>

<h1 align="center">Soberix</h1>

<p align="center">
  <a href="https://github.com/JADRT22/soberix/releases/latest"><img src="https://img.shields.io/github/v/release/JADRT22/soberix?style=flat-square" alt="Última release"></a>
  <a href="https://github.com/JADRT22/soberix/stargazers"><img src="https://img.shields.io/github/stars/JADRT22/soberix?style=flat-square" alt="Stars"></a>
  <a href="https://github.com/JADRT22/soberix/actions/workflows/tests.yml"><img src="https://img.shields.io/github/actions/workflow/status/JADRT22/soberix/tests.yml?branch=main&style=flat-square&label=tests" alt="Testes"></a>
  <a href="https://github.com/JADRT22/soberix/blob/main/LICENSE"><img src="https://img.shields.io/github/license/JADRT22/soberix?style=flat-square" alt="Licença"></a>
  <img src="https://img.shields.io/badge/platform-Linux-fcc624?style=flat-square" alt="Plataforma: Linux">
</p>

<p align="center">
  Gerenciador de launcher de Roblox open-source para Linux — o que o <a href="https://github.com/bloxstraplabs/bloxstrap">Bloxstrap</a>
  faz para o Windows, construído sobre o <a href="https://sober.vinegarhq.org/">Sober</a>.
</p>

<p align="center">
  <a href="https://jadrt22.github.io/soberix/"><b>🌐 Site</b></a> ·
  <a href="https://github.com/JADRT22/soberix/releases/latest"><b>⬇ Download</b></a>
</p>

---

O **Soberix** gerencia o [Sober](https://sober.vinegarhq.org/) — o runtime da VinegarHQ que
roda o cliente Android do Roblox nativamente no Linux, sem Wine. O Sober faz o trabalho
pesado; o Soberix o gerencia do mesmo jeito que o Bloxstrap gerencia o cliente do Windows:
perfis de qualidade, FastFlags, mods, activity tracking e backups — por trás de uma interface
amigável.

> [!WARNING]
> Desde 30/09/2025, o Roblox só respeita FastFlags em uma **allowlist** — flags fora da lista
> são ignoradas pelo cliente. O Soberix só escreve flags da allowlist conhecida.
> Referência: [Sober tips & tricks](https://vinegarhq.org/Sober/Configuration/TipsAndTricks.html)

## ✨ Funcionalidades

- 🎮 **Jogar com um clique** — um menu compacto com o botão **JOGAR**; seu perfil de qualidade
  é aplicado automaticamente a cada abertura. Sem lock-in: abrir o Sober direto continua
  funcionando, e flags setadas manualmente são sempre preservadas.
- 🕹️ **Activity tracking** — mostra o que você está jogando (nome real do jogo, resolvido pela
  API pública do Roblox) e permite **reentrar no servidor exato** em que você estava, mesmo
  depois de fechar o Sober — além de histórico de servidores visitados e ações rápidas na
  taskbar (Jogar / Reentrar).
- ⭐ **Jogos recentes e favoritos** — chips na tela inicial para reabrir um jogo com um clique.
- 🔄 **Verificador de updates** — consulta o GitHub Releases e **baixa o novo AppImage** para
  `~/Downloads`; o atalho do menu se reaponta sozinho quando você abre a nova versão.
- 📊 **Perfis de qualidade** — presets *Leve* (mudança pequena), *Médio* (equilibrado) e
  *Completo* (FPS máximo), cada um explicando exatamente o que muda antes de aplicar.
- ⚡ **Editor de FastFlags** — seguro pela allowlist, com descrições legíveis do que cada flag
  faz, além de modo manual para usuários avançados.
- 🧩 **Gerenciador de mods** — instala mods `.zip` no `asset_overlay` do Sober (protegido
  contra zip-slip), lista e remove — além de **mods populares em 1 clique**
  (som de morte mudo embutido; sons/cursores clássicos assim que existir um espelho da
  comunidade).
- 💾 **Backups** — snapshots automáticos do `config.json` antes de cada escrita, com restore.
- 🩺 **Doctor** — verifica CPU (SSE4.1/4.2), Flatpak, Sober e Vulkan.
- 🌎 **7 idiomas** — English, Português, Español, Français, Deutsch, Русский, 日本語:
  detectado automaticamente do locale do sistema, trocável na hora nas configurações.
- 💬 **Discord Rich Presence** — um switch para mostrar o que você joga no Discord
  (funcionalidade nativa do Sober, gerenciada com toggle seguro para backups).
- 🖥️ **GUI GTK4** *e* um **CLI** completo — simples para iniciantes, scriptável para avançados.

## 🤔 Por que não "usar o Bloxstrap logo"?

- **O Bloxstrap é Windows-only** (WPF/.NET) e depende de mecanismos do Windows (registro,
  `ClientSettings/ClientAppSettings.json`, pasta `Modifications/`) — e não está mais em
  desenvolvimento ativo.
- No Linux, a fundação correta é o **Sober** (Flatpak `org.vinegarhq.Sober`), que roda o
  cliente **Android** do Roblox nativamente — sem Wine, sem camada de tradução.
- O Sober é closed-source e Flatpak-only; os pontos de integração corretos são o
  `config.json` e o `asset_overlay` documentados — exatamente o que o Soberix gerencia.

## 📥 Instalação

> Visão geral, screenshots e FAQ no **[site](https://jadrt22.github.io/soberix/)**.

> [!NOTE]
> **Requisito:** o Flatpak [Sober](https://sober.vinegarhq.org/).
> ```bash
> flatpak install flathub org.vinegarhq.Sober
> ```

Baixe o AppImage mais recente na página de [**Releases**](https://github.com/JADRT22/soberix/releases/latest):

```bash
chmod +x Soberix-*.AppImage
./Soberix-*.AppImage
```

Também funciona com duplo clique (marque como executável uma vez). Novas releases são
construídas automaticamente pelo CI — para atualizar, baixe o novo AppImage e substitua o
antigo (o banner de update pode baixar para você). Suas configurações, flags e mods ficam em
`~/.local/share`/`~/.local/state` e nunca são tocados.

Opcionalmente, registre no menu de aplicativos (feito automaticamente na primeira abertura):

```bash
./Soberix-*.AppImage install-menu
```

### Requisitos

- Linux x86_64 com SSE4.1 e SSE4.2 (`grep -o sse4_1 /proc/cpuinfo`)
- [Flatpak](https://flatpak.org/) com o Flathub configurado, mais o Flatpak do Sober
- Python 3.11+ com PyGObject/GTK 4 ao rodar do código-fonte:
  - Arch/CachyOS: `sudo pacman -S python-gobject gtk4`
  - Debian/Ubuntu: `sudo apt install python3-gi gir1.2-gtk-4.0`

### Rodar do código-fonte

```bash
git clone https://github.com/JADRT22/soberix.git
cd soberix
python3 -m soberix            # GUI
python3 -m soberix doctor     # CLI (sem precisar de GTK)
```

Ou construa seu próprio AppImage: `./tools/build-appimage.sh`

## 🚀 Uso

A GUI abre em um menu pequeno: **JOGAR** (aplica seu perfil e abre o Roblox) e
**Configurações** (perfil de qualidade, FastFlags, mods, servidores, backups, checagens do
sistema, idioma).

Para quem prefere o terminal:

```text
soberix play                       # abre o Roblox com seu perfil salvo
soberix play 2753915549            # abre um jogo por place ID ou URL
soberix play 2753915549 --profile light|medium|full|default|off

soberix doctor                     # checagem do ambiente (CPU, flatpak, Sober, Vulkan)
soberix install-menu               # cria o atalho no menu de aplicativos
soberix config show|set|reset      # opções oficiais do config do Sober
soberix fflags list|get|set|unset  # FastFlags seguros pela allowlist
soberix fflags preset leve|medio|completo|default
soberix mods list|install|remove|clear   # mods no asset_overlay (.zip)
soberix mod-presets [id]           # mods populares (mute death sound funciona offline)
soberix games                      # jogos recentes (* = favorito)
soberix status                     # jogo/servidor detectado agora nos logs do Sober
soberix rejoin                     # reabre o último servidor em que você esteve
soberix servers                    # servidores visitados (com links de rejoin)
soberix backup create|list|restore # snapshots do config.json
soberix launch [--place ID]        # abertura simples do Sober
```

## 🔧 Como o Soberix modifica o Sober

| O quê          | Mecanismo                                                       |
|----------------|-----------------------------------------------------------------|
| Config/fflags  | `~/.var/app/org.vinegarhq.Sober/config/sober/config.json`       |
| Mods           | `~/.var/app/org.vinegarhq.Sober/data/sober/asset_overlay/`      |
| Backups        | `~/.local/share/soberix/backups/`                               |
| Estado Soberix | `~/.local/state/soberix/` (configurações, histórico, log)       |

O Sober só lê o config na inicialização: depois de mudar qualquer coisa, feche e reabra o
Roblox (vale para FastFlags e mods).

## 🗺️ Como se compara

| | Bloxstrap (Windows) | Sober (Linux) | **Soberix (Linux)** |
|---|---|---|---|
| Open source | ✅ MIT | ❌ Closed | ✅ MIT |
| Papel | Gerencia o cliente Windows | Roda o cliente Android | Gerencia o Sober |
| Distribuição | Installer (publicado pelo CI) | Flatpak | AppImage (publicado pelo CI) |

## 🔒 Segurança & privacidade

- O app nunca lê nem transmite seu cookie de sessão do Roblox (`cookies`, `state`).
- Os backups contêm apenas o `config.json`.
- Sem telemetria. 100% open source. O activity tracking lê apenas os arquivos de log locais
  do Sober.
- Mods são arquivos `.zip` que você fornece (ou o preset embutido offline), protegidos contra
  zip-slip.

## ⚠️ Legal & limitações

- O Soberix **não é afiliado** à Roblox Corporation nem à VinegarHQ.
- Clientes não oficiais podem em teoria violar os ToS do Roblox; a VinegarHQ afirma que o uso
  normal do Sober "muito raramente" gera moderação. Use por sua conta e risco. Sem
  multi-instance, bots ou exploits — o Sober bloqueia multi-instance por design.
- **FastFlags**: só a allowlist pós-30/09/2025 funciona; a Roblox pode mudá-la a qualquer
  momento.
- **Studio**: o Sober não roda o Roblox Studio (para isso, use o Vinegar via Wine).

## 🤝 Contribuindo

Issues e PRs são bem-vindos! O projeto é Python puro (só stdlib; GTK4/PyGObject para a GUI).
Rode a suíte de testes com `python3 -m pytest` (os smoke tests da GUI precisam de GTK4/Xvfb;
a GUI precisa de python-gobject e gtk4 instalados).

## 📄 Licença

[MIT](LICENSE) — a mesma do Bloxstrap.

---

<p align="center">
  <sub><i>Não afiliado à Roblox Corporation nem à VinegarHQ.</i></sub>
</p>

<p align="center"><a href="README.md">🇺🇸 Read in English</a></p>
