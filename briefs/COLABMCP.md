# COLABMCP brief: autonomous real-Colab test loop

Tools: the `colab` MCP server (static bridge ~/colab-bridge/colab_bridge.py over googlecolab/colab-mcp)
for all notebook work, and the cua_repl / node_repl Chrome surface ONLY to approve the connection dialog.

1. Call `colab.connect`. It opens a new Colab tab in the user's Chrome (DISPLAY=:1) that shows a dialog
   asking whether to connect to a local MCP server. With the Chrome surface, find that tab and click the
   approve/connect button of THAT dialog only (the user authorised exactly this). Then call `colab.connect`
   until it returns "connected" (if it says timed out, call it again and approve the new tab).
   Never click sign-in, OAuth/permission grants for Google accounts, Save, Share, or anything else.
2. Use `colab.get_cells`; reuse the scratch notebook. Add one code cell (`colab.add_code_cell`) that:
   rm -rf /content/tritflow; git clone --depth 1 --branch <REF, default colab-v0>
   https://github.com/PenguinEino/tritflow /content/tritflow; prints `git -C /content/tritflow log -1 --format=%H`;
   executes /content/tritflow/notebook/tritflow_tr1um.ipynb with nbclient (timeout=1800, kernel python3,
   allow_errors=True, resources={'metadata':{'path':'/content/tritflow'}}); prints total seconds and, for every
   code cell, index, id, ok/ERROR and the full ANSI-stripped traceback of each error.
   Run it with `colab.run_code_cell` (takes ~5–8 min).
3. On errors: read the traceback, find the cause in the repository, and report it (do not commit or push;
   the integrator releases). If asked to iterate, you may test a fix by patching files inside /content/tritflow
   in the same cell before executing, then report the exact diff.
4. Record the result (commit hash, total time, per-cell table, full tracebacks) in docs/status/COLABMCP.md
   and in your final answer. Delete the cells you added at the end.
