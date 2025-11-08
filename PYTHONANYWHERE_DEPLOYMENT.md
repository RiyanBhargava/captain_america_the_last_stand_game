# PythonAnywhere Deployment Guide
# Captain America: The Last Stand

## Step 1: Upload Your Project to PythonAnywhere

1. **Sign up** at https://www.pythonanywhere.com/
2. **Open a Bash console** in PythonAnywhere
3. **Clone or upload your project**:
   ```bash
   git clone <your-repo-url>
   # OR upload files manually via Files tab
   ```

## Step 2: Set Up Virtual Environment

```bash
cd captain_america_ultron_shield_defense
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Step 3: Configure Database

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --noinput
```

## Step 4: Configure Web App

1. Go to **Web** tab in PythonAnywhere
2. Click **Add a new web app**
3. Choose **Manual configuration** (not Django wizard!)
4. Choose **Python 3.10**

### Configure WSGI file:
Click on the WSGI configuration file link and replace with:

```python
import os
import sys

# Add your project directory to the sys.path
path = '/home/YOUR_USERNAME/captain_america_ultron_shield_defense'
if path not in sys.path:
    sys.path.insert(0, path)

# Set environment variables
os.environ['DJANGO_SETTINGS_MODULE'] = 'shield_defense.settings'

# Activate virtual environment
activate_this = '/home/YOUR_USERNAME/captain_america_ultron_shield_defense/venv/bin/activate_this.py'
with open(activate_this) as file:
    exec(file.read(), dict(__file__=activate_this))

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

### Configure Virtual Environment:
- Set virtualenv path: `/home/YOUR_USERNAME/captain_america_ultron_shield_defense/venv`

### Configure Static Files:
- URL: `/static/`
- Directory: `/home/YOUR_USERNAME/captain_america_ultron_shield_defense/staticfiles`

## Step 5: Update Settings for Production

Edit `shield_defense/settings.py`:

```python
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Add your PythonAnywhere domain
ALLOWED_HOSTS = ['your-username.pythonanywhere.com']

# Static files
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATIC_URL = '/static/'

# Database (PythonAnywhere uses absolute paths)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': '/home/YOUR_USERNAME/captain_america_ultron_shield_defense/db.sqlite3',
    }
}
```

## Step 6: Set Up Scheduled Task for Game Loop

**THIS IS THE KEY FOR BACKGROUND PROCESSING!**

1. Go to **Tasks** tab in PythonAnywhere
2. Create a new scheduled task
3. Set it to run **every minute** (or every hour, adjust based on free tier limits)
4. Command:
   ```bash
   /home/YOUR_USERNAME/captain_america_ultron_shield_defense/venv/bin/python /home/YOUR_USERNAME/captain_america_ultron_shield_defense/manage.py process_games
   ```

**Note:** Free tier allows limited scheduled tasks. For better performance:
- **Paid tier**: Run every minute for smooth gameplay
- **Free tier**: Run every hour (games will be slower but functional)

## Step 7: Reload Web App

1. Go back to **Web** tab
2. Click **Reload** button
3. Visit your site: `https://your-username.pythonanywhere.com`

## Important Notes for PythonAnywhere:

### Free Tier Limitations:
- **No continuous background processes** (that's why we use scheduled tasks)
- **Limited CPU time** (be mindful of game loop frequency)
- **One web app only**
- **Scheduled tasks have limits** (1 per day on free tier)

### Alternative: Always-On Tasks (Paid Only):
If you upgrade to a paid account, you can run the continuous game loop:
```bash
/home/YOUR_USERNAME/captain_america_ultron_shield_defense/venv/bin/python /home/YOUR_USERNAME/captain_america_ultron_shield_defense/manage.py run_game_loop
```
This would be set up as an **Always-on task** in the Tasks tab.

## Troubleshooting:

### If games aren't updating:
1. Check the scheduled task is running (view in Tasks tab)
2. Check error logs in Web tab → Error log
3. Verify database permissions

### If static files aren't loading:
```bash
python manage.py collectstatic --noinput
```
Then reload web app.

### Database issues:
Make sure database path is absolute in settings.py

## Testing the Deployment:

1. Register a new user
2. Start a game
3. Wait for scheduled task to run (check Tasks tab for next run time)
4. Ultron should move and game should update

## Performance Tips:

- **Free tier**: Set scheduled task to run every 5-10 minutes
- **Paid tier**: Run every minute for near real-time gameplay
- Consider upgrading to paid tier (~$5/month) for better performance
- Use always-on tasks for continuous game loop (paid only)

## Your URLs:
- Main site: `https://your-username.pythonanywhere.com/`
- Admin: `https://your-username.pythonanywhere.com/admin/`
- Game: `https://your-username.pythonanywhere.com/game/`
- Leaderboard: `https://your-username.pythonanywhere.com/leaderboard/`
