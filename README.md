## Service 2 (Data Processing Service) - Port 8001
- **Purpose**: Processes user data and provides analytics
- **Features**:
  - Processes user data (calculates name length, email domain, age categories, etc.)
  - Provides analytics and statistics
  - Stores processed user data
  - Cross-service communication testing

## API Endpoints

- `GET /` - Service status
- `GET /health` - Health check
- `POST /process-user` - Process user data
- `GET /processed-users/{user_id}` - Get processed user data
- `GET /processed-users` - Get all processed users
- `DELETE /processed-users/{user_id}` - Delete processed user data
- `GET /analytics` - Get analytics summary
- `GET /cross-service-test` - Test communication with Service 1
- `POST /batch-process` - Process all users from Service 1

## Interactive API Documentation

http://localhost:8001/docs