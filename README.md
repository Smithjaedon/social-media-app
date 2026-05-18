# Social Media App

A modern social media application built with **FastAPI**, **Tortoise ORM**, and **PostgreSQL**. Features real-time WebSocket support and JWT-based authentication with Redis token blacklisting.

---

## Core Features

### User Management ✅

- [x] User registration with username, email, password
- [x] Display name management
- [x] Bio management (update own or others' bios)
- [x] Password hashing and secure authentication
- [x] JWT access tokens (30 min expiry)
- [x] JWT refresh tokens (7 day expiry)
- [x] Token blacklist via Redis for logout support
- [x] Cookie-based authentication with HTTP-only, secure cookies
- [x] Disable user accounts

### Posts ✅

- [x] Create posts with title and content
- [x] Get all posts with pagination
- [x] Get posts by username
- [x] Get posts by user ID
- [x] View individual post details
- [x] Delete posts (owner-only)
- [x] Feed endpoint showing posts sorted by likes
- [x] Following feed - see posts from followed users only
- [x] Like/unlike posts
- [x] Post statistics: like count and comment count

### Followers ✅

- [x] Follow users
- [x] Unfollow users
- [x] View your follows list
- [x] Get follower/following counts on profiles
- [x] Recommended users (randomized suggestions)

### Comments ✅

- [x] Create comments on posts
- [x] View all comments on a post
- [x] View user's comment history
- [x] Like/unlike comments
- [x] Delete comments
- [x] Comment statistics: like count

### Authentication & Authorization ✅

- [x] Secure JWT token authentication
- [x] Refresh token rotation
- [x] Token blacklist on logout (Redis-based)
- [x] Username/password verification
- [x] Role-based access control (owner-only delete)

---

## Architecture Overview

```
┌─────────────────┐
│   Frontend      │  React/Vue/Svelte app (TBD)
└────────┬────────┘
         │ HTTPS
         ▼
┌─────────────────┐
│    API Routes   │  FastAPI endpoints
├─────────────────┤
│  /users         │  User management
│  /posts         │  Post CRUD operations
│  /follows       │  Follow/unfollow logic
│  /comments      │  Comment system
│  /auth          │  Login, register, logout
│  /feed          │  Feed endpoints
│  /bio           │  Bio management
└────────┬────────┘
         │ HTTP/WS
         ▼
┌─────────────────┐
│   Database      │  PostgreSQL (Tortoise ORM)
├─────────────────┤
│    Redis        │  Token blacklisting, sessions
└─────────────────┘
```

---

## Project Structure

```
social-media-app/
├── app/
│   ├── routers/       # API route handlers
│   │   ├── auth.py    # Authentication logic (JWT + Redis)
│   │   ├── bio.py     # Bio management endpoints
│   │   ├── users.py   # User CRUD and recommendations
│   │   ├── posts.py   # Post CRUD and feed endpoints
│   │   ├── follows.py # Follow/unfollow logic
│   │   └── comments.py# Comment system
│   ├── models.py      # Tortoise ORM database models
│   ├── schemas.py     # Pydantic request/response schemas
│   ├── auth.py        # JWT authentication with token management
│   ├── middleware.py  # Request/response middleware
│   ├── database.py    # Tortoise ORM configuration
│   └── ws/            # WebSocket handlers (ConnectionManager)
├── scripts/           # Data generation scripts for seeding
│   ├── generate_user.py
│   ├── generate_posts.py
│   ├── generate_comments.py
│   ├── generate_likes.py
│   ├── generate_follows.py
│   └── add_bio.py
├── .env               # Environment variables
├── pyproject.toml     # Project dependencies and configuration
├── docker-compose.yml # Docker setup for all services
└── README.md          # This file
```

---

## Database Models

### User Model

- `id` - UUID (primary key)
- `display_name` - Optional display name
- `username` - Unique username
- `bio` - Optional biography text
- `email` - Email address
- `hashed_password` - Securely hashed password
- `disabled` - Account status

### Post Model

- `id` - UUID (primary key)
- `title` - Post title
- `content` - Post content
- `created_at` - Creation timestamp
- `updated_at` - Last update timestamp
- `author` - Foreign key to User
- Relations: comments, likes

### Comment Model

- `id` - UUID (primary key)
- `content` - Comment text
- `created_at` - Creation timestamp
- `post` - Foreign key to Post
- `author` - Foreign key to User
- Relations: replies, likes

### Reply Model (Comment Threads)

- `id` - UUID (primary key)
- `content` - Reply text
- `created_at` - Creation timestamp
- `comment` - Parent comment foreign key
- `author` - Foreign key to User
- `parent_reply` - Self-referential for nested replies
- Relations: child replies, likes

### Like Model

- `id` - Auto-incrementing integer (primary key)
- Links to User and optionally Post or Comment
- Prevents duplicate likes per user

### Follow Model

- `id` - UUID (primary key)
- `follower` - Foreign key to User
- `following` - Foreign key to User
- Unique constraint on follower/following pair

---

## Authentication Flow

1. **Registration**: POST `/auth/register` with username, email, display name, password
2. **Login**: POST `/auth/token` with credentials → receives cookies (access_token + refresh_token)
3. **Access Token**: 30-minute JWT stored in HTTP-only secure cookie
4. **Refresh Token**: UUID rotated on each use for long-lived sessions (7 days)
5. **Logout**: POST `/auth/logout` → adds token to Redis blacklist
6. **Refresh**: POST `/auth/token/refresh` → rotates refresh token, issues new access token

---

## Quick Start

### Prerequisites

- Python 3.12+
- PostgreSQL 16+
- Redis 7+

### Installation with Docker (Recommended)

```bash
# Copy environment file and configure
cp .env.example .env
# Edit .env with your settings

# Build and run all services
docker compose up --build
```

### Manual Installation

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
uv pip install -e .

# Set up PostgreSQL and Redis (configure in .env)

# Run database migrations
uv run python -c "from app.database import create_db_and_tables; create_db_and_tables()"

# Run the development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Generate Test Data (Optional)

After starting PostgreSQL and running migrations, use these scripts to seed your database:

```bash
# Generate users
uv run scripts/generate_user.py

# Generate posts
uv run scripts/generate_posts.py

# Generate comments
uv run scripts/generate_comments.py

# Generate likes
uv run scripts/generate_likes.py

# Generate follow relationships
uv run scripts/generate_follows.py

# Add bios to users
uv run scripts/add_bio.py
```

---

## API Endpoints Reference

### Authentication

| Method | Endpoint              | Description          |
| ------ | --------------------- | -------------------- |
| POST   | `/auth/register`      | Register new user    |
| POST   | `/auth/token`         | Login                |
| POST   | `/auth/token/refresh` | Refresh access token |
| POST   | `/auth/logout`        | Logout               |
| GET    | `/auth/users/me/`     | Get current user     |

### Users

| Method | Endpoint                             | Description           |
| ------ | ------------------------------------ | --------------------- |
| GET    | `/users`                             | List all users        |
| GET    | `/users/by-username/{username}`      | Get user by username  |
| GET    | `/users/by-id/{user_id}`             | Get user by ID        |
| PATCH  | `/users/display-name/{display_name}` | Update display name   |
| GET    | `/users/recommend`                   | Get recommended users |

### Bio

| Method | Endpoint                      | Description               |
| ------ | ----------------------------- | ------------------------- |
| GET    | `/bio`                        | Get current user's bio    |
| PATCH  | `/bio`                        | Update current user's bio |
| GET    | `/bio/by-username/{username}` | Get another user's bio    |
| PATCH  | `/bio/by-username/{username}` | Update another user's bio |

### Posts

| Method | Endpoint                        | Description                   |
| ------ | ------------------------------- | ----------------------------- |
| GET    | `/posts`                        | List all posts                |
| GET    | `/posts/by-username/{username}` | Get posts by username         |
| GET    | `/posts/by-user-id/{user_id}`   | Get posts by user ID          |
| POST   | `/posts`                        | Create new post               |
| GET    | `/post/{id}`                    | Get single post details       |
| DELETE | `/posts/{post_id}`              | Delete a post (owner-only)    |
| GET    | `/feed`                         | Get feed of popular posts     |
| GET    | `/following`                    | Get posts from followed users |

### Comments

| Method | Endpoint                    | Description             |
| ------ | --------------------------- | ----------------------- |
| POST   | `/posts/{post_id}/comments` | Add comment to post     |
| GET    | `/posts/{id}/comments`      | Get comments on a post  |
| GET    | `/comments`                 | Get all user's comments |
| POST   | `/comments/{id}/like`       | Like a comment          |
| DELETE | `/comments/{id}/unlike`     | Unlike a comment        |
| DELETE | `/comment/{id}`             | Delete a comment        |

### Follows

| Method | Endpoint              | Description              |
| ------ | --------------------- | ------------------------ |
| POST   | `/user/{id}/follow`   | Follow a user            |
| DELETE | `/user/{id}/unfollow` | Unfollow a user          |
| GET    | `/follows`            | Get your follows list    |
| GET    | `/following`          | Get posts from following |

---

## Environment Variables

Create a `.env` file:

```env
SECRET_KEY=your-secure-secret-key-here
DATABASE_URL=tortoise://postgres://user:password@localhost:5432/social_media
REDIS_URL=redis://localhost:6379

# PostgreSQL configuration
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=password
DB_NAME=social_media
```

---

## Technology Stack

### Backend

- **FastAPI** - Modern async web framework
- **Tortoise ORM** - Async SQLAlchemy-like ORM
- **Pydantic** - Data validation and settings management
- **JWT** - JSON Web Token authentication
- **pwdlib** - Password hashing (Argon2)
- **Redis** - Session/token management
- **FastAPI Pagination** - Automatic pagination

### Database & Caching

- **PostgreSQL** - Primary database
- **Redis** - Token blacklisting, refresh tokens

### Development Tools

- **uvicorn** - ASGI server
- **docker-compose** - Container orchestration
- **Ruff** - Python linter and formatter
- **pytest** - Testing framework

---

## Configuration

Generate Pydantic models from database schema:

```bash
# Tortoise ORM will auto-generate schemas on startup
# Set in app/database.py with generate_schemas=True
```

---

## API Documentation

Once running, access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## Future Enhancements

### Planned Features

- [ ] End-to-end encryption for private messages
- [ ] Real-time WebSocket notifications (likes, comments)
- [ ] Comment replies/threaded discussions
- [ ] Hashtags and mentions
- [ ] Rich media posts (images, videos, GIFs)
- [ ] Content moderation API
- [ ] User reporting system
- [ ] Automated spam detection
- [ ] NSFW content filtering
- [ ] Redis caching layer for performance
- [ ] Image CDN integration
- [ ] Postman collection
- [ ] Docker Compose optimization
- [ ] Unit test suite
- [ ] API versioning strategy

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

MIT License - see LICENSE file for details

---

## Acknowledgments

- **Tortoise ORM** for async database support
- **FastAPI** for its exceptional web framework capabilities
- **Pydantic** for type-safe data validation
- **Redis** for high-performance caching and token management
- **PostgreSQL** for reliable, powerful relational storage
