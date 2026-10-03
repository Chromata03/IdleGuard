# IdleGuard

IdleGuard helps prevent unwanted idle timeouts or logouts by simulating your selected keyboard or mouse activity.

## Features

- Adjustable interval input in seconds
- Start and stop controls
- Settings menu with Options and Exit
- Configurable keyboard key (defaults to Left Shift) and mouse controls for nudging or moving to a saved screen point; both restore the cursor afterward
- Windows idle-time display and a two-second check for whether selected activity advances the last-input timestamp
- Dark-themed Windows UI
- Custom application icon
- EXE build support with PyInstaller

Windows exposes the time since the last input, but does not identify which application caused it. The inactivity check reports whether the last-input timestamp advanced during the selected-method test; other input arriving during that test can also advance it.

## Project icon

The app is configured to use the selected icon: `keystroke2.ico`.

## Requirements

- Python 3.11+
- Windows 10/11
- Tkinter
- PyAutoGUI
- PyInstaller

## Set up the virtual environment

From the project folder:

```bat
cd /d "%USERPROFILE%\source\repos\Keystrokes"
.\.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Run the app locally

```bat
cd /d "%USERPROFILE%\source\repos\Keystrokes"
.\.venv\Scripts\activate
python app.py
```

## Build the EXE

Build the Windows executable directly from the application entry point:

```bat
cd /d "%USERPROFILE%\source\repos\Keystrokes"
.\.venv\Scripts\activate
python -m PyInstaller --noconfirm --clean --name "IdleGuard" --icon "keystroke2.ico" app.py
```

The output will be created in the `dist\` folder.

## Build and publish with a publisher name

Before publishing, define the application identity that will appear to users on Windows and in the digital signature.

```bat
set "APP_NAME=IdleGuard"
set "PUBLISHER_NAME=Your Company Name"
set "PUBLISHER_URL=https://your-company.example"
```

Use these values when building the package or installer:

```bat
cd /d "%USERPROFILE%\source\repos\Keystrokes"
.\.venv\Scripts\activate
python -m PyInstaller --noconfirm --clean --name "%APP_NAME%" --icon "keystroke2.ico" app.py
```

If you distribute the app via an installer, keep the publisher name consistent with the certificate subject and your application metadata.

## Code-sign the EXE (Authenticode signature)

To make sure the file is clearly your program, sign it with an Authenticode code-signing certificate. The publisher name should match the certificate subject or the company name used in the certificate.

### Option 1: Use a certificate from a trusted certificate authority

```bat
cd /d "%USERPROFILE%\source\repos\Keystrokes"
.\.venv\Scripts\activate
signtool sign /n "%PUBLISHER_NAME%" /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 "dist\%APP_NAME%.exe"
```

### Option 2: Use a certificate file

```bat
cd /d "%USERPROFILE%\source\repos\Keystrokes"
.\.venv\Scripts\activate
signtool sign /f "C:\Path\To\Your\Certificate.pfx" /p "YOUR_CERT_PASSWORD" /n "%PUBLISHER_NAME%" /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 "dist\%APP_NAME%.exe"
```

> Store `.pfx` files and passwords securely. Do not commit them to source control or share them in public documentation.

### Option 3: Create a temporary self-signed test certificate

```powershell
New-SelfSignedCertificate -CertStoreLocation Cert:\CurrentUser\My -Type CodeSigningCert -Subject "CN=Your Company Name"
```

Then export the certificate to a `.pfx` file and sign the EXE with the same `signtool` command above.

> A self-signed certificate is okay for testing, but users may see a trust warning unless the certificate is installed on their machine or a trusted certificate authority signs it.

## Optional: package for distribution

To create a more polished published build, wrap the signed executable in an installer such as Inno Setup or WiX. Set the installer publisher name to the same value as `PUBLISHER_NAME` so the Windows installation experience matches the signed app identity.

## Notes

- Run with appropriate Windows permissions.
- Use responsibly to avoid unintended keyboard or mouse activity.
- If you want to redistribute the app, use a real code-signing certificate from a trusted certificate authority.
- Keep certificates, passwords, and private keys out of the repository and out of public documentation.