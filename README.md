# IdleGuard

IdleGuard simulates keyboard or mouse activity at a chosen interval to help keep your computer active.

## Download

Open the repository's **Releases** page and download `IdleGuard.exe` from the latest release. GitHub also displays automatically generated source archives; those are not needed to run the application.

## Using IdleGuard

1. Enter how often IdleGuard should simulate activity, in seconds. The default is 240 seconds.
2. Select **Start** to begin or **Stop** to end the simulation.
3. To change the activity method, open **Settings > Options**.

## Options

- **Keyboard press:** Enable keyboard activity, then select **Change...** and press the key you want IdleGuard to send. Left Shift is selected by default.
- **Mouse Movement:** Enable mouse activity and choose **Nudge and return** or **Saved point and return**. Both modes return the pointer to its original position after moving.
- **Saved point:** Enter screen coordinates, or select **Use cursor position** and move the pointer to the desired location during the three-second countdown.
- **Check selected method:** Sends the selected activity once and checks whether Windows' last-input timestamp advances. The displayed system idle time refreshes every second.

Windows reports when input last occurred but does not identify which application caused it. Other keyboard or mouse input during the check may also advance the timestamp, and application or system policies can still affect timeout behavior.

Close the Options window to return to the main screen. Use **Settings > Exit** or close the main window to stop IdleGuard and exit.

## Versioning and releases

Releases use semantic version tags in `MAJOR.MINOR.PATCH` format, such as `v1.0.0`. Increase the patch number for fixes, the minor number for backward-compatible features, and the major number for breaking changes.

To publish a version, push your changes to GitHub, then create and push a tag for the commit you want to release:

```bash
git tag v1.0.0
git push origin v1.0.0
```

GitHub Actions builds the Windows executable and creates a release named with that tag. The release includes one downloadable application file, `IdleGuard.exe`. Use a new tag for each release, for example `v1.0.1` or `v1.1.0`.