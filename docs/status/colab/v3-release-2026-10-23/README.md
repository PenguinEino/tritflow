# v3 release check, fresh Colab VMs (CLI), 2026-10-23

Source: branch notebook-v3, commit 3fccb46 (notebooks pin bbf252f). No overlay or upload; the notebooks fetched their pinned commit from GitHub.

- English: rc=0, 372 s including setup.
- Japanese: rc=0, 447 s including setup.

Both: KLayout 0.30.6, ngspice-42; DRC 0 / LVS match / SPICE pass for the first circuit and dot4; the edited-HDL full flow passes (max error 0.042 V).
