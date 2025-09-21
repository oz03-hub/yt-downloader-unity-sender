# Installation
0. Ensure you have access to Angwin and Unity clusters!
1. Establish an ssh connection from Angwin to Unity. You should either copy your existing ssh keys from local or create new one. Either way just ensure you can ssh into Unity from Angwin. This will be important later on.
1. Create virtual environment `python3 -m venv yt-dlp-env`
2. ACtivate `source yt-dlp-env/bin/activate`
3. Install dependencies `pip install -r requirements.txt`
4. Periodically run `pip install -U yt-dlp` so you are on the latest version at all times.

Please read the following notes as part of installation and set up too, very important.

Note: If you are on Angwin, run `ssh wells` while connected to the Angwin cluster. The Wells machine is the machine we primarily use for our workload. On Wells, create a directory under `/tmp`, notice absolute path. We will refer to this path as TMP_PATH.

Note: On Unity you should create a `scratch space`, which can store very large collections up to terabytes. Connect to Unity cluster, and read [this document](https://docs.unity.rc.umass.edu/documentation/managing-files/hpc-workspace/#send-an-email-reminder-before-workspace-expiration). You can run `ws_allocate -m yourusername@umass.edu -r 3 yt-lang-detect 30`. This will give you a 30 days space, that you can extend 5 times, so your space will actually 6 months if you don't forget to extend it! You can extend by `ws_extend yt-lang-detect 30`. You can also create a space that the whole PI group can access, or share with individual users with `ws_share share yt-lang-detect username2_umass_edu`. Use `ws_list -v` to view your spaces. After you create your scratch space note down the path. We will refer to this path as SCRATCH_PATH.

5. Go into `downloader_sender.py` and change to paths to the respective paths you just created.

6. We will need to create an ssh-key without password to make syncs to Unity.
7. Run `ssh-keygen -t rsa -b 4096 -f ~/.ssh/ytb_rsync_key -N ""`, then `ssh-copy-id -i ~/.ssh/ytb_rsync_key unity`. This command will copy your key to Unity and add it to authorized_keys. Make sure your Angwin account is well protected because someone can use this unprotected key to get into your Unity account.

# Usage (New Version)
1. Environment Setup

Activate your virtual environment:

`source yt-dlp-end/bin/activate`

2. Run the Combined Downloader + Sender

Open a new tmux session:

`tmux new -s downloader_sender`


Inside the tmux session, run the new script:

`python3 downloader_sender.py --ids ids.txt --out_dir /tmp/rec-downloads --cookies ytcldemoX.txt --start X --stop Y`


Replace:

ids.txt with your list of YouTube video IDs.

/tmp/rec-downloads with the directory for temporary .wav files (they will be auto-deleted after sending).

ytcldemoX.txt with your cookies file.

X and Y with the range of IDs you want to process.

Detach from tmux with ctrl+b then d.

The script will:

Download .wav files from YouTube.

Immediately rsync them to the Unity destination.

Delete the local copies.

Update collected_ids.txt as a checkpoint to avoid re-downloading already-processed IDs.

3. Monitoring

Periodically reattach with:

`tmux attach -t downloader_sender`


If you see repeated failures with messages like:

[fatal] 50 consecutive errors — aborting (likely bad cookies).


then your cookies have expired. Refresh them and re-run the same command with the same --start and --stop values. The script will skip IDs already present in collected_ids.txt and retry only the failed ones.

## Notes

Do not delete collected_ids.txt. It’s your checkpoint file.

If you refresh cookies, rerun the same command—it won’t redo successful downloads.

You only need one tmux session now, since the script downloads and sends automatically.

# Replacing cookies
Before:
1. Open a google window non-incognito. Yes, we will need google chrome to use its extensions.
2. Install get-cookies-local extension. I use this one: https://chromewebstore.google.com/detail/cclelndahbckbenkjhflpdbgdldlbecc?utm_source=item-share-cb.
3. Click on manage extensions on google settings and allow incognito for the cookies extension you just downloaded and pin to tool bar.


1. Still in incognite mode. Create a throw-away gmail account to be used in youtube. Enter address and password in this file below.
2. Open an incognito tab and log in to your account on youtube. Skip any MFA steps etc offered by google.
3. While logged in head to youtube.com/robots.txt.
4. In robots.txt click on the cookie extension and copy to clipboard, then paste it into a txt in this repo. After you have changed the cookies make sure the argument for the downloader is correct when you run it again.

# Accounts
## Google
1. ytcldemo1@gmail.com, ytcl2000
2. ytcl2demo2@gmail.com, ytcl2000
3. ytcl03648@gmail.com, ytcl2000
4. ytcl756@gmail.com, ytcl2000
