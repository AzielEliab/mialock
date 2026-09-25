# M.I.A.Lock

See one person's documented events on a map — when they happened, where, and how long each one lasted.

**Author:** Aziel Eliab · Apache-2.0 · Forks welcome.

## Start

1. Install:

```bash
pip install -e .
```

2. See the next step:

```bash
mialock
```

3. Open the map:

```bash
mialock ui
```

Then open the address it prints. The default is http://127.0.0.1:8765/

Choose a person and press **Show events**.

## Everyday commands

| Command | What you get |
| --- | --- |
| `mialock ui` | Local map. `mialock map` does the same thing. |
| `mialock people` | Who is in the casebook. |

Add `--json` when a script needs the data instead of the sentences.

## Advanced

| Command | What you get |
| --- | --- |
| `mialock search-options` | Search modes (active, archives, Doe, cold case). |
| `mialock queries doe_cold` | Search text you can run yourself. |
| `mialock doe-match --subject subj-elena-cold-demo` | Doe notices ranked as leads to check. |
| `mialock coverage --subject subj-elena-cold-demo` | Which sources were searched. |
| `mialock geojson subj-elena-cold-demo` | A short summary. `--json` or `-o file.geojson` writes the map data. |

On the map, **Advanced** holds search mode, uncertainty ellipses, and coverage heat.

## Notes

Doe results are compatibility leads. Check the source record before you treat a notice as the person. Coverage color shows how thoroughly a source was searched.

Pins use the packaged sample casebook unless you pass `--casebook`.

## Phone

Flutter sources are in [`mobile/`](mobile/). Application id `com.azieeliab.mialock`.

```bash
cd mobile
flutter create --org com.azieeliab --project-name mialock .
flutter pub get
flutter run
```

## Agents

Human commands print plain text. Add `--json` for the same payload as JSON. The local map keeps `/api/...` as JSON. Ask the map page for JSON with `Accept: application/json`.

Suite mesh proxy: https://mialock-download-tracker.vibelock.workers.dev/v1/mesh — default off. QNS-CD-1.0 is a hub cite. Local qnsd is [qnm-node](https://github.com/AzielEliab/qnm-node).
