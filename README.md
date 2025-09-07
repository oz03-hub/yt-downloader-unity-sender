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

5. Go into `unity_sender_listener.py` and change to paths to the respective paths you just created.

6. We will need to create an ssh-key without password to make syncs to Unity.
7. Run `ssh-keygen -t rsa -b 4096 -f ~/.ssh/ytb_rsync_key -N ""`, then `ssh-copy-id -i ~/.ssh/ytb_rsync_key unity`. This command will copy your key to Unity and add it to authorized_keys. Make sure your Angwin account is well protected because someone can use this unprotected key to get into your Unity account.

# Usage
1. Run `source yt-dlp-end/bin/activate`.
2. Open a new tmux session with `tmux new -s unity_sender`.
3. In the tmux session, run `python3 unity_sender_listener.py`. This script will listen for newly added files in the `/tmp` directory and sync them to unity. 
4. You can forget about this tmux session now, just exit with `ctrl+b` then `d`. You can occasionally check-in to see if it crashed.

Now to run the downloader.
1. Run `source yt-dlp-end/bin/activate`.
2. Open a new tmux session with `tmux new -s downloader`.
3. In the tmux session, run `python3 download_audio.py --ids ids.txt --out_dir ${YOUR TMP_PATH} --cookies ytcldemoX.txt --start X --stop Y`.
4. Exit tmux session same way, periodically check-in to make sure the cookies are not expired.

Note: I left a comment about how to detect cookie expiration, if you have practice with email service might set up an alert mechanism.

Note: Don't delete the `collected_ids.txt` it is for checkpointing downloaded ids. When you get cookie errors, run the script from same start to stop and it will retry to download the failed ones, but not the ones it already downloaded.

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
