# EVO-X2 BIOS Update Procedure

How to update the GMKTec EVO-X2 ([Sixunited AXB35-02 board](https://strixhalo.wiki/Hardware/Boards/Sixunited_AXB35)) BIOS and expose the GFX/UMA memory allocation menu.

## Why this matters

On BIOS **1.04 and below**, the GPU memory allocation can only be changed via a GMKTec Windows utility. On **1.05 and above**, a `GFX Configuration` menu exposes UMA allocation directly in BIOS — no Windows required for ongoing changes. Strix Halo's unified memory architecture lets you carve out up to ~112 GB of the 128 GB pool for the integrated GPU; the [strixhalo wiki community](https://strixhalo.wiki/) consensus sweet spot is **96 GB UMA / 32 GB OS** (GPU can still spill into system RAM via GTT, so you don't lose capacity).

## Hardware reference

- Box: GMKTec EVO-X2 ([product page](https://www.gmktec.com/products/evo-x2-ai-mini-pc))
- Board: Sixunited AXB35-02 ([wiki](https://strixhalo.wiki/Hardware/Boards/Sixunited_AXB35))
- SoC: AMD Ryzen AI MAX+ 395 ([AMD page](https://www.amd.com/en/products/processors/laptop/ryzen/ai-max.html))
- Firmware list & downloads: [strixhalo wiki firmware page](https://strixhalo.wiki/Hardware/Boards/Sixunited_AXB35/Firmware)
- Recovery (if you brick it): [Restoring Corrupted BIOS guide](https://strixhalo.wiki/Guides/Sixunited_AXB35/Restoring_Corrupted_BIOS) — requires CH341A programmer + WSON8 8×6mm clip; this board has **no dual BIOS or flashback button**

## What you need

| Item | Source |
|---|---|
| BIOS pack `AXB35-02_GMK_SW1.05_20250729.zip` (~25 MB) | [strixhalo wiki firmware page](https://strixhalo.wiki/Hardware/Boards/Sixunited_AXB35/Firmware) |
| Hiren's BootCD PE ISO (~3.3 GB) | [hirensbootcd.org](https://www.hirensbootcd.org/) |
| Two USB sticks (≥8 GB for Hiren's, ≥1 GB for BIOS pack) | — |
| A Windows machine to flash Hiren's via [Rufus](https://rufus.ie/) (recommended) — or [balenaEtcher](https://etcher.balena.io/) on Mac/Linux if no Windows nearby | — |

> **Note on Etcher vs Rufus:** Etcher on macOS writes raw and macOS sometimes can't enumerate the resulting USB — that's cosmetic, the USB still boots fine on UEFI hardware. Rufus on Windows produces a layout that's visible everywhere. Either works for the EVO-X2.

## The procedure (Method 1: WinPE)

This is what actually worked. The strixhalo wiki [explicitly lists Hiren's as a valid flash environment](https://strixhalo.wiki/Hardware/Boards/Sixunited_AXB35/Firmware) since it's a full WinPE.

1. **Flash Hiren's BootCD PE to a USB stick** (≥8 GB) with Rufus or Etcher. Standard ISO write, nothing special.
2. **Extract the BIOS pack onto a second USB stick** formatted FAT32. After extraction the layout will be:
   ```
   AXB35-02_GMK_SW1.05_shutdownCommand_20250729/
     ├── Afu_WinFlash/        ← Windows AFU utility + .bat wrapper
     ├── EXE_WinFlash/        ← Single-exe wrapper (easiest)
     ├── ROM/AXB3502105.bin   ← The actual BIOS image (32 MB)
     ├── Shell/               ← UEFI Shell flash (Method 3, alternative)
     └── AMD_Flash_BIOS_SOP.docx
   ```
3. **Boot the EVO-X2 from the Hiren's USB**:
   - Plug both USBs into rear ports (front ports share a polyfuse and may starve the keyboard)
   - Power on → tap `F7` repeatedly → boot menu
   - Pick `UEFI: <Hiren's USB>`
   - WinPE desktop loads in ~30 s
4. **Run the BIOS flasher**:
   - Open File Explorer → navigate to the BIOS pack USB → `EXE_WinFlash/`
   - Double-click `AXB3502105.exe` → confirm UAC
   - Progress bars run. **Do NOT touch keyboard/mouse. Do NOT lose power.**
   - System auto-shuts-down on completion (the bundled command uses `/Shutdown` — confirmed in [`Afu_WinFlash/AXB35-02_BIOS_WinFlash.bat`](https://strixhalo.wiki/Hardware/Boards/Sixunited_AXB35/Firmware))
5. **Power back on** → tap `Del` → enter BIOS
6. **Verify** Main tab shows `EVO-X2 1.05`
7. **Set GFX UMA**: Advanced → `GFX Configuration` → pick allocation (96 GB recommended)
8. **F10** → Save & Exit → boot Ubuntu

### Verify from Ubuntu

```bash
sudo dmidecode -s bios-version          # → EVO-X2 1.05
lspci -k | grep -i amdgpu               # → "Kernel driver in use: amdgpu"
rocm-smi --showmeminfo vram             # → ~103079215104 bytes (= 96 GiB)
```

## Alternative methods (not used, but documented)

The BIOS pack supports three flash paths per [GMKTec's SOP](https://strixhalo.wiki/Hardware/Boards/Sixunited_AXB35/Firmware) (translated from Chinese):

- **Method 1 — Hiren's WinPE** (this doc): boot WinPE, run `EXE_WinFlash/AXB3502105.exe`
- **Method 2 — Stock Windows**: install Windows on the box, run the same .exe. Painful on Strix Halo because Win11 25H2's inbox storage drivers don't see the NVMe controller until the GMKTec/AMD chipset pack is loaded — see "Failed approaches" below
- **Method 3 — UEFI Shell**: boot any UEFI Shell from USB, `cd` into `Shell/`, run `AXB35-02_BIOS_UpdateEFI.nsh`. Cleanest if the EVO-X2 BIOS exposed a built-in UEFI Shell (it doesn't out of the box — would need a Shell.efi placed at `/EFI/BOOT/BOOTX64.EFI` on the USB)

The `/Shutdown` argument can be replaced with `/REBOOT` if you prefer auto-reboot instead of auto-shutdown — see the AFU help section in `Afu_WinFlash/readme.txt`.

## EC firmware

EC firmware is **independent** and not bundled with the 1.05 BIOS pack. The flash command does NOT include `/E`, `/EC`, or `/ECUF` flags, so the EC stays at whatever it was before. As of writing, jarvis was on EC `1.01.03` before and after the BIOS flash — no change. The wiki's "EC first, BIOS last" rule only applies when you have both updates pending.

## Failed approaches (so future-you doesn't repeat them)

1. **Boot GMKTec's "Win 11 Pro without LLM" ISO directly** — it's a raw UDF WinPE deployment image (`partition-scheme: none`). UEFI won't boot it from USB without manually building a proper partition table around it. We tried Etcher → flashed cleanly → not in `F7` boot menu → dead end
2. **Stock Win11 25H2 install ISO** ([microsoft.com](https://www.microsoft.com/software-download/windows11)) — boots cleanly, but Setup hits "no drives found" because Strix Halo's storage controller isn't in Microsoft's inbox driver set. The GMKTec [driver pack `EVO-X2_Win11_24H2_Driver_list_V007.zip`](https://www.gmktec.com/pages/drivers-and-software) (1.65 GB on Google Drive) has the needed chipset drivers — but the file consistently throws Google's per-file download quota error. The "Make a copy" workaround failed too. Extracting the AMD chipset INFs from the GMKtec WinPE's `Install.wim` with `wimlib-imagex` and loading them via "Load driver" produced "no compatible drivers found" — the deployed-Windows form of those INFs doesn't validate during Setup
3. **AMD chipset drivers from [amd.com](https://www.amd.com/en/support)** — AMD's per-model page for Ryzen AI MAX+ 395 lists only Adrenalin (GPU) and the Auto-Detect tool. No standalone chipset driver for mobile Strix Halo. AMD's own note: *"AMD recommends OEM-provided drivers"* — confirming the GMKTec pack is the canonical source

Net: the WinPE path (Hiren's) skips all of this. Don't bother with Win11 install just to flash BIOS.

## Notes

- Pi-hole may block Microsoft's Win11 download validation and Google Drive download endpoints. If a download silently fails, suspect DNS — temporarily switch Mac/Wi-Fi DNS to `1.1.1.1` + `8.8.8.8`:
  ```bash
  sudo networksetup -setdnsservers Wi-Fi 1.1.1.1 8.8.8.8
  sudo dscacheutil -flushcache && sudo killall -HUP mDNSResponder
  # Restore later:
  sudo networksetup -setdnsservers Wi-Fi Empty
  ```
- macOS Disk Utility error `-69825` (`kIOReturnDeviceError`) on USB erase often signals end-of-life flash chip wear, especially after several rapid flash cycles. If a USB starts throwing it, retire it.
- After flashing, BIOS may reset Secure Boot / Fast Boot / Boot order to defaults — re-verify on first boot.
