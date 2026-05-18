# API Endpoints Reference

## Authentication & Users

| Endpoint              | Method | Action                                                  | Frontend Use Case                      |
| --------------------- | ------ | ------------------------------------------------------- | -------------------------------------- |
| `/auth/register`      | POST   | Register new user with username, email, password        | Sign up flow                           |
| `/auth/token`         | POST   | Login with credentials → returns access/refresh cookies | Sign in modal/login form               |
| `/auth/token/refresh` | POST   | Refresh expired access token using refresh cookie       | Auto-renew auth on background tab      |
| `/auth/logout`        | POST   | Logout user, blacklist token                            | Log out button/action                  |
| `/auth/users/me`      | GET    | Get current authenticated user data                     | Header dropdown/user menu profile card |

---

## User Profiles

| Endpoint                        | Method | Action                                              | Frontend Use Case                      |
| ------------------------------- | ------ | --------------------------------------------------- | -------------------------------------- |
| `/users/by-username/{username}` | GET    | Get full profile (posts, follower/following counts) | User profile page header + stats cards |
| `/users/by-id/{user_id}`        | GET    | Get basic user info                                 | Feed item author avatar display        |
| `/users`                        | GET    | List all users                                      | Browse/explore profiles grid view      |
| `/users/recommend`              | GET    | Get recommended users to follow                     | "Discover" / "Who to Follow" tab       |
| `/users/display-name`           | PATCH  | Update current user's display name                  | Profile settings form                  |

---

## Bios

| Endpoint                      | Method | Action                 | Frontend Use Case                 |
| ----------------------------- | ------ | ---------------------- | --------------------------------- |
| `/bio`                        | GET    | Get current user's bio | User profile "About" section      |
| `/bio/by-username/{username}` | GET    | Get another user's bio | Display on public profile page    |
| `/bio`                        | PATCH  | Update own bio         | Profile settings form             |
| `/bio/by-username/{username}` | PATCH  | Edit any user's bio    | Mod/admin tools or direct edit UI |

---

## Posts

| Endpoint                        | Method | Action                            | Frontend Use Case               |
| ------------------------------- | ------ | --------------------------------- | ------------------------------- |
| `/posts`                        | GET    | Get all posts (paginated)         | Feed default view (all posts)   |
| `/feed`                         | GET    | Get popular posts sorted by likes | "For You" / "Trending" feed tab |
| `/posts/by-username/{username}` | GET    | Get specific user's posts         | User profile "Posts" tab        |
| `/posts/by-user-id/{user_id}`   | GET    | Get posts by authenticated user   | Own posts management view       |
| `/post/{id}`                    | GET    | Get single post with comments     | Individual post detail page     |
| `/posts`                        | POST   | Create new post                   | New Post composer/button        |
| `/posts/{post_id}`              | DELETE | Delete own post                   | Delete post (owner-only) action |

---

## Likes

| Endpoint                  | Method | Action           | Frontend Use Case           |
| ------------------------- | ------ | ---------------- | --------------------------- |
| `/posts/{post_id}/like`   | POST   | Like a post      | Post heart button toggle    |
| `/posts/{post_id}/unlike` | DELETE | Unlike a post    | Remove like from post       |
| `/comments/{id}/like`     | POST   | Like a comment   | Comment heart button toggle |
| `/comments/{id}/unlike`   | DELETE | Unlike a comment | Remove like from comment    |

---

## Comments

| Endpoint                    | Method | Action                  | Frontend Use Case              |
| --------------------------- | ------ | ----------------------- | ------------------------------ |
| `/posts/{post_id}/comments` | POST   | Add comment to post     | Comment input + submit button  |
| `/posts/{id}/comments`      | GET    | Get comments on a post  | Post detail comments section   |
| `/comments`                 | GET    | Get all user's comments | Own activity / moderation view |
| `/comment/{id}`             | DELETE | Delete own comment      | Remove own comment action      |

---

## Follow System

| Endpoint              | Method | Action                        | Frontenr Use Case                          |
| --------------------- | ------ | ----------------------------- | ------------------------------------------ |
| `/user/{id}/follow`   | POST   | Follow a user                 | User profile "Follow" button               |
| `/user/{id}/unfollow` | DELETE | Unfollow a user               | User profile "Following → Unfollow" button |
| `/follows`            | GET    | Get following list            | View who I'm following page                |
| `/following`          | GET    | Get posts from followed users | "Following" feed tab                       |

---

## Quick Frontend Flow Guide

### Initial Load

1. Fetch current user: `GET /auth/users/me` → populate header dropdown
2. Fetch recommended users: `GET /users/recommend` → populate "Who to Follow"

### User Profile Page

1. Header: `GET /users/by-username/{username}` → display profile picture, name, bio, follower/following counts
2. Posts tab: `GET /posts/by-username/{username}?page=1&size=20`
3. Bio section: included in #1 response

### Feed Pages

1. For You (Trending): `GET /feed?page=1&size=20`
2. Following: `GET /following?page=1&size=20`
3. All Posts: `GET /posts?page=1&size=20`

### Post Detail Page

1. Content: `GET /post/{id}` → display title, content, like count, comment count
2. Comments section: included in #1 response
3. Author info: included in #1 response

### Create New Post (Composer)

1. Open compose screen
2. User types title + content
3. Click "Post" → `POST /posts` with body `{title, content}`
4. Redirect to feed or show success toast

### Like/Unlike Posts

1. Heart button click → toggle state
2. Optimistic UI: immediately update heart icon and count
3. Backend call: `POST /posts/{post_id}/like` or `DELETE /posts/{post_id}/unlike`

### Follow Button on Profile

1. Click "Follow" → optimistic UI change to "Following"
2. API call: `POST /user/{id}/follow`
3. On success, update header dropdown user count if needed

### Comments Section

1. Load comments on post detail: `GET /posts/{id}/comments`
2. New comment: `POST /posts/{post_id}/comments` with `{content}`
3. Like comment: `POST /comments/{id}/like`

---

## Notes for Frontend Developers

- **Pagination**: All list endpoints return paginated results (check response structure)
- **Authentication**: Most endpoints require valid JWT cookie in request headers
- **Image uploads**: Not currently supported (see planned features)
- **Like counts**: Stored in annotations, updated via separate like endpoints
- **Comments are loaded eagerly**: When fetching a post, comments array is included in response
- **Author data**: Included with every post/comment for easy avatar/name display
