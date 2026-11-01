# Setup guide

Time: about 20 minutes the first time. You need a Mac or Linux computer, a USB-C cable that carries data, and a reMarkable 2.

> Tested on reMarkable 2, firmware **3.29.1.0**. Other versions may need changes to the mod.

## 1. Connect over SSH

1. On the tablet, open **Settings → Help → Copyrights and licenses**. The SSH password and the tablet's IP addresses are listed at the bottom.
2. Plug the tablet into your computer and keep it awake. Over USB it is always at `10.11.99.1`.
3. Set up key-based login so scripts can connect without the password:

   ```bash
   ssh-keygen -t ed25519 -f ~/.ssh/remarkable
   ssh-copy-id -o StrictHostKeyChecking=accept-new -i ~/.ssh/remarkable.pub root@10.11.99.1
   ```

   On macOS, if you gave the key a passphrase, store it in Keychain once with `ssh-add --apple-use-keychain ~/.ssh/remarkable`.

4. Optional: add this to `~/.ssh/config` so `ssh remarkable` works:

   ```
   Host remarkable
     HostName 10.11.99.1
     User root
     IdentityFile ~/.ssh/remarkable
     IdentitiesOnly yes
   ```

**If the connection hangs:** the tablet is asleep, or your computer lost its address on the USB link. Run `ifconfig | grep 10.11.99` — you should see `10.11.99.2`. If not, unplug and replug with the tablet awake.

## 2. Back up the tablet

```bash
mkdir -p ~/remarkable-backups
ssh root@10.11.99.1 'tar -C /home/root/.local/share/remarkable -cf - xochitl' > ~/remarkable-backups/xochitl-$(date +%F).tar
```

This copies every notebook and book on the tablet. Keep it somewhere safe.

## 3. Install xovi

Follow the official instructions in [asivery/rm-xovi-extensions](https://github.com/asivery/rm-xovi-extensions). For the reMarkable 2, use the **arm32** release. In short:

```bash
scp xovi-arm32.tar.gz root@10.11.99.1:/tmp/xovi.tar.gz
ssh root@10.11.99.1 'tar -xzf /tmp/xovi.tar.gz -C /home/root'
```

Then build the lookup table for your firmware:

```bash
ssh root@10.11.99.1 '/home/root/xovi/rebuild_hashtable'
```

> **Important:** this script stops the tablet's interface and does **not** restart it. When it prints "Hashtable rebuilt", run
> `ssh root@10.11.99.1 'systemctl start xochitl'` — otherwise the screen stays frozen.

## 4. Create the Commonplace notebook

On the tablet, create a **folder** named **Commonplace**, and inside it a **notebook** named **Commonplace 2026** (this year; any template). Notecards are added to the end of it.

**One notebook per year.** Each January, create the next one (*Commonplace 2027*) in the same folder — that's the only yearly chore. If you've set up the Mac sync, it switches the mod to the new notebook automatically and reminds you on New Year's if it doesn't exist yet; until then, notecards keep going into the most recent earlier year's. Without the sync, run `install.sh` again after creating it.

Prefer a single notebook? Name it anything and pass it to the installer: `NOTEBOOK_NAME="My Quotes" ./scripts/install.sh …`

## 5. Install the mod

From this repository:

```bash
./scripts/install.sh root@10.11.99.1
```

The script:

1. checks that xovi and its lookup table are installed,
2. finds this year's Commonplace notebook and saves its ID in `/home/root/commonplace/config.json`,
3. copies `mod/commonplace.qmd` to the tablet,
4. starts xovi (the screen restarts once).

## 6. Try it

1. Open any book (EPUB or PDF) and tap **❝** in the toolbar. It turns black and switches to the capture tool.
2. Drag diagonally from the first word to the last (this also highlights it), or draw a loop around it.
3. Tap **Save** or **Save + note**.

## After a firmware update

xovi does not survive a reboot, and mods are tied to the firmware version. After updating:

1. Rebuild the lookup table (step 3, including restarting the interface).
2. Start xovi: `ssh root@10.11.99.1 '/home/root/xovi/start'`.
3. Test one capture. If the ❝ button is missing or nothing happens, check the log:

   ```bash
   ssh root@10.11.99.1 'journalctl -u xochitl --since "-10min" | grep -E "QC |qmldiff|TypeError"'
   ```

Sleep and closing the cover are fine. Each time the tablet fully restarts (power off, flat battery, crash, firmware update), start xovi again with `/home/root/xovi/start`.

## Uninstall

```bash
./scripts/uninstall.sh root@10.11.99.1
```

This removes the mod and restarts the interface. Your cards and the files in `/home/root/commonplace/` are kept. Rebooting also returns the tablet to stock.

## Troubleshooting

| What you see | What to do |
|---|---|
| No ❝ button | xovi isn't running (reboot stops it). Run `/home/root/xovi/start`. |
| "Commonplace notebook not set up" | Run `install.sh` again after creating the notebook. |
| "Couldn't make the notecard" | The notebook took too long to open. Try again; if it repeats, send the log lines from the command above in an issue. |
| Screen frozen after `rebuild_hashtable` | Run `systemctl start xochitl` on the tablet. |
