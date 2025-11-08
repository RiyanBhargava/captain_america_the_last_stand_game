# 🛡️ Captain America: The Last Stand

A Django-based real-time strategy game where you play as Captain America defending hostages from Ultron escaping through a 15×15 maze.

## 🎮 Game Features

- **Real-time Gameplay**: WebSocket-powered real-time game experience
- **AI Pathfinding**: Ultron uses A* algorithm for intelligent movement
- **Strategic Shield Placement**: Three types of shields with different effects
- **Google Authentication**: Sign in with Google or manual registration
- **Leaderboard System**: Track high scores and player statistics
- **Captain America Theme**: Marvel-inspired design and graphics

## 🛡️ Shield Types

1. **Blue Shield (Full Block)**: Completely blocks Ultron's path
2. **Yellow Shield (Delay)**: Increases hostage timer by 2 seconds when passed through
3. **Red Shield (Pause)**: Pauses Ultron for 2 seconds when passed through

## 🎯 Game Rules

- Ultron starts at one edge and tries to reach the opposite edge
- Place shields every 4 seconds to block or hinder Ultron
- Ultron moves at 0.8 seconds per tile
- Win by preventing Ultron from reaching the exit for 40+ seconds
- Lose if Ultron reaches the exit before the timer

## 🚀 Setup Instructions

### Prerequisites
- Python 3.8+
- Redis (for WebSocket channels)

### Installation

1. **Clone the repository**
   ```bash
   cd "c:\Users\riyan\OneDrive\Desktop\IEI BPDC\captain_america_ultron_shield_defense"
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   - Copy `.env.example` to `.env`
   - Add your Google OAuth credentials:
     ```
     GOOGLE_OAUTH2_CLIENT_ID=your-google-client-id
     GOOGLE_OAUTH2_CLIENT_SECRET=your-google-client-secret
     ```

4. **Run migrations**
   ```bash
   python manage.py migrate
   ```

5. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

6. **Start Redis server**
   - Install and start Redis on your system
   - Default connection: `redis://localhost:6379/0`

7. **Run the development server**
   ```bash
   python manage.py runserver
   ```

8. **Access the game**
   - Open http://127.0.0.1:8000 in your browser
   - Sign up or login to start playing

## 🔧 Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Google+ API
4. Create OAuth 2.0 credentials
5. Add authorized origins:
   - `http://localhost:8000`
   - `http://127.0.0.1:8000`
6. Add authorized redirect URIs:
   - `http://localhost:8000/auth/google-auth/`
   - `http://127.0.0.1:8000/auth/google-auth/`

## 🎨 Project Structure

```
captain_america_ultron_shield_defense/
├── authentication/          # User authentication app
├── game/                   # Main game logic app
├── static/                 # Static files (CSS, JS, images)
├── templates/              # HTML templates
├── shield_defense/         # Django project settings
├── manage.py
├── requirements.txt
└── README.md
```

## 🎯 API Endpoints

- `/auth/login/` - Login page
- `/auth/register/` - Registration page
- `/auth/google-auth/` - Google OAuth endpoint
- `/game/` - Main game interface
- `/game/leaderboard/` - Leaderboard page
- `/api/game/start/` - Start new game
- `/api/game/place-shield/` - Place shield
- `/ws/game/<id>/` - WebSocket game connection

## 🏆 Scoring System

- **Win**: Score = Final hostage timer × 10
- **Lose**: Score = Time survived × 5
- Points are added to total score and tracked in leaderboard

## 🛠️ Technologies Used

- **Backend**: Django, Django Channels, Redis
- **Frontend**: HTML5, CSS3, JavaScript, WebSockets
- **Database**: SQLite (development), PostgreSQL (production ready)
- **Authentication**: Google OAuth 2.0, Django Auth
- **Real-time**: WebSockets with Redis backing store
- **AI**: A* pathfinding algorithm

## 🎮 How to Play

1. **Sign In**: Use Google or create a manual account
2. **Start Game**: Click "Start New Game" button
3. **Select Shield**: Choose from blue, yellow, or red shields
4. **Place Shields**: Click on grid tiles to place shields (4-second cooldown)
5. **Watch Ultron**: Ultron moves every 0.8 seconds using pathfinding
6. **Win Condition**: Prevent Ultron from reaching exit for 40+ seconds
7. **Strategy**: Use blue shields to block, yellow for extra time, red to pause

## 🐛 Troubleshooting

- **WebSocket Connection Issues**: Ensure Redis is running
- **Static Files Not Loading**: Run `python manage.py collectstatic`
- **Google Auth Not Working**: Check OAuth credentials and redirect URIs
- **Game Not Starting**: Check browser console for JavaScript errors

## 📱 Browser Compatibility

- Chrome 80+
- Firefox 75+
- Safari 13+
- Edge 80+

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📝 License

This project is for educational purposes. Marvel characters and themes are property of Marvel Entertainment.

## 🎯 Future Enhancements

- [ ] Multiplayer support
- [ ] Mobile responsive design
- [ ] Sound effects and background music
- [ ] Multiple difficulty levels
- [ ] Power-ups and special abilities
- [ ] Tournament mode
- [ ] Social features (friend challenges)

## 👨‍💻 Developer

Built with ❤️ for the IEI BPDC project using Django and modern web technologies.

---

**Ready to defend the hostages? Assemble and play! 🛡️**
